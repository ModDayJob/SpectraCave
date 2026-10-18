"""Calibration records and derived spectra. Never modifies source evidence."""
import copy,hashlib,json,datetime
import numpy as np

def fit(rows,model='origin'):
    if model not in ('origin','affine'):raise ValueError('Unknown wavelength model')
    if not isinstance(rows,list) or len(rows)>100:raise ValueError('Provide at most 100 line assignments')
    clean=[]
    for i,r in enumerate(rows):
        try:d,w=float(r['distance']),float(r['wavelength'])
        except (ValueError,TypeError,KeyError):raise ValueError(f'Line {i+1}: enter both a measured pixel distance and a laboratory wavelength') from None
        role=r.get('role','fit')
        if role not in ('fit','check','exclude'):raise ValueError('Invalid assignment role')
        if not np.isfinite([d,w]).all() or d<=0 or w<=0:raise ValueError('Distances and wavelengths must be finite and positive')
        clean.append({'id':str(r.get('id',i))[:80],'name':str(r.get('name','Manual line'))[:100],'distance':d,'wavelength':w,'role':role,'reference_source':str(r.get('reference_source','Observer-assigned; no external source supplied'))[:500],'identity_verified':False})
    train=[r for r in clean if r['role']=='fit'];n=len(train);parameters=1 if model=='origin' else 2
    if n<3:raise ValueError('At least three fit lines are required; check lines are not used in the fit')
    x=np.array([r['distance'] for r in train]);y=np.array([r['wavelength'] for r in train])
    if len(np.unique(x))!=len(x) or len(np.unique(y))!=len(y):raise ValueError('Fit lines must have distinct distances and wavelengths')
    if np.any(np.diff(y[np.argsort(x)])<=0):raise ValueError('Assigned wavelengths must increase with distance from the white star')
    X=np.c_[x/1000,np.ones(n)] if model=='affine' else (x/1000)[:,None]
    if np.linalg.matrix_rank(X)<parameters:raise ValueError('Degenerate line assignments')
    coeff=np.linalg.lstsq(X,y,rcond=None)[0];scale=float(coeff[0]/1000);offset=float(coeff[1]) if model=='affine' else 0.
    if scale<=0:raise ValueError('Distances must increase with wavelength; fitted dispersion is not positive')
    for r in clean:r.update(predicted_nm=scale*r['distance']+offset,residual_nm=scale*r['distance']+offset-r['wavelength'])
    residual=np.array([r['residual_nm'] for r in clean if r['role']=='fit']);checks=[r for r in clean if r['role']=='check']
    loo=[]
    for i,r in enumerate(train):
        keep=np.arange(n)!=i;c=np.linalg.lstsq(X[keep],y[keep],rcond=None)[0]
        if np.linalg.matrix_rank(X[keep])<parameters:continue
        loo.append({'id':r['id'],'predicted_minus_reference_nm':float(X[i]@c-y[i])})
    warnings=['Manual line identities are not independently verified.','Fit residuals and leave-one-out errors are not absolute wavelength accuracy.','Reference-to-target transfer may depend on detector position, focus and optical geometry.']
    if any('region' in r['name'].lower() for r in train):warnings.append('A blended-region assignment is included: its listed center is not an exact isolated laboratory line centroid.')
    if not checks:warnings.append('No held-out line check supplied.')
    if model=='affine':warnings.append('Free intercept: zero distance need not map to zero wavelength; do not interpret this as a grating geometry model.')
    if np.ptp(x)<100:warnings.append('Fit lines span fewer than 100 original pixels; extrapolation may be unstable.')
    return {'schema_version':1,'model':model,'scale_nm_per_pixel':scale,'offset_nm':offset,'lines':clean,'fit_count':n,'check_count':len(checks),'rms_nm':float(np.sqrt(np.mean(residual**2))),'max_fit_error_nm':float(np.max(np.abs(residual))),'max_check_error_nm':max((abs(r['residual_nm']) for r in checks),default=None),'leave_one_out':loo,'fit_interval_pixels':[float(x.min()),float(x.max())],'condition_number_scaled':float(np.linalg.cond(X)),'degrees_of_freedom':n-parameters,'weighting':'unweighted; no per-line centroid uncertainties supplied','status':'provisional manual calibration','warnings':warnings}

