"""Build the final self-contained editorial map from audited model outputs."""
import csv,hashlib,json,shutil
from shapely.geometry import shape,mapping
from shapely.ops import transform
from clean_data import DAY,OUT,PROJECT

def main():
 audit=json.loads((OUT/'day04_audit.json').read_text())
 rows=list(csv.DictReader((OUT/'manhattan_halal_locations.csv').open()))
 assert audit['csv_sha256']==hashlib.sha256((OUT/'manhattan_halal_locations.csv').read_bytes()).hexdigest()
 boundary=transform(PROJECT.transform,shape(json.loads((OUT/'manhattan_boundary.geojson').read_text())['features'][0]['geometry']))
 xmin,ymin,xmax,ymax=boundary.bounds
 scale=790/(ymax-ymin)
 def screen(x,y,z=None):return 96+(x-xmin)*scale,70+(ymax-y)*scale
 land=mapping(transform(screen,boundary.simplify(8)))
 points=[]
 for r in rows:
  x,y=screen(*PROJECT.transform(float(r['longitude']),float(r['latitude'])))
  points.append(dict(r,x=round(x,3),y=round(y,3),cluster_id=int(r['cluster_id'])))
 clusters=json.loads((OUT/'manhattan_halal_clusters.geojson').read_text())['features']
 for f in clusters:
  f['geometry']=mapping(transform(screen,transform(PROJECT.transform,shape(f['geometry']))))
  f['properties']['center']=screen(*PROJECT.transform(*f['properties']['centroid']))
 # Five largest clusters receive labels; all others remain inspectable.
 selected=sorted(clusters,key=lambda f:(-f['properties']['locations'],f['properties']['cluster_id']))[:5]
 # Label placements are cartographic only; geometry and memberships stay calculated.
 placements={1:{'x':470,'y':726,'lines':['EAST VILLAGE /','LOWER EAST SIDE'],'anchor':'start'},2:{'x':150,'y':714,'lines':['GREENWICH','VILLAGE'],'anchor':'end'},3:{'x':490,'y':599,'lines':['KIPS BAY /','GRAMERCY'],'anchor':'start'},5:{'x':205,'y':548,'lines':['MIDTOWN WEST','/ CHELSEA'],'anchor':'end'},8:{'x':490,'y':488,'lines':['LENOX HILL /','SUTTON PLACE'],'anchor':'start'}}
 labels=[dict(f['properties'],**placements[f['properties']['cluster_id']]) for f in selected]
 data={'points':points,'land':land,'context':[],'clusters':clusters,'labels':labels,'stats':audit['dbscan_selected'],'total':len(rows),'scale_km_px':scale*1000,'csv_sha256':audit['csv_sha256'],'config_sha256':hashlib.sha256((DAY/'config.json').read_bytes()).hexdigest()}
 text=(DAY/'map-template.html').read_text().replace('__MAP_DATA__',json.dumps(data,separators=(',',':')).replace('</','<\\/'))
 text=text.replace('__TOTAL__',str(len(rows))).replace('__CLUSTER_COUNT__',str(audit['dbscan_selected']['clusters'])).replace('__NOISE_COUNT__',str(audit['dbscan_selected']['noise_locations'])).replace('__PERCENT__',str(round(audit['dbscan_selected']['percentage_clustered']))).replace('__LARGEST__',str(max(f['properties']['locations'] for f in clusters)))
 (DAY/'map.html').write_text(text)
 for name in ['manhattan_halal_locations.csv','manhattan_halal_locations.geojson','manhattan_halal_clusters.geojson','manhattan_boundary.geojson','dbscan_parameter_sweep.csv','day04_audit.json','analysis.json']:
  shutil.copyfile(OUT/name,DAY/name)
 print('Rendered',len(points),'locations and',len(clusters),'clusters')

if __name__=='__main__':main()
