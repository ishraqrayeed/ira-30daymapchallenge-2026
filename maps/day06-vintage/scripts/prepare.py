"""Preserve the full inventory, audit its fields, and derive real terrain contours."""
import collections,json,os
from pathlib import Path
import numpy as np
from osgeo import gdal,ogr,osr
from qgis.core import *
from qgis.PyQt.QtCore import QVariant
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'data/raw';OUT=ROOT/'data/processed';OUT.mkdir(exist_ok=True)
app=QgsApplication([],False);app.initQgis();p=QgsProject.instance();crs=QgsCoordinateReferenceSystem('EPSG:26913');p.setCrs(crs);gdal.UseExceptions()
raw=QgsVectorLayer(str(RAW/'structures_esri.json'),'Town historic structures source','ogr');assert raw.isValid(); streets=QgsVectorLayer(str(RAW/'streets.geojson'),'OSMnx street geometry','ogr');assert streets.isValid()
gpkg=OUT/'telluride_inventory.gpkg'
if gpkg.exists():gpkg.unlink()
def save(l,name):
 opt=QgsVectorFileWriter.SaveVectorOptions();opt.driverName='GPKG';opt.layerName=name;opt.ct=QgsCoordinateTransform(l.crs(),crs,p)
 if gpkg.exists():opt.actionOnExistingFile=QgsVectorFileWriter.CreateOrOverwriteLayer
 result=QgsVectorFileWriter.writeAsVectorFormatV3(l,str(gpkg),p.transformContext(),opt);assert result[0]==0,result
 out=QgsVectorLayer(str(gpkg)+'|layername='+name,name,'ogr');assert out.isValid();return out
inventory=save(raw,'inventory_source');roads=save(streets,'streets')
ids=json.loads((RAW/'ids.json').read_text())['objectIds'];assert raw.featureCount()==len(ids)==inventory.featureCount();assert {f['OBJECTID'] for f in inventory.getFeatures()}==set(ids)
field_audit={}
for f in raw.fields():
 vals=collections.Counter(str(feat[f.name()]) if not QgsVariantUtils.isNull(feat[f.name()]) else '' for feat in raw.getFeatures());field_audit[f.name()]={'type':f.typeName(),'nonblank':sum(n for v,n in vals.items() if v.strip()),'distinct':len(vals),'top_values':dict(vals.most_common(20))}
# No undocumented year extraction, historic imagery, or guessed dates.
classified=QgsVectorLayer('MultiPolygon?crs=EPSG:26913','Inventory with explicit evidence classes','memory');pr=classified.dataProvider();pr.addAttributes(list(inventory.fields())+[QgsField('date_class',QVariant.String),QgsField('construction_year',QVariant.Int),QgsField('date_evidence',QVariant.String),QgsField('display_class',QVariant.String),QgsField('provenance',QVariant.String)]);classified.updateFields()
historic_ratings={'Contributing','Supporting','Local Landmark','Significant Landmark Interior'};class_counts=collections.Counter();rating_counts=collections.Counter();status_counts=collections.Counter();invalid=[]
for old in inventory.getFeatures():
 geometry=QgsGeometry(old.geometry());assert not geometry.isEmpty()
 if not geometry.isGeosValid():invalid.append(old['OBJECTID']);geometry=geometry.makeValid()
 assert geometry.isGeosValid();geometry.convertToMultiType()
 rating=old['Rating'];status=old['status'];legacy=status in ['demolished','old structures map'];group='legacy' if legacy else 'historic_rating' if rating in historic_ratings else 'other_or_unrated'
 f=QgsFeature(classified.fields());f.setGeometry(geometry);f.setAttributes(old.attributes()+['undated',None,'GIS has no construction date; surveyed forms not joined',group,'Town of Telluride FeatureServer/23; OBJECTID retained']);pr.addFeatures([f]);class_counts[group]+=1;rating_counts[str(rating)]+=1;status_counts[str(status)]+=1
