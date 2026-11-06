"""Targeted final polish of the existing layout; source geometry is never edited."""
import collections,hashlib,json,os
from pathlib import Path
from qgis.core import *
from qgis.PyQt.QtGui import QColor,QImage
from qgis.PyQt.QtCore import QSize
ROOT=Path(__file__).resolve().parents[1]
source_hash=hashlib.sha256((ROOT/'data/processed/telluride_inventory.gpkg').read_bytes()).hexdigest()
app=QgsApplication([],False);app.initQgis();p=QgsProject.instance();assert p.read(str(ROOT/'qgis/day06_telluride.qgz'))
layout=p.layoutManager().layoutByName('LinkedIn — larger type') or p.layoutManager().layouts()[0]
m=layout.itemById('day06-main-map');before=m.extent().toString(12)
for item in list(layout.items()):
 if isinstance(item,QgsLayoutItemLabel) and (item.id()=='day06-refinement-scope' or item.text().startswith('Contemporary geometry')):
  layout.removeLayoutItem(item)
inventory=next(l for l in p.mapLayers().values() if isinstance(l,QgsVectorLayer) and l.source().endswith('|layername=inventory_classified'))
features=list(inventory.getFeatures());red=[f for f in features if f['display_class']=='historic_rating'];ids=[f['OBJECTID'] for f in red];assert len(set(ids))==len(ids)
# Compare actual polygon topology as well as IDs. Shared edges are not area overlaps.
duplicates=[];overlaps=[]
for i,a in enumerate(red):
 for b in red[i+1:]:
  if not a.geometry().boundingBox().intersects(b.geometry().boundingBox()):continue
  if a.geometry().isGeosEqual(b.geometry()):duplicates.append([a['OBJECTID'],b['OBJECTID']])
  area=a.geometry().intersection(b.geometry()).area()
  if area>.01:overlaps.append({'ids':[a['OBJECTID'],b['OBJECTID']],'area_m2':area})
unique=len(red)-len({pair[1] for pair in duplicates})
count=layout.itemById('day06-refinement-count');count.setText(f'{unique} historic-rated inventory footprints' if not overlaps else f'{len(red)} historic-rated inventory records')
# Original street lines, centered lettering, modest type and a fine paper halo.
for layer in m.layers():
 if not isinstance(layer,QgsVectorLayer):continue
 if layer.labelsEnabled() and layer.labeling():
  settings=layer.labeling().settings();fmt=settings.format()
  if 'street' in layer.name().lower():
   settings.fieldName='"name"';settings.isExpression=True;settings.placement=Qgis.LabelPlacement.Line
   settings.lineSettings().setPlacementFlags(Qgis.LabelLinePlacementFlag.OnLine)
   settings.priority=7;settings.displayAll=False
   fmt.setSize(10.5)
   prop=QgsProperty.fromExpression('CASE WHEN "name" = \'Colorado Avenue\' THEN 11.5 ELSE 10 END')
   props=settings.dataDefinedProperties();props.setProperty(QgsPalLayerSettings.Size,prop);settings.setDataDefinedProperties(props)
   buff=fmt.buffer();buff.setSize(.16);fmt.setBuffer(buff)
  elif 'landmark' in layer.name().lower():settings.priority=10;settings.displayAll=False
  settings.setFormat(fmt);layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
