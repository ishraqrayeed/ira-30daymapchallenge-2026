
'use strict';
const MAP_DATA=@@DATA@@;
const pitch=document.getElementById('pitch'), tooltip=document.getElementById('tooltip');
const shots=new Map(MAP_DATA.shots.map(s=>[s.source_event_id,s]));
let locked=null;
function clearSelection(){pitch.classList.remove('inspecting');pitch.querySelectorAll('.selected').forEach(n=>n.classList.remove('selected'));tooltip.hidden=true;}
function inspect(id,position){
  const s=shots.get(id);if(!s)return;clearSelection();pitch.classList.add('inspecting');
  pitch.querySelectorAll('[data-event]').forEach(n=>n.classList.toggle('selected',n.dataset.event===id));
  tooltip.replaceChildren();const heading=document.createElement('strong');heading.textContent=`ARGENTINA v ${s.opponent}`;tooltip.append(heading);
  const outcome=document.createElement('div');outcome.textContent=`Recorded ${s.clock} · ${s.outcome}${s.is_penalty?' · Penalty':''}`;tooltip.append(outcome);
  const metrics=document.createElement('div');metrics.className='metrics';metrics.textContent=`${s.distance_to_goal_m.toFixed(1)} m from goal · ${s.sight_angle_deg.toFixed(1)}° view`;tooltip.append(metrics);
  tooltip.hidden=false;const bounds=tooltip.getBoundingClientRect();
  let left=Math.min(position.x+16,innerWidth-bounds.width-12),top=position.y+20;
  if(top+bounds.height>innerHeight-12)top=position.y-bounds.height-16;
  tooltip.style.left=`${Math.max(12,left)}px`;tooltip.style.top=`${Math.max(12,top)}px`;
}
pitch.querySelectorAll('.marker').forEach(marker=>{
  marker.addEventListener('pointerenter',e=>{if(e.pointerType!=='touch'&&!locked)inspect(marker.dataset.event,{x:e.clientX,y:e.clientY});});
  marker.addEventListener('pointerleave',()=>{if(!locked)clearSelection();});
  marker.addEventListener('focus',()=>{if(!locked){const b=marker.getBoundingClientRect();inspect(marker.dataset.event,{x:b.left,y:b.top});}});
  marker.addEventListener('blur',()=>{if(!locked)clearSelection();});
  marker.addEventListener('click',e=>{e.stopPropagation();const id=marker.dataset.event;if(locked===id){locked=null;clearSelection();}else{locked=id;inspect(id,{x:e.clientX,y:e.clientY});}});
  marker.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();const b=marker.getBoundingClientRect();marker.dispatchEvent(new MouseEvent('click',{bubbles:true,clientX:b.left,clientY:b.top}));}});
});
document.addEventListener('click',()=>{locked=null;clearSelection();});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){locked=null;clearSelection();}});
