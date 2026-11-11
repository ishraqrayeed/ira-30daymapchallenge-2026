"""Download verified, explicitly reusable Freesound previews and make compact excerpts.
Original downloads require a Freesound login; no login bypass is attempted.
Metadata and license approval live in recordings.json. Source HTML/audio stay ignored.
"""
from pathlib import Path
import argparse, hashlib, json, re, subprocess, urllib.request, shutil
import numpy as np
from scipy.io import wavfile
ROOT=Path(__file__).resolve().parent
CACHE=ROOT.parents[1]/'data/day11-traffic/audio'

def fetch(url,path):
    if not path.exists():
        request=urllib.request.Request(url,headers={'User-Agent':'30DayMapChallenge/2026 (public educational sound gallery)'})
        with urllib.request.urlopen(request,timeout=60) as response: path.write_bytes(response.read())
    return path.read_bytes()

def main():
    CACHE.mkdir(parents=True,exist_ok=True); (ROOT/'traffic-audio').mkdir(exist_ok=True)
    parser=argparse.ArgumentParser(); parser.add_argument('--city'); args=parser.parse_args()
    manifest=json.loads((ROOT/'recordings.json').read_text())
    for city in manifest['cities']:
        if args.city and city['id'] != args.city: continue
        r=city['recording']
        if not r or not r.get('approved'): continue
        print('Processing '+city['city'],flush=True)
        if r.get('source_type') == 'youtube':
            if r['license'] != 'Used with permission' or not r.get('permission_basis'):
                raise ValueError('Explicit permission is required')
            existing=list(CACHE.glob('dhaka-source.*'))
            if not existing:
                downloader=shutil.which('yt-dlp')
                if not downloader: raise RuntimeError('Install yt-dlp to download the permissioned Dhaka source')
                subprocess.run([downloader,'--no-playlist','-f','bestaudio','-o',str(CACHE/'dhaka-source.%(ext)s'),r['source_url']],check=True)
                existing=list(CACHE.glob('dhaka-source.*'))
            src=next(p for p in existing if p.suffix in ['.webm','.m4a','.mp3','.opus'])
            preview=None
        else:
            html=fetch(r['source_url'],CACHE/(city['id']+'.html')).decode()
            expected='Creative Commons 0' if r['license']=='CC0 1.0' else 'Attribution 4.0'
            if expected not in html: raise ValueError('License changed')
            urls=re.findall(r'https://cdn\.freesound\.org/previews/[^\s\"<>]+-hq\.mp3',html)
            if not urls: raise ValueError('No explicit preview URL: '+city['id'])
            preview=urls[0]; src=CACHE/(city['id']+'.mp3'); fetch(preview,src)
        wav=CACHE/(city['id']+'.wav')
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(src),'-ss',str(r.get('segment_start_s',0)),'-t','25','-ar','44100','-ac','2',str(wav)],check=True)
        rate,data=wavfile.read(wav); signal=data.astype(np.float64)/32768
        peak=float(np.max(np.abs(signal))); rms=float(np.sqrt(np.mean(signal**2)))
        # Fixed gain only: target -24 dBFS RMS, ceiling -3 dBFS peak, maximum +12 dB.
        factor=min(10**(-24/20)/max(rms,1e-10),10**(-3/20)/max(peak,1e-10),10**(12/20))
        signal*=factor
        # 40 ms edge fades prevent cuts clicking; no crossfade or looping.
        fade=min(int(rate*.04),len(signal)//2)
        signal[:fade]*=np.linspace(0,1,fade)[:,None]; signal[-fade:]*=np.linspace(1,0,fade)[:,None]
        wavfile.write(wav,rate,(np.clip(signal,-1,1)*32767).astype(np.int16))
        target=ROOT/'traffic-audio'/(city['id']+'.mp3')
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(wav),'-codec:a','libmp3lame','-b:a','128k',str(target)],check=True)
        city['audio']='traffic-audio/'+target.name; city['status']='available'; city.pop('unavailable_reason',None)
        r.update(preview_url=preview,download_basis='Permissioned source audio track' if r.get('source_type')=='youtube' else 'Freesound publicly supplied high-quality MP3 preview; original not bundled',source_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),output_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),excerpt_duration_s=round(len(signal)/rate,3),gain_db=round(20*np.log10(factor),3),processed_peak_dbfs=round(20*np.log10(max(np.max(np.abs(signal)),1e-10)),3))
        (ROOT/'recordings.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
if __name__=='__main__': main()
