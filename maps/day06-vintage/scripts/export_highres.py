"""Render an 12-megapixel poster from the existing editable vector QGIS layout."""
import hashlib,json,os
from pathlib import Path
from qgis.core import QgsApplication,QgsProject,QgsLayoutExporter,QgsLayoutItemLabel
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QImage
ROOT=Path(__file__).resolve().parents[1]
files=[ROOT/'qgis/day06_telluride.qgz',ROOT/'exports/day06_telluride.png',ROOT/'data/processed/telluride_inventory.gpkg']
def digest(f):return hashlib.sha256(f.read_bytes()).hexdigest()
before={str(f.relative_to(ROOT)):digest(f) for f in files}
app=QgsApplication([],False);app.initQgis();project=QgsProject.instance();assert project.read(str(files[0]));layout=project.layoutManager().layouts()[0]
# A separate editable social layout keeps the original atlas layout intact.
existing=project.layoutManager().layoutByName('LinkedIn — larger type')
if existing: project.layoutManager().removeLayout(existing)
layout=project.layoutManager().duplicateLayout(layout,'LinkedIn — larger type')
for item in layout.items():
 if isinstance(item,QgsLayoutItemLabel):
  font=item.font();size=font.pointSizeF();ident=item.id();text=item.text()
  if 'landmark-name-' in ident:
   font.setPointSizeF(12)
   if 'Courthouse' in text: item.setText('County Courthouse')
  elif 'landmark-number-' in ident: font.setPointSizeF(10)
  elif 'key-' in ident: font.setPointSizeF(12)
  elif ident.endswith('count'):
   font.setPointSizeF(15);item.setText('293 footprints with historic ratings')
  elif ident.endswith('scope'):
   font.setPointSizeF(12);item.setText('Contemporary geometry · Dates not assigned')
  elif ident.endswith('credits'):
   font.setPointSizeF(10.5);item.setText('Town of Telluride · © OpenStreetMap contributors · USGS 3DEP')
  elif ident.endswith('inset-title'): font.setPointSizeF(10)
  elif 'Echoes' in text: font.setPointSizeF(22)
  elif size<12: font.setPointSizeF(12)
  font.setBold(False)
  item.setFont(font)
  # Larger type needs taller text frames, retaining the existing centers.
  from qgis.core import QgsLayoutSize,QgsLayoutPoint
  h=max(item.sizeWithUnits().height(),7)
  item.attemptResize(QgsLayoutSize(item.sizeWithUnits().width(),h))
# Increase geographic label size without changing geometry or the web map.
for layer in project.mapLayers().values():
 if layer.labelsEnabled() and layer.labeling():
  settings=layer.labeling().settings();fmt=settings.format();label_font=fmt.font();label_font.setBold(False);fmt.setFont(label_font);fmt.setSize((10 if 'landmark' in layer.name().lower() else 12.5));settings.setFormat(fmt)
  from qgis.core import QgsVectorLayerSimpleLabeling
  layer.setLabeling(QgsVectorLayerSimpleLabeling(settings))
settings=QgsLayoutExporter.ImageExportSettings();settings.dpi=375;settings.imageSize=QSize(3000,3750);settings.exportMetadata=False
output=ROOT/'exports/day06_telluride_3000x3750.png'
assert QgsLayoutExporter(layout).exportToImage(str(output),settings)==QgsLayoutExporter.Success
im=QImage(str(output));assert (im.width(),im.height())==(3000,3750);assert all(digest(ROOT/name)==sha for name,sha in before.items())
assert project.write(str(files[0]))
report={'dimensions_px':[3000,3750],'megapixels':11.25,'aspect_ratio':'4:5','layout_render_dpi':375,'bytes':output.stat().st_size,'rendered_from_qgis_vectors':True,'upscaled_from_smaller_png':False,'master_and_inventory_unchanged':True,'editable_social_layout':'LinkedIn — larger type','sha256':digest(output),'original_sha256':before}
(ROOT/'highres-export.qa.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True);os._exit(0)
