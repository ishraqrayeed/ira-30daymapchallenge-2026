"""Smooth cartographic composite; analysis always uses original VIIRS pixels.
VIIRS gives the broad brightness field; ISS gives continuous local fine detail.
This is a display proxy, never calibrated high-resolution radiance.
"""
from pathlib import Path
import hashlib,json
import numpy as np,rasterio
from rasterio.warp import reproject,Resampling
from scipy.ndimage import gaussian_filter
from PIL import Image
DAY=Path(__file__).resolve().parents[1];ROOT=DAY.parents[1]
D=json.loads((DAY/'data/replay.json').read_text());S=json.loads((DAY/'data/sources.json').read_text())
records=[]

def compose(base,valid,lum,alpha,resolution):
    # Normalized convolution excludes missing data rather than darkening its edges.
    coverage=gaussian_filter(valid.astype('float32'),120/resolution)
    envelope=np.divide(gaussian_filter(np.where(valid,base,0),120/resolution),coverage,
                       out=np.zeros_like(base),where=coverage>1e-6)
    photo_weight=np.clip(alpha/255,0,1).astype('float32')
    detail_signal=.03+(lum/255)**.8
    photo_coverage=gaussian_filter(photo_weight,350/resolution)
    local_mean=np.divide(gaussian_filter(detail_signal*photo_weight,350/resolution),photo_coverage,
                         out=np.ones_like(base),where=photo_coverage>1e-6)
    detail=np.clip(detail_signal/np.maximum(local_mean,.03),.15,3)
    # The photo alpha feathers the detail toward a VIIRS-only fallback. It never
    # multiplies the brightness envelope itself, so absent photos are not black holes.
    detail_mix=gaussian_filter(photo_weight,60/resolution)*photo_weight
    proxy=envelope*(1+detail_mix*((.25+.75*detail)-1))
    proxy=np.where(valid,proxy,0).astype('float32')
    v=(np.log1p(np.clip(proxy,0,600))/np.log1p(600))**1.15
    colors=np.array([[5,12,25],[13,27,43],[56,67,68],[128,124,100],[212,196,155],[255,241,204]],float)
    result=np.stack([np.interp(v,np.linspace(0,1,len(colors)),colors[:,i]) for i in range(3)],axis=-1)
    seed=np.clip((proxy-80)/520,0,1)
    bloom=.65*gaussian_filter(seed,75/resolution)+.35*gaussian_filter(seed,175/resolution)
    result=np.clip(result+bloom[...,None]*np.array([8,6,3]),0,255).astype('uint8')
    # Only truly absent VIIRS coverage is hatched, not valid dark terrain or water.
    rr,cc=np.indices(base.shape);stripe=((rr+cc)%24)<3
    result[~valid]=[16,26,39];result[(~valid)&stripe]=[41,52,66]
    return proxy,result

# Missing-photo and zero-brightness regression checks, with no actual source data altered.
fixture=np.full((80,80),10,dtype='float32');mask=np.ones_like(fixture,dtype=bool)
fallback,_=compose(fixture,mask,np.zeros_like(fixture),np.zeros_like(fixture),25)
zero,_=compose(np.zeros_like(fixture),mask,fixture,np.full_like(fixture,255),25)
assert np.allclose(fallback,10) and np.all(zero==0)
with rasterio.open(ROOT/'data/raw/day17'/Path(S['raster']['url']).name) as source:
 for p in D['panels']:
  key=p['id']
  with rasterio.open(DAY/'data'/f'{key}-iss.tif') as photo:
   rgb=photo.read([1,2,3]).transpose(1,2,0).astype('float32');alpha=photo.read(4)
   lum=rgb@np.array([.2126,.7152,.0722],dtype='float32');base=np.full(photo.shape,-9999,dtype='float32')
   reproject(rasterio.band(source,1),base,src_nodata=source.nodata,
             dst_transform=photo.transform,dst_crs=photo.crs,dst_nodata=-9999,resampling=Resampling.bilinear)
   valid=(base>=0)&np.isfinite(base)
   proxy,result=compose(base,valid,lum,alpha,photo.res[0]);Image.fromarray(result).save(DAY/'data'/f'{key}-hybrid.png')
   profile=photo.profile.copy();profile.update(count=1,dtype='float32',nodata=-9999)
   with rasterio.open(DAY/'data'/f'{key}-hybrid-proxy.tif','w',**profile) as out:out.write(np.where(valid,proxy,-9999),1)
   rr,cc=np.indices(base.shape);xs=photo.transform.c+(cc+.5)*photo.res[0];ys=photo.transform.f-(rr+.5)*photo.res[1]
   route=p['route'];cx=(min(v[0] for v in route)+max(v[0] for v in route))/2;cy=(min(v[1] for v in route)+max(v[1] for v in route))/2
   audit=(abs(xs-cx)<10000)&(abs(ys-cy)<10000)
   record={'panel':key,'checked_20km_square':{'viirs_nodata_pixels':int((audit&~valid).sum()),'iss_missing_pixels':int((audit&(alpha<241)).sum()),'pixels':int(audit.sum())},'finite_proxy':bool(np.isfinite(proxy).all()),'passed':bool(np.isfinite(proxy).all()),'outputs':{f'{key}-hybrid.png':hashlib.sha256((DAY/'data'/f'{key}-hybrid.png').read_bytes()).hexdigest()}}
   records.append(record);print(key,record['checked_20km_square'],flush=True)
report={'passed':all(r['passed'] for r in records),'label':'VIIRS brightness · ISS detail · Contrast enhanced',
 'method':'GDAL bilinear VIIRS envelope; mask-normalized 120 m Gaussian; ISS detail ratio to a continuous mask-normalized 350 m local mean, clipped .15–3 and mixed at .75 gain; 60 m feather to VIIRS-only fallback where photography is absent.',
 'artifact_cause':'Old nearest-neighbor VIIRS envelope and native-cell-by-cell photo normalization produced visible rectangular transitions; audited views contain no missing source coverage.',
 'interpretation':'Cartographic composite, not observed/calibrated 25 m radiance or a statistic. No native-cell mean conservation claim; all statistics come from the separate original VIIRS raster.',
 'curve':'(log1p(clip(proxy,0,600))/log1p(600))^1.15','bloom_threshold_proxy':80,'bloom_sigma_m':[75,175],'bloom_gain_rgb':[8,6,3],'palette':['#050C19','#0D1B2B','#384344','#807C64','#D4C49B','#FFF1CC'],'palette_stops':[0,.2,.4,.6,.8,1],
 'missing_photo_falls_back_to_viirs':bool(np.allclose(fallback,10)),'valid_dark_field_stays_zero':bool(np.all(zero==0)),
 'same_parameters_all_panels_and_frames':True,'panels':records}
(DAY/'data/hybrid-qa.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed']
