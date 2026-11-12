/* Continuous GPU ribbons sample real corridors; direction and speed are artistic. */
(function(root){
 'use strict';
 const vertex=`#version 300 es
 precision highp float;
 uniform mat4 u_matrix;
 uniform sampler2D u_paths;
 uniform float u_time,u_dpr,u_mpp,u_kind,u_glow;
 uniform vec2 u_viewport;
 in vec4 a_data;
 in vec3 a_shape;
 out float v_alpha;
 out float v_side;
 vec4 position(float phase){
   float cell=clamp(phase,0.0,1.0)*255.0;
   int lo=int(floor(cell));
   vec2 a=texelFetch(u_paths,ivec2(lo,int(a_data.x)),0).rg;
   vec2 b=texelFetch(u_paths,ivec2(min(255,lo+1),int(a_data.x)),0).rg;
   return u_matrix*vec4(mix(a,b,fract(cell)),0.0,1.0);
 }
 void main(){
   float time=u_time;
   float phase=fract(a_data.y+max(0.0,time-a_data.w)*a_data.z);
   float tail=min(.16,22.0*u_mpp/(a_shape.z*1000.0));
   float along=max(0.0,phase-a_shape.x*tail);
   vec4 p=position(along);
   if(u_kind<.5){
     vec4 before=position(max(0.0,along-.0006)),after=position(min(1.0,along+.0006));
     vec2 tangent=(after.xy/after.w-before.xy/before.w)*u_viewport;
     tangent=length(tangent)>.00001?normalize(tangent):vec2(1.0,0.0);
     vec2 normal=vec2(-tangent.y,tangent.x);
     float width=u_glow>.5?5.0:1.35;
     p.xy+=normal*a_shape.y*width*u_dpr/u_viewport*p.w;
   }
   gl_Position=p;
   gl_PointSize=(u_glow>.5?17.0:4.2)*u_dpr;
   float life=smoothstep(0.0,tail+.015,phase)*(1.0-smoothstep(.94,1.0,phase));
   v_alpha=life*smoothstep(a_data.w,a_data.w+.7,time)*pow(1.0-a_shape.x,1.65);
   v_side=a_shape.y;
 }`;
 const fragment=`#version 300 es
 precision highp float;
 uniform float u_kind,u_glow;
 in float v_alpha;
 in float v_side;
 out vec4 color;
 void main(){
   float falloff;
   if(u_kind>.5){vec2 p=gl_PointCoord*2.0-1.0;float d=dot(p,p);if(d>1.0)discard;falloff=exp(-d*4.5);}
   else falloff=exp(-v_side*v_side*(u_glow>.5?3.5:2.2));
   float a=v_alpha*falloff*(u_glow>.5?.10:.78);
   color=vec4(vec3(.28,.83,1.0)*a,a);
 }`;
 function shader(gl,type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s}
 class PulseParticles{
  constructor(routes,lines,state,mobile){this.id='electrical-pulse';this.type='custom';this.renderingMode='2d';this.routes=routes.routes;this.state=state;this.count=mobile?72:180;this.available=false}
  onAdd(map,gl){
   this.map=map;
   if(!gl.createVertexArray||gl.getParameter(gl.MAX_TEXTURE_SIZE)<Math.max(256,this.routes.length))throw Error('WebGL2 is needed for continuous light trails');
   const program=this.program=gl.createProgram();
   for(const [type,source] of [[gl.VERTEX_SHADER,vertex],[gl.FRAGMENT_SHADER,fragment]]){const s=shader(gl,type,source);gl.attachShader(program,s);gl.deleteShader(s)}
   gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(program));
   this.uniforms={};for(const name of ['u_matrix','u_paths','u_time','u_dpr','u_mpp','u_kind','u_glow','u_viewport'])this.uniforms[name]=gl.getUniformLocation(program,name);
   const data=new Float32Array(256*this.routes.length*4);
   this.routes.forEach((r,row)=>{for(let x=0;x<256;x++){data[(row*256+x)*4]=r.samples[x*2];data[(row*256+x)*4+1]=r.samples[x*2+1]}});
   this.texture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,this.texture);
   for(const [key,value] of [[gl.TEXTURE_MIN_FILTER,gl.NEAREST],[gl.TEXTURE_MAG_FILTER,gl.NEAREST],[gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE],[gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE]])gl.texParameteri(gl.TEXTURE_2D,key,value);
   gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA32F,256,this.routes.length,0,gl.RGBA,gl.FLOAT,data);
   const random=PulseCore.seeded(12026),ribbons=[],heads=[],weights=this.routes.map(r=>Math.max(2,r.length_km)),total=weights.reduce((a,b)=>a+b,0);
   for(let i=0;i<this.count;i++){
    let value=random()*total,row=0;while(row<weights.length-1&&value>weights[row])value-=weights[row++];
    const r=this.routes[row],phase=random(),speed=(11+random()*7.5)/Math.max(3,r.length_km),base=[row,phase,speed,PulseCore.trailTime(r.reveal)];
    heads.push(...base,0,0,r.length_km);
    for(let segment=0;segment<20;segment++)for(const [step,side] of [[0,-1],[0,1],[1,-1],[1,-1],[0,1],[1,1]])ribbons.push(...base,(segment+step)/20,side,r.length_km);
   }
   this.resources=[];
   const buffer=vertices=>{
    const vao=gl.createVertexArray(),vbo=gl.createBuffer();gl.bindVertexArray(vao);gl.bindBuffer(gl.ARRAY_BUFFER,vbo);gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(vertices),gl.STATIC_DRAW);
    for(const [name,size,offset] of [['a_data',4,0],['a_shape',3,16]]){const loc=gl.getAttribLocation(program,name);gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,size,gl.FLOAT,false,28,offset)}
    const resource={vao,vbo,count:vertices.length/7};this.resources.push(resource);return resource;
   };
   this.ribbons=buffer(ribbons);this.heads=buffer(heads);gl.bindVertexArray(null);gl.bindTexture(gl.TEXTURE_2D,null);this.available=true;
  }
  render(gl,args){
   if(!this.available)return;
   gl.disable(gl.DEPTH_TEST);gl.depthMask(false);gl.enable(gl.BLEND);gl.blendFunc(gl.ONE,gl.ONE);gl.useProgram(this.program);
   const u=this.uniforms,canvas=this.map.getCanvas();
   gl.uniformMatrix4fv(u.u_matrix,false,args.defaultProjectionData?.mainMatrix||args);
   gl.uniform1f(u.u_time,this.state.time);gl.uniform1f(u.u_dpr,canvas.width/Math.max(1,canvas.clientWidth));
   gl.uniform1f(u.u_mpp,40075016.686*Math.cos(this.map.getCenter().lat*Math.PI/180)/(512*2**this.map.getZoom()));gl.uniform2f(u.u_viewport,canvas.width,canvas.height);
   gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,this.texture);gl.uniform1i(u.u_paths,0);
   for(const glow of [1,0]){
    gl.uniform1f(u.u_glow,glow);gl.uniform1f(u.u_kind,0);gl.bindVertexArray(this.ribbons.vao);gl.drawArrays(gl.TRIANGLES,0,this.ribbons.count);
    gl.uniform1f(u.u_kind,1);gl.bindVertexArray(this.heads.vao);gl.drawArrays(gl.POINTS,0,this.heads.count);
   }
   gl.bindVertexArray(null);gl.bindTexture(gl.TEXTURE_2D,null);
  }
  onRemove(map,gl){for(const r of this.resources||[]){gl.deleteBuffer(r.vbo);gl.deleteVertexArray(r.vao)}if(this.texture)gl.deleteTexture(this.texture);if(this.program)gl.deleteProgram(this.program);this.available=false}
 }
 root.PulseParticles=PulseParticles;
})(globalThis);