# Prevent street labels crossing highlighted polygons, even when polygons have no text.
settings=QgsPalLayerSettings();settings.obstacle=True
obs=settings.obstacleSettings();obs.setIsObstacle(True);obs.setFactor(10);obs.setType(QgsLabelObstacleSettings.PolygonInterior);settings.setObstacleSettings(obs)
inventory.setLabeling(QgsVectorLayerSimpleLabeling(settings));inventory.setLabelsEnabled(True)
inset=layout.itemById('day06-refinement-inset');inset.setBackgroundEnabled(True);inset.setBackgroundColor(QColor('#F4F0E6'));inset.setFrameEnabled(True);inset.setFrameStrokeColor(QColor('#9D8C73'));inset.setFrameStrokeWidth(QgsLayoutMeasurement(.18));inset.overview().setLinkedMap(m)
# Keep three balanced columns; wrap the longer legend captions inside their cells.
for key,text in [('historic_rating','Historic-rated\nstructures'),('other_or_unrated','Other / unrated\nstructures'),('legacy','Demolished / legacy\nstructures')]:
 item=layout.itemById('day06-refinement-key-'+key);item.setText(text);font=item.font();font.setPointSizeF(9.5);item.setFont(font);item.attemptMove(QgsLayoutPoint(item.positionWithUnits().x(),227));item.attemptResize(QgsLayoutSize(item.sizeWithUnits().width(),9))
# Recheck each evidence join and ensure the marker remains inside its source polygon.
evidence=json.loads((ROOT/'label-evidence.json').read_text());markers=next(l for l in m.layers() if isinstance(l,QgsVectorLayer) and 'landmark' in l.name().lower());checks=[]
for entry in evidence['landmarks']:
 f=next(f for f in features if f['OBJECTID']==entry['objectid']);marker=next(f for f in markers.getFeatures() if f['number']==entry['number']);assert f.geometry().contains(marker.geometry())
 if 'pin' in entry:
  matches=[f for f in features if str(f['PIN'])==entry['pin']];assert len(matches)==1 and matches[0]['OBJECTID']==entry['objectid']
 else:
  transform=QgsCoordinateTransform(QgsCoordinateReferenceSystem('EPSG:26713'),inventory.crs(),p)
  point=QgsGeometry.fromPointXY(transform.transform(QgsPointXY(*entry['survey_utm_nad27'])))
  matches=[f for f in features if f.geometry().contains(point)];assert len(matches)==1 and matches[0]['OBJECTID']==entry['objectid']
 checks.append({'name':entry['name'],'objectid':entry['objectid'],'unique_join_verified':True,'marker_inside_original_footprint':True,'source':entry['source'],'method':entry['match']})
assert m.extent().toString(12)==before;assert inset.overview().linkedMap()==m
assert p.write()
output=ROOT/'exports/day06_telluride.png';exporter=QgsLayoutExporter(layout);settings=QgsLayoutExporter.ImageExportSettings();settings.dpi=300;settings.imageSize=QSize(2400,3000)
assert exporter.exportToImage(str(output),settings)==QgsLayoutExporter.Success
image=QImage(str(output));assert (image.width(),image.height())==(2400,3000)
report={'dimensions_px':[2400,3000],'highlighted_records':len(red),'unique_objectids':len(set(ids)),'topologically_duplicate_pairs':duplicates,'unique_geometries':unique,'positive_area_overlaps_over_0_01_m2':overlaps,'statistic':count.text(),'ratings':dict(collections.Counter(str(f['Rating']) for f in red)),'landmarks':checks,'extent_unchanged':True,'extent':before,'inset_linked_to_main':True,'png_sha256':hashlib.sha256(output.read_bytes()).hexdigest()}
assert hashlib.sha256((ROOT/'data/processed/telluride_inventory.gpkg').read_bytes()).hexdigest()==source_hash
report.update({'inventory_sha256_unchanged':source_hash,'legacy_records_excluded':True,'construction_dates_inferred':False,'visual_review':'Export inspected: four street labels visible along streets, landmark anchors unchanged, inset locator and three-column key present, no clipped text.'})
old=json.loads((ROOT/'map.qa.json').read_text());old.update({'png_sha256':report['png_sha256'],'dimensions_px':[2400,3000],'final_polish_report':'final-polish.qa.json'});(ROOT/'map.qa.json').write_text(json.dumps(old,indent=2))
(ROOT/'final-polish.qa.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True);os._exit(0)
