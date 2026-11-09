"""Fetch the small real NASA Blue Marble globe asset without image synthesis."""
from pathlib import Path
import requests
P=Path(__file__).resolve().parent/'data/nasa-blue-marble.jpg'
def main():
 if P.exists():print(f'Using existing NASA globe asset: {P}');return
 r=requests.get('https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi',params={'service':'WMS','version':'1.1.1','request':'GetMap','layers':'BlueMarble_ShadedRelief_Bathymetry','styles':'','format':'image/jpeg','srs':'EPSG:4326','bbox':'-180,-90,180,90','width':2048,'height':1024},timeout=90)
 r.raise_for_status()
 if not r.content.startswith(b'\xff\xd8'):raise ValueError('NASA did not return a JPEG')
 P.write_bytes(r.content);print(f'NASA globe asset: {len(r.content)} bytes')
if __name__=='__main__':main()
