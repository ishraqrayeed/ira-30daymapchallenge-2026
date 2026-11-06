"""Check provenance, complete feature preservation, evidence classes and vector-only print."""
import hashlib,json,os
from pathlib import Path
from qgis.core import *
from qgis.PyQt.QtGui import QImage
ROOT=Path(__file__).resolve().parents[1];D=ROOT/'data/processed';app=QgsApplication([],False);app.initQgis()
manifest=json.loads((ROOT/'source-manifest.json').read_text())
for item in manifest['downloads']:
 assert hashlib.sha256((ROOT/'data/raw'/item['file']).read_bytes()).hexdigest()==item['sha256'],item['file']
audit=json.loads((ROOT/'data-audit.json').read_text());qa=json.loads((ROOT/'map.qa.json').read_text());p=QgsProject.instance();assert p.read(str(ROOT/'qgis/day06_telluride.qgz'))
for l in p.mapLayers().values():assert l.isValid(),l.source()
source=QgsVectorLayer(str(ROOT/'data/raw/structures_esri.json'),'raw','ogr')
def layer(name):
 l=QgsVectorLayer(str(D/'telluride_inventory.gpkg')+'|layername='+name,name,'ogr');assert l.isValid() and l.crs().authid()=='EPSG:26913';return l
original=layer('inventory_source');classified=layer('inventory_classified');undated=layer('undated_structures');pre=layer('verified_pre1900');roads=layer('streets');contours=layer('terrain_contours')
assert source.featureCount()==original.featureCount()==classified.featureCount()==undated.featureCount()==manifest['structures']
raw={f['OBJECTID']:f for f in source.getFeatures()}
for f in original.getFeatures():
 before=raw[f['OBJECTID']];assert f.geometry().isGeosEqual(before.geometry())
 for fld in source.fields():
  a,b=before[fld.name()],f[fld.name()];assert (QgsVariantUtils.isNull(a) and QgsVariantUtils.isNull(b)) or a==b,(f['OBJECTID'],fld.name())
for l in [classified,roads,contours]:
 assert l.featureCount()>0
 assert all(not f.geometry().isEmpty() and f.geometry().isGeosValid() for f in l.getFeatures())
assert pre.featureCount()==0 and audit['pre1900_count'] is None
assert all(QgsVariantUtils.isNull(f['construction_year']) and f['date_class']=='undated' for f in classified.getFeatures())
assert roads.featureCount()==manifest['osm_road_edges']
layout=p.layoutManager().layouts()[0];m=next(i for i in layout.items() if isinstance(i,QgsLayoutItemMap) and i.id()=='day06-main-map');assert len(m.layers())==6 and all(isinstance(l,QgsVectorLayer) for l in m.layers())
assert all(not any(token in l.source().lower() for token in ['sanborn','1893','sheet03','jp2']) for l in m.layers())
assert classified.extent().xMinimum()>248000 and classified.extent().xMaximum()<255000 and classified.extent().yMinimum()>4200000 and classified.extent().yMaximum()<4206000
im=QImage(str(ROOT/'exports/day06_telluride.png'));assert (im.width(),im.height())==(2400,3000);assert im.pixelColor(0,0).name().upper()=='#F4F0E6'
assert hashlib.sha256((ROOT/'exports/day06_telluride.png').read_bytes()).hexdigest()==qa['png_sha256']
assert qa['gpkg_sha256_before']==qa['gpkg_sha256_after']==hashlib.sha256((D/'telluride_inventory.gpkg').read_bytes()).hexdigest()
assert qa['scale_increase_from_previous'] > 1.7
inset=next(i for i in layout.items() if isinstance(i,QgsLayoutItemMap) and i.id()=='day06-refinement-inset')
assert inset.extent().contains(classified.extent()) and inset.overview().linkedMap()==m
assert all(isinstance(l,QgsVectorLayer) for l in inset.layers())
assert abs(qa['original_map_width_m']/m.extent().width()-qa['linear_scale_multiplier'])<1e-9
assert sum(isinstance(i,QgsLayoutItemShape) and i.id().startswith('day06-refinement-swatch-') for i in layout.items())==3
red=[f for f in classified.getFeatures() if f['display_class']=='historic_rating']
assert len(red)==qa['highlighted_source_footprints']
assert sum(f.geometry().intersects(m.extent()) for f in red)==qa['displayed_classes']['historic_rating']
assert all(f.geometry().intersects(inset.extent()) for f in red)
assert qa['landmark_label_count']==3 and qa['street_label_count']==4 and qa['river_label_count']==1
assert any(isinstance(i,QgsLayoutItemLabel) and i.text()=='Echoes of a Mining Town' for i in layout.items())
assert any(isinstance(i,QgsLayoutItemLabel) and i.text()==f'{len(red)} footprints with historic ratings · town inventory' for i in layout.items())
report={'passed':True,'full_source_attributes_and_geometry_preserved':True,'source_records':original.featureCount(),'street_edges':roads.featureCount(),'contour_features':contours.featureCount(),'all_print_layers_vector':True,'archival_rasters_used':False,'construction_years_inferred':False,'pre1900_count':None,'all_source_records_undated':True,'display_classes':audit['display_class_counts'],'project_reopened':True,'png_dimensions':[2400,3000],'unchanged_geopackage_verified':True,'linear_map_scale_multiplier':qa['linear_scale_multiplier'],'graphic_legend_swatches_verified':3,'highlighted_footprints_verified':len(red),'downtown_highlighted_footprints':qa['displayed_classes']['historic_rating'],'full_inventory_visible_in_inset':True,'inset_extent_locator_verified':True}
(ROOT/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True);os._exit(0)
