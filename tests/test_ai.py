import sys,unittest,json,io
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
class AITests(unittest.TestCase):
    def setUp(self):
        self.result={'checks':[{'file':'private-name.fit','spectral_peak':1234}],'rejected':[{'file':'private.fit','reason':'clipped'}],'calibration_status':'uncalibrated','chemical_identifications':[]}
        self.chart={'axis':[1,2,3],'full':[4,5,6]}
    def test_prompt_omits_names_and_preserves_limits(self):
        p=app.evidence_prompt(self.result,self.chart);self.assertNotIn('private',p);self.assertIn('uncalibrated',p);self.assertIn('not three human experts',p)
    def test_no_key_failure(self):
        with patch.dict(app.os.environ,{},clear=True):
            with self.assertRaisesRegex(ValueError,'OPENAI_API_KEY'):app.ai_review(self.result,self.chart,'example-model')
    def test_responses_payload_and_parse(self):
        def reply(req,timeout):
            body=json.loads(req.data);self.assertEqual(body['model'],'example-model');self.assertFalse(body['store']);self.assertNotIn('private',body['input']);self.assertEqual(req.full_url,'https://api.openai.com/v1/responses')
            return io.BytesIO(json.dumps({'output':[{'type':'message','content':[{'type':'output_text','text':'Calibration insufficient.'}]}]}).encode())
        with patch.dict(app.os.environ,{'OPENAI_API_KEY':'test-only-dummy'}),patch('app.urllib.request.urlopen',reply):self.assertEqual(app.ai_review(self.result,self.chart,'example-model'),'Calibration insufficient.')
if __name__=='__main__':unittest.main()
