import sys,unittest,tempfile
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import engine

def fits(path,a,extra=None):
    h={'SIMPLE':'T','BITPIX':'16','NAXIS':'2','NAXIS1':str(a.shape[1]),'NAXIS2':str(a.shape[0]),'BZERO':'32768','BSCALE':'1',**(extra or {})}
    cards=''.join((f'{k:<8}= {v}').ljust(80) for k,v in h.items())+'END'.ljust(80);cards=cards.ljust((len(cards)+2879)//2880*2880)
    path.write_bytes(cards.encode()+((a.astype(np.int32)-32768).astype('>i2')).tobytes())

class EngineTests(unittest.TestCase):
    def test_fits_unsigned_and_incomplete(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.fit';a=np.arange(100,dtype=np.uint16).reshape(10,10)+32000;fits(p,a);b,h,c=engine.read(p);np.testing.assert_array_equal(a,b)
            p.write_bytes(p.read_bytes()[:-10])
            with self.assertRaisesRegex(ValueError,'Incomplete'):engine.read(p)
            p.write_bytes(b'')
            with self.assertRaisesRegex(ValueError,'Incomplete'):engine.header(p)
    def test_calibration_and_bad_pairs(self):
        c=engine.calibration([[800,400],[1000,500],[1200,600]]);self.assertAlmostEqual(c['scale_nm_per_pixel'],.5);self.assertAlmostEqual(c['rms_nm'],0)
        with self.assertRaises(ValueError):engine.calibration([[1,2],[1,3],[2,4]])
    def test_color_cell_average(self):
        a=np.arange(48).reshape(6,8);v,f=engine.intensity(a,{'BAYERPAT':'RGGB'});self.assertEqual(f,2);self.assertEqual(v.shape,(3,4));self.assertAlmostEqual(v[0,1]-v[0,0],2)
    def test_extract_shift_and_clipping(self):
        yy,xx=np.indices((700,1400))
        def make(sx,sy,peak):
            dist=sx-xx;trace=sy-.08*dist;a=np.ones((700,1400))*1200;a+=peak*np.exp(-.5*((yy-trace)/2)**2)*((dist>=100)&(dist<=500));a+=60000*np.exp(-((xx-sx)**2+(yy-sy)**2)/8);return np.minimum(a,65520)
        p,c=engine.extract(make(1100,400,10000),{},65520,[1100,400],window=(100,500));q,d=engine.extract(make(1110,405,10000),{},65520,[1100,400],window=(100,500));np.testing.assert_allclose(p[:,1],q[:,1],rtol=.02);self.assertEqual(c['clipped_pixels'],0)
        _,c=engine.extract(make(1100,400,90000),{},65520,[1100,400],window=(100,500));self.assertGreater(c['clipped_pixels'],0)
    def test_successful_batch_serializes(self):
        yy,xx=np.indices((700,1400));dist=1100-xx
        a=1200+10000*np.exp(-.5*((yy-(400-.08*dist))/2)**2)*((dist>=100)&(dist<=500))+60000*np.exp(-((xx-1100)**2+(yy-400)**2)/8)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.fit';fits(p,a,{'INSTRUME':"'ZWO ASI585MC Pro'",'EXPTIME':'1.'})
            result,chart=engine.analyze([str(p)],Path(d)/'out',[1100,400],{'min_distance':100,'max_distance':500})
            self.assertEqual(result['used_frames'],1);self.assertIsNone(result['repeatability_correlation']);self.assertTrue((Path(d)/'out/evidence.json').exists())
    def test_batch_rejects_clipped(self):
        yy,xx=np.indices((700,1400));a=np.ones((700,1400))*1200;dist=1100-xx;trace=400-.08*dist;a+=90000*np.exp(-.5*((yy-trace)/2)**2)*((dist>=100)&(dist<=500));a+=60000*np.exp(-((xx-1100)**2+(yy-400)**2)/8);a=np.minimum(a,65520)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a.fit';fits(p,a,{'INSTRUME':"'ZWO ASI585MC Pro'",'EXPTIME':'1.'})
            with self.assertRaisesRegex(ValueError,'No usable'):engine.analyze([str(p)],Path(d)/'out',[1100,400],{'min_distance':100,'max_distance':500})
if __name__=='__main__':unittest.main()
