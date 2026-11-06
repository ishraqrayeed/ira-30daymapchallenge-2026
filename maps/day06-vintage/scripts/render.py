"""Refine the existing editable QGIS project without rebuilding or modifying data."""
import collections,hashlib,json,os
from pathlib import Path
from qgis.core import *
from qgis.PyQt.QtCore import Qt,QSize
from qgis.PyQt.QtGui import QColor,QFont,QImage
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/processed';E=ROOT/'exports';Q=ROOT/'qgis';PROJECT=Q/'day06_telluride.qgz'
app=QgsApplication([],False);app.initQgis();p=QgsProject.instance();assert p.read(str(PROJECT)), 'Existing QGIS project required'
gpkg=D/'telluride_inventory.gpkg';before=hashlib.sha256(gpkg.read_bytes()).hexdigest()
baseline={'original_map_width_m':2856,'original_map_height_m':2550}
def source_layer(name):
 return next(l for l in p.mapLayers().values() if isinstance(l,QgsVectorLayer) and l.source().endswith('|layername='+name))
buildings=source_layer('inventory_classified');streets=source_layer('streets');contours=source_layer('terrain_contours')
layout=p.layoutManager().layouts()[0];m=next(i for i in layout.items() if isinstance(i,QgsLayoutItemMap) and not i.id().startswith('day06-refinement-'));m.setId('day06-main-map')
# Downtown core, approximately twice the previous main-map scale. The valley remains north-up.
m.attemptResize(QgsLayoutSize(179.2,156))
center=QgsPointXY(252820,4202700);w=1250;h=w*156/179.2
m.zoomToExtent(QgsRectangle(center.x()-w/2,center.y()-h/2,center.x()+w/2,center.y()+h/2));m.setMapRotation(0)
p.viewSettings().setDefaultViewExtent(QgsReferencedRectangle(m.extent(),p.crs()))
root=QgsRuleBasedRenderer.Rule(None)
for filt,color,width in [('"elevation_m" % 250 = 0','149,132,105,145','0.14'),('"elevation_m" % 250 <> 0','159,144,119,100','0.070')]:
 rule=QgsRuleBasedRenderer.Rule(QgsLineSymbol.createSimple({'line_color':color,'line_width':width,'joinstyle':'round'}));rule.setFilterExpression(filt);root.appendChild(rule)
contours.setRenderer(QgsRuleBasedRenderer(root))
for cat in buildings.renderer().categories():
 if cat.value()=='historic_rating':
  buildings.renderer().updateCategorySymbol(buildings.renderer().categoryIndexForValue(cat.value()),QgsFillSymbol.createSimple({'color':'143,56,42,255','outline_color':'126,48,37,255','outline_width':'0.09','outline_style':'solid','joinstyle':'miter'}))
# Reuse the existing header and map item; replace only subtitle/footer furniture.
for item in list(layout.items()):
 if not isinstance(item,QgsLayoutItem):continue
 if item.id().startswith('day06-refinement-'):
  layout.removeLayoutItem(item);continue
 if isinstance(item,QgsLayoutItemLabel):
  text=item.text()
  if text=='The Historic Structures Inventory':item.setText('Echoes of a Mining Town')
  elif text.startswith(('Brick red:','Pale ink:','Downtown detail','Town of Telluride  /')):layout.removeLayoutItem(item)
labels=[]
def label(text,x,y,w,h,size=9,color='#443A2D',italic=False,align=Qt.AlignHCenter,ident=''):
 item=QgsLayoutItemLabel(layout);item.setId('day06-refinement-'+ident);item.setText(text);f=QFont('Baskerville');f.setPointSizeF(size);f.setItalic(italic);item.setFont(f);item.setFontColor(QColor(color));item.setHAlign(align);item.setVAlign(Qt.AlignVCenter);item.setMargin(0);layout.addLayoutItem(item);item.attemptMove(QgsLayoutPoint(x,y));item.attemptResize(QgsLayoutSize(w,h));labels.append(text);return item
