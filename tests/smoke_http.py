"""Exercise a real local HTTP server and extraction with synthetic FITS only."""
import copy,hashlib,json,sys,tempfile,threading,time,urllib.request,urllib.error
from pathlib import Path
from unittest.mock import patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
from test_engine import fits

def main():
 with tempfile.TemporaryDirectory() as temp:
  base=Path(temp).resolve();captures=base/'capture folder';captures.mkdir();(base/'static').mkdir();(base/'static/index.html').write_text('Synthetic test')
  yy,xx=np.indices((700,1400));dist=1100-xx
  data=1200+10000*np.exp(-.5*((yy-(400-.08*dist))/2)**2)*((dist>=100)&(dist<=500))+60000*np.exp(-((xx-1100)**2+(yy-400)**2)/8)
  for i in range(2):fits(captures/f'Light_{i}.fit',data,{'OBJECT':"'Synthetic star'",'INSTRUME':"'ZWO ASI585MC'",'EXPTIME':'1.'})
  originals={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in captures.iterdir()}
  with patch.object(app,'BASE',base),patch.object(app,'DEFAULT',str(captures)),patch.dict(app.JOBS,{},clear=True):
   app.restore_results();server=app.ThreadingHTTPServer(('127.0.0.1',0),app.Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url=f'http://127.0.0.1:{server.server_port}'
   def call(path,data=None,auth=True,host=None):
    headers={'X-Stellar-Token':app.TOKEN} if auth else {}
    if host:headers['Host']=host
    req=urllib.request.Request(url+path,data=json.dumps(data).encode() if data is not None else None,headers=headers)
    try:
     with urllib.request.urlopen(req,timeout=10) as r:return r.status,json.load(r)
    except urllib.error.HTTPError as e:return e.code,json.load(e)
   try:
    assert call('/api/state')[0]==200
    assert call('/api/state',host='untrusted.invalid')[0]==403
    assert call('/api/scan',{'folder':str(captures)},auth=False)[0]==403
    code,inv=call('/api/scan',{'folder':str(captures).replace(' ',r'\ ')});assert code==200 and len(inv['groups'])==1
    group=inv['groups'][0]['id'];assert call('/api/preview',{'group':group})[0]==200
    code,created=call('/api/analyze',{'group':group,'label':'Synthetic target','x':1100,'y':400,'min_distance':100,'max_distance':500,'direction':-1,'slope':-.08,'scale':''});assert code==200
    ident=created['id']
    for _ in range(100):
     job=call('/api/state')[1]['jobs'][ident]
     if job['state']!='running':break
     time.sleep(.05)
    assert job['state']=='done',job
    assert job['result']['used_frames']==2 and not job['result']['settings']['scale']
    parent=copy.deepcopy(job)
    q={'reference_job':ident,'name':'Synthetic calibration','model':'origin','rows':[{'distance':d,'wavelength':d*.5} for d in (100,250,500)]}
    code,record=call('/api/calibration/save',q);assert code==200
    code,derived=call('/api/calibration/apply',{'calibration_id':record['id'],'target_job':ident,'confirm_transfer':True});assert code==200
    state=call('/api/state')[1];assert state['jobs'][ident]==parent and state['jobs'][derived['id']]['result']['chemical_identifications']==[]
    with urllib.request.urlopen(url+'/results/'+derived['id']+'/spectrum.csv') as r:assert b'approx_wavelength_nm' in r.read()
    assert originals=={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in captures.iterdir()}
    print('HTTP smoke passed: host/token checks, escaped path, preview, extraction, saved calibration, derived copy, export, originals preserved.')
   finally:server.shutdown();server.server_close();thread.join(timeout=5)
if __name__=='__main__':main()
