'use strict';
const output=document.querySelector('#results'), reports=[];
function render(){output.replaceChildren(...reports.map(text=>{const line=document.createElement('div');line.textContent=text;return line}))}
const delay=ms=>new Promise(r=>setTimeout(r,ms));
function check(condition,message){reports.push((condition?'PASS ':'FAIL ')+message);render();if(!condition)throw Error(message)}
function doc(id){return document.getElementById(id).contentDocument}
function win(id){return document.getElementById(id).contentWindow}
async function until(fn){for(let n=0;n<80;n++){if(fn())return;await delay(100)}throw Error('Timed out waiting for media or UI')}
async function prepare(){
  if(new URLSearchParams(location.search).get('view')==='laptop'){
    document.querySelector('#desktop').style.width='1280px';
    document.querySelector('#desktop').style.height='650px';
    document.querySelector('#desktop').previousElementSibling.textContent='Laptop · 1280 × 650';
  }
  const html=await (await fetch('map.html')).text();
  const instrumentation='<base href="'+location.href+'"><script>window.qaErrors=[];window.addEventListener("error",e=>qaErrors.push(e.message));window.addEventListener("unhandledrejection",e=>qaErrors.push(String(e.reason)));const oldError=console.error;console.error=(...args)=>{qaErrors.push(args.join(" "));oldError(...args)};<\/script>';
  for(const id of ['desktop','mobile'])document.getElementById(id).srcdoc=html.replace('<head>','<head>'+instrumentation);
  await until(()=>['desktop','mobile'].every(id=>doc(id)?.querySelectorAll('.city').length===12));
  await until(()=>['desktop','mobile'].every(id=>[...doc(id).images].every(i=>i.complete&&i.naturalWidth>0)));
  for(const id of ['desktop','mobile']){
    const d=doc(id),w=win(id),buttons=[...d.querySelectorAll('.city')];
    check(d.images.length===12,id+': all twelve SVG maps rendered');
    check(d.documentElement.scrollWidth<=w.innerWidth,id+': no horizontal overflow');
    check(buttons.every(b=>Math.abs(b.querySelector('.disc').getBoundingClientRect().width-b.querySelector('.disc').getBoundingClientRect().height)<1),id+': circular aspect ratios');
    check(w.getComputedStyle(d.querySelector('.gallery')).gridTemplateColumns.split(' ').length===(id==='desktop'?4:2),id+': expected grid columns');
    check(w.TrafficGallery.audio.paused&&!w.TrafficGallery.audio.getAttribute('src'),id+': no autoplay');
    check(d.querySelector('#player').hidden,id+': controls hidden before selection');
    if(id==='desktop')check(d.documentElement.scrollHeight<=w.innerHeight,id+': whole gallery fits vertically ('+d.documentElement.scrollHeight+'/'+w.innerHeight+'px; header '+d.querySelector('header').offsetHeight+', grid '+d.querySelector('.gallery').offsetHeight+', player '+d.querySelector('.listening').offsetHeight+', footer '+d.querySelector('footer').offsetHeight+', circle '+buttons[0].querySelector('.disc').offsetWidth+')');
    check(buttons.every(b=>b.tagName==='BUTTON'&&b.getAttribute('aria-label')),id+': native labeled keyboard buttons');
    check(buttons[7].dataset.id==='sydney'&&buttons[10].dataset.id==='johannesburg',id+': final city order');
    if(id==='desktop')check(Math.abs(buttons[0].querySelector('.disc').getBoundingClientRect().width-Math.max(84,Math.min(147,(w.innerHeight-400)/3)))<1,'desktop: maps respond to available browser height');
    check(!w.qaErrors.length,id+': no runtime or console errors');
  }
  reports.push('Ready for actual audio checks.');render();document.querySelector('#run').disabled=false;
}
prepare().catch(e=>output.textContent+='\nERROR '+e.message);
document.querySelector('#run').onclick=async()=>{
  document.querySelector('#run').disabled=true;
  try{
    const d=doc('desktop'),w=win('desktop'),a=w.TrafficGallery.audio,buttons=[...d.querySelectorAll('.city')];
    for(const b of buttons){
      b.click();await until(()=>!a.paused&&!a.error&&a.currentTime>0);
      check(!d.querySelector('#player').hidden,b.dataset.id+': actual audio playing with compact player');
      check(d.documentElement.scrollHeight<=w.innerHeight,'whole gallery and selected player fit vertically');
      check(d.querySelectorAll('.selected').length===1&&d.querySelectorAll('.playing').length===1,b.dataset.id+': one selected/playing city');
      check(d.querySelector('#now').textContent.includes(w.TrafficGallery.selected.city),'player names selected city');
      check(Number.isFinite(a.duration)&&a.duration>0,'duration from actual media metadata');
      check(d.querySelector('#credit').textContent.includes(w.TrafficGallery.selected.recording.creator),'verified creator attribution');
      b.click();check(a.paused,'active city pauses');check(!d.querySelector('.city.playing'),'paused state stops active animation');
      b.click();await until(()=>!a.paused);check(!a.paused,'active city resumes');
    }
    const range=d.querySelector('#progress');range.value=50;range.dispatchEvent(new w.Event('input'));await until(()=>a.currentTime>=a.duration*.45);check(a.currentTime<=a.duration*.6,'seek follows actual duration');
    d.querySelector('#mute').click();check(a.muted&&d.querySelector('#mute').getAttribute('aria-pressed')==='true','mute state');
    d.querySelector('#mute').click();check(!a.muted,'unmute');
    d.querySelector('#toggle').click();check(a.paused,'player pause');d.querySelector('#toggle').click();await until(()=>!a.paused);check(!a.paused,'player resume');
    d.querySelector('#toggle').click();check(a.paused,'desktop playback stopped before mobile test');
    // Repeat a real touch-sized interaction in the mobile viewport.
    const md=doc('mobile'),mw=win('mobile');md.querySelector('[data-id="sydney"]').click();await until(()=>!mw.TrafficGallery.audio.paused&&mw.TrafficGallery.audio.currentTime>0);check(md.querySelector('#now').textContent.includes('Sydney'),'mobile Sydney playback');md.querySelector('#toggle').click();check(mw.TrafficGallery.audio.paused,'mobile player pause');
    check(!w.qaErrors.length&&!mw.qaErrors.length,'no runtime, rejection or console errors after playback');
    reports.push('COMPLETE');render();
  }catch(e){output.textContent+='\nERROR '+e.message}finally{document.querySelector('#run').disabled=false}
};

document.querySelector('#focus-city').onclick=()=>{doc('desktop').querySelector('[data-id="dhaka"]').focus();};
if(new URLSearchParams(location.search).get('view')==='mobile'){
 const style=document.createElement('style');
 style.textContent='body>*{display:none!important}#mobile{display:block!important;position:absolute;top:12px;left:calc(50% - 156px);transform:scale(.8);transform-origin:top left}';
 document.head.append(style);
}
