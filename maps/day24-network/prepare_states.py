"""Prepare a compact Census display; scoring uses the unsimplified source polygons."""
from pathlib import Path
import json,hashlib
import geopandas as gpd
DAY=Path(__file__).resolve().parent;CACHE=DAY.parents[1]/'data/raw/day24'
if __name__=='__main__':
 source=CACHE/'states-2024.zip';g=gpd.read_file(source);g=g[~g.STUSPS.isin(['AK','HI','PR','GU','VI','MP','AS'])].to_crs(4326)
 (CACHE/'states-full.geojson').write_text(g[['STUSPS','NAME','STATEFP','geometry']].to_json(drop_id=True))
 display=g[['STUSPS','NAME','STATEFP','geometry']].to_crs(5070);display.geometry=display.geometry.simplify(250,preserve_topology=True);display=display.to_crs(4326)
 obj=json.loads(display.to_json(drop_id=True));labels=[]
 for f in obj['features']:
  f['id']=f['properties']['STUSPS']
  geom=g[g.STUSPS==f['id']].geometry.iloc[0];parts=list(geom.geoms) if geom.geom_type=='MultiPolygon' else [geom];label=max(parts,key=lambda a:a.area).representative_point()
  labels.append({'id':f['id'],'name':f['properties']['NAME'],'coordinates':[round(label.x,5),round(label.y,5)]})
 def rounder(o):
  if isinstance(o,float):return round(o,5)
  if isinstance(o,list):return [rounder(x) for x in o]
  if isinstance(o,dict):return {k:rounder(v) for k,v in o.items()}
  return o
 (DAY/'data/states.geojson').write_text(json.dumps(rounder(obj),separators=(',',':'))+'\n');(DAY/'data/state-labels.json').write_text(json.dumps(labels,separators=(',',':'))+'\n')
 (DAY/'data/census-source.json').write_text(json.dumps({'url':'https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_state_500k.zip','vintage':2024,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'display_simplification_m':250,'scoring_geometry':'Original 1:500,000 Census polygons, not simplified display.','features':49,'counted_states':48,'dc_counted':False},indent=2)+'\n');print('Prepared 48 states plus uncounted DC.')
