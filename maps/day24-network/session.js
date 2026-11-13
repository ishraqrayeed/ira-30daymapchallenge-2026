/* Atomic candidate-route validation. The accepted trip never changes until validation succeeds. */
(function(root){'use strict';const Core=typeof module!=='undefined'?require('./core.js'):root.RoadTripCore;
 const emptyRoute=()=>({centimetres:0,seconds:0,states:[],segments:[],geometry:{type:'MultiLineString',coordinates:[]}});
 class TripSession{
  constructor(route,{onCommit=()=>{},onPending=()=>{},onReject=()=>{}}={}){this.route=route;this.onCommit=onCommit;this.onPending=onPending;this.onReject=onReject;this.stops=[];this.result=emptyRoute();this.history=[];this.generation=0;this.pending=false}
  snapshot(){return {stops:structuredClone(this.stops),result:this.result}}
  remember(){this.history.push(this.snapshot());if(this.history.length>60)this.history.shift()}
  async edit(prepare){const token=++this.generation,base=structuredClone(this.stops);this.pending=true;this.onPending(true);try{const stops=await prepare(base);if(token!==this.generation)return {accepted:false,reason:'stale'};if(JSON.stringify(stops)===JSON.stringify(this.stops))return {accepted:false,reason:'unchanged'};if(!Array.isArray(stops)||stops.length>64)throw Error('An itinerary may contain up to 64 stops.');const result=stops.length<2?emptyRoute():await this.route(stops);if(token!==this.generation)return {accepted:false,reason:'stale'};if(!Number.isFinite(result.centimetres)||result.centimetres<0)throw Error('The routing engine returned an invalid distance. Your accepted trip is unchanged.');if(!Core.withinBudget(result.centimetres)){const rejection={accepted:false,reason:'budget',proposedMiles:result.centimetres/Core.CM_PER_MILE,remainingMiles:Core.score(this.result).remainingMiles};this.onReject(rejection);return rejection}this.remember();this.stops=stops;this.result=result;this.pending=false;this.onCommit(this);return {accepted:true,result}}catch(error){if(token!==this.generation)return {accepted:false,reason:'stale'};const rejection={accepted:false,reason:'routing',message:error.message};this.onReject(rejection);return rejection}finally{if(token===this.generation){this.pending=false;this.onPending(false)}}}
  cancelPending(){++this.generation;this.pending=false;this.onPending(false)}
  undo(){if(this.pending){this.cancelPending();return}++this.generation;this.pending=false;if(this.history.length){const old=this.history.pop();this.stops=old.stops;this.result=old.result;this.onCommit(this)}this.onPending(false)}
  clear(){++this.generation;this.pending=false;if(this.stops.length)this.remember();this.stops=[];this.result=emptyRoute();this.onCommit(this);this.onPending(false)}
 }
 const api={TripSession,emptyRoute};root.RoadTripSession=api;if(typeof module!=='undefined')module.exports=api;
})(typeof self!=='undefined'?self:globalThis);
