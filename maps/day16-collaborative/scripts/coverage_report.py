"""Report actual retained coverage separately from rendering density."""
from acquire import *
from collections import Counter

def main():
 data=json.loads((HERE/'data/observations.json').read_text());selection=json.loads((HERE/'data/station-selection.json').read_text());quality=json.loads((HERE/'data/scientific-qa.json').read_text());render=json.loads((HERE/'data/render-selection-qa.json').read_text())
 states=json.loads((HERE/'data/states.geojson').read_text())['features'];state_names={f['properties']['STUSPS']:f['properties']['NAME'] for f in states if f['properties']['STUSPS']!='DC'}
 retained=Counter(s['state'] for s in data['stations']);candidate_states={s['state'] for s in selection['eligible']}|{'OK'}
 report=dict(date=data['date'],utc_start=data['times_utc'][0],utc_end=data['times_utc'][-1],receivers=len(data['stations']),state_count=len(retained),states=dict(sorted(retained.items())),measurements=sum(len(s['records']) for s in data['stations']),illustrated_links_final=render['epochs'][-1]['links'],illustrated_links_min=min(r['links'] for r in render['epochs']),illustrated_links_max=max(r['links'] for r in render['epochs']),desktop_link_limit=render['desktopLimit'],mobile_link_limit=render['mobileLimit'],candidate_count=len(selection['selected']),candidate_state_count=len({s['state'] for s in selection['selected']}),quality_exclusions=quality['excluded_stations'],prior_quality_exclusions=selection.get('known_quality_exclusions',[]),unrepresented_states={s:state_names[s] for s in sorted(set(state_names)-set(retained))},states_without_verified_D1_headers={s:state_names[s] for s in sorted(set(state_names)-candidate_states)},states_with_candidate_but_failed_quality=sorted(candidate_states-set(retained)),scope='Selected November 1 NOAA daily RINEX D1 archive and published-coordinate pipeline; not evidence that GNSS or Doppler measurements are absent from these states generally.',json_bytes=(HERE/'data/observations.json').stat().st_size)
 (HERE/'data/coverage-summary.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
if __name__=='__main__':main()
