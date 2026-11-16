"""Scientific checks of actual timestamps, observables, signs, orbit interpolation."""
from preprocess import *
import georinex as gr
import json,hashlib

def main():
 data=json.loads((HERE/'data/observations.json').read_text());qa=json.loads((HERE/'data/scientific-qa.json').read_text());orbit=Orbits(CACHE/'orbit.sp3.gz')
 assert len(data['stations'])==qa['stations']>=50
 assert data['gps_seconds']==list(range(64800,68401,60))
 assert data['times_utc'][0]=='2026-11-01T17:59:42Z' and data['times_utc'][-1]=='2026-11-01T18:59:42Z'
 audits={a['station'].upper():a for a in qa['station_audits']};count=0
 for s in data['stations']:
  audit=audits[s['id']];assert audit['correlation']>.98 and abs(audit['median_residual_hz'])<=100 and audit['residual_mad_hz']<=25
  assert audit['sign_disagreements']==0
  assert -125<s['lon']<-66 and 24<s['lat']<50
  assert s['rinex_doppler_to_received_shift_sign']==1
  seen=set()
  for row in s['records']:
   index,prn,doppler,az,el,snr,range_rate=row;assert (index,prn) not in seen;seen.add((index,prn));assert 0<=index<61 and prn in data['satellite_ecef_m'];assert el>=10 and abs(doppler)<=10000 and 0<=az<360;assert (abs(doppler)<=100 or doppler*range_rate<=0);count+=1
 assert count==qa['observations']
 # Independent library cross-check of the custom streaming RINEX2 parser.
 station='nyet';dataset=gr.load(CACHE/(station+'.obs.gz'),use='G',meas=['D1'],tlim=['2026-11-01T18:00:00','2026-11-01T18:02:00'],interval=60)
 _,records=header_and_observations(CACHE/(station+'.obs.gz'));checked=0
 for r in records:
  if r['gps_seconds']>START+120:continue
  stamp=np.datetime64('2026-11-01T00:00:00')+np.timedelta64(int(r['gps_seconds']),'s')
  value=float(dataset.D1.sel(time=stamp,sv=r['prn']).values)
  assert value==r['doppler_hz'],(value,r);checked+=1
 assert checked>10
 # Compare interpolation to withheld SP3 nodes (leave-one-out 9-node polynomial).
 interpolation_errors=[]
 for prn,records in orbit.data.items():
  ts=np.array([r[0] for r in records]);xyz=np.stack([r[1] for r in records])
  for k in np.flatnonzero((ts>=START)&(ts<=END)):
   nodes=np.argsort(abs(ts-ts[k]));nodes=nodes[nodes!=k][:9];nodes.sort();p=BarycentricInterpolator((ts[nodes]-ts[k])/900,xyz[nodes],axis=0)(0)
   interpolation_errors.append(float(np.linalg.norm(p-xyz[k])))
 assert max(interpolation_errors)<10
 report=dict(passed=True,stations=len(data['stations']),observations=count,independent_georinex_values_checked=checked,georinex_exact_match=True,maximum_sp3_leave_one_out_error_m=max(interpolation_errors),max_station_residual_mad_hz=max(audits[s['id']]['residual_mad_hz'] for s in data['stations']),minimum_station_doppler_correlation=min(audits[s['id']]['correlation'] for s in data['stations']),clock_offset_exclusions=qa['excluded_stations'],json_bytes=(HERE/'data/observations.json').stat().st_size,dataset_sha256=hashlib.sha256((HERE/'data/observations.json').read_bytes()).hexdigest())
 (HERE/'data/validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
