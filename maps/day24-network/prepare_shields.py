"""Place collision-friendly route shields on actual, reference-tagged OSM highways."""
from pathlib import Path
from collections import defaultdict
import json,gzip,math
from shapely.geometry import LineString
from pyproj import Transformer
DAY=Path(__file__).resolve().parent;P=Transformer.from_crs(4326,5070,always_xy=True)
def main():
 source=json.loads(gzip.decompress((DAY/'data/highways.geojson.gz').read_bytes()));candidates=defaultdict(list)
 for f in source['features']:
  num=f['properties']['shield']
  if not num:continue
  lines=f['geometry']['coordinates'] if f['geometry']['type']=='MultiLineString' else [f['geometry']['coordinates']]
  for line in lines:
   if len(line)<2:continue
   p=LineString(line).interpolate(.5,normalized=True);x,y=P.transform(p.x,p.y);candidates[num].append((x,y,[p.x,p.y]))
 features=[]
 for number,points in sorted(candidates.items()):
  national=[];detail=[]
  for x,y,c in sorted(points):
   major=number in ['5','10','25','40','70','80','95'] and all((x-a)**2+(y-b)**2>300000**2 for a,b in national)
   if major:national.append((x,y))
   if not major and any((x-a)**2+(y-b)**2<70000**2 for a,b in detail):continue
   detail.append((x,y));features.append({'type':'Feature','properties':{'shield':number,'national':major},'geometry':{'type':'Point','coordinates':c}})
 (DAY/'data/shields.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features},separators=(',',':'))+'\n');print('Verified-reference shields:',len(features))
if __name__=='__main__':main()