historic=[f for f in buildings.getFeatures() if f['display_class']=='historic_rating'];shown=[f for f in buildings.getFeatures() if f.geometry().intersects(m.extent())];shown_red=[f for f in shown if f['display_class']=='historic_rating']
assert len(historic)==293
label(f'{len(historic)} footprints with historic ratings · town inventory',12,54,179.2,6,9.5,color='#8F382A',ident='count')
# A quiet locator inset shows the entire unchanged inventory and links its extent to the main detail.
inset=QgsLayoutItemMap(layout);inset.setId('day06-refinement-inset');layout.addLayoutItem(inset)
inset.attemptMove(QgsLayoutPoint(143,68));inset.attemptResize(QgsLayoutSize(45,30));inset.setCrs(p.crs());inset.setLayers([buildings,streets,contours]);inset.setKeepLayerSet(True)
full=QgsRectangle(buildings.extent());full.grow(125);inset.zoomToExtent(full);inset.setBackgroundEnabled(True);inset.setBackgroundColor(QColor('#F4F0E6'));inset.setFrameEnabled(True);inset.setFrameStrokeColor(QColor('#B8AA94'));inset.setFrameStrokeWidth(QgsLayoutMeasurement(.10));inset.setZValue(m.zValue()+10)
overview=inset.overview();overview.setLinkedMap(m);overview.setFrameSymbol(QgsFillSymbol.createSimple({'style':'no','outline_color':'143,56,42,255','outline_width':'0.22'}))
label('TOWN CONTEXT',143,62,45,5,6.5,ident='inset-title')
# Add sparse verified labels, retaining the original source GeoPackage unchanged.
from label_context import prepare_labels
street_labels,river,landmark_labels,label_audit=prepare_labels(p,buildings,streets,ROOT)
streets.setLabelsEnabled(False)
def line_labels(layer,expression,size=8,italic=False,color='#625748'):
 settings=QgsPalLayerSettings();settings.fieldName=expression;settings.isExpression=True;settings.placement=QgsPalLayerSettings.Line;settings.scaleVisibility=False;settings.labelPerPart=False
 fmt=QgsTextFormat();font=QFont('Baskerville');font.setItalic(italic);fmt.setFont(font);fmt.setSize(size);fmt.setColor(QColor(color));buffer=QgsTextBufferSettings();buffer.setEnabled(True);buffer.setSize(.4);buffer.setColor(QColor('#F4F0E6'));fmt.setBuffer(buffer);settings.setFormat(fmt);layer.setLabeling(QgsVectorLayerSimpleLabeling(settings));layer.setLabelsEnabled(True)
street_labels.renderer().setSymbol(QgsLineSymbol.createSimple({'line_color':'0,0,0,0','line_width':'0'}));line_labels(street_labels,'upper("name")',8)
river.renderer().setSymbol(QgsLineSymbol.createSimple({'line_color':'122,112,92,190','line_width':'.17','joinstyle':'round'}));line_labels(river,'upper("name")',8,True)
landmark_labels.renderer().setSymbol(QgsMarkerSymbol.createSimple({'name':'circle','color':'244,240,230,255','outline_color':'143,56,42,255','outline_width':'.18','size':'3.4'}))
settings=QgsPalLayerSettings();settings.fieldName='number';settings.placement=Qgis.LabelPlacement.OverPoint;settings.dist=0;settings.quadOffset=Qgis.LabelQuadrantPosition.Over
fmt=QgsTextFormat();fmt.setFont(QFont('Baskerville',7));fmt.setSize(7);fmt.setColor(QColor('#8F382A'));settings.setFormat(fmt);landmark_labels.setLabeling(QgsVectorLayerSimpleLabeling(settings));landmark_labels.setLabelsEnabled(True)
m.setLayers([landmark_labels,street_labels,river,buildings,streets,contours])
# The inset remains quiet and uses only the original three context layers.
for number,x,tw in [(1,15,60),(2,85,46),(3,143,46)]:
 item=next(f for f in landmark_labels.getFeatures() if f['number']==number)
 circle=QgsLayoutItemShape(layout);circle.setId('day06-refinement-landmark-key-'+str(number));circle.setShapeType(QgsLayoutItemShape.Ellipse);circle.setSymbol(QgsFillSymbol.createSimple({'color':'244,240,230,255','outline_color':'143,56,42,255','outline_width':'.16'}));layout.addLayoutItem(circle);circle.attemptMove(QgsLayoutPoint(x,220.5));circle.attemptResize(QgsLayoutSize(3.4,3.4))
 label(str(number),x,219.2,3.4,6,7,color='#8F382A',ident='landmark-number-'+str(number))
 label(item['key_name'],x+5.5,219.2,tw-5.5,6,7.6,align=Qt.AlignLeft,ident='landmark-name-'+str(number))

