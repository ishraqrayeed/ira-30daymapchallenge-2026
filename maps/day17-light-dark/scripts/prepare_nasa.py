"""Cache NASA's public georeferenced ISS map tiles and warp into replay CRS.
The official GeoTIFF download returned HTTP 502; these are the same portal's
published georeferenced Web Mercator tiles, not manually placed JPEGs.
"""
import concurrent.futures,hashlib,json,math,subprocess
from pathlib import Path
import numpy as np,rasterio
from rasterio.warp import reproject,Resampling,transform_bounds
from rasterio.transform import from_origin
from PIL import Image,ImageFilter
from shapely.geometry import shape,box
from shapely.ops import transform as geom_transform
from pyproj import Transformer
DAY=Path(__file__).resolve().parents[1];ROOT=DAY.parents[1];CACHE=ROOT/'data/raw/day17/nasa';CACHE.mkdir(parents=True,exist_ok=True)
Z=12;R=20037508.342789244;N=2**Z;TILE=2*R/N;SIZE=2560
SOURCES={'jfk':{'photo':'ISS072-E-184896','date':'2024-10-27','catalog_resolution_m':11.98},'den':{'photo':'ISS070-E-103355','date':'2024-02-28','catalog_resolution_m':24.19}}
def job(args):
 key,mrf,x,y=args;path=CACHE/f'{mrf}-{Z}-{x}-{y}.png';url=f'https://eol.jsc.nasa.gov/images/MapTiles/tiled_astronaut_photos/{mrf}/{Z}/{x}/{y}.png'
 if not path.exists():subprocess.run(['curl','-fsSL','--retry','4','--max-time','40',url,'-o',str(path)],check=True,capture_output=True)
 return x,y,path,url
D=json.loads((DAY/'data/replay.json').read_text());sources={}
for p in D['panels']:
 key=p['id'];mrf=SOURCES[key]['photo'];lo=transform_bounds(p['crs'],3857,*p['bounds_m'],densify_pts=31);x0=max(0,math.floor((lo[0]+R)/TILE));x1=min(N-1,math.floor((lo[2]+R)/TILE));y0=max(0,math.floor((R-lo[3])/TILE));y1=min(N-1,math.floor((R-lo[1])/TILE));foot=shape(json.loads((DAY/'data/nasa-selection.json').read_text())[key]['geometry']); footprint=geom_transform(Transformer.from_crs(4326,3857,always_xy=True).transform,foot); jobs=[(key,mrf,x,y) for y in range(y0,y1+1) for x in range(x0,x1+1) if footprint.intersects(box(-R+x*TILE,R-(y+1)*TILE,-R+(x+1)*TILE,R-y*TILE))];print(key,len(jobs),'public tiles',flush=True)
 mosaic=np.zeros(((y1-y0+1)*256,(x1-x0+1)*256,4),dtype='uint8');files=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for x,y,path,url in pool.map(job,jobs):
   im=np.asarray(Image.open(path).convert('RGBA'));mosaic[(y-y0)*256:(y-y0+1)*256,(x-x0)*256:(x-x0+1)*256]=im;files.append({'url':url,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 src_tr=from_origin(-R+x0*TILE,R-y0*TILE,TILE/256,TILE/256);dst_tr=from_origin(p['bounds_m'][0],p['bounds_m'][3],p['span_m']/SIZE,p['span_m']/SIZE);dest=np.zeros((4,SIZE,SIZE),dtype='uint8')
 for band in range(4):reproject(mosaic[:,:,band],dest[band],src_transform=src_tr,src_crs=3857,dst_transform=dst_tr,dst_crs=p['crs'],resampling=Resampling.bilinear)
 with rasterio.open(DAY/'data'/f'{key}-iss.tif','w',driver='GTiff',width=SIZE,height=SIZE,count=4,dtype='uint8',crs=p['crs'],transform=dst_tr,compress='deflate') as ds:ds.write(dest)
 rgb=dest[:3].transpose(1,2,0).astype(float);luma=rgb@np.array([.2126,.7152,.0722]);v=np.clip(luma/255,0,1)**.8
 colors=np.array([[5,12,25],[9,19,33],[28,40,49],[99,101,89],[190,178,144],[255,241,204]],float)
 result=np.stack([np.interp(v,np.linspace(0,1,len(colors)),colors[:,i]) for i in range(3)],axis=-1)
 # Display-only, fixed threshold and ground-space bloom. No photo values enter the VIIRS chart.
 seed=np.clip((luma-170)/85,0,1)*(dest[3]>0);im=Image.fromarray((seed*255).astype('uint8'));bloom=np.asarray(im.filter(ImageFilter.GaussianBlur(1.5)),float)/255
 result=np.clip(result+bloom[...,None]*np.array([22,17,10]),0,255).astype('uint8');result[dest[3]==0]=[5,12,25];Image.fromarray(result).save(DAY/'data'/f'{key}-iss.png')
 sources[key]={**SOURCES[key],'photo_page':f'https://eol.jsc.nasa.gov/SearchPhotos/photo.pl?mission={mrf.split("-")[0]}&roll=E&frame={mrf.split("-")[-1]}','source':'NASA Earth Science and Remote Sensing Unit, NASA Johnson Space Center','georeference':'NASA ExplorePhotos official Web Mercator tiles, z12','display_resolution_m':p['span_m']/SIZE,'native_tile_resolution_m_at_equator':TILE/256,'tiles':files,'curve':'(luminance/255)^0.8; common navy-to-ivory palette','bloom_threshold':170,'bloom_sigma_m':1.5*p['span_m']/SIZE,'bloom_gain_rgb':[22,17,10],'noncomparable_photometric_exposures':True,'outputs':{f'{key}-iss.{suffix}':hashlib.sha256((DAY/'data'/f'{key}-iss.{suffix}').read_bytes()).hexdigest() for suffix in ['tif','png']}}
 print(key,'ready',flush=True)
(DAY/'data/nasa-sources.json').write_text(json.dumps(sources,indent=2)+'\n')
