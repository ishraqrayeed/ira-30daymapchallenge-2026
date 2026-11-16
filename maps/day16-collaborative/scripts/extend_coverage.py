"""Inspect previously unscanned files rather than assume coordinate inventory is complete."""
from acquire import *
import zlib,re
from pyproj import Transformer

def main():
 old=json.loads((CACHE/'all-header-scan.json').read_text());seen={s['id'] for s in old}
 files={l.split()[0].split('/')[-2]:l.split()[0] for l in (CACHE/'files.list').read_text().splitlines()[1:] if '.26o.gz' in l and '/sum_' not in l}
 remaining=sorted((s,k) for s,k in files.items() if s not in seen)
 print('Additional station headers:',len(remaining),flush=True)
 def scan(job):
  s,key=job;path=CACHE/(s+'-extension-scan.gz')
  try:
   if not path.exists():subprocess.run(['curl','-fsSL','--retry','1','--max-time','40','--range','0-16383',BASE+key,'-o',str(path)],check=True,stderr=subprocess.DEVNULL)
   h=zlib.decompressobj(31).decompress(path.read_bytes()).decode('ascii','replace').split('END OF HEADER')[0];lines=[l for l in h.splitlines() if 'TYPES OF OBS' in l]
   doppler=any(re.search(r'\bD1\b',l) for l in lines);xyz=next((list(map(float,l[:60].split())) for l in h.splitlines() if 'APPROX POSITION XYZ' in l),None)
   lon,lat,height=Transformer.from_crs(4978,4979,always_xy=True).transform(*xyz) if xyz else (0,0,0)
   return dict(id=s,doppler=doppler,lon=lon,lat=lat,conus_candidate=bool(doppler and -125<lon<-66 and 24<lat<50),observation_lines=lines)
  except Exception as e:return dict(id=s,error=str(e))
 with ThreadPoolExecutor(max_workers=10) as pool:results=list(pool.map(scan,remaining))
 from shapely.geometry import shape,Point
 states=json.loads((HERE/'data/states.geojson').read_text())['features']
 for r in results:
  if r.get('conus_candidate'):
   r['state']=next((f['properties']['STUSPS'] for f in states if shape(f['geometry']).intersects(Point(r['lon'],r['lat']))),None)
 selection=json.loads((HERE/'data/station-selection.json').read_text());existing_states={s['state'] for s in selection['selected'] if s['id']!='sgpo'}
 new=[r for r in results if r.get('conus_candidate') and r.get('state') and r['state'] not in existing_states]
 import sys
 if '--apply' in sys.argv:
  for r in new:
   if not any(s['id']==r['id'] for s in selection['selected']):selection['selected'].append(r)
  selection['extension_method']='Remaining archive headers scanned; new-state Doppler candidates prioritized, subject to subsequent scientific validation'
  (HERE/'data/station-selection.json').write_text(json.dumps(selection,indent=2)+'\n')
 report=dict(new_state_candidates=new,original_headers=len(old),additional_headers=len(results),additional_doppler_conus_candidates=[r for r in results if r.get('conus_candidate')],failed=sum('error' in r for r in results),date=DATE)
 (HERE/'data/coverage-extension.json').write_text(json.dumps(report,indent=2)+'\n');(CACHE/'coverage-extension-full.json').write_text(json.dumps(results,indent=2)+'\n');print('Checked',len(results),'additional headers; new-state candidates:',[(r['id'],r['state']) for r in new],flush=True)
if __name__=='__main__':main()
