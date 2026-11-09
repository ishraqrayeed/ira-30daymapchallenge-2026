"""Download only GHSL 100 m tile R5_C8 for source-supported historical epochs."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests,hashlib,json,time
P=Path(__file__).resolve().parent;CACHE=P.parents[1]/'data/raw/day09/ghsl'
YEARS=list(range(1975,2021,5))
BASE='https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_S_GLOBE_R2023A'
def name(year):return f'GHS_BUILT_S_E{year}_GLOBE_R2023A_54009_100_V1_0_R5_C8.zip'
def url(year):return f'{BASE}/GHS_BUILT_S_E{year}_GLOBE_R2023A_54009_100/V1-0/tiles/{name(year)}'
def get(year):
 target=CACHE/name(year)
 if not target.exists():
  for attempt in range(3):
   try:
    r=requests.get(url(year),timeout=(20,180));r.raise_for_status()
    if not r.content.startswith(b'PK'):raise ValueError('Not a ZIP archive')
    target.write_bytes(r.content);break
   except Exception:
    if attempt==2:raise
    time.sleep(2)
 print(year,target.stat().st_size,flush=True)
 return {'year':year,'url':url(year),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
def main():
 CACHE.mkdir(parents=True,exist_ok=True)
 with ThreadPoolExecutor(max_workers=3) as pool:records=list(pool.map(get,YEARS))
 r=requests.get(f'{BASE}/GHS_BUILT_S_E1985_GLOBE_R2023A_54009_100/V1-0/copyright.txt',timeout=40);r.raise_for_status();(CACHE/'copyright.txt').write_text(r.text)
 (CACHE/'downloads.json').write_text(json.dumps(records,indent=2)+'\n');print('Historical tile download complete.',flush=True)
if __name__=='__main__':main()
