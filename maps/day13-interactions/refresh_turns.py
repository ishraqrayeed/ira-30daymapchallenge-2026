"""Rebuild turn rules without recomputing unchanged geometry or Census intersections."""
import json,gzip,hashlib
from prepare_graph import DAY,load,topology
if __name__=='__main__':
 ways,rules,rejected=load();edges,turns,stats=topology(ways,rules);source=DAY/'data/graph.json.gz';g=json.loads(gzip.decompress(source.read_bytes()));assert len(edges)==len(g['edges']);incoming={};outgoing={}
 for i,e in enumerate(edges):
  assert e['first']==g['edges'][i][6] and e['last']==g['edges'][i][7]
  incoming.setdefault(e['v'],[]).append(i);outgoing.setdefault(e['u'],[]).append(i)
 prohibited=set()
 for node,fr,to,restriction,rid in turns:
  ins=[i for i in incoming.get(node,[]) if edges[i]['last'] in fr];outs=outgoing.get(node,[]);only=restriction.startswith('only_')
  for i in ins:
   for j in outs:
    target=edges[j]['first'] in to
    if restriction in ['no_u_turn','only_u_turn'] and set(fr)==set(to):target=target and edges[j]['v']==edges[i]['u']
    if (only and not target) or (not only and target):prohibited.add((i,j))
 g['turns']=sorted(prohibited);compressed=gzip.compress(json.dumps(g,separators=(',',':')).encode(),compresslevel=9,mtime=0);source.write_bytes(compressed)
 p=DAY/'data/graph.qa.json';q=json.loads(p.read_text());q['applied_node_turn_prohibitions']=len(prohibited);q['graph_gzip_bytes']=len(compressed);q['same_way_u_turn_rule']='Only the return edge is prohibited; legal continuation on the same OSM way remains available.';p.write_text(json.dumps(q,separators=(',',':'))+'\n')
 p=DAY/'data/sources.json';q=json.loads(p.read_text());q['graph_sha256']=hashlib.sha256(compressed).hexdigest();p.write_text(json.dumps(q,separators=(',',':'))+'\n');print('Turn prohibitions:',len(prohibited),flush=True)
