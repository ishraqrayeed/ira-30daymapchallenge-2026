"""Blender 4.5+ background: build a geographically faithful, camera-ready poster."""
import bpy
import json
import math
import sys
from pathlib import Path
from mathutils import Vector, Quaternion
from bpy_extras.object_utils import world_to_camera_view

HERE=Path(__file__).resolve().parent
config=json.loads((HERE/'segment.json').read_text())
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
preview='--preview' in args
az=float(args[args.index('--az')+1]) if '--az' in args else config['camera']['azimuth']
elev=float(args[args.index('--elev')+1]) if '--elev' in args else config['camera']['elevation']
roll=float(args[args.index('--roll')+1]) if '--roll' in args else config['camera']['roll']
tag=f'{az:g}-{elev:g}-{roll:g}'
vertical=float(args[args.index('--vertical')+1]) if '--vertical' in args else config['default_vertical_scale']
tag+=f'-z{vertical:g}'
data=json.loads((HERE/'data/route.json').read_text())
pts=[Vector(p) for p in data['points']]
origin=(pts[0]+pts[-1])/2
origin.z=min(p.z for p in pts)
pts=[(p-origin)/1000 for p in pts]  # all three dimensions in km, true vertical scale
for p in pts:p.z*=vertical
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=int(args[args.index('--samples')+1]) if '--samples' in args else (24 if preview else 96)
scene.cycles.use_denoising=True
scene.render.resolution_x=1000 if preview else 3200
scene.render.resolution_y=1250 if preview else 4000
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.image_settings.color_mode='RGB'
scene.render.dither_intensity=0
scene.render.use_file_extension=True
scene.render.image_settings.compression=40
scene.render.use_overwrite=True
scene.render.film_transparent=False
scene.render.image_settings.color_depth='8'
scene.render.use_stamp=False
scene.render.use_compositing=True
scene.render.use_sequencer=False
scene.world.color=(.18,.18,.18)
scene.view_settings.view_transform='Standard'
scene.view_settings.look='None'
scene.view_settings.exposure=0
scene.view_settings.gamma=1

def material(name,color,emission=False):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    n=m.node_tree.nodes.get('Principled BSDF');n.inputs['Base Color'].default_value=(*color,1)
    n.inputs['Roughness'].default_value=.72
    if emission:
        nodes=m.node_tree.nodes;nodes.clear()
        n=nodes.new('ShaderNodeEmission');n.inputs['Color'].default_value=(*color,1)
        output=nodes.new('ShaderNodeOutputMaterial');m.node_tree.links.new(n.outputs[0],output.inputs['Surface'])
    return m
amber=material('Warm amber • road top',(.68,.30,.065))
amber.node_tree.nodes.get('Principled BSDF').inputs['Emission Color'].default_value=(.68,.30,.065,1)
amber.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=.55
edge=material('Burnished dark edge',(.19,.065,.017))
edge.node_tree.nodes.get('Principled BSDF').inputs['Emission Color'].default_value=(.19,.065,.017,1)
edge.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=.65
cream=material('Warm ivory typography',(.84,.81,.73),True)
muted=material('Muted typography',(.36,.39,.39),True)
accent=material('Amber typography',(.84,.43,.14),True)
background=material('Matte charcoal',(.011,.015,.018),True)

# Two rails around the unchanged centerline; bounded miters retain tight hairpins.
width=config['ribbon_width_m']/1000;thickness=config['ribbon_thickness_m']/1000
verts=[]
for i,p in enumerate(pts):
    before=pts[max(0,i-1)];after=pts[min(len(pts)-1,i+1)]
    tangent=after-before;tangent.z=0;tangent.normalize()
    normal=Vector((-tangent.y,tangent.x,0))
    for side,zoff in [(-1,0),(1,0),(-1,-thickness),(1,-thickness)]:
        verts.append(p+normal*(side*width/2)+Vector((0,0,zoff)))
faces=[];mats=[]
for i in range(len(pts)-1):
    a=i*4;b=a+4
    faces.extend([(a,a+1,b+1,b),(a+2,b+2,b+3,a+3),(a,b,b+2,a+2),(a+1,a+3,b+3,b+1)])
    mats.extend([0,1,1,1])
faces.extend([(0,2,3,1),(len(verts)-4,len(verts)-3,len(verts)-1,len(verts)-2)]);mats.extend([1,1])
faces=[tuple(reversed(f)) for f in faces]  # outward normals, including +Z on the top
mesh=bpy.data.meshes.new('US 550 • continuous ribbon');mesh.from_pydata(verts,[],faces);mesh.update()
from collections import Counter
edge_counts=Counter(tuple(sorted((a,b))) for face in faces for a,b in zip(face,face[1:]+face[:1]))
assert all(n==2 for n in edge_counts.values()), 'Ribbon must be closed and manifold'
assert len(verts)-len(edge_counts)+len(faces)==2, 'Ribbon topology must be a single closed strip'
mesh_qa=dict(vertices=len(verts),faces=len(faces),edges=len(edge_counts),closed_manifold=True,
             euler_characteristic=2,centerline_vertices=len(pts))
road=bpy.data.objects.new(f'US 550 • {width*1000:g} m display width • {vertical:g}× vertical',mesh);scene.collection.objects.link(road)
road.data.materials.append(amber);road.data.materials.append(edge)
for poly,idx in zip(mesh.polygons,mats):poly.material_index=idx
road['horizontal_crs']='EPSG:26913';road['vertical_exaggeration']=vertical
road['width_m']=width*1000;road['thickness_m']=thickness*1000;road['elevation']='3DEP DEM approximation; not surveyed road height'

