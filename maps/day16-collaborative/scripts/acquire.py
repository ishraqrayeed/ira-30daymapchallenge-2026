"""Cache public NOAA observations/orbits; sources never enter browser payload."""
from pathlib import Path
import subprocess, json,hashlib,datetime
from concurrent.futures import ThreadPoolExecutor
HERE=Path(__file__).resolve().parents[1];CACHE=HERE.parents[1]/'data/raw/day16-symphony';BASE='https://noaa-cors-pds.s3.amazonaws.com/'
DATE='2026-11-01';DOY='305';YEAR='2026'
PILOT=['azbr','lflo','mwrd','nyet','mafa','tn30','zefr']
def fetch(key,name=None):
 p=CACHE/(name or key.split('/')[-1]);p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():
  temp=p.with_suffix(p.suffix+'.part');subprocess.run(['curl','-fsSL','--retry','2','--max-time','180',BASE+key,'-o',str(temp)],check=True);temp.replace(p)
 return p

def download(station):
 paths=[]
 compact=not (CACHE/(station+'.obs.gz')).exists()
 obskey=f'rinex/{YEAR}/{DOY}/{station}/{station}{DOY}0.26'+('d.gz' if compact else 'o.gz')
 obsname=station+('.crx.gz' if compact else '.obs.gz')
 for key,name in [(obskey,obsname),(f'coord/coord_20/{station}_20.coord.txt',station+'.coord.txt'),(f'station_log/{station}.log.txt',station+'.log.txt')]:
  try:paths.append(fetch(key,name))
  except subprocess.CalledProcessError:
   if name.endswith(('.obs.gz','.crx.gz')):raise
 print('CACHED',station,flush=True)
 return station

def main():
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--stations',nargs='+',default=None);a=p.parse_args()
 if a.stations is None:
  selection=HERE/'data/station-selection.json'
  a.stations=[s['id'] for s in json.loads(selection.read_text())['selected']] if selection.exists() else PILOT
 fetch(f'rinex/{YEAR}/{DOY}/IGS0OPSRAP_20263050000_01D_15M_ORB.SP3.gz','orbit.sp3.gz')
 with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(download,a.stations))
 manifest=dict(date=DATE,archive=BASE,stations=a.stations,orbit='rinex/2026/305/IGS0OPSRAP_20263050000_01D_15M_ORB.SP3.gz',retrieved_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in CACHE.iterdir() if p.name.endswith(('.obs.gz','.crx.gz','.coord.txt','.log.txt','.sp3.gz'))})
 (HERE/'data/sources.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':main()