classified.updateExtents();display=save(classified,'inventory_classified')
# Separate date-status layers make an empty verified subset distinguishable from no old buildings.
for name,expression in [('undated_structures','"date_class" = \'undated\''),('verified_pre1900','"construction_year" < 1900')]:
 subset=display.materialize(QgsFeatureRequest().setFilterExpression(expression));save(subset,name)
# All modern vector inputs are retained; terrain is converted to editable contours.
dem=gdal.Open(str(RAW/'dem.tif'));assert dem.RasterCount==1 and dem.GetRasterBand(1).DataType==gdal.GDT_Float32
values=dem.ReadAsArray();nodata=dem.GetRasterBand(1).GetNoDataValue();valid=np.isfinite(values)&(values!=nodata if nodata is not None else True);z=values[valid];assert z.size>1e6 and 2000<float(np.median(z))<5000
terrain=gdal.Warp(str(OUT/'terrain_26913.tif'),dem,dstSRS='EPSG:26913',resampleAlg='bilinear',creationOptions=['COMPRESS=LZW']);assert terrain
# Hillshade saved for optional editing only; poster uses contours, so every visible map layer is vector.
gdal.DEMProcessing(str(OUT/'hillshade.tif'),terrain,'hillshade',azimuth=315,altitude=40,computeEdges=True)
ds=ogr.Open(str(gpkg),1);srs=osr.SpatialReference();srs.ImportFromEPSG(26913);cont=ds.CreateLayer('terrain_contours',srs,ogr.wkbLineString);cont.CreateField(ogr.FieldDefn('id',ogr.OFTInteger));cont.CreateField(ogr.FieldDefn('elevation_m',ogr.OFTReal));gdal.ContourGenerate(terrain.GetRasterBand(1),50,0,[],0,0,cont,0,1);cont=None;ds=None;terrain=None
contours=QgsVectorLayer(str(gpkg)+'|layername=terrain_contours','Terrain contours','ogr');assert contours.isValid() and contours.featureCount()>0
survey={'gis_date_fields':[],'survey_index':'https://www.telluride.gov/391/2013-Telluride-Historic-Architectural-Su','consulted_form':'https://www.telluride.gov/DocumentCenter/View/2117/ColoradoAvenue103W-REVISED?bidId=','sample_address':'103 W. Colorado Avenue','sample_resource_id':'5SM.1541','sample_parcel':'477901119003','sample_construction_estimate':1886,'sample_date_is_estimate':True,'sample_page':3,'sample_parcel_matches_in_inventory':sum(str(f['PIN'])=='477901119003' for f in inventory.getFeatures()),'join_applied':False,'reason':'Sample survey parcel not found in GIS PIN. Survey log uses site IDs and primary/secondary resources; source GIS has no matching site IDs or addresses. No dates propagated by proximity, district period, or shared parcel assumptions. A complete audited survey-to-footprint crosswalk is outside this first version.','pre1900_count':None,'verified_joined_pre1900_records':0,'undated_records':raw.featureCount()}
assert survey['sample_parcel_matches_in_inventory']==0
report={'source_records':raw.featureCount(),'source_geometry':QgsWkbTypes.displayString(raw.wkbType()),'source_crs':raw.crs().authid(),'processing_crs':crs.authid(),'field_audit':field_audit,'rating_counts':dict(rating_counts),'status_counts':dict(status_counts),'display_class_counts':dict(class_counts),'historic_rating_records_including_legacy':sum(n for k,n in rating_counts.items() if k in historic_ratings),'pre1900_count':None,'undated_records':raw.featureCount(),'date_inference_performed':False,'source_geometry_repairs_in_display_layer':invalid,'contours':contours.featureCount(),'contour_interval_m':50,'dem_range_m':[float(z.min()),float(z.max())],'survey_review':survey,'extents':{l.name():l.extent().toString() for l in [inventory,roads,contours]}}
(ROOT/'data-audit.json').write_text(json.dumps(report,indent=2));(ROOT/'survey-review.json').write_text(json.dumps(survey,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['field_audit','survey_review','extents']},indent=2),flush=True);os._exit(0)
