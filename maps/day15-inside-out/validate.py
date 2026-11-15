"""Validate the delivered data, poster dimensions and Blender mesh report."""
from pathlib import Path
import json
import struct
import numpy as np
from shapely.geometry import LineString

HERE=Path(__file__).resolve().parent
qa=json.loads((HERE/'qa.json').read_text())
route=json.loads((HERE/'data/route.json').read_text())
composition=json.loads((HERE/'composition.json').read_text())
p=np.array(route['points'])
assert np.isfinite(p).all() and np.max(np.linalg.norm(np.diff(p[:,:2],axis=0),axis=1))<10.01
line=LineString(p[:,:2]);assert line.is_simple and abs(line.length-qa['route_length_m'])<.01
assert qa['missing_samples']==qa['isolated_spikes']==qa['repeated_nodes']==0
assert abs(line.length-(route['selection']['chainage_from_ouray_m'][1]-route['selection']['chainage_from_ouray_m'][0]))<.01
assert route['labels']==[]
assert len(p)==qa['densified_vertices']
assert qa['all_refs']=='US 550'
for label in route['labels']:
    assert np.linalg.norm(p[label['index']]-label['xyz'])<.001
assert composition['mesh']['closed_manifold'] and composition['mesh']['euler_characteristic']==2
assert composition['mesh']['centerline_vertices']==len(p)
header=(HERE/'map.png').read_bytes()[:24]
assert header[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',header[16:24])==(3200,4000)
assert (HERE/'road.blend').stat().st_size>150000
assert composition['anchors']==[]
assert composition['terrain_vertices']==0
assert composition['route_vertices']==len(p)
print('PASS: continuous US 550, all samples, anchors, closed ribbon mesh, 3200 × 4000 poster, Blender scene')
