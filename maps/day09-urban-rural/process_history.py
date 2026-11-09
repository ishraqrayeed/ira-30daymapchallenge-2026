"""Reproduce Las Vegas GHSL epochs, exact raster metrics, changes and light web layers."""
from pathlib import Path
import math,json,zipfile,hashlib
import numpy as np
import rasterio
from rasterio.windows import from_bounds,Window
from rasterio.features import geometry_mask,shapes
from rasterio.warp import reproject,Resampling
from rasterio.transform import from_bounds as texture_transform
import geopandas as gpd
from shapely.geometry import Polygon,shape,mapping
from shapely.ops import transform,unary_union
from shapely.validation import make_valid
from pyproj import Transformer
from PIL import Image
from download_history import CACHE,YEARS,name,url
P=Path(__file__).resolve().parent;OUT=P/'data/history'
BBOX=(-115.50,35.88,-114.85,36.45)
THRESHOLD=1000 # square metres built-up surface in each 10000 m² equal-area cell (10%).
COLORS={'blue':(23,63,104),'new':(66,143,145)}
def aoi_polygon():
 w,s,e,n=BBOX;v=[]
 for a,b in [((w,s),(e,s)),((e,s),(e,n)),((e,n),(w,n)),((w,n),(w,s))]:
  v.extend([(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t) for t in np.linspace(0,1,64,endpoint=False)])
 return Polygon(v)
def polygons(mask,affine):
 geoms=[shape(g) for g,value in shapes(mask.astype('uint8'),mask=mask,transform=affine) if value==1]
 return make_valid(unary_union(geoms)) if geoms else Polygon()
