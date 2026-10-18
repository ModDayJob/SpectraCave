"""Read-only FITS spectroscopy. Numerical evidence is separate from interpretation."""
from pathlib import Path
import hashlib, json, math, time
import numpy as np
from PIL import Image
VERSION='0.3.0-beta.1'
LIMITS={'max_pixels':40_000_000,'max_header_blocks':100}

def header(path):
    cards={}
    with open(path,'rb') as f:
        for _ in range(LIMITS['max_header_blocks']):
            block=f.read(2880)
            if len(block)!=2880: raise ValueError('Incomplete FITS header')
            for i in range(0,2880,80):
                s=block[i:i+80].decode('ascii')
                if s[:8].strip()=='END': return cards,f.tell()
                if s[8:10]=='= ':
                    value=s[10:].strip()
                    if value.startswith("'"):
                        end=value.find("'",1)
                        cards[s[:8].strip()]=value[1:end].strip()
                    else: cards[s[:8].strip()]=value.split('/')[0].strip()
    raise ValueError('FITS END card missing')

def read(path):
    h,off=header(path)
    if h.get('NAXIS')!='2': raise ValueError('Only two-dimensional primary FITS images supported')
    nx,ny=int(h['NAXIS1']),int(h['NAXIS2']);bit=int(h['BITPIX'])
    types={8:'u1',16:'>i2',32:'>i4',-32:'>f4',-64:'>f8'}
    if bit not in types or nx<2 or ny<2 or nx*ny>LIMITS['max_pixels']: raise ValueError('Unsupported image size or BITPIX')
    dtype=np.dtype(types[bit]);n=nx*ny
    if Path(path).stat().st_size<off+n*dtype.itemsize: raise ValueError('Incomplete FITS pixel data; file may still be copying')
    raw=np.fromfile(path,dtype=dtype,count=n,offset=off).reshape(ny,nx).astype(np.float32)
    a=raw*float(h.get('BSCALE',1))+float(h.get('BZERO',0))
    if not np.isfinite(a).all(): raise ValueError('Image contains nonfinite pixels')
    # A camera-specific ceiling is not universal. Only infer ASI585's 12-bit data mapped into 16 bits.
    ceiling=65520 if '585' in h.get('INSTRUME','') and bit==16 and float(h.get('BZERO',0))==32768 else (float(h.get('BZERO',0))+(2**(bit-1)-1)*float(h.get('BSCALE',1)) if bit>8 else (255.0 if bit==8 else None))
    return a,h,ceiling

