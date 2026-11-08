"""Download countywide public-domain Census TIGER streets and generalize for display."""
from pathlib import Path
import json, urllib.request, hashlib, datetime
import geopandas as gpd
from shapely.geometry import mapping
H=Path(__file__).resolve().parent; R=H.parents[1]/'data/raw/day08-utopia';R.mkdir(parents=True,exist_ok=True)
m=H/'source-manifest.json';records=json.loads(m.read_text());features=[]
for fips,name in [('48113','Dallas'),('48439','Tarrant'),('48121','Denton'),('48085','Collin')]:
 filename=f'tl_2025_{fips}_roads.zip';url='https://www2.census.gov/geo/tiger/TIGER2025/ROADS/'+filename;p=R/filename
 if not p.exists():
  p.write_bytes(urllib.request.urlopen(url,timeout=90).read())
 records=[r for r in records if r['file']!=filename];records.append({'file':filename,'url':url,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'retrieved_utc':datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat(),'coverage':name+' County; 2025 TIGER/Line; US public domain'})
 g=gpd.read_file('zip://'+str(p));g=g[g.MTFCC.isin(['S1100','S1200','S1400'])].to_crs(32614)
 # Generalization retains connected road endpoints. Omit <100m local fragments
 # at this regional scale; primary/secondary segments are retained at all lengths.
 g=g[(g.MTFCC!='S1400')|(g.geometry.length>=100)].copy();g.geometry=g.geometry.simplify(20);g=g.to_crs(4326)
 for _,r in g.iterrows():features.append({'type':'Feature','geometry':mapping(r.geometry),'properties':{'kind':{'S1100':'highway','S1200':'arterial','S1400':'street'}[r.MTFCC]}})
 print(name,len(g),'street segments',flush=True)
 m.write_text(json.dumps(records,indent=2)+'\n')
(H/'streets.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features},separators=(',',':'))+'\n')
print(len(features),'total segments')
