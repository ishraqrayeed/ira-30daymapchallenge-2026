importScripts('core.js');
let graph;
self.onmessage=async({data})=>{try{graph=graph||fetch('data/network.json').then(r=>{if(!r.ok)throw Error('Walking data could not be loaded.');return r.json()});const result=FoodCore.route(await graph,data.stops);self.postMessage({id:data.id,result})}catch(e){graph=null;self.postMessage({id:data.id,error:e.message})}};