def area(name,location,power,size):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=location
    o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
area('Large warm key',(-8,-4,15),2200,12)
area('Soft fill',(6,10,10),900,10)
camdata=bpy.data.cameras.new('Perspective switchbacks');cam=bpy.data.objects.new('Perspective switchbacks',camdata);scene.collection.objects.link(cam);scene.camera=cam
camdata.type='PERSP';camdata.lens=config['camera']['focal_length_mm'];camdata.sensor_fit='HORIZONTAL';camdata.clip_start=.001;camdata.clip_end=500
aspect=.8
a=math.radians(az);e=math.radians(elev)
direction=Vector((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)))
rotation=(-direction).to_track_quat('-Z','Y') @ Quaternion(Vector((0,0,1)),math.radians(roll))
cam.rotation_euler=rotation.to_euler()
# Fit the isolated ribbon, including its edges and end caps.
fitpoints=verts
center=Vector(tuple((min(p[i] for p in fitpoints)+max(p[i] for p in fitpoints))/2 for i in range(3)))
def screen(p):return world_to_camera_view(scene,cam,p)
low=.03;high=5.
for _ in range(40):
    distance=(low+high)/2;cam.location=center+direction*distance;bpy.context.view_layer.update()
    projected=[screen(p) for p in fitpoints]
    pw=max(p.x for p in projected)-min(p.x for p in projected)
    ph=max(p.y for p in projected)-min(p.y for p in projected)
    if min(p.z for p in projected)<=.01 or pw>.86 or ph>.48:low=distance
    else:high=distance
cam.location=center+direction*high;bpy.context.view_layer.update()
projected=[screen(p) for p in fitpoints]
camdata.shift_x=(min(p.x for p in projected)+max(p.x for p in projected))/2-.5
camdata.shift_y=((min(p.y for p in projected)+max(p.y for p in projected))/2-.44)/aspect
bpy.context.view_layer.update()
frame=camdata.view_frame(scene=scene)
fx0,fx1=min(p.x for p in frame),max(p.x for p in frame)
fy0,fy1=min(p.y for p in frame),max(p.y for p in frame)
fz=abs(frame[0].z)
overlay_depth=.1
W=(fx1-fx0)*overlay_depth/fz;H=(fy1-fy0)*overlay_depth/fz
def at(u,v,depth=overlay_depth):
    return cam.location+rotation@Vector(((fx0+(fx1-fx0)*u)*depth/fz,(fy0+(fy1-fy0)*v)*depth/fz,-depth))
def text(name,body,u,v,size,mat,font='sans',align='LEFT'):
    c=bpy.data.curves.new(name,'FONT');c.body=body;c.size=size*H;c.align_x=align
    c.space_character=1.05;c.space_line=1.05
    path='/System/Library/Fonts/Supplemental/'+('Georgia.ttf' if font=='serif' else 'Arial.ttf')
    if Path(path).exists():c.font=bpy.data.fonts.load(path,check_existing=True)
    o=bpy.data.objects.new(name,c);scene.collection.objects.link(o);o.location=at(u,v);o.rotation_euler=cam.rotation_euler;c.materials.append(mat)
    return o
def line2d(name,coords,mat,radius=.00025):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.bevel_depth=H*radius;c.bevel_resolution=2
    s=c.splines.new('POLY');s.points.add(len(coords)-1)
    for p,(u,v) in zip(s.points,coords):p.co=(*at(u,v,.099),1)
    o=bpy.data.objects.new(name,c);scene.collection.objects.link(o);c.materials.append(mat)

# A camera-facing matte background gives an even charcoal field without terrain.
bpy.ops.mesh.primitive_plane_add(size=2,location=at(.5,.5,100))
back=bpy.context.object;back.name='Charcoal backdrop';back.rotation_euler=cam.rotation_euler;back.scale=(W*100/overlay_depth,H*100/overlay_depth,1);back.data.materials.append(background)
text('Day and theme','15  /  INSIDE OUT',.085,.932,.012,accent)
text('Title','The Road Carved\nInto the Mountains',.08,.857,.044,cream,'serif')
text('Subtitle','Switchbacks of the Million Dollar Highway',.085,.740,.0125,muted)
line2d('Header rule',[(.085,.708),(.915,.708)],muted,.00012)

anchors=[]

line2d('Footer rule',[(.085,.163),(.915,.163)],muted,.00012)
text('Method note','OpenStreetMap centerline · USGS 3DEP elevation',.085,.110,.010,muted)
text('Attribution','© OpenStreetMap contributors · USGS 3DEP · 30DayMapChallenge 2026',.085,.066,.0082,muted)
scene['reproduction']='blender --background --python build_scene.py'
scene['camera_angles']=dict(azimuth=az,elevation=elev,roll=roll)
scene.render.filepath=str(HERE/('review/'+tag+'.png' if preview else 'map.png'))
Path(scene.render.filepath).parent.mkdir(exist_ok=True)
bpy.ops.file.pack_all()
if not preview:
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'road.blend'))
    (HERE/'composition.json').write_text(json.dumps(dict(camera=dict(azimuth=az,elevation=elev,roll=roll),anchors=anchors,resolution=[3200,4000],vertical_scale=vertical,width_m=width*1000,thickness_m=thickness*1000,projection='perspective',route_vertices=len(pts),terrain_vertices=0,mesh=mesh_qa),indent=2)+'\n')
bpy.ops.render.render(write_still=True)
