"""Prepare real geographic reveal bands for the eastern-edge cinematic."""
import json, math
from pathlib import Path
import geopandas as gpd
import numpy as np
from shapely.geometry import Polygon, LineString, Point, box, mapping, shape
from shapely.ops import transform, unary_union
from shapely.validation import make_valid
from pyproj import Transformer
P=Path(__file__).resolve().parent
PROJECT=Transformer.from_crs(4326,32611,always_xy=True).transform
INVERSE=Transformer.from_crs(32611,4326,always_xy=True).transform

def save(name,features):
    (P/'data'/name).write_text(json.dumps({'type':'FeatureCollection','features':features},separators=(',',':'))+'\n')
def feature(g,p):return {'type':'Feature','geometry':mapping(transform(INVERSE,g)),'properties':p}
def polygons(g):
    if g.geom_type in ('Polygon','MultiPolygon'):return g
    return unary_union([v for v in g.geoms if v.geom_type in ('Polygon','MultiPolygon')])
def prepare():
    boundary=gpd.read_file(P/'data/boundary.geojson').to_crs(32611).geometry.iloc[0]
    footprint=make_valid(Polygon(boundary.coords))
    # Selected using three real satellite previews and NLCD contrast / edge geometry.
    target_lat=36.175
    crossing=transform(PROJECT,LineString([(-115.1,target_lat),(-114.98,target_lat)]))
    point=boundary.intersection(crossing)
    if point.geom_type!='Point':raise ValueError('Selected edge must have one crossing')
    x,y=point.x,point.y
    extent=box(x-2800,y-4200,x+2800,y+4200)
    local_urban=polygons(make_valid(footprint.intersection(extent)))
    urban=footprint
    desert=polygons(make_valid(extent.difference(footprint)))
    edge=boundary.intersection(extent)
    # Densification stays on the existing projected boundary; no smoothing / straightening.
    lines=[edge] if edge.geom_type=='LineString' else list(edge.geoms)
    dense=[]
    for line in lines:
        coords=list(line.coords);points=[]
        for a,b in zip(coords,coords[1:]):
            count=max(1,math.ceil(math.dist(a,b)/50))
            points.extend([(a[0]+(b[0]-a[0])*i/count,a[1]+(b[1]-a[1])*i/count) for i in range(count)])
        dense.append(LineString(points+[coords[-1]]))
    save('urban-footprint.geojson',[feature(footprint,{'threshold_pct':50,'kind':'NLCD-derived developed footprint; not administrative'})])
    save('edge-boundary.geojson',[feature(line,{'id':i,'kind':'actual developed boundary; densified 50 m'}) for i,line in enumerate(dense)])
    save('edge-landscapes.geojson',[feature(urban,{'side':'urban'}),feature(desert,{'side':'desert'})])
    max_distance=math.ceil(max(Point(v).distance(edge) for v in footprint.exterior.coords)/75)*75+75
    levels=list(range(0,4575,75))+list(range(5500,max_distance,1000))+[max_distance]
    bands=[]; previous=edge.buffer(0)
    for i,(inner,outer) in enumerate(zip(levels,levels[1:])):
        buffered=edge.buffer(outer,resolution=128).simplify(.5,preserve_topology=True)
        shell=buffered.difference(previous);previous=buffered
        for side,land in [('urban',urban),('desert',desert)]:
            g=polygons(make_valid(land.intersection(shell)))
            if not g.is_empty:bands.append(feature(g,{'side':side,'inner_m':inner,'outer_m':outer,'band':i}))
    save('edge-reveal-bands.geojson',bands)
    grid=gpd.read_file(P/'data/grid.geojson').to_crs(32611)
    scores={}
    for side,window in [('west',box(x-2500,y-1500,x,y+1500)),('east',box(x,y-1500,x+2500,y+1500))]:
        rows=grid[grid.intersects(window)];areas=np.array([g.intersection(window).area for g in rows.geometry])
        scores[side]={'developed_pct':round(float(np.dot(areas,rows.developed_pct)/areas.sum()),2),'sample_area_km2':round(float(areas.sum()/1e6),3)}
    union_bands={side:unary_union([transform(PROJECT, shape(f['geometry'])) for f in bands if f['properties']['side']==side]) for side in ['urban','desert']}
    for side,land in [('urban',urban),('desert',desert)]:
        if union_bands[side].symmetric_difference(land).area>1:raise ValueError('Reveal bands do not cover landscape')
    lon,lat=INVERSE(x,y)
    config={'target':{'lon':lon,'lat':lat,'range':5000,'heading':0,'pitch':-86},'regional':{'lon':-115.19,'lat':36.16,'range':100000,'heading':0,'pitch':-90},'world':{'lon':-105,'lat':35,'range':22000000,'heading':0,'pitch':-90},'duration_seconds':10,'band_step_m':75,'max_reveal_distance_m':max_distance,'local_reveal_distance_m':4500,'reveal_origin':'selected real eastern boundary, not all perimeter edges','area_crs':'EPSG:32611','selection':'Sunrise Manor / Frenchman Mountain eastern edge at 36.175 N; central imagery candidate selected over southern irregular edge and northern airfield. Refined from 36.190 N using NLCD contrast.','comparison':scores,'urban_area_m2':urban.area,'local_urban_area_m2':local_urban.area,'desert_area_m2':desert.area,'edge_length_m':edge.length,'bands':len(bands),'geometry_qa':{'valid':all(g.is_valid for g in [urban,desert,footprint]),'overlap_m2':urban.intersection(desert).area,'partition_error_m2':urban.intersection(extent).union(desert).symmetric_difference(extent).area,'bands_cover_both_landscapes':True},'limitations':['Boundary resolution is 500 m NLCD zonal classification, not parcels or a surveyed urban limit','Desert polygon is outside the developed footprint within the study window, including roads and small isolated development','Esri imagery and NLCD 2021 differ in acquisition dates']}
    (P/'data/cinematic.json').write_text(json.dumps(config,indent=2)+'\n');print(json.dumps(config,indent=2))
if __name__=='__main__':prepare()
