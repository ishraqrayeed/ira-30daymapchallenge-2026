"""Reproduce Day 17 from public ADS-B JSON and the specified VIIRS COG.
Python Rasterio calls GDAL for the display warps. Analysis uses native pixels.
"""
import argparse, csv, hashlib, json, math, subprocess
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import reproject, Resampling, transform_bounds
from rasterio.transform import from_origin
from pyproj import Geod, Transformer, CRS
from PIL import Image, ImageFilter
ROOT=Path(__file__).resolve().parents[3]; DAY=ROOT/'maps/day17-light-dark'; RAW=ROOT/'data/raw/day17'
MILE=1609.344; GEOD=Geod(ellps='WGS84'); SPAN=64000; SIZE=1024
FILE='nightlights.average_viirs.v21_m_500m_s_20240101_20241231_go_epsg4326_v20250904.tif'
FLIGHT='https://adsb.aero/api/v1/flights/a6bbef%3A2025-10-15T23%3A57%3A13Z'
def dump(path,data): path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def fetch(url,path):
    if not path.exists(): subprocess.run(['curl','-fL','--retry','2','--max-time','240',url,'-o',str(path)],check=True)
def iso(t): return datetime.fromtimestamp(t,timezone.utc).isoformat().replace('+00:00','Z')
def lengths(p):
    return np.r_[0,np.cumsum([GEOD.inv(*a[:2],*b[:2])[2] for a,b in zip(p,p[1:])])]
def interp(p,t,d,s):
    i=min(max(np.searchsorted(d,s,side='right')-1,0),len(d)-2); f=(s-d[i])/(d[i+1]-d[i]); az,_,dist=GEOD.inv(*p[i][:2],*p[i+1][:2]); lon,lat,_=GEOD.fwd(*p[i][:2],az,dist*f)
    return [lon,lat,float(p[i][2]*(1-f)+p[i+1][2]*f)],float(t[i]*(1-f)+t[i+1]*f)
