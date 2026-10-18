import io,json,tempfile,unittest,os
from pathlib import Path
from unittest.mock import patch
import app,engine,calibration

class ReleaseSafetyTests(unittest.TestCase):
    def test_pasted_paths_and_literal_backslash(self):
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)/'capture folder';folder.mkdir()
            for value in (str(folder),str(folder).replace(' ',r'\ '),'"'+str(folder)+'"'):
                self.assertEqual(engine.inventory(value)['root'],str(folder.resolve()))
            if os.name!='nt':
                literal=Path(temp)/r'literal\ folder';literal.mkdir()
                self.assertEqual(engine.inventory(str(literal))['root'],str(literal.resolve()))
    def test_missing_folder_and_blank_calibration(self):
        with self.assertRaisesRegex(ValueError,'Enter the folder'):engine.inventory('')
        with self.assertRaisesRegex(ValueError,'Line 1: enter both'):calibration.fit([{'distance':'','wavelength':486}])
    def request(self,payload,length=None,token=None):
        h=app.Handler.__new__(app.Handler);body=json.dumps(payload).encode();h.path='/api/scan';h.headers={'Content-Length':str(len(body) if length is None else length),'X-Stellar-Token':app.TOKEN if token is None else token};h.rfile=io.BytesIO(body);h.safe_host=lambda:True;out=[];h.send_json=lambda obj,code=200:out.append((code,obj));h.do_POST();return out[0]
    def test_invalid_requests_and_missing_token(self):
        self.assertEqual(self.request([],token='invalid')[0],403)
        for payload in ([],None,4):self.assertEqual(self.request(payload)[0],400)
        self.assertEqual(self.request({},length=-1)[0],400)
        self.assertEqual(self.request({},length=1000001)[0],400)

if __name__=='__main__':unittest.main()
