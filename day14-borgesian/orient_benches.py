"""Infer display facing toward the closest mapped path; never change OSM tags/positions."""
import math
from shapely.geometry import shape
from shapely.affinity import scale
from shapely.ops import nearest_points
from shapely.strtree import STRtree

SX=111320*math.cos(math.radians(39.75))
SY=111320
COMPASS={name:i*22.5 for i,name in enumerate(['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW'])}

def recorded_direction(value):
    text=str(value or '').strip().upper()
    if text in COMPASS:return COMPASS[text]
    try:
        angle=float(text)
        return angle%360 if math.isfinite(angle) else None
    except ValueError:return None

def orient_benches(features):
    paths=[];ids=[]
    def lines(g):
        if g.geom_type in ['LineString','LinearRing']:return [g]
        return [line for part in getattr(g,'geoms',[]) for line in lines(part)]
    for f in features:
        if f['properties']['kind']=='path':
            for line in lines(shape(f['geometry'])):
                if line.length:
                    paths.append(scale(line,xfact=SX,yfact=SY,origin=(0,0)));ids.append(f['properties']['osm'])
    tree=STRtree(paths) if paths else None
    counts={'osm':0,'nearest trail':0,'display fallback':0}
    for f in features:
        p=f['properties']
        if p['kind']!='bench' or f['geometry']['type']!='Point':continue
        angle=recorded_direction(p.get('direction'));basis='osm'
        if angle is None:
            basis='display fallback';angle=0
            if tree is not None:
                bench=scale(shape(f['geometry']),xfact=SX,yfact=SY,origin=(0,0))
                index=int(tree.nearest(bench));line=paths[index];target=nearest_points(bench,line)[1]
                distance=bench.distance(target)
                if distance<=50:
                    dx,dy=target.x-bench.x,target.y-bench.y
                    if distance<.05:
                        along=line.project(target);a=line.interpolate(max(0,along-.25));b=line.interpolate(min(line.length,along+.25))
                        dx,dy=-(b.y-a.y),b.x-a.x
                    angle=math.degrees(math.atan2(dx,dy))%360;basis='nearest trail'
                    p['facing_path']=ids[index];p['facing_path_distance_m']=round(distance,2)
        p['display_direction']=round(angle,3);p['direction_basis']=basis;counts[basis]+=1
    return counts
