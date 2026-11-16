"""State-first, capped, spatially dispersed sampling of verified D1 headers."""
from acquire import *
from pyproj import Geod
from collections import Counter

def main():
 path=HERE/'data/station-selection.json';prior=json.loads(path.read_text())
 if not (CACHE/'selection-before-expansion.json').exists():(CACHE/'selection-before-expansion.json').write_text(json.dumps(prior,indent=2)+'\n')
 # Only stations with published coordinates and verified D1, plus previously
 # validated extensions. No ranking by measured Doppler or satellite count.
 candidates={s['id']:s for s in prior['eligible']}
 for s in prior['selected']:candidates[s['id']]=s
 known_bad=set(prior.get('known_quality_exclusions',[]))|{r['station'] for r in json.loads((HERE/'data/scientific-qa.json').read_text()).get('excluded_stations',[])}
 eligible=sorted([s for s in candidates.values() if s['id'] not in known_bad],key=lambda s:s['id'])
 geod=Geod(ellps='WGS84');selected=[]
 def distance(s):return min((geod.inv(s['lon'],s['lat'],c['lon'],c['lat'])[2] for c in selected),default=float('inf'))
 # Include one geographically separated receiver in every available state first.
 for state in sorted({s['state'] for s in eligible}):
  choices=[s for s in eligible if s['state']==state]
  validated=[s for s in choices if (CACHE/(s['id']+'-processed.json')).exists()]
  selected.append(max(validated or choices,key=lambda s:(distance(s),s['id'])))
 # Preserve current validated receivers, then favor states with fewer samples.
 current={s['id'].lower() for s in json.loads((HERE/'data/observations.json').read_text())['stations']}
 for s in eligible:
  if s['id'] in current and s not in selected:selected.append(s)
 while len(selected)<min(120,len(eligible)):
  counts=Counter(s['state'] for s in selected)
  remaining=[s for s in eligible if s not in selected and counts[s['state']]<20]
  if not remaining:break
  minimum=min(counts[s['state']] for s in remaining)
  choices=[s for s in remaining if counts[s['state']]==minimum]
  selected.append(max(choices,key=lambda s:(distance(s),s['id'])))
 report=dict(date=DATE,candidates=prior['candidates'],with_doppler=prior['with_doppler'],scan_failures=prior['scan_failures'],method='One receiver per eligible state first; preserve validated current sample; fill least represented states using WGS84 maximin distance. Target 120, cap 20 per state. No Doppler magnitude ranking.',target_receivers=120,state_cap=20,known_quality_exclusions=sorted(known_bad),selected=selected,eligible=prior['eligible'])
 path.write_text(json.dumps(report,indent=2)+'\n');print('Selected candidates',len(selected),'states',dict(Counter(s['state'] for s in selected)),flush=True)
if __name__=='__main__':main()
