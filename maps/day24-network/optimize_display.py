"""Group identical cartographic styles without changing any highway coordinates."""
from pathlib import Path
from collections import defaultdict
import json,gzip
DAY=Path(__file__).resolve().parent
def main():
 source=DAY/'data/highways.geojson.gz';obj=json.loads(gzip.decompress(source.read_bytes()));groups={}
 for f in obj['features']:
  p=f['properties'];key=(p['ref'],p['kind'],p['shield'],p['major'])
  if key not in groups:groups[key]={'type':'Feature','properties':{k:p[k] for k in ['ref','kind','shield','major']},'geometry':{'type':'MultiLineString','coordinates':[]}}
  coords=f['geometry']['coordinates'];groups[key]['geometry']['coordinates'].extend(coords if f['geometry']['type']=='MultiLineString' else [coords])
 out={'type':'FeatureCollection','features':list(groups.values())};source.write_bytes(gzip.compress(json.dumps(out,separators=(',',':')).encode(),compresslevel=9,mtime=0));qa=json.loads((DAY/'data/graph.qa.json').read_text());qa['display_feature_groups']=len(out['features']);qa['display_gzip_bytes']=source.stat().st_size;(DAY/'data/graph.qa.json').write_text(json.dumps(qa,separators=(',',':'))+'\n');print('Display feature groups:',len(out['features']),'bytes:',source.stat().st_size)

if __name__=='__main__':main()
