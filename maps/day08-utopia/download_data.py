"""Fetch public source snapshots; raw caches never enter Git."""
from pathlib import Path
import concurrent.futures, hashlib, json, urllib.request, datetime
ROOT=Path(__file__).resolve().parents[2]
CACHE=ROOT/'data/raw/day08-utopia'
SOURCES={
'places.zip':'https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_48_place_500k.zip',
'airports.csv':'https://davidmegginson.github.io/ourairports-data/airports.csv',
'dart.zip':'https://www.dart.org/transitdata/latest/google_transit.zip',
'trinity.zip':'https://gtfsdata.ridetm.org/gtfs/fwtatransitdata.zip',
'dcta.zip':'https://gtfs.remix.com/dcta_denton_tx_us.zip',
'nyc-stations.json':'https://data.ny.gov/resource/39hk-dx4f.json?$limit=5000',
'nyc-routes.geojson':'https://data.ny.gov/resource/s692-irgq.geojson?$limit=5000',
'counties.zip':'https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_county_500k.zip',
'nyc-boroughs.geojson':'https://data.cityofnewyork.us/resource/gthc-hcne.geojson?$limit=10',
}
def fetch(item):
 name,url=item; p=CACHE/name
 if not p.exists():
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (Day8 open geographic art project)'})
  p.write_bytes(urllib.request.urlopen(req,timeout=120).read())
 b=p.read_bytes()
 return {'file':name,'url':url,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'retrieved_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
if __name__=='__main__':
 CACHE.mkdir(parents=True,exist_ok=True)
 manifest=ROOT/'maps/day08-utopia/source-manifest.json'
 records=[r for r in json.loads(manifest.read_text()) if r['file'] not in SOURCES] if manifest.exists() else []
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  for item, future in [(i,pool.submit(fetch,i)) for i in SOURCES.items()]:
   try: records.append(future.result()); print(item[0],records[-1]['bytes'],flush=True)
   except Exception as e: print(item[0],str(e),flush=True)
 (ROOT/'maps/day08-utopia/source-manifest.json').write_text(json.dumps(records,indent=2)+'\n')
