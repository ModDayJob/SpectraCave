import sys,unittest,tempfile,json,io,copy
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
import test_calibration
class RouteTests(unittest.TestCase):
    def send(self,path,payload):
        h=app.Handler.__new__(app.Handler);body=json.dumps(payload).encode();h.path=path;h.headers={'Content-Length':str(len(body)),'X-Stellar-Token':app.TOKEN};h.rfile=io.BytesIO(body);h.safe_host=lambda:True;response=[];h.send_json=lambda obj,code=200:response.append((code,obj));h.do_POST();return response[0]
    def test_save_apply_preserves_reference(self):
        source=test_calibration.CalibrationTests().source();source.update(state='done',label='Synthetic reference');before=copy.deepcopy(source)
        with tempfile.TemporaryDirectory() as tmp,patch.object(app,'BASE',Path(tmp)),patch.dict(app.JOBS,{'parent':source},clear=True):
            q={'reference_job':'parent','rows':test_calibration.CalibrationTests().rows()+[{'distance':1300,'wavelength':651,'role':'check'}],'model':'origin'}
            code,fit=self.send('/api/calibration/fit',q);self.assertEqual(code,200);self.assertEqual(fit['fit_count'],3);self.assertEqual(fit['check_count'],1)
            code,record=self.send('/api/calibration/save',{**q,'name':'Synthetic test record'});self.assertEqual(code,200);self.assertTrue((Path(tmp)/'results/calibrations'/f"{record['id']}.json").exists())
            code,error=self.send('/api/calibration/apply',{'calibration_id':record['id'],'target_job':'parent','confirm_transfer':False});self.assertEqual(code,400)
            code,result=self.send('/api/calibration/apply',{'calibration_id':record['id'],'target_job':'parent','confirm_transfer':True});self.assertEqual(code,200);self.assertEqual(app.JOBS['parent'],before);self.assertIn(result['id'],app.JOBS);self.assertEqual(app.JOBS[result['id']]['result']['chemical_identifications'],[]);self.assertTrue((Path(tmp)/'results'/result['id']/'spectrum.csv').exists())
if __name__=='__main__':unittest.main()
