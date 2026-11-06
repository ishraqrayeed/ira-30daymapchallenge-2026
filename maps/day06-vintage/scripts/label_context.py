"""Derive sparse label features from cached OSM and verified Town survey matches."""
import json,xml.etree.ElementTree as ET
from qgis.core import *
from qgis.PyQt.QtCore import QVariant

def prepare_labels(project,buildings,streets,root):
    crs=QgsCoordinateReferenceSystem('EPSG:26913');evidence=json.loads((root/'label-evidence.json').read_text())
    # Rewrite only this small derived label file; preserve the authoritative inventory GeoPackage.
    destination=root/'data/processed/label_context.gpkg'
    # Release previous project handles before replacing the derived label container.
    for layer in list(project.mapLayers().values()):
        if 'label_context.gpkg' in layer.source():project.removeMapLayer(layer.id())
    if destination.exists():destination.unlink()
    def write(name,geometry,fields,rows):
        layer=QgsVectorLayer(geometry+'?crs=EPSG:26913',name,'memory');provider=layer.dataProvider();provider.addAttributes([QgsField(n,t) for n,t in fields]);layer.updateFields()
        for attrs,geom in rows:
            if geometry.startswith('Multi'):geom.convertToMultiType()
            f=QgsFeature(layer.fields());f.setAttributes(attrs);f.setGeometry(geom);assert geom.isGeosValid() and not geom.isEmpty();provider.addFeatures([f])
        layer.updateExtents();options=QgsVectorFileWriter.SaveVectorOptions();options.driverName='GPKG';options.layerName=name
        if destination.exists():options.actionOnExistingFile=QgsVectorFileWriter.CreateOrOverwriteLayer
        result=QgsVectorFileWriter.writeAsVectorFormatV3(layer,str(destination),project.transformContext(),options);assert result[0]==0,result
        saved=QgsVectorLayer(str(destination)+'|layername='+name,name,'ogr');assert saved.isValid();project.addMapLayer(saved);return saved
    canonical={'Colorado Avenue':{'West Colorado Avenue','East Colorado Avenue'},'Oak Street':{'North Oak Street','South Oak Street'},'Fir Street':{'North Fir Street','South Fir Street'},'Pine Street':{'North Pine Street','South Pine Street'}}
    road_rows=[]
    for label,names in canonical.items():
        features=[f for f in streets.getFeatures() if str(f['name']) in names];assert features,label
        geometry=QgsGeometry.unaryUnion([f.geometry() for f in features]).mergeLines()
        road_rows.append(([label,'OSMnx; original named street geometry'],geometry))
    street_labels=write('street_labels','MultiLineString',[('name',QVariant.String),('source',QVariant.String)],road_rows)
    tree=ET.parse(root/'data/raw/streets.osm').getroot();nodes={n.attrib['id']:QgsPointXY(float(n.attrib['lon']),float(n.attrib['lat'])) for n in tree.findall('node')};transform=QgsCoordinateTransform(QgsCoordinateReferenceSystem('EPSG:4326'),crs,project);river_rows=[];river_ids=[]
    for way in tree.findall('way'):
        tags={t.attrib['k']:t.attrib['v'] for t in way.findall('tag')}
        if tags.get('name')=='San Miguel River' and tags.get('waterway')=='river':
            pts=[nodes[n.attrib['ref']] for n in way.findall('nd')];g=QgsGeometry.fromPolylineXY(pts);g.transform(transform);river_rows.append((['San Miguel River',way.attrib['id']],g));river_ids.append(way.attrib['id'])
    assert river_rows
    # One merged feature gives one river label while retaining source-way provenance.
    river_geometry=QgsGeometry.unaryUnion([g for _,g in river_rows]).mergeLines()
    river=write('river','MultiLineString',[('name',QVariant.String),('osm_ways',QVariant.String)],[(['San Miguel River',','.join(river_ids)],river_geometry)])
    rows=[];matches=[]
    for item in evidence['landmarks']:
        candidates=[f for f in buildings.getFeatures() if f['OBJECTID']==item['objectid']];assert len(candidates)==1
        feature=candidates[0]
        if 'pin' in item:
            assert str(feature['PIN'])==item['pin'];assert sum(str(f['PIN'])==item['pin'] for f in buildings.getFeatures())==1
        else:
            tr=QgsCoordinateTransform(QgsCoordinateReferenceSystem('EPSG:26713'),crs,project);pt=tr.transform(QgsPointXY(*item['survey_utm_nad27']));ref=QgsGeometry.fromPointXY(pt);hits=[f['OBJECTID'] for f in buildings.getFeatures() if f.geometry().intersects(ref)];assert hits==[item['objectid']],hits
        point=feature.geometry().pointOnSurface();assert feature.geometry().contains(point)
        rows.append(([item['number'],item['name'],item['key_name'],item['objectid'],item['source']],point));matches.append({'number':item['number'],'name':item['name'],'objectid':item['objectid'],'point_on_matched_footprint':True,'match':item['match']})
    landmarks=write('landmark_labels','Point',[('number',QVariant.Int),('name',QVariant.String),('key_name',QVariant.String),('objectid',QVariant.Int),('source',QVariant.String)],rows)
    return street_labels,river,landmarks,{'landmarks':matches,'street_names':list(canonical),'river_name':'San Miguel River','river_osm_way_ids':river_ids,'original_inventory_modified':False}
