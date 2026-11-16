"""Preserve measured RINEX D1; independently validate sign using SP3 range rate."""
from acquire import *
import gzip,re,math
import numpy as np
from scipy.interpolate import BarycentricInterpolator
from pyproj import Transformer
C=299792458.;F0=1575420000.;OMEGA=7.2921151467e-5
START=18*3600;END=19*3600;TIMES=np.arange(START,END+1,60,dtype=float)

def header_and_observations(path):
    records=[];obs=[];header=[];receiver='';position=None;interval=None;timesystem=None
    if not path.exists():
        import io,hatanaka
        compact=path.with_name(path.name.replace('.obs.gz','.crx.gz'))
        stream=io.TextIOWrapper(io.BytesIO(hatanaka.decompress(compact.read_bytes())),encoding='ascii',errors='replace')
    else:stream=gzip.open(path,'rt',errors='replace')
    with stream as f:
        for line in f:
            header.append(line.rstrip());label=line[60:].strip()
            if label=='# / TYPES OF OBSERV':obs+=line[:60].split()[1:] if not obs else line[:60].split()
            if label=='APPROX POSITION XYZ':position=list(map(float,line[:60].split()))
            if label=='REC # / TYPE / VERS':receiver=line[:60].strip()
            if label=='INTERVAL':interval=float(line[:10])
            if label=='TIME OF FIRST OBS':timesystem=line[48:51].strip() or 'GPS'
            if label=='END OF HEADER':break
        assert 'D1' in obs,'No measured GPS L1 Doppler'
        assert timesystem=='GPS',f'Unsupported RINEX time system {timesystem}'
        di=obs.index('D1');li=obs.index('L1') if 'L1' in obs else None;si=obs.index('S1') if 'S1' in obs else None
        for line in f:
            if not line.strip():continue
            flag=int(line[28:29] or 0);n=int(line[29:32])
            if flag not in (0,1):
                for _ in range(n):next(f)
                continue
            sec=int(line[10:12])*3600+int(line[13:15])*60+float(line[15:26])
            ids=line[32:68]
            for _ in range((n-1)//12):ids+=next(f)[32:68]
            satellites=[ids[i:i+3].strip() for i in range(0,n*3,3)]
            keep=START<=sec<=END and abs(sec-round(sec/60)*60)<.001
            if sec>END:break
            for prn in satellites:
                rows=[next(f).rstrip('\n').ljust(80) for _ in range((len(obs)+4)//5)]
                if not keep or not prn.startswith('G'):continue
                fields=''.join(rows)
                def val(i):
                    try:return float(fields[16*i:16*i+14])
                    except ValueError:return None
                doppler=val(di)
                if doppler is not None:records.append(dict(gps_seconds=sec,prn=prn,doppler_hz=doppler,carrier_phase_cycles=val(li) if li is not None else None,snr_dbhz=val(si) if si is not None else None))
    return dict(observation_types=obs,receiver=receiver,header_ecef_m=position,interval_s=interval,time_system=timesystem,header=header),records

class Orbits:
    def __init__(self,path):
        self.data={};self.time_system=None
        with gzip.open(path,'rt') as f:
            for l in f:
                if l.startswith('%c') and self.time_system is None:self.time_system=l[9:12]
                if l.startswith('*'):
                    v=l[1:].split();t=int(v[3])*3600+int(v[4])*60+float(v[5])
                elif l.startswith('PG'):
                    prn=l[1:4];xyz=np.array([float(l[4+i*14:18+i*14]) for i in range(3)])*1000
                    if np.linalg.norm(xyz)>1e6 and np.isfinite(xyz).all():self.data.setdefault(prn,[]).append((t,xyz))
        assert self.time_system=='GPS',self.time_system
        self.interps={}
        for prn,records in self.data.items():
            ts=np.array([r[0] for r in records]);xyz=np.stack([r[1] for r in records]);nodes=np.argsort(abs(ts-(START+END)/2))[:10];nodes.sort()
            # Ten-node local polynomial across one hour, with padding on both sides.
            self.interps[prn]=BarycentricInterpolator((ts[nodes]-START)/900,xyz[nodes],axis=0)
    def at(self,prn,t):return self.interps[prn]((np.asarray(t)-START)/900)
    def apparent(self,prn,t,receiver):
        p=self.at(prn,t);tau=np.linalg.norm(p-receiver,axis=-1)/C
        for _ in range(2):
            p=self.at(prn,np.asarray(t)-tau);w=OMEGA*tau
            p=np.stack([np.cos(w)*p[...,0]+np.sin(w)*p[...,1],-np.sin(w)*p[...,0]+np.cos(w)*p[...,1],p[...,2]],axis=-1)
            tau=np.linalg.norm(p-receiver,axis=-1)/C
        return p
    def geometry(self,prn,t,receiver):
        p=self.apparent(prn,t,receiver);delta=p-receiver;ran=np.linalg.norm(delta)
        rate=(np.linalg.norm(self.apparent(prn,t+.5,receiver)-receiver)-np.linalg.norm(self.apparent(prn,t-.5,receiver)-receiver))
        lon,lat,h=Transformer.from_crs(4978,4979,always_xy=True).transform(*receiver);phi=np.deg2rad(lat);lam=np.deg2rad(lon);dx,dy,dz=delta
        east=-np.sin(lam)*dx+np.cos(lam)*dy;north=-np.sin(phi)*np.cos(lam)*dx-np.sin(phi)*np.sin(lam)*dy+np.cos(phi)*dz;up=np.cos(phi)*np.cos(lam)*dx+np.cos(phi)*np.sin(lam)*dy+np.sin(phi)*dz
        return dict(elevation_deg=float(np.rad2deg(np.arctan2(up,np.hypot(east,north)))),azimuth_deg=float(np.rad2deg(np.arctan2(east,north))%360),range_m=float(ran),range_rate_mps=float(rate),predicted_doppler_hz=float(-F0/C*rate))

def station_position(station,header):
    path=CACHE/(station+'.coord.txt')
    if not path.exists():raise ValueError('Published NGS coordinate file unavailable')
    text=path.read_text();it=text.split('ITRF2020 POSITION')[1].split('NAD_83')[0]
    xyz=[float(re.search(r'\b'+axis+r'\s*=\s*([-\d.]+)',it).group(1)) for axis in 'XYZ']
    # Propagate published ARP coordinate at epoch 2020.0 using ITRF velocity.
    epoch=2026+304/365
    for i,axis in enumerate('XYZ'):
        m=re.search(r'V'+axis+r'\s*=\s*([-\d.]+)',it)
        if m:xyz[i]+=float(m.group(1))*(epoch-2020)
    lon,lat,h=Transformer.from_crs(4978,4979,always_xy=True).transform(*xyz)
    return np.array(xyz),dict(id=station.upper(),lon=round(lon,7),lat=round(lat,7),height_m=round(h,3),ecef_m=xyz,receiver=header['receiver'],coordinate_source='NGS ITRF2020 ARP + published velocity',coordinate_epoch=epoch)

def process(stations):
    orbit=Orbits(CACHE/'orbit.sp3.gz');out=[];audit=[];rejected=[]
    for station in stations:
        try:
            cache=CACHE/(station+'-processed.json')
            if cache.exists():
                obj=json.loads(cache.read_text());qa=obj['audit'];audit.append(qa)
                if abs(qa['median_residual_hz'])>100 or qa['residual_mad_hz']>25:
                    rejected.append(dict(station=station,reason='D1 has a large common residual (>100 Hz) or noisy residual (>25 Hz MAD); raw sign cannot safely label motion',median_residual_hz=qa['median_residual_hz']));continue
                out.append(obj['station']);continue
            header,raw=header_and_observations(CACHE/(station+'.obs.gz'));xyz,meta=station_position(station,header);filtered=[];counts=dict(raw=len(raw),missing_orbit=0,implausible=0,below_mask=0)
            for row in raw:
                if row['prn'] not in orbit.interps:counts['missing_orbit']+=1;continue
                if not np.isfinite(row['doppler_hz']) or abs(row['doppler_hz'])>10000:counts['implausible']+=1;continue
                geom=orbit.geometry(row['prn'],row['gps_seconds'],xyz)
                if geom['elevation_deg']<10:counts['below_mask']+=1;continue
                filtered.append(dict(**row,**geom))
            assert len(filtered)>100,'Too few valid observations'
            measured=np.array([r['doppler_hz'] for r in filtered]);pred=np.array([r['predicted_doppler_hz'] for r in filtered]);corr=float(np.corrcoef(measured,pred)[0,1]);sign=1 if corr>0 else -1
            assert abs(corr)>.98,f'Doppler sign not validated for {station}: {corr}'
            residual=sign*measured-pred;offset=float(np.median(residual));mad=float(np.median(abs(residual-offset)))
            # Direction uses measured sign after verified convention, never predicted color.
            # Retain measurements and residuals; disagreements are marked ambiguous.
            for r in filtered:
                value=sign*r['doppler_hz'];r['physical_shift_hz']=value
                r['direction']='near-zero' if abs(value)<=100 else ('approaching' if value>0 else 'receding')
                r['sign_agrees_with_orbit']=bool(value*r['predicted_doppler_hz']>=0 or abs(value)<=100)
            meta.update(observation_type='D1',signal='GPS L1',carrier_hz=F0,rinex_interval_s=header['interval_s'],rinex_doppler_to_received_shift_sign=sign,records=filtered)
            qa=dict(station=station,correlation=corr,measured_sign_multiplier=sign,median_residual_hz=offset,residual_mad_hz=mad,sign_disagreements=sum(not r['sign_agrees_with_orbit'] for r in filtered),counts=counts,kept=len(filtered),observation_types=header['observation_types'])
            cache.write_text(json.dumps(dict(station=meta,audit=qa),separators=(',',':')))
            audit.append(qa)
            if abs(offset)>100 or mad>25:
                rejected.append(dict(station=station,reason='Large common (>100 Hz) or noisy (>25 Hz MAD) residual',median_residual_hz=offset));continue
            out.append(meta);print(station,qa,flush=True)
        except (AssertionError,ValueError,KeyError,OSError) as exc:
            rejected.append(dict(station=station,reason=str(exc),classification='unavailable_or_failed_scientific_quality'))
            print('EXCLUDED',station,str(exc),flush=True)
    # Satellite actual positions are geocentric ECEF metres at observation epochs.
    positions={prn:np.round(orbit.at(prn,TIMES),1).tolist() for prn in orbit.interps}
    public=[]
    selection=json.loads((HERE/'data/station-selection.json').read_text()) if (HERE/'data/station-selection.json').exists() else {'selected':[]}
    state_codes={s['id'].upper():s['state'] for s in selection['selected']}
    for s in out:
        rows=[[int((r['gps_seconds']-START)/60),r['prn'],r['doppler_hz'],round(r['azimuth_deg'],4),round(r['elevation_deg'],4),r['snr_dbhz'],round(r['range_rate_mps'],4)] for r in s['records']]
        public.append(dict(s,records=rows,state=state_codes.get(s['id'])))
    payload=dict(record_fields=['epoch_index','prn','measured_d1_hz','azimuth_deg','elevation_deg','snr_dbhz','range_rate_mps'],doppler_convention={'display':'Measured RINEX D1 in Hz, sign verified against geometric range rate','physical_sign_transform':'signed_received_shift_hz = station_sign_multiplier * raw_D1_hz; all retained multipliers are +1; no clock bias removed','positive':'approaching','negative':'receding'},orbit_sample_interval_s=5,orbit_times_gps=np.arange(START,END+1,5).tolist(),satellite_orbit_ecef_m={prn:np.round(orbit.at(prn,np.arange(START,END+1,5)),2).tolist() for prn in orbit.interps},title='THE INVISIBLE SYMPHONY',date=DATE,time_system='UTC',gps_minus_utc_s=18,times_utc=[f'2026-11-01T{int((t-18)//3600):02d}:{int((t-18)%3600//60):02d}:{int((t-18)%60):02d}Z' for t in TIMES],gps_seconds=TIMES.tolist(),sample_interval_s=60,near_zero_hz=100,elevation_mask_deg=10,signal='GPS L1',carrier_hz=F0,stations=public,satellite_ecef_m=positions,orbit_product='IGS0OPSRAP_20263050000_01D_15M_ORB.SP3',notes='Measured D1 samples; no temporal interpolation of measurements. Skyward map arcs are schematic; globe uses actual ECEF geometry.')
    (HERE/'data/observations.json').write_text(json.dumps(payload,separators=(',',':'))+'\n')
    (HERE/'data/scientific-qa.json').write_text(json.dumps(dict(stations=len(out),observations=sum(len(s['records']) for s in out),station_audits=audit,excluded_stations=rejected),indent=2)+'\n')
    print('PAYLOAD',len(out),'stations',sum(len(s['records']) for s in out),'measurements',flush=True)
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--stations',nargs='+',default=None);args=p.parse_args()
    stations=args.stations or [s['id'] for s in json.loads((HERE/'data/station-selection.json').read_text())['selected']]
    process(stations)
