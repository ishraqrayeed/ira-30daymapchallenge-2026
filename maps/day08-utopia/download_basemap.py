"""Build a light, source-backed DFW basemap from public-domain Census TIGER data."""
from pathlib import Path
import json,urllib.request,hashlib,datetime
import geopandas as gpd
from shapely.geometry import mapping
H=Path(__file__).resolve().parent;R=H.parents[1]/'data/raw/day08-utopia';R.mkdir(parents=True,exist_ok=True)
manifest=H/'source-manifest.json';records=json.loads(manifest.read_text());water=[];roads=[]
for fips,name in [('48113','Dallas'),('48439','Tarrant'),('48121','Denton'),('48085','Collin')]:
 file=f'tl_2025_{fips}_areawater.zip';url='https://www2.census.gov/geo/tiger/TIGER2025/AREAWATER/'+file;p=R/file
 if not p.exists():p.write_bytes(urllib.request.urlopen(url,timeout=90).read())
 records=[r for r in records if r['file']!=file];records.append({'file':file,'url':url,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'retrieved_utc':datetime.datetime.fromtimestamp(p.stat().st_mtime,datetime.timezone.utc).isoformat(),'coverage':name+' County; 2025 TIGER/Line areal water; US public domain'})
 g=gpd.read_file('zip://'+str(p)).to_crs(32614)
 keep=(g.geometry.area>=250000)|((g.FULLNAME.fillna('').str.contains('Trinity',case=False))&(g.geometry.area>=5000))
 g=g[keep].copy();g.geometry=g.geometry.simplify(25,preserve_topology=True);g=g.to_crs(4326)
 for _,r in g.iterrows():water.append({'type':'Feature','geometry':mapping(r.geometry),'properties':{'name':r.FULLNAME if isinstance(r.FULLNAME,str) else '', 'county':name,'kind':'water'}})
 print(name,'water',len(g),flush=True)
 # Cached 2025 road files were already downloaded and attributed by download_streets.py.
 roadfile=R/f'tl_2025_{fips}_roads.zip'
 if not roadfile.exists():raise FileNotFoundError('Run download_streets.py first: '+str(roadfile))
 g=gpd.read_file('zip://'+str(roadfile));g=g[g.MTFCC=='S1100'].to_crs(32614).copy();g.geometry=g.geometry.simplify(30);g=g.to_crs(4326)
 for _,r in g.iterrows():roads.append({'type':'Feature','geometry':mapping(r.geometry),'properties':{'name':r.FULLNAME if isinstance(r.FULLNAME,str) else '', 'kind':'highway'}})
 manifest.write_text(json.dumps(records,indent=2)+'\n')
(H/'basemap-water.geojson').write_text(json.dumps({'type':'FeatureCollection','features':water},separators=(',',':'))+'\n')
(H/'basemap-highways.geojson').write_text(json.dumps({'type':'FeatureCollection','features':roads},separators=(',',':'))+'\n')
print('Saved',len(water),'water polygons and',len(roads),'primary road segments')
