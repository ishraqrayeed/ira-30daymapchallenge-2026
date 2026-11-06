"""Export public browser vectors from the unchanged QGIS inventory and context layers."""
import hashlib,json,math,os
from pathlib import Path
from qgis.core import *
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'web';OUT.mkdir(exist_ok=True)
app=QgsApplication([],False);app.initQgis();p=QgsProject.instance();assert p.read(str(ROOT/'qgis/day06_telluride.qgz'))
original=ROOT/'data/processed/telluride_inventory.gpkg';before=hashlib.sha256(original.read_bytes()).hexdigest()
crs=QgsCoordinateReferenceSystem('EPSG:4326');tr=QgsCoordinateTransform(p.crs(),crs,p)
def layer(name):return next(l for l in p.mapLayers().values() if isinstance(l,QgsVectorLayer) and l.source().endswith('|layername='+name))
def clean(v):return None if QgsVariantUtils.isNull(v) else v
landmarks=layer('landmark_labels');names={f['objectid']:{'name':f['name'],'number':f['number'],'source':f['source']} for f in landmarks.getFeatures()}
def feature(f,properties,tolerance=0):
 g=QgsGeometry(f.geometry())
 if tolerance:g=g.simplify(tolerance)
 g.transform(tr);assert g.isGeosValid() and not g.isEmpty()
 return {'type':'Feature','properties':properties,'geometry':json.loads(g.asJson(7))}
def collection(features):return {'type':'FeatureCollection','features':features}
source=layer('inventory_classified')
buildings=collection([feature(f,{'id':f['OBJECTID'],'rating':clean(f['Rating']),'status':clean(f['status']),'group':f['display_class'],'bldg_id':clean(f['BLDG_ID']),**names.get(f['OBJECTID'],{})}) for f in source.getFeatures()])
streets=collection([feature(f,{'name':clean(f['name']),'source_id':str(f['osmid'])}) for f in layer('streets').getFeatures()])
contours=collection([feature(f,{'elevation_m':f['elevation_m'],'index':int(f['elevation_m'])%250==0},1.0) for f in layer('terrain_contours').getFeatures()])
river=collection([feature(f,{'name':f['name'],'osm_ways':f['osm_ways']}) for f in layer('river').getFeatures()])
points=collection([feature(f,{'number':f['number'],'name':f['name'],'key_name':f['key_name'],'id':f['objectid'],'source':f['source']}) for f in landmarks.getFeatures()])
main=next(i for i in p.layoutManager().layouts()[0].items() if isinstance(i,QgsLayoutItemMap) and i.id()=='day06-main-map')
core=QgsGeometry.fromRect(main.extent())
def bounds(rect):
 b=tr.transformBoundingBox(rect);return [[b.yMinimum(),b.xMinimum()],[b.yMaximum(),b.xMaximum()]]
label_features=[]
for group in [layer('street_labels'),layer('river')]:
 for f in group.getFeatures():
  g=f.geometry().intersection(core)
  parts=g.asMultiPolyline() if g.isMultipart() else [g.asPolyline()]
  parts=[pts for pts in parts if len(pts)>1]
  if not parts:continue
  g=max([QgsGeometry.fromPolylineXY(pts) for pts in parts],key=lambda v:v.length());d=g.length()/2;at=g.interpolate(d);a=g.interpolate(max(0,d-5)).asPoint();b=g.interpolate(min(g.length(),d+5)).asPoint();a=tr.transform(QgsPointXY(a));b=tr.transform(QgsPointXY(b));at.transform(tr)
  label_features.append({'type':'Feature','geometry':json.loads(at.asJson(7)),'properties':{'name':f['name'],'kind':'river' if group.name()=='river' else 'street','direction':[[a.y(),a.x()],[b.y(),b.x()]]}})
assert len(buildings['features'])==1131 and sum(f['properties']['group']=='historic_rating' for f in buildings['features'])==293
assert len({f['properties']['id'] for f in buildings['features']})==1131
summary={'source_records':1131,'historic_rated_footprints':293,'groups':{name:sum(f['properties']['group']==name for f in buildings['features']) for name in ['historic_rating','other_or_unrated','legacy']},'pre1900_count':None,'source_date':'2026-11-05','downtown_bounds':bounds(main.extent()),'town_bounds':bounds(source.extent()),'terrain_bounds':bounds(layer('terrain_contours').extent()),'construction_dates_assigned':False}
data={'summary':summary,'buildings':buildings,'streets':streets,'contours':contours,'river':river,'landmarks':points,'labels':collection(label_features)}
file=OUT/'map-data.json';file.write_text(json.dumps(data,separators=(',',':'),ensure_ascii=False));assert hashlib.sha256(original.read_bytes()).hexdigest()==before
qa={'source_records':1131,'historic_rated_footprints':293,'unique_objectids':1131,'landmarks':len(points['features']),'vector_layers':list(data.keys())[1:],'coordinate_crs':'EPSG:4326','contour_simplification_m':1.0,'inventory_simplified':False,'public_properties':'Allowlisted rating, status, classification and source identifiers; no inferred dates','original_inventory_sha256':before,'source_inventory_unchanged':True,'web_data_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'web_data_bytes':file.stat().st_size}
(ROOT/'web-data.qa.json').write_text(json.dumps(qa,indent=2));print(json.dumps(qa,indent=2),flush=True);os._exit(0)
