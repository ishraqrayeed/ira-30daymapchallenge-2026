"""Order US 550, retain every vertex, densify to <=10 m, sample 3DEP."""
from pathlib import Path
import json
import hashlib
import numpy as np
import networkx as nx
import rasterio
from pyproj import Transformer
from shapely.geometry import LineString, Point
from shapely.ops import substring
from download_data import CACHE, HERE

def main():
    osm=json.loads((CACHE/'osm.json').read_text())
    nodes={}
    for e in osm['elements']:
        if e['type']=='node':
            nodes[e['id']]={**nodes.get(e['id'],{}),**e}
    project=Transformer.from_crs(4326,26913,always_xy=True).transform
    xy={i:np.array(project(n['lon'],n['lat'])) for i,n in nodes.items()}
    graph=nx.Graph()
    ways={e['id']:e for e in osm['elements'] if e['type']=='way'}
    for way in ways.values():
        assert way['tags']['ref']=='US 550'
        for a,b in zip(way['nodes'],way['nodes'][1:]):
            length=float(np.linalg.norm(xy[b]-xy[a]))
            if length: graph.add_edge(a,b,weight=length,way=way['id'])
    def nearest(lon,lat):
        p=np.array(project(lon,lat))
        return min(graph,key=lambda n:np.linalg.norm(xy[n]-p))
    # Stop at the mapped pass itself; exclude every segment south of it.
    passnode=next(n for n in nodes.values() if n.get('tags',{}).get('name')=='Red Mountain Pass')
    start=nearest(-107.6714,38.0228)
    end=passnode['id'] if passnode['id'] in graph else nearest(passnode['lon'],passnode['lat'])
    assert np.linalg.norm(xy[end]-np.array(project(passnode['lon'],passnode['lat'])))<1
    path=nx.shortest_path(graph,start,end,weight='weight')
    assert len(path)==len(set(path))
    original=np.array([xy[n] for n in path])
    line=LineString(original)
    assert line.is_simple and 20000<line.length<22000
    selection=json.loads((HERE/'segment.json').read_text())
    cut_start,cut_end=selection['chainage_from_ouray_m']
    source_chain=np.r_[0,np.cumsum(np.linalg.norm(np.diff(original,axis=0),axis=1))]
    selected=sorted({graph[a][b]['way'] for i,(a,b) in enumerate(zip(path,path[1:]))
                     if source_chain[i]<cut_end and source_chain[i+1]>cut_start})
    line=substring(line,cut_start,cut_end)
    original=np.array(line.coords)
    assert line.is_simple and abs(line.length-(cut_end-cut_start))<.01
    # Split each edge separately, preserving all original OSM bends exactly.
    dense=[]
    for a,b in zip(original,original[1:]):
        count=int(np.ceil(np.linalg.norm(b-a)/10))
        dense.extend(a+(b-a)*t/count for t in range(count))
    dense=np.array([*dense,original[-1]])
    chain=np.r_[0,np.cumsum(np.linalg.norm(np.diff(dense,axis=0),axis=1))]
    with rasterio.open(CACHE/'elevation.tif') as ds:
        assert ds.crs.to_epsg()==26913
        grid=ds.read(1,masked=True)
        inv=~ds.transform
        col,row=inv*(dense[:,0],dense[:,1]); col-=.5;row-=.5
        c=np.floor(col).astype(int); r=np.floor(row).astype(int)
        assert np.all((c>=0)&(r>=0)&(c+1<ds.width)&(r+1<ds.height))
        dx=col-c;dy=row-r
        z=(grid[r,c]*(1-dx)*(1-dy)+grid[r,c+1]*dx*(1-dy)+grid[r+1,c]*(1-dx)*dy+grid[r+1,c+1]*dx*dy)
        assert np.ma.count_masked(z)==0 and np.isfinite(z).all()
        z=np.asarray(z)
        resolution=list(ds.res)
    # Flag an isolated sample >12 m from both neighbors with agreeing neighbors.
    spike=np.where((np.abs(z[1:-1]-(z[:-2]+z[2:])/2)>12)&(np.abs(z[:-2]-z[2:])<6))[0]+1
    assert len(spike)==0, f'Unresolved spikes: {spike}'
    raw_z=z.copy()
    # A 20 m Gaussian on a uniform 5 m chainage grid suppresses DEM-scale
    # roughness, without moving or simplifying any horizontal route vertex.
    uniform=np.arange(0,chain[-1],5.)
    uniform=np.r_[uniform,chain[-1]]
    heights=np.interp(uniform,chain,z)
    kernel=np.exp(-.5*(np.arange(-12,13)/4)**2);kernel/=kernel.sum()
    smooth=np.convolve(np.pad(heights,12,mode='edge'),kernel,mode='valid')
    z=np.interp(chain,uniform,smooth)
    z[0]=raw_z[0];z[-1]=raw_z[-1]
    labels=[]
    inverse=Transformer.from_crs(26913,4326,always_xy=True).transform
    endpoints=[dict(role=role,longitude=inverse(*dense[i])[0],latitude=inverse(*dense[i])[1],
                    elevation_m=float(z[i])) for role,i in [('approach',0),('exit',len(z)-1)]]
    output=HERE/'data';output.mkdir(exist_ok=True)
    (output/'route.json').write_text(json.dumps(dict(crs='EPSG:26913',length_m=line.length,points=np.column_stack([dense,z]).round(4).tolist(),labels=labels,selection=selection)))
    qa=dict(passed=True,route_length_m=line.length,original_vertices=len(original),densified_vertices=len(z),
            max_spacing_m=float(np.diff(chain).max()),selected_osm_ways=selected,all_refs='US 550',
            repeated_nodes=0,self_intersections=False,missing_samples=0,isolated_spikes=len(spike),
            raster_resolution_m=resolution,elevation_range_m=[float(z.min()),float(z.max())],labels=labels,
            smoothing='Gaussian sigma 20 m, radius 60 m, uniform 5 m chainage; endpoints retained',
            max_smoothing_change_m=float(np.max(abs(z-raw_z))),
            endpoints=endpoints,selection=selection,net_climb_m=float(z[-1]-z[0]),
            max_adjacent_grade=float(np.max(abs(np.diff(z)/np.diff(chain)))))
    (HERE/'qa.json').write_text(json.dumps(qa,indent=2)+'\n')
    manifest=json.loads((CACHE/'manifest.json').read_text())
    service=json.loads((CACHE/'service.json').read_text())
    manifest['elevation_resolution_note']='USGS multi-resolution 3DEP dynamic service, exported/resampled to a 10 m UTM grid; this is not a claim of uniform native 10 m source resolution.'
    manifest['service_metadata']={k:service.get(k) for k in ['description','copyrightText','pixelSizeX','pixelSizeY','spatialReference']}
    manifest['photograph']={**selection['photo_display'],
        'sha256':hashlib.sha256((output/'instagram-reference.jpg').read_bytes()).hexdigest()}
    (HERE/'sources.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(qa,indent=2))

if __name__=='__main__': main()
