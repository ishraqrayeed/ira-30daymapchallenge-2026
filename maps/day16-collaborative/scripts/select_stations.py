"""Reproducible availability scan, then geographic maximin selection."""
from acquire import *
import re,zlib
import numpy as np

def inventory():
    present={l.split()[0].split('/')[-2]:l.split()[0] for l in (CACHE/'files.list').read_text().splitlines()[1:] if '.26o.gz' in l}
    sites=[]
    for line in (CACHE/'coordinates.txt').read_text().splitlines():
        v=line.split()
        if len(v)<17 or v[0].lower() not in present:continue
        try:
            lat=float(v[2])+float(v[3])/60+float(v[4])/3600;lon=float(v[6])+float(v[7])/60+float(v[8])/3600
            if v[5]=='S':lat=-lat
            if v[9]=='W':lon=-lon
        except ValueError:continue
        if 24<lat<50 and -125<lon<-66 and v[14]=='US' and v[15] not in ['AK','HI','PR']:
            sites.append(dict(id=v[0].lower(),lat=lat,lon=lon,state=v[15],key=present[v[0].lower()]))
    return sites

def scan(s):
    name=s['id'];p=CACHE/(name+'-eligibility.json')
    if p.exists():return json.loads(p.read_text())
    try:
        path=CACHE/(name+'-scan.gz')
        if not path.exists():subprocess.run(['curl','-fsSL','--retry','1','--max-time','45','--range','0-16383',BASE+s['key'],'-o',str(path)],check=True,stderr=subprocess.DEVNULL)
        header=zlib.decompressobj(31).decompress(path.read_bytes()).decode('ascii','replace').split('END OF HEADER')[0]
        lines=[l for l in header.splitlines() if 'TYPES OF OBS' in l]
        obj=dict(**s,doppler=any(re.search(r'\bD1\b',l) for l in lines),observation_lines=lines)
    except Exception as e:obj=dict(**s,doppler=False,error=str(e))
    p.write_text(json.dumps(obj));return obj

def main():
    fetch(f'rinex/{YEAR}/{DOY}/2026.305.files.list','files.list')
    fetch('coord/coord_20/itrf2020_geo.comp.txt','coordinates.txt')
    sites=inventory();print('Scanning',len(sites),'CONUS station headers',flush=True)
    with ThreadPoolExecutor(max_workers=12) as pool:results=list(pool.map(scan,sites))
    available=sorted([s for s in results if s.get('doppler')],key=lambda s:s['id'])
    chosen=[s for s in available if s['id'] in PILOT]
    if not chosen:chosen=[available[0]]
    # Greedy maximin great-circle distance, independent of Doppler magnitude.
    from pyproj import Geod
    geod=Geod(ellps='WGS84')
    while len(chosen)<min(64,len(available)):
        remaining=[s for s in available if s not in chosen]
        def distance(s):return min(geod.inv(s['lon'],s['lat'],c['lon'],c['lat'])[2] for c in chosen)
        chosen.append(max(remaining,key=distance))
    report=dict(date=DATE,candidates=len(sites),with_doppler=len(available),scan_failures=sum('error' in s for s in results),method='Greedy maximin WGS84 geographic distance, seeded by validated pilot; no Doppler-magnitude ranking',selected=chosen,eligible=available)
    (HERE/'data/station-selection.json').write_text(json.dumps(report,indent=2)+'\n');(CACHE/'all-header-scan.json').write_text(json.dumps(results,indent=2)+'\n')
    print('ELIGIBLE',len(available),'SELECTED',len(chosen),'STATES',sorted({s['state'] for s in chosen}),flush=True)
if __name__=='__main__':main()
