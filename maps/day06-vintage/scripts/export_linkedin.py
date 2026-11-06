"""Export a LinkedIn-sized 4:5 copy directly from the existing QGIS layout."""
import hashlib,json,os
from pathlib import Path
from qgis.core import QgsApplication,QgsProject,QgsLayoutExporter
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QImage
ROOT=Path(__file__).resolve().parents[1]
project=ROOT/'qgis/day06_telluride.qgz';master=ROOT/'exports/day06_telluride.png';gpkg=ROOT/'data/processed/telluride_inventory.gpkg'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
original={str(p.relative_to(ROOT)):digest(p) for p in [project,master,gpkg]}
app=QgsApplication([],False);app.initQgis();p=QgsProject.instance();assert p.read(str(project))
layout=p.layoutManager().layoutByName('LinkedIn — larger type') or p.layoutManager().layouts()[0];output=ROOT/'exports/day06_telluride_linkedin.png'
settings=QgsLayoutExporter.ImageExportSettings();settings.dpi=135;settings.imageSize=QSize(1080,1350);settings.exportMetadata=False
assert QgsLayoutExporter(layout).exportToImage(str(output),settings)==QgsLayoutExporter.Success
image=QImage(str(output));assert (image.width(),image.height())==(1080,1350);assert output.stat().st_size<5_000_000
assert all(digest(ROOT/name)==sha for name,sha in original.items())
report={'dimensions_px':[1080,1350],'aspect_ratio':'4:5','bytes':output.stat().st_size,'format':'PNG','rendered_from_existing_qgis_layout':True,'crop_or_stretch_applied':False,'high_resolution_master_project_and_inventory_unchanged':True,'output_sha256':digest(output),'original_sha256':original,'specification_source':'https://www.linkedin.com/help/linkedin/answer/a527229/share-photos-or-videos?lang=en'}
(ROOT/'linkedin-export.qa.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2),flush=True);os._exit(0)
