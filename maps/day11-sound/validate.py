"""Validate the gallery's bundled GIS/audio deliverables without live requests."""
from pathlib import Path
import hashlib,json,subprocess,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parent
m=json.loads((ROOT/'recordings.json').read_text());qa=json.loads((ROOT/'streets/qa.json').read_text())
expected=['dhaka','new-york','mumbai','london','tokyo','cairo','bangkok','sydney','istanbul','sao-paulo','johannesburg','mexico-city']
assert [c['id'] for c in m['cities']]==expected
assert len(qa)==12
for c in m['cities']:
 p=ROOT/'streets'/f"{c['id']}.svg";svg=ET.parse(p).getroot();ns={'s':'http://www.w3.org/2000/svg'}
 assert svg.attrib['viewBox']=='0 0 300 300'
 circle=svg.find('s:defs/s:clipPath/s:circle',ns)
 assert circle.attrib=={'cx':'150','cy':'150','r':'150'}
 assert all(path.get('d') for path in svg.findall('.//s:path',ns))
 q=qa[c['id']];assert q['radius_m']==1000 and q['rendered_line_parts']>10
 assert q['center_lat_lon']==c['map_center']
 assert hashlib.sha256(p.read_bytes()).hexdigest()==q['sha256']
 if not c['audio']:
  assert c['status']=='unavailable' and c.get('unavailable_reason')
  continue
 assert c['recording'] and c['recording']['approved']
 assert c['audio'] and (ROOT/c['audio']).is_file()
 assert hashlib.sha256((ROOT/c['audio']).read_bytes()).hexdigest()==c['recording']['output_sha256']
 probe=json.loads(subprocess.check_output(['ffprobe','-v','quiet','-show_format','-of','json',str(ROOT/c['audio'])]))
 assert 14 <= float(probe['format']['duration']) <= 26
 assert c['recording']['processed_peak_dbfs'] <= -2.99
print(f"PASS: 12 OSM SVGs, consistent scale/centers/hashes; {sum(bool(c['audio']) for c in m['cities'])} verified audio files and explicit unavailable states; duration and peak checks.")
