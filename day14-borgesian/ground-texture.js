/* Decorative, seamless lawn texture; it does not encode observed ground conditions. */
export function grassPattern(){
  const size=256,canvas=document.createElement('canvas');canvas.width=canvas.height=size;
  const ctx=canvas.getContext('2d'),pixels=ctx.createImageData(size,size);let seed=714;
  const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)|0;return (seed>>>0)/4294967296;};
  for(let y=0;y<size;y++)for(let x=0;x<size;x++){
    const broad=4*Math.cos(x*Math.PI/64)*Math.cos(y*Math.PI/128),mown=2*Math.sin(x*Math.PI/32),grain=(random()-.5)*12;
    const i=(y*size+x)*4;pixels.data[i]=132+broad+mown+grain;pixels.data[i+1]=145+broad+mown+grain;pixels.data[i+2]=91+broad+grain;pixels.data[i+3]=255;
  }
  ctx.putImageData(pixels,0,0);
  for(let i=0;i<2100;i++){
    const x=random()*size,y=random()*size,h=1+random()*4,lean=(random()-.5)*3;
    ctx.strokeStyle=i%5===0?'rgba(213,201,137,.35)':'rgba(67,91,43,.28)';ctx.lineWidth=.55+random()*.5;
    for(const dx of [-size,0,size])for(const dy of [-size,0,size]){
      ctx.beginPath();ctx.moveTo(x+dx,y+dy);ctx.quadraticCurveTo(x+dx+lean*.35,y+dy-h*.5,x+dx+lean,y+dy-h);ctx.stroke();
    }
  }
  return ctx.getImageData(0,0,size,size);
}
