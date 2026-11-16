"""Inspect NOAA public archive and real RINEX headers before visualization."""
from pathlib import Path
import subprocess,json,zlib,gzip,xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
CACHE=Path(__file__).resolve().parents[3]/'data/raw/day16-symphony'
BASE='https://noaa-cors-pds.s3.amazonaws.com/'

def get(key,path,header=False):
    if path.exists():return path.read_bytes()
    cmd=['curl','-fsSL','--retry','2','--max-time','60']
    if header:cmd+=['--range','0-65535']
    subprocess.run(cmd+[BASE+key,'-o',str(path)],check=True)
    return path.read_bytes()

def main():
    for key,name in [('?list-type=2&delimiter=/','root.xml'),('rinex/2026/305/2026.305.files.list','files.list')]:
        get(key,CACHE/name)
    print((CACHE/'root.xml').read_text()[:4000],flush=True)
    print((CACHE/'files.list').read_text()[:1000],flush=True)
    stations=['p041','p176','p056','txau','txsa','txda','nrc1','nrc2','ncbr','ncbe','mdga','mdsc','ohli','ohcl','iacd','iaam','mnsl','mndu','sacr','p474','p301','p360','p595','wvch','vabg','flmi','flor','al30','garl','ilcg']
    def inspect(station):
        try:
            key=f'rinex/2026/305/{station}/{station}3050.26o.gz';data=get(key,CACHE/(station+'-header.gz'),True)
            text=zlib.decompressobj(31).decompress(data).decode('ascii','replace');header=text.split('END OF HEADER')[0]
            (CACHE/(station+'-header.txt')).write_text(header)
            lines=[l for l in header.splitlines() if '# / TYPES OF OBSERV' in l or 'SYS / # / OBS TYPES' in l]
            doppler=any('D1' in l for l in lines)
            print(station,'DOPPLER',doppler,' '.join(lines),flush=True)
            return dict(station=station,url=BASE+key,doppler=doppler,observation_lines=lines)
        except Exception as e:print('FAILED',station,str(e)[:100],flush=True);return dict(station=station,error=str(e))
    with ThreadPoolExecutor(max_workers=5) as pool:results=list(pool.map(inspect,stations))
    (CACHE/'header-scan.json').write_text(json.dumps(results,indent=2)+'\n')
if __name__=='__main__':main()