def main():
    argparse.ArgumentParser(description=__doc__).parse_args(); RAW.mkdir(parents=True,exist_ok=True); out=DAY/'data';out.mkdir(exist_ok=True)
    for url,name in [(FLIGHT,'flight.json'),('https://zenodo.org/api/records/17294744','zenodo.json'),('https://adsb.aero/api/v1/airports/KJFK','jfk.json'),('https://adsb.aero/api/v1/airports/KDEN','den.json'),('https://zenodo.org/records/17294744/files/'+FILE+'?download=1',FILE)]: fetch(url,RAW/name)
    flight=json.loads((RAW/'flight.json').read_text()); assert (flight['callsign'],flight['registration'],flight['icao24'],flight['start_airport_ident'],flight['end_airport_ident'])==('DAL424','N533DT','a6bbef','KJFK','KDEN')
    assert hashlib.md5((RAW/FILE).read_bytes()).hexdigest()=='0b976892d40c2d0d99177c727289eaf2'
    segments=flight['path']['coordinates']; times=flight['timestamps']; panels=[]; features=[]; rows=[]
    with rasterio.open(RAW/FILE) as src:
        print('Raster',src.shape,src.crs,src.res,src.nodata,src.dtypes)
        for key,idx,arrival,lon0,lat0 in [('jfk',0,False,-73.855,40.615),('den',-1,True,-104.675,39.955)]:
            p=segments[idx]; t=times[idx];d=lengths(p); assert d[-1]>5*MILE
            start=d[-1]-5*MILE if arrival else 0; end=start+5*MILE
            distances=np.unique(np.r_[start,d[(d>start)&(d<end)],end]); route=[interp(p,t,d,s) for s in distances]
            # Densify geodesic legs for accurate projected replay; do not manufacture observations.
            dense_s=np.unique(np.r_[distances,np.linspace(start,end,501)]); dense=[interp(p,t,d,s) for s in dense_s]
            crs=CRS.from_proj4(f'+proj=aeqd +lat_0={lat0} +lon_0={lon0} +datum=WGS84 +units=m +no_defs'); xy=Transformer.from_crs(4326,crs,always_xy=True)
            # Every panel has exactly the same metric extent, pixel count and transfer function.
            bounds=[-SPAN/2,-SPAN/2,SPAN/2,SPAN/2]; trans=from_origin(bounds[0],bounds[3],SPAN/SIZE,SPAN/SIZE)
            arr=np.full((SIZE,SIZE),-9999,dtype='float32')
            reproject(rasterio.band(src,1),arr,src_transform=src.transform,src_crs=src.crs,dst_transform=trans,dst_crs=crs,src_nodata=src.nodata,dst_nodata=-9999,resampling=Resampling.nearest)
            with rasterio.open(out/(key+'-brightness.tif'),'w',driver='GTiff',height=SIZE,width=SIZE,count=1,dtype='float32',crs=crs,transform=trans,nodata=-9999,compress='deflate') as dest: dest.write(arr,1)
            # Published stored values are 10 x original radiance; keep stored units explicit.
            valid=arr!=-9999; v=np.log1p(np.clip(arr,0,600))/np.log1p(600); v=np.where(valid,v,0)**1.15
            colors=np.array([[5,12,25],[13,27,43],[56,67,68],[128,124,100],[212,196,155],[255,241,204]],float)
            rgb=np.stack([np.interp(v,np.linspace(0,1,len(colors)),colors[:,i]) for i in range(3)],axis=-1)
            # One fixed bloom threshold (80 stored units), gain and ground-space blur for both panels.
            seed=np.where(valid,np.clip((arr-80)/520,0,1),0)
            seed_img=Image.fromarray((seed*255).astype('uint8'))
            bloom=.65*np.asarray(seed_img.filter(ImageFilter.GaussianBlur(1)),float)/255+.35*np.asarray(seed_img.filter(ImageFilter.GaussianBlur(3)),float)/255
            rgb=np.clip(rgb+bloom[...,None]*np.array([42,32,18]),0,255).astype('uint8');Image.fromarray(rgb).save(out/(key+'-lights.png'))
            profile=[]
            for mile in range(6):
                point,ts=interp(p,t,d,start+mile*MILE);lon,lat=point[:2]; radius=3*MILE
                edge=[GEOD.fwd(lon,lat,a,radius)[:2] for a in range(0,360,5)];xs,ys=zip(*edge)
                w=from_bounds(min(xs),min(ys),max(xs),max(ys),src.transform); window=rasterio.windows.Window(math.floor(w.col_off),math.floor(w.row_off),math.ceil(w.col_off+w.width)-math.floor(w.col_off),math.ceil(w.row_off+w.height)-math.floor(w.row_off)); vals=src.read(1,window=window,masked=True); tr=src.window_transform(window)
                rr,cc=np.indices(vals.shape); xx,yy=rasterio.transform.xy(tr,rr,cc); xx=np.asarray(xx);yy=np.asarray(yy)
                _,_,dist=GEOD.inv(np.full(xx.shape,lon),np.full(yy.shape,lat),xx,yy)
                mask=(dist<=radius)&~np.ma.getmaskarray(vals)&np.isfinite(vals.data)&(vals.data>=0)
                selected=vals.data[mask]; assert selected.size>0
                row={'panel':key,'mile':mile,'longitude':lon,'latitude':lat,'timestamp_utc':iso(ts),'median_stored_value':float(np.median(selected)),'valid_pixels':int(selected.size)};profile.append(row);rows.append(row)
            coords=[r[0] for r in route];route_xy=[[*xy.transform(*r[0][:2]),float((s-start)/MILE),r[1]] for s,r in zip(dense_s,dense)]
            assert all(abs(pt[0])<SPAN/2-4000 and abs(pt[1])<SPAN/2-4000 for pt in route_xy),key
            airports=json.loads((RAW/(key+'.json')).read_text()); airport={k:airports[k] for k in ['ident','lon','lat','elevation_ft']}
            panel={'id':key,'crs':crs.to_string(),'bounds_m':bounds,'bounds_wgs84':list(transform_bounds(crs,4326,*bounds,densify_pts=41)),'width':SIZE,'height':SIZE,'span_m':SPAN,'route':route_xy,'profile':profile,'profile_median':float(np.median([r['median_stored_value'] for r in profile])),'start_utc':iso(route[0][1]),'end_utc':iso(route[-1][1]),'airport':airport,'airport_xy':list(xy.transform(airport['lon'],airport['lat'])),'endpoint_airport_distance_m':GEOD.inv(*(coords[-1] if arrival else coords[0])[:2],airport['lon'],airport['lat'])[2]}
            panel['labels']=[{'text':name,'xy':list(xy.transform(lon,lat)),'kind':kind} for name,lon,lat,kind in ({'jfk':[('NEW YORK',-73.99,40.755,''),('Newark',-74.172,40.735,''),('Brooklyn',-73.895,40.650,''),('Atlantic Ocean',-73.75,40.20,'water')],'den':[('DENVER',-104.99,39.74,''),('Boulder',-105.27,40.015,''),('Aurora',-104.83,39.73,''),('Eastern plains',-104.34,40.14,'water')]}[key])]
            panels.append(panel);features.append({'type':'Feature','properties':{'panel':key,'length_miles':5,'start_utc':panel['start_utc'],'end_utc':panel['end_utc'],'endpoint_basis':'last recorded position' if arrival else 'first recorded position'},'geometry':{'type':'LineString','coordinates':coords}})
    ratio=panels[0]['profile_median']/panels[1]['profile_median']; gaps=[{'from':iso(a[-1]),'to':iso(b[0]),'seconds':b[0]-a[-1]} for a,b in zip(times,times[1:])]
    data={'title':'The First 5, the Last 5','flight':{k:flight[k] for k in ['flight_id','callsign','registration','icao24','start_ts','end_ts','start_airport_ident','end_airport_ident','point_count','raw_point_count']},'span_m':SPAN,'stretch':{'minimum':0,'maximum':600,'function':'(log1p(clip(value,0,600))/log1p(600)) ** 1.15','label':'Contrast enhanced','bloom_threshold_stored':80,'bloom_blur_pixels':[1,3],'bloom_gain_rgb':[42,32,18],'units':'OpenLandMap stored brightness (10 × original VNL radiance)'},'ratio':ratio,'panels':panels,'gaps':gaps,'endpoint_note':'Segments are anchored to the first and last recorded positions; exact liftoff and touchdown are not identified.'}
    dump(out/'bounds.json',{p['id']:{k:p[k] for k in ['crs','bounds_m','bounds_wgs84','width','height','span_m']} for p in panels})
    dump(out/'replay.json',data);dump(out/'routes.geojson',{'type':'FeatureCollection','features':features})
    with (out/'profiles.csv').open('w') as f: writer=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");writer.writeheader();writer.writerows(rows)
    sources={'retrieved_utc':datetime.now(timezone.utc).isoformat(),'flight':{'url':FLIGHT,'sha256':sha(RAW/'flight.json'),'upstream':'adsb.lol via adsb.aero','access':'public unauthenticated API','license':'ODbL-1.0','license_url':'https://www.adsb.lol/docs/open-data/historical'},'raster':{'url':'https://zenodo.org/records/17294744/files/'+FILE,'sha256':sha(RAW/FILE),'md5':'0b976892d40c2d0d99177c727289eaf2','license':'CC-BY-4.0','year':2024,'credit':'EOG Annual VNL V2; OpenLandMap / Tomislav Hengl v0.4','native_crs':str(src.crs),'native_resolution':list(src.res)},'software':{'rasterio':rasterio.__version__,'gdal':rasterio.__gdal_version__},'outputs':{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name not in ['sources.json','validation.json']}}
    dump(out/'sources.json',sources)
    print('Profile medians',[(p['id'],p['profile_median']) for p in panels],'ratio',ratio,'gaps',gaps)
if __name__=='__main__': main()
