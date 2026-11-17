"""Independent distance, timing, raster alignment and native-pixel sampling checks."""
import hashlib,json,math
from pathlib import Path
import numpy as np
import rasterio
from pyproj import Geod,Transformer
DAY=Path(__file__).resolve().parents[1];ROOT=DAY.parents[1];RAW=ROOT/'data/raw/day17';G=Geod(ellps='WGS84');MILE=1609.344
D=json.loads((DAY/'data/replay.json').read_text());S=json.loads((DAY/'data/sources.json').read_text());F=json.loads((RAW/'flight.json').read_text());routes=json.loads((DAY/'data/routes.geojson').read_text())['features'];checks={};details=[]
checks['flight_identity']=(D['flight']['callsign'],D['flight']['registration'],D['flight']['icao24'],D['flight']['start_airport_ident'],D['flight']['end_airport_ident'])==('DAL424','N533DT','a6bbef','KJFK','KDEN')
checks['original_hashes']=hashlib.sha256((RAW/'flight.json').read_bytes()).hexdigest()==S['flight']['sha256'] and hashlib.sha256((RAW/Path(S['raster']['url']).name).read_bytes()).hexdigest()==S['raster']['sha256']
checks['shared_display_scale']=len({(p['span_m'],p['width'],p['height']) for p in D['panels']})==1
checks['fixed_cinematic_curve']=D['stretch']['bloom_threshold_stored']==80 and D['stretch']['label']=='Contrast enhanced'
for p,f,idx in zip(D['panels'],routes,[0,-1]):
    coords=f['geometry']['coordinates'];length=sum(G.inv(*a[:2],*b[:2])[2] for a,b in zip(coords,coords[1:])); forward=Transformer.from_crs(4326,p['crs'],always_xy=True);inverse=Transformer.from_crs(p['crs'],4326,always_xy=True)
    checks[p['id']+'_5_statute_miles']=abs(length/MILE-5)<1e-6
    checks[p['id']+'_recorded_endpoint']=np.allclose(coords[0] if idx==0 else coords[-1],F['path']['coordinates'][idx][0 if idx==0 else -1],atol=1e-9)
    checks[p['id']+'_direction_and_time']=all(a[2]<b[2] and a[3]<b[3] for a,b in zip(p['route'],p['route'][1:]))
    with rasterio.open(DAY/'data'/f"{p['id']}-brightness.tif") as crop:
        checks[p['id']+'_georeferenced']=crop.crs is not None and crop.width==crop.height==1024 and abs(crop.res[0]-62.5)<1e-9 and tuple(crop.bounds)==tuple(p['bounds_m'])
        # Video's narrower vertical extent is the strictest viewport.
        checks[p['id']+'_route_in_frame']=all(abs(v[0])<62000 and abs(v[1])<11000-1500 for v in p['route'])
        checks[p['id']+'_raster_track_alignment']=all(np.linalg.norm(np.array(forward.transform(*inverse.transform(v[0],v[1])))-np.array(v[:2]))<1e-6 for v in p['route'])
    # Independent generous native-pixel windows; exact geodesic circle test on pixel centers.
    values=[]
    with rasterio.open(RAW/Path(S['raster']['url']).name) as source:
        for row in p['profile']:
            lon,lat=row['longitude'],row['latitude'];cx,cy=source.index(lon,lat)[::-1];win=rasterio.windows.Window(cx-25,cy-25,51,51);a=source.read(1,window=win,masked=True);rr,cc=np.indices(a.shape);xs,ys=rasterio.transform.xy(source.window_transform(win),rr,cc);xs=np.asarray(xs);ys=np.asarray(ys);_,_,dist=G.inv(np.full(xs.shape,lon),np.full(ys.shape,lat),xs,ys);mask=(dist<=3*MILE)&~np.ma.getmaskarray(a)&(a.data>=0);val=float(np.median(a.data[mask]));values.append(val)
            if val!=row['median_stored_value']:raise AssertionError((p['id'],row['mile'],val,row['median_stored_value']))
    checks[p['id']+'_native_profiles_verified']=len(values)==6 and float(np.median(values))==p['profile_median']
    details.append({'panel':p['id'],'length_miles':length/MILE,'native_profile_median':float(np.median(values)),'endpoint_airport_distance_m':p['endpoint_airport_distance_m'],'start_utc':p['start_utc'],'end_utc':p['end_utc']})
checks['ratio_verified']=D['ratio']==D['panels'][0]['profile_median']/D['panels'][1]['profile_median']
checks['selected_windows_do_not_cross_gap']=all(p['end_utc']<=g['from'] or p['start_utc']>=g['to'] for p in D['panels'] for g in D['gaps'])

N=json.loads((DAY/'data/nasa-sources.json').read_text())
for p in D['panels']:
    key=p['id']
    with rasterio.open(DAY/'data'/f'{key}-iss.tif') as photo:
        checks[key+'_nasa_route_coverage']=all(photo.read(4,window=rasterio.windows.Window(photo.index(v[0],v[1])[1],photo.index(v[0],v[1])[0],1,1))[0,0]>240 for v in p['route'])
        checks[key+'_nasa_shared_resolution']=photo.res==(25.0,25.0)
        checks[key+'_nasa_same_crs']=photo.crs==rasterio.crs.CRS.from_string(p['crs'])
    checks[key+'_nasa_hashes']=all(hashlib.sha256((DAY/'data'/name).read_bytes()).hexdigest()==digest for name,digest in N[key]['outputs'].items())

H=json.loads((DAY/'data/hybrid-qa.json').read_text())
checks['hybrid_display_qa']=H['passed'] and H['missing_photo_falls_back_to_viirs'] and H['valid_dark_field_stays_zero'] and H['same_parameters_all_panels_and_frames']
checks['ratio_rounds_to_12_8']=round(D['ratio'],1)==12.8
result={'passed':all(checks.values()),'checks':checks,'panels':details,'gaps':D['gaps'],'analysis':'Native values; no color curve, display warp, bloom or inferred gap positions used for sampling.','replay_sha256':hashlib.sha256((DAY/'data/replay.json').read_bytes()).hexdigest()}
(DAY/'data/validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert result['passed']
