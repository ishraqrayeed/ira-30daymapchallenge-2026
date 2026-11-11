/* One shared media element guarantees mutually exclusive playback. */
'use strict';
const gallery = document.getElementById('gallery');
const now = document.getElementById('now');
const credit = document.getElementById('credit');
const toggle = document.getElementById('toggle');
const mute = document.getElementById('mute');
const player = document.getElementById('player');
const progress = document.getElementById('progress');
const audio = new Audio();
audio.preload = 'none';
let selected = null, cities = [], request = 0, context, analyser, samples, frame, lastDraw = 0;
const reduced = matchMedia('(prefers-reduced-motion: reduce)');
const canvas = document.getElementById('waveform'), pen = canvas.getContext('2d');
function safeLink(label, href) {
  const a = document.createElement('a'); a.textContent = label; a.href = href;
  a.target = '_blank'; a.rel = 'noopener'; return a;
}
function duration() {
  return Number.isFinite(audio.duration) && audio.duration > 0
    ? audio.duration : selected?.recording?.excerpt_duration_s || 0;
}
function clock(seconds) {
  const value = Math.max(0, Math.floor(Number(seconds) || 0));
  return `${Math.floor(value / 60)}:${String(value % 60).padStart(2, '0')}`;
}
function updateProgress() {
  const total = duration(), current = audio.currentTime || 0;
  document.getElementById('elapsed').textContent = clock(current);
  document.getElementById('duration').textContent = clock(total);
  progress.value = total ? Math.min(100, current / total * 100) : 0;
  progress.disabled = !Number.isFinite(audio.duration) || audio.duration <= 0;
  progress.setAttribute('aria-valuetext', `${clock(current)} of ${clock(total)}`);
}
function sync() {
  const playing = selected && !audio.paused && !audio.ended && !audio.error;
  for (const button of gallery.children) {
    const active = button.dataset.id === selected?.id;
    button.classList.toggle('selected', active);
    button.classList.toggle('playing', Boolean(active && playing));
    button.setAttribute('aria-pressed', String(active));
    const city = cities.find(c => c.id === button.dataset.id);
    button.setAttribute('aria-label', !city.audio ? `${city.city}: traffic audio unavailable` :
      `${active && playing ? 'Pause' : active && !audio.ended ? 'Resume' : 'Play'} traffic sounds from ${city.city}`);
    button.querySelector('.city-note').textContent = button.dataset.mapError ? 'Map unavailable' :
      !city.audio ? 'Audio unavailable' : active ? playing ? 'Listening' : audio.ended ? 'Finished' : 'Paused' : '';
  }
  player.hidden = !selected?.audio;
  toggle.textContent = playing ? 'Pause' : 'Play';
  toggle.setAttribute('aria-label', `${playing ? 'Pause' : 'Play'} traffic sounds from ${selected?.city || 'selected city'}`);
  mute.textContent = audio.muted ? 'Unmute' : 'Mute';
  mute.setAttribute('aria-pressed', String(audio.muted));
  updateProgress();
  refreshVisualization();
}
function attribution(city) {
  credit.replaceChildren();
  if (!city.audio) {
    credit.textContent = 'A verified reusable traffic recording is not available yet.';
    if (city.reference) credit.append(document.createTextNode(' · '), safeLink(`${city.reference.creator} · Dhanmondi 27 source ↗`, city.reference.source_url));
    return;
  }
  const r = city.recording;
  credit.append(document.createTextNode('Street traffic · Recorded by '), safeLink(r.creator, r.source_url));
  if (r.license_url) credit.append(document.createTextNode(' · '), safeLink(r.license, r.license_url));
  credit.append(document.createTextNode(' · '), safeLink('Original recording ↗', r.source_url));
}
function initAnalyser() {
  try {
    if (!context) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return;
      context = new AC(); analyser = context.createAnalyser(); analyser.fftSize = 256;
      samples = new Uint8Array(analyser.fftSize);
      const source = context.createMediaElementSource(audio);
      source.connect(analyser); analyser.connect(context.destination);
    }
    context.resume().catch(() => {});
  } catch (_) { /* Native playback remains available without a waveform. */ }
}
async function play() {
  if (!selected?.audio) return;
  const version = ++request, city = selected;
  initAnalyser(); now.textContent = `Loading: ${city.city}`;
  try {
    if (audio.ended) audio.currentTime = 0;
    await audio.play();
    if (version !== request) return;
    now.textContent = `Now playing: ${city.city}${audio.muted ? ' · muted' : ''}`;
  } catch (error) {
    if (version !== request) return;
    now.textContent = error.name === 'NotAllowedError' ? 'Playback was blocked. Press Play to try again.' : `${city.city} · Recording unavailable. Try another city.`;
  }
  sync();
}
function pause() {
  ++request; audio.pause();
  if (selected?.audio) now.textContent = `Paused: ${selected.city}`;
  sync();
}
function select(city) {
  if (selected?.id === city.id) {
    if (!city.audio) return;
    if (audio.paused) play(); else pause();
    return;
  }
  ++request; audio.pause(); audio.removeAttribute('src'); audio.load();
  selected = city; attribution(city); sync();
  if (!city.audio) { now.textContent = `${city.city}, ${city.country} · Audio temporarily unavailable`; return; }
  audio.src = city.audio; play();
}
function draw(now = 0) {
  frame = null;
  const live = analyser && !audio.paused && !audio.ended && !audio.muted && !audio.error && !reduced.matches;
  if (!live || now - lastDraw >= 32) {
    lastDraw = now;
    pen.clearRect(0,0,canvas.width,canvas.height);
    pen.strokeStyle = audio.muted ? '#bbbeb5' : '#D18A45'; pen.lineWidth = 1.5; pen.beginPath();
    if (live) analyser.getByteTimeDomainData(samples);
    for (let x=0; x<canvas.width; x++) {
      const value = live ? (samples[Math.floor(x / canvas.width * samples.length)]-128)/128 : 0;
      const y = canvas.height/2 + value*canvas.height*.46;
      x ? pen.lineTo(x,y) : pen.moveTo(x,y);
    }
    pen.stroke();
    for (const button of gallery.children) {
      const bars = button.querySelectorAll('.equalizer i');
      bars.forEach((bar, index) => {
        let level = .2;
        if (live && button.dataset.id === selected?.id) {
          const start = Math.floor(index * samples.length / 4), end = Math.floor((index+1)*samples.length / 4);
          let sum = 0;
          for(let n=start;n<end;n++) sum += ((samples[n]-128)/128)**2;
          level = Math.min(1, .2 + Math.sqrt(sum/(end-start))*5);
        }
        bar.style.transform = `scaleY(${level})`;
      });
    }
  }
  if (live) frame = requestAnimationFrame(draw);
}
function refreshVisualization() {
  if (frame) cancelAnimationFrame(frame);
  frame = null; draw();
}
reduced.addEventListener('change', refreshVisualization);
progress.addEventListener('input', () => {
  if (Number.isFinite(audio.duration) && audio.duration > 0) {
    audio.currentTime = Number(progress.value) / 100 * audio.duration;
    updateProgress();
  }
});
for(const event of ['loadedmetadata','durationchange','timeupdate','seeked']) audio.addEventListener(event, updateProgress);
toggle.onclick = () => { if (audio.paused) play(); else pause(); };
mute.onclick = () => {
  audio.muted = !audio.muted; sync();
  if (selected?.audio && !audio.paused) now.textContent = `Now playing: ${selected.city}${audio.muted ? ' · muted' : ''}`;
};
audio.addEventListener('ended', () => { if(selected) now.textContent = `Finished: ${selected.city}, ${selected.country} · Play to listen again`; sync(); });
audio.addEventListener('error', () => { if(selected?.audio) now.textContent = `${selected.city} · Recording unavailable. Try another city.`; sync(); });
audio.addEventListener('pause', sync);
audio.addEventListener('playing', sync);
document.addEventListener('visibilitychange', () => { if(document.hidden) pause(); });
window.addEventListener('pagehide', () => { pause(); cancelAnimationFrame(frame); context?.close(); });
fetch('recordings.json?v=johannesburg').then(r => { if (!r.ok) throw Error('Manifest'); return r.json(); }).then(manifest => {
  cities = manifest.cities;
  for(const city of cities) {
    const button = document.createElement('button'); button.type = 'button'; button.className = 'city'; button.dataset.id = city.id; button.classList.toggle('unavailable', !city.audio);
    const disc = document.createElement('span'); disc.className = 'disc';
    const img = document.createElement('img'); img.src = `streets/${city.id}.svg?v=${city.map_version || "traffic"}`; img.alt = `${city.city} public street network, north up, two kilometers across`; img.width = 300; img.height = 300;
    img.onerror = () => {
      if (!img.dataset.retried) {
        img.dataset.retried = 'true';
        img.src = `streets/${city.id}.svg?v=${city.map_version || 'traffic'}&retry=${Date.now()}`;
        return;
      }
      button.dataset.mapError = 'true';
      button.querySelector('.city-note').textContent = 'Map unavailable';
    };
    const hover = document.createElement('span'); hover.className = 'hover-play'; hover.setAttribute('aria-hidden','true');
    const indicator = document.createElement('span'); indicator.className = 'equalizer'; indicator.setAttribute('aria-hidden','true');
    for(let n=0;n<4;n++) indicator.append(document.createElement('i'));
    disc.append(img,hover,indicator);
    const name = document.createElement('span'); name.className = 'city-name'; name.textContent = city.city;
    const note = document.createElement('span'); note.className = 'city-note'; note.setAttribute('aria-hidden','true');
    button.append(disc,name,note); button.onclick = () => select(city); gallery.append(button);
  }
  sync();
}).catch(() => { now.textContent = 'The city collection could not load. Please refresh the page.'; });
// Read-only inspection surface for browser QA; no autoplay or extra audio elements.
window.TrafficGallery = { get audio(){ return audio; }, get selected(){ return selected; } };