# Small swatches use the same source class symbols; the legacy patch stays unfilled.
legend=[(24,'historic_rating','Historic ratings',49),(82,'other_or_unrated','Other / unrated',48),(139,'legacy','Demolished / legacy',45)]
for x,key,text,tw in legend:
 symbol=next(c.symbol().clone() for c in buildings.renderer().categories() if c.value()==key)
 if key=='legacy': symbol=QgsFillSymbol.createSimple({'style':'no','outline_color':'145,128,101,230','outline_width':'0.12','outline_style':'dash'})
 swatch=QgsLayoutItemShape(layout);swatch.setId('day06-refinement-swatch-'+key);swatch.setShapeType(QgsLayoutItemShape.Rectangle);swatch.setSymbol(symbol);layout.addLayoutItem(swatch);swatch.attemptMove(QgsLayoutPoint(x,230));swatch.attemptResize(QgsLayoutSize(4.8,2.7));swatch.setFrameEnabled(False)
 label(text,x+7,228.5,tw,6,8,align=Qt.AlignLeft,ident='key-'+key)
label('Contemporary geometry · Construction dates not assigned',12,237,179.2,6,7.5,italic=True,ident='scope')
label('Town of Telluride · © OpenStreetMap contributors (ODbL) · USGS 3DEP',12,246,179.2,5,7,ident='credits')
p.setTitle('TELLURIDE — Echoes of a Mining Town');p.setFileName(str(PROJECT));assert p.write()
settings=QgsLayoutExporter.ImageExportSettings();settings.dpi=300;settings.imageSize=QSize(2400,3000);settings.exportMetadata=False
assert QgsLayoutExporter(layout).exportToImage(str(E/'day06_telluride.png'),settings)==QgsLayoutExporter.Success
im=QImage(str(E/'day06_telluride.png'));assert (im.width(),im.height())==(2400,3000)
assert hashlib.sha256(gpkg.read_bytes()).hexdigest()==before
qa={'title':'TELLURIDE','subtitle':'Echoes of a Mining Town','dimensions_px':[2400,3000],'qgis':Qgis.QGIS_VERSION,'crs':p.crs().authid(),'all_print_map_layers_vector':all(isinstance(l,QgsVectorLayer) for l in m.layers()),'archival_images_used':False,'print_layers':[l.name() for l in m.layers()],'map_extent':m.extent().toString(),'label_audit':label_audit,'landmark_label_count':landmark_labels.featureCount(),'street_label_count':street_labels.featureCount(),'river_label_count':river.featureCount(),'main_map_scope':'downtown historic core','inset_scope':'full inventory extent','inset_map_extent':inset.extent().toString(),'inset_contains_full_inventory':inset.extent().contains(buildings.extent()),'inset_links_to_main_map':overview.linkedMap()==m,'previous_refinement_map_width_m':2331.428571428638,'scale_increase_from_previous':2331.428571428638/m.extent().width(),'main_map_id':m.id(),'inset_map_id':inset.id(),'displayed_inventory_records':len(shown),'displayed_classes':dict(collections.Counter(f['display_class'] for f in shown)),'labels':labels,'pre1900_count':None,'highlighted_source_footprints':len(historic),'highlighted_distinct_nonnull_bldg_ids':len({f['BLDG_ID'] for f in historic if not QgsVariantUtils.isNull(f['BLDG_ID'])}),'highlighted_null_bldg_id_records':sum(QgsVariantUtils.isNull(f['BLDG_ID']) for f in historic),'statistic_unit':'source polygon footprints, not distinct physical buildings','linear_scale_multiplier':baseline['original_map_width_m']/m.extent().width(),'original_map_width_m':baseline['original_map_width_m'],'current_map_width_m':m.extent().width(),'graphic_legend_swatches':3,'index_contour_interval_m':250,'minor_contour_interval_m':50,'gpkg_sha256_before':before,'gpkg_sha256_after':hashlib.sha256(gpkg.read_bytes()).hexdigest(),'existing_project_refined_in_place':True,'png_sha256':hashlib.sha256((E/'day06_telluride.png').read_bytes()).hexdigest(),'publication_authorized':False}
(ROOT/'map.qa.json').write_text(json.dumps(qa,indent=2));print(json.dumps(qa,indent=2),flush=True);os._exit(0)