def distances(result,chart):
    oldscale=result['settings'].get('scale');x=np.asarray(chart['axis'],float)
    if oldscale:
        return (x-float(result['settings'].get('offset_nm',0)))/float(oldscale)
    return x

def digest(chart):return hashlib.sha256(json.dumps(chart,sort_keys=True,allow_nan=False).encode()).hexdigest()

def derive(source,record,response=None):
    """Return a new evidence/chart pair; source remains bit-for-bit untouched."""
    if source['result'].get('response_corrected'):raise ValueError('Start from an uncorrected extraction to avoid recalibrating or correcting response-weighted flux twice')
    result=copy.deepcopy(source['result']);chart=copy.deepcopy(source['chart']);d=distances(result,chart)
    scale=float(record['scale_nm_per_pixel']);offset=float(record.get('offset_nm',0));w=d*scale+offset
    if not np.isfinite(w).all() or np.any(w<=0) or np.any(np.diff(w)<=0):raise ValueError('Calibration yields invalid wavelengths over this spectrum')
    result['settings'].update(scale=scale,offset_nm=offset,calibration_id=record.get('id'))
    result.update(axis='approximate wavelength (nm)',calibration_status='provisional saved wavelength calibration',chemical_identifications=[])
    result['provenance']={'parent_job':source['id'],'parent_chart_sha256':digest(source['chart']),'calibration_id':record.get('id'),'reference_job':record.get('reference',{}).get('job_id'),'applied_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
    chart.update(axis=w.tolist(),label=result['axis'])
    lo,hi=record['fit_interval_pixels'];outside=int(np.sum((d<lo)|(d>hi)))
    result['calibration_diagnostics']={'extrapolated_samples':outside,'total_samples':len(d),'rms_fit_nm':record['rms_nm'],'max_held_out_error_nm':record.get('max_check_error_nm'),'status':'not independently validated'}
    if outside:result['limitations'].append(f'{outside} wavelength samples lie outside the reference fit interval.')
    if response is not None:
        curve=np.asarray(response['points'],float)
        if curve.ndim!=2 or curve.shape[1]!=2 or len(curve)<3 or len(curve)>50000 or not np.isfinite(curve).all() or (curve<=0).any() or (np.diff(curve[:,0])<=0).any():raise ValueError('Response requires at least three strictly increasing positive wavelength,sensitivity pairs')
        if not str(response.get('source','')).strip():raise ValueError('Provide the response-curve source and how it was obtained')
        mask=(w>=curve[0,0]-1e-9)&(w<=curve[-1,0]+1e-9)
        if mask.sum()<20:raise ValueError('Response curve overlaps fewer than 20 spectral samples')
        sensitivity=np.interp(w[mask],curve[:,0],curve[:,1]);sensitivity/=np.median(sensitivity)
        if not np.isfinite(sensitivity).all() or np.any(sensitivity<=0):raise ValueError('Response sensitivity is numerically unstable')
        for key in ['full','odd','even']:
            if chart.get(key) is not None:
                corrected=np.asarray(chart[key])[mask]/sensitivity
                if not np.isfinite(corrected).all():raise ValueError('Response correction produces nonfinite flux')
                chart[key]=corrected.tolist()
        chart['axis']=np.clip(w[mask],curve[0,0],curve[-1,0]).tolist();result['response_corrected']=True;result['provenance']['response']={'source':str(response['source'])[:1000],'curve_sha256':hashlib.sha256(curve.tobytes()).hexdigest(),'normalization':'median sensitivity over covered target samples','coverage_nm':[float(curve[0,0]),float(curve[-1,0])],'cropped_samples':int((~mask).sum()),'validated':False,'saved_curve_file':'response-curve.json'}
        result['limitations']=[s for s in result['limitations'] if s!='No dark, flat, atmospheric or instrument-response correction.']
        result['limitations']+=['User-supplied relative response curve applied; source and applicability not independently verified.','No dark, flat or independent atmospheric correction. Relative flux is not absolute flux.']
    if chart.get('even') is not None:
        odd=np.asarray(chart['odd']);even=np.asarray(chart['even']);result['repeatability_correlation']=float(np.corrcoef(odd,even)[0,1]) if np.std(odd)>0 and np.std(even)>0 else None
    return result,chart