def intensity(a,h):
    factor=2 if h.get('BAYERPAT') else 1
    if factor==2:
        ny,nx=a.shape;v=a[:ny//2*2,:nx//2*2].reshape(ny//2,2,nx//2,2).mean((1,3))
    else: v=a.copy()
    return v-np.median(v),factor

def sources(v,count=8):
    # Compact-source proposals, not catalog identities. Humans confirm zero orders.
    if min(v.shape)<20: return []
    ii=np.pad(np.cumsum(np.cumsum(v,0),1),((1,0),(1,0)))
    score=ii[9:,9:]-ii[:-9,9:]-ii[9:,:-9]+ii[:-9,:-9]
    answer=[];noise=max(float(np.median(np.abs(v-np.median(v)))*1.4826),1)
    for _ in range(count):
        y,x=np.unravel_index(np.argmax(score),score.shape);peak=float(score[y,x]);x+=4;y+=4
        if peak<noise*81*8: break
        answer.append({'x':int(x),'y':int(y),'score':peak})
        score[max(0,y-35):min(score.shape[0],y+35),max(0,x-35):min(score.shape[1],x+35)]=-np.inf
    return answer

def inventory(folder):
    if not isinstance(folder,str) or not folder.strip():raise ValueError('Enter the folder containing your FITS captures')
    root=Path(folder).expanduser()
    if not root.is_dir():
        pasted=folder.strip()
        if len(pasted)>1 and pasted[0]==pasted[-1] and pasted[0] in ('"', "'"):pasted=pasted[1:-1]
        root=Path(pasted.replace('\\ ', ' ')).expanduser()
    root=root.resolve()
    if not root.is_dir(): raise ValueError('Folder not found. Paste an existing folder path; spaces are allowed.')
    groups={};errors=[]
    for path in sorted(root.rglob('*')):
        if path.suffix.lower() not in ('.fit','.fits','.fts') or not path.is_file(): continue
        try:
            h,off=header(path)
            if h.get('NAXIS')!='2':raise ValueError('Only two-dimensional primary FITS captures are supported')
            nx,ny=int(h.get('NAXIS1',0)),int(h.get('NAXIS2',0))
            if nx<2 or ny<2 or nx*ny>LIMITS['max_pixels'] or int(h.get('BITPIX',0)) not in (8,16,32,-32,-64):raise ValueError('Unsupported capture dimensions or BITPIX')
            expected=off+int(h.get('NAXIS1',0))*int(h.get('NAXIS2',0))*abs(int(h.get('BITPIX',16)))//8
            if path.stat().st_size<expected: raise ValueError('Incomplete file')
            # Include focus, temperature, dimensions and pointing/filter settings; avoid silently mixing sessions.
            cfg={k:h.get(k,'') for k in ['OBJECT','FILTER','INSTRUME','EXPTIME','GAIN','XBINNING','YBINNING','FOCUSPOS','BAYERPAT','NAXIS1','NAXIS2','FOCALLEN','SET-TEMP','ROTATOR']}
            cfg['kind']='Preview' if path.name.lower().startswith('preview') else 'Light' if h.get('IMAGETYP','').lower().strip()=='light' or path.name.lower().startswith('light') else h.get('IMAGETYP','Unknown')
            key=hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()[:16]
            group=groups.setdefault(key,{'id':key,'settings':cfg,'files':[]});group['files'].append(str(path))
        except (ValueError,OSError,UnicodeError) as e: errors.append({'file':str(path),'error':str(e)})
    return {'root':str(root),'groups':list(groups.values()),'errors':errors}

def calibration(pairs):
    p=np.asarray(pairs,dtype=float)
    if p.ndim!=2 or p.shape[1]!=2 or len(p)<3 or not np.isfinite(p).all() or (p<=0).any(): raise ValueError('Provide at least three positive distance,wavelength pairs')
    if len(np.unique(p[:,0]))!=len(p): raise ValueError('Line distances must be distinct')
    scale=float(p[:,0]@p[:,1]/(p[:,0]@p[:,0]));res=p[:,0]*scale-p[:,1]
    return {'scale_nm_per_pixel':scale,'pairs':p.tolist(),'residual_nm':res.tolist(),'rms_nm':float(np.sqrt(np.mean(res**2))),'status':'provisional manual line assignment; not independently validated'}

def extract(a,h,ceiling,seed,slope=-0.08,direction=-1,near=60,window=(350,1100)):
    v,factor=intensity(a,h);sx,sy=[float(z)/factor for z in seed]
    # Track the selected source locally so a nearby brighter star cannot silently replace it.
    ix,iy=int(round(sx)),int(round(sy));rad=int(near/factor)
    y0,y1=max(4,iy-rad),min(v.shape[0]-4,iy+rad+1);x0,x1=max(4,ix-rad),min(v.shape[1]-4,ix+rad+1)
    if y0>=y1 or x0>=x1: raise ValueError('Selected star is outside frame')
    cut=v[y0:y1,x0:x1];j,i=np.unravel_index(np.argmax(cut),cut.shape);sx=x0+i;sy=y0+j
    # Windows are physical original sensor pixels, independent of Bayer processing.
    dist=np.arange(int(window[0]/factor),int(window[1]/factor)+1)
    x=sx+direction*dist;guess=sy+slope*dist
    valid=(x>=2)&(x<v.shape[1]-2)&(guess>=40)&(guess<v.shape[0]-40)
    dist,x,guess=dist[valid],x[valid],guess[valid]
    if len(x)<30: raise ValueError('Not enough room for the chosen spectrum range')
    ridge=np.array([int(y)-14+np.argmax(v[int(y)-14:int(y)+15,c]) for c,y in zip(x,guess)])
    coef=np.polyfit(dist,ridge,1);res=ridge-np.polyval(coef,dist);good=np.abs(res-np.median(res))<max(3,3*np.median(np.abs(res-np.median(res))))
    if good.sum()<20: raise ValueError('Unable to fit a stable trace')
    coef=np.polyfit(dist[good],ridge[good],1);ys=np.polyval(coef,dist)
    flux=[];peak=-np.inf;clipped=0;widths=[]
    for c,y in zip(x,ys):
        j=int(round(y))
        if j<34 or j+34>=v.shape[0]: raise ValueError('Trace crosses image edge')
        bg=np.median(np.r_[v[j-32:j-22,c],v[j+23:j+33,c]]);col=v[j-12:j+13,c]-bg
        flux.append(col.sum());raw=a[(j-12)*factor:(j+13)*factor,c*factor:(c+1)*factor];peak=max(peak,float(raw.max()))
        if ceiling is not None:clipped+=int(np.sum(raw>=ceiling))
        ids=np.where(col>=max(col.max()/2,1))[0]
        if len(ids):widths.append(float((ids[-1]-ids[0]+1)*factor))
    return np.c_[dist*factor,flux],{'zero_order':[int(sx*factor),int(sy*factor)],'spectral_peak':peak,'clipped_pixels':clipped,'ceiling':ceiling,'trace_slope':float(coef[0]),'ridge_scatter_pixels':float(np.std((ridge-np.polyval(coef,dist))[good])*factor),'cross_trace_width_pixels':float(np.median(widths)) if widths else None,'bayer_factor':factor}

def analyze(files,out,seed,options,progress=lambda s:None):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);profiles=[];checks=[];rejected=[];tracked=seed;common=np.arange(int(options['min_distance']),int(options['max_distance'])+1,2,dtype=float)
    for i,path in enumerate(files):
        progress(f'Exposure {i+1} of {len(files)}')
        try:
            a,h,ceiling=read(path);p,check=extract(a,h,ceiling,tracked,slope=float(options.get('slope',-.08)),direction=int(options.get('direction',-1)),window=(options['min_distance'],options['max_distance']))
            tracked=check['zero_order'];check['file']=Path(path).name;checks.append(check)
            if check['clipped_pixels']:rejected.append({'file':Path(path).name,'reason':'clipped spectrum'});continue
            if p[0,0]>common[0] or p[-1,0]<common[-1]: raise ValueError('Incomplete requested spectral coverage')
            exposure=float(h.get('EXPTIME',h.get('EXPOSURE',0)))
            if exposure<=0: raise ValueError('Missing positive exposure time')
            profiles.append(np.interp(common,p[:,0],p[:,1])/exposure)
        except (ValueError,OSError,KeyError) as e: rejected.append({'file':Path(path).name,'reason':str(e)})
    if not profiles: raise ValueError('No usable exposures. Check star selection, trace direction/range, and clipping.')
    arr=np.array(profiles);full=np.median(arr,0);odd=np.median(arr[::2],0);even=np.median(arr[1::2],0) if len(arr)>1 else None
    scale=options.get('scale');axis=common*float(scale) if scale else common
    result={'version':VERSION,'used_frames':len(arr),'input_frames':len(files),'rejected':rejected,'checks':checks,'settings':options,'axis':'approximate wavelength (nm)' if scale else 'distance from zero order (pixels)','response_corrected':False,'chemical_identifications':[],'calibration_status':'provisional transferred scale' if scale else 'uncalibrated','repeatability_correlation':float(np.corrcoef(odd,even)[0,1]) if even is not None and np.std(odd)>0 and np.std(even)>0 else None,'limitations':['Source selection is user-confirmed, not independently catalog matched.','Trace overlap may contaminate the aperture.','No dark, flat, atmospheric or instrument-response correction.','Repeatability does not establish chemical identity.','No abundance, temperature, or radial velocity is fitted.']}
    np.savetxt(out/'spectrum.csv',np.c_[axis,full,odd,even if even is not None else np.full(len(axis),np.nan)],delimiter=',',header='axis,signal_per_second,odd_frames,even_frames',comments='')
    np.save(out/'individual-profiles.npy',arr)
    (out/'evidence.json').write_text(json.dumps(result,indent=2,allow_nan=False))
    chart={'axis':axis.tolist(),'full':full.tolist(),'odd':odd.tolist(),'even':even.tolist() if even is not None else None,'label':result['axis']}
    (out/'chart.json').write_text(json.dumps(chart,allow_nan=False))
    text=f"Used {len(arr)} of {len(files)} frames. Calibration: {result['calibration_status']}. No element or molecule is automatically confirmed.\n\n"+'\n'.join(result['limitations'])
    (out/'findings.txt').write_text(text)
    return result,chart