def main():
 OUT.mkdir(parents=True,exist_ok=True);arrays=[];records=[];affine=None;source_crs=None;common=None
 for year in YEARS:
  archive=CACHE/name(year)
  with zipfile.ZipFile(archive) as z:members=[n for n in z.namelist() if n.lower().endswith('.tif')]
  if len(members)!=1:raise ValueError(f'Unexpected TIFF members: {members}')
  with rasterio.open(f'/vsizip/{archive}/{members[0]}') as src:
   if source_crs is None:
    source_crs=src.crs;project=Transformer.from_crs(4326,source_crs,always_xy=True).transform
    aoi=transform(project,aoi_polygon());raw=from_bounds(*aoi.bounds,transform=src.transform)
    col,row=math.floor(raw.col_off),math.floor(raw.row_off)
    window=Window(col,row,math.ceil(raw.col_off+raw.width)-col,math.ceil(raw.row_off+raw.height)-row)
    affine=src.window_transform(window);dimensions=(int(window.height),int(window.width));inside=geometry_mask([mapping(aoi)],dimensions,affine,invert=True)
    common=inside.copy();reference=(src.crs,src.transform,src.width,src.height)
   if (src.crs,src.transform,src.width,src.height)!=reference:raise ValueError('GHSL grids are not identical')
   if abs(abs(affine.a*affine.e)-10000)>.01:raise ValueError('Expected 100 m equal-area cells')
   values=src.read(1,window=window)
   valid=(values!=src.nodata)&(values<=10000);common&=valid
   arrays.append(values)
  records.append({'year':year,'url':url(year),'zip_bytes':archive.stat().st_size,'zip_sha256':hashlib.sha256(archive.read_bytes()).hexdigest()})
  print('Read',year,dimensions,flush=True)
 if not common.any():raise ValueError('No common valid coverage')
 inverse=Transformer.from_crs(source_crs,4326,always_xy=True).transform
 masks=[(a>=THRESHOLD)&common for a in arrays]
 texture_size=(1024,1024);dst_affine=texture_transform(*BBOX,*texture_size)
 def png(mask,filename,color):
  dst=np.zeros(texture_size[::-1],dtype='uint8')
  reproject(mask.astype('uint8'),dst,src_transform=affine,src_crs=source_crs,dst_transform=dst_affine,dst_crs='EPSG:4326',resampling=Resampling.nearest,dst_nodata=0)
  rgba=np.zeros((*dst.shape,4),dtype='uint8');rgba[:,:,:3]=color;rgba[:,:,3]=dst*255
  Image.fromarray(rgba,'RGBA').save(OUT/filename,optimize=True)
  return f'data/history/{filename}'
 series=[];footprints=[];changes=[];previous=None
 first_area=float(np.count_nonzero(masks[0])*.01)
 for year,values,mask in zip(YEARS,arrays,masks):
  footprint=polygons(mask,affine)
  full=png(mask,f'{year}-footprint.png',COLORS['blue'])
  gain=mask if previous is None else mask&~previous
  loss=np.zeros_like(mask) if previous is None else previous&~mask
  stable=mask if previous is None else previous&mask
  textures={'footprint':full,'stable':png(stable,f'{year}-stable.png',COLORS['blue']),'gain':png(gain,f'{year}-gain.png',COLORS['blue']),'highlight':png(gain,f'{year}-new.png',COLORS['new']),'loss':png(loss,f'{year}-loss.png',COLORS['blue'])}
  area=float(np.count_nonzero(mask)*.01);gain_area=float(np.count_nonzero(gain)*.01) if previous is not None else 0.;loss_area=float(np.count_nonzero(loss)*.01)
  temporal='Satellite-anchor-aligned model estimate' if year in (1975,1990,2000) else 'Source-interpolated estimate' if year<2020 else 'Source-extrapolated estimate (2018 imagery anchor)'
  row={'year':year,'temporal_definition':temporal,'developed_km2':round(area,4),'developed_mi2':round(area/2.589988110336,4),'built_surface_km2':round(float(values[common].astype('float64').sum()/1e6),6),'change_from_first_km2':round(area-first_area,4),'change_from_first_pct':round((area/first_area-1)*100,4),'gain_km2':round(gain_area,4),'loss_km2':round(loss_area,4),'texture':textures,'selected_cells':int(mask.sum()),'source_decreasing_cells':0 if previous is None else int(((values<arrays[YEARS.index(year)-1])&common).sum())}
  series.append(row)
  # GeoJSON is a downloadable GIS companion; the browser uses exact classified raster textures.
  simplified=footprint.simplify(10,preserve_topology=True)
  footprints.append({'geometry':transform(inverse,simplified),'year':year,'developed_km2':area,'temporal_definition':temporal,'simplified_area_error_pct':0 if area==0 else (simplified.area-footprint.area)/footprint.area*100})
  if previous is not None:
   for kind,m in [('gain',gain),('loss',loss)]:
    geom=polygons(m,affine)
    if not geom.is_empty:changes.append({'geometry':transform(inverse,geom.simplify(10,preserve_topology=True)),'year':year,'kind':kind,'area_km2':float(m.sum()*.01)})
   if abs((int(mask.sum())-int(previous.sum()))*.01-gain_area+loss_area)>1e-8:raise ValueError('Epoch area balance failed')
  previous=mask
  print(year,row['developed_km2'],row['built_surface_km2'],'gain/loss',gain_area,loss_area,flush=True)
 gpd.GeoDataFrame(footprints,crs=4326).to_file(P/'data/history-footprints.geojson',driver='GeoJSON')
 if changes:gpd.GeoDataFrame(changes,crs=4326).to_file(P/'data/history-changes.geojson',driver='GeoJSON')
 nodata_excluded=int((inside&~common).sum())
 metadata={'title':'Las Vegas — The Desert That Became a City','source':'European Commission JRC GHS-BUILT-S R2023A, 100 m, tile R5_C8, total built-up surface','source_url':'https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php','methodology_url':'https://human-settlement.emergency.copernicus.eu/documents/GHSL_Data_Package_2023.pdf','license':'CC BY 4.0, European Commission JRC; source copyright.txt','epochs':YEARS,'temporal_notice':'All epochs are GHSL model estimates. Five-year outputs are not independent satellite observations. Intermediate epochs are source-interpolated; 2020 extrapolates from the 2018 anchor. No 2025/2030 projections included.','observation_anchors':[1975,1990,2000,2014,2018],'classification':'Developed-cell footprint: at least 1000 m² built-up surface in a 100 m × 100 m equal-area cell (10%). This is not municipal area or measured land conversion.','threshold_built_surface_m2':THRESHOLD,'cell_area_m2':10000,'analysis_crs':source_crs.to_string(),'analysis_transform':list(affine)[:6],'native_window_shape':list(dimensions),'study_bbox_wgs84':BBOX,'study_selection':'Native equal-area cells whose centers lie inside the geographic study rectangle, using a densified projected boundary.','common_valid_cells':int(common.sum()),'excluded_nodata_cells':nodata_excluded,'texture_bounds':BBOX,'texture_size':texture_size,'texture_crs':'EPSG:4326','texture_resampling':'Nearest-neighbor classification for display; metrics computed from original equal-area cells, not display images.','vector_simplification_m':10,'series':series,'sources':records,'qa':{'identical_source_grids':True,'common_valid_coverage':True,'area_balance_passed':True,'nonmonotonic_threshold_losses_km2':sum(r['loss_km2'] for r in series),'decreasing_built_surface_cells':sum(r['source_decreasing_cells'] for r in series),'max_vector_area_error_pct':max(abs(f['simplified_area_error_pct']) for f in footprints)},'display':{'overview':{'lon':-115.15,'lat':36.16,'range':105000,'heading':0,'pitch':-65},'world':{'lon':-105,'lat':35,'range':22000000,'heading':0,'pitch':-90}}}
 (P/'data/history.json').write_text(json.dumps(metadata,indent=2)+'\n')
 print('Historical processing complete',flush=True)
if __name__=='__main__':main()
