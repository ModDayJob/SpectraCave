import sys,unittest,copy,json
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import calibration
class CalibrationTests(unittest.TestCase):
    def rows(self):return [{'id':str(i),'distance':d,'wavelength':d*.5,'role':'fit'} for i,d in enumerate([800,1000,1200])]
    def source(self):
        x=np.arange(700,1401,2,dtype=float);y=100+np.sin(x/100)
        return {'id':'parent','result':{'settings':{'scale':.4,'offset_nm':5},'response_corrected':False,'limitations':['No dark, flat, atmospheric or instrument-response correction.'],'checks':[],'rejected':[]},'chart':{'axis':(x*.4+5).tolist(),'full':y.tolist(),'odd':y.tolist(),'even':(y*1.01).tolist()}}
    def test_origin_and_holdout_exclusion(self):
        rows=self.rows()+[{'distance':1400,'wavelength':703,'role':'check'},{'distance':1400,'wavelength':999,'role':'exclude'}]
        f=calibration.fit(rows);self.assertAlmostEqual(f['scale_nm_per_pixel'],.5);self.assertAlmostEqual(f['max_check_error_nm'],3);self.assertEqual(f['fit_count'],3);self.assertEqual(len(f['leave_one_out']),3);self.assertEqual(f['degrees_of_freedom'],2)
    def test_affine_and_no_auto_validation(self):
        rows=self.rows()
        for r in rows:r['wavelength']+=12
        f=calibration.fit(rows,'affine');self.assertAlmostEqual(f['offset_nm'],12);self.assertAlmostEqual(f['scale_nm_per_pixel'],.5);self.assertIn('provisional',f['status'])
    def test_bad_assignments(self):
        for rows in [self.rows()[:2],self.rows()+[{'distance':float('nan'),'wavelength':500}],self.rows()+[self.rows()[0]]]:
            with self.assertRaises(ValueError):calibration.fit(rows)
        rows=self.rows()
        for r in rows:r['wavelength']=1000-r['distance']*.5
        with self.assertRaises(ValueError):calibration.fit(rows)
    def test_derive_preserves_parent_and_inverse_old_axis(self):
        src=self.source();before=copy.deepcopy(src);f=calibration.fit(self.rows());f['id']='record'
        r,c=calibration.derive(src,f);self.assertEqual(src,before);self.assertAlmostEqual(c['axis'][0],350);self.assertEqual(c['full'],src['chart']['full']);self.assertEqual(r['chemical_identifications'],[]);self.assertGreater(r['calibration_diagnostics']['extrapolated_samples'],0);json.dumps(r,allow_nan=False)
    def test_response_no_extrapolation_and_relative_flux(self):
        src=self.source();f=calibration.fit(self.rows());response={'points':[[400,2],[500,2],[600,2]],'source':'synthetic constant response'}
        r,c=calibration.derive(src,f,response);self.assertTrue(r['response_corrected']);self.assertAlmostEqual(c['axis'][0],400);self.assertAlmostEqual(c['axis'][-1],600);self.assertEqual(len(c['full']),201);self.assertFalse(r['provenance']['response']['validated'])
        derived={'id':'corrected','result':r,'chart':c}
        with self.assertRaises(ValueError):calibration.derive(derived,f,response)
    def test_bad_response(self):
        for points in [[[400,1],[400,2],[500,1]],[[400,0],[500,1],[600,1]],[[2000,1],[2100,1],[2200,1]]]:
            with self.assertRaises(ValueError):calibration.derive(self.source(),calibration.fit(self.rows()),{'points':points,'source':'test'})
        with self.assertRaises(ValueError):calibration.derive(self.source(),calibration.fit(self.rows()),{'points':[[400,1],[500,1],[600,1]],'source':''})
if __name__=='__main__':unittest.main()
