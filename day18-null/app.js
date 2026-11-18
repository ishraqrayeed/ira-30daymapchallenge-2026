const $ = id => document.getElementById(id);
const ml = window.maplibregl;
const clamp = (value, min = 0, max = 1) => Math.max(min, Math.min(max, value));
const lerp = (a, b, t) => a + (b - a) * t;
const smooth = value => { const t = clamp(value); return t * t * (3 - 2 * t); };
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
const compact = matchMedia('(max-width: 670px)');
const features = items => ({ type: 'FeatureCollection', features: items });
const geo = (type, coordinates, properties = {}) => ({ type: 'Feature', geometry: { type, coordinates }, properties });
const format = (n, digits = 1) => n.toLocaleString('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits });
const DURATION = 28_000;
const CITY_LABELS = new Set(['St. Louis', 'Columbia', 'Kansas City', 'Topeka', 'Salina', 'Hays', 'Goodland', 'Limon', 'Denver']);

async function getJSON(file) {
  const response = await fetch(new URL(file, import.meta.url));
  if (!response.ok) throw new Error(`Unable to load ${file} (${response.status})`);
  return response.json();
}

function lowerBound(items, mile, getMile) {
  let left = 0;
  let right = items.length;
  while (left < right) {
    const mid = (left + right) >> 1;
    if (getMile(items[mid]) < mile) left = mid + 1;
    else right = mid;
  }
  return left;
}

function position(data, mile) {
  const i = clamp(lowerBound(data.route, mile, p => p[2]), 1, data.route.length - 1);
  const a = data.route[i - 1], b = data.route[i];
  const t = clamp((mile - a[2]) / (b[2] - a[2]));
  return [lerp(a[0], b[0], t), lerp(a[1], b[1], t)];
}
function nearestPlace(data, mile) {
  const i = lowerBound(data.places, mile, p => p.mile);
  const a = data.places[Math.max(0, i - 1)], b = data.places[Math.min(i, data.places.length - 1)];
  return mile - a.mile < b.mile - mile ? a.name : b.name;
}
const BAND_COLORS = {moderate: '#f2dfc7', high: '#dda66d', extreme: '#ad612a'};
const BAND_OPACITY = {moderate: .73, high: .68, extreme: .72};
const PAPER = '#f7f2e8';
function bandSwatch(band) {
  const opacity = BAND_OPACITY[band];
  const rgb = (color, i) => parseInt(color.slice(i, i + 2), 16);
  return `rgb(${[1, 3, 5].map(i => Math.round(lerp(rgb(PAPER, i), rgb(BAND_COLORS[band], i), opacity))).join(', ')})`;
}
const STORIES = new Map([
  [424, {title: 'West of Salina', landscape: 'The road straightens. The scenery starts repeating itself.',
    notes: [[0, 'Straightness'], [3, 'Successive samples with the same cover']]}],
  [640, {title: 'Around Goodland', landscape: 'Fields. More fields. And then some more fields.',
    notes: [[2, 'Dominant cover'], [0, 'Straightness']]}],
  [728, {title: 'Eastern Colorado', landscape: 'Still driving. Still grassland. Are we there yet?',
    notes: [[3, 'Successive samples with the same cover']]}],
]);
const LANDMARKS = [
  {start: 128, segment: 16, coordinates: [-92.560933, 38.977450], title: 'Rocheport, Missouri',
    landscape: 'The Missouri River winds past limestone bluffs. Enjoy the scenery while it lasts.'},
  {start: 248, segment: 31, coordinates: [-94.581, 39.109], title: 'Kansas City',
    landscape: 'One last big city. Then the long road west begins.'},
];

function traveledColor(progress) {
  return ['case', ['<=', ['line-progress'], progress], '#57331f', 'rgba(0, 0, 0, 0)'];
}

function routeProgress(route) {
  let total = 0;
  const lengths = route.map((point, i) => {
    const p = ml.MercatorCoordinate.fromLngLat(point.slice(0, 2));
    if (i) {
      const q = ml.MercatorCoordinate.fromLngLat(route[i - 1].slice(0, 2));
      total += Math.hypot(p.x - q.x, p.y - q.y);
    }
    return total;
  });
  return mile => {
    const i = clamp(lowerBound(route, mile, p => p[2]), 1, route.length - 1);
    const fraction = (mile - route[i - 1][2]) / (route[i][2] - route[i - 1][2]);
    return lerp(lengths[i - 1], lengths[i], fraction) / total;
  };
}

function style(data, analysis) {
  const route = data.route.map(p => p.slice(0, 2));
  const {start, end} = analysis.longest ?? {start: 0, end: 0};
  const longest = analysis.longest
    ? [position(data, start), ...data.route.filter(p => p[2] > start && p[2] < end).map(p => p.slice(0, 2)), position(data, end)]
    : route;
  const reveal = ['coalesce', ['feature-state', 'light'], 0];
  const color = ['match', ['get', 'band'], 'moderate', BAND_COLORS.moderate,
    'high', BAND_COLORS.high, BAND_COLORS.extreme];
  const line = (id, source, paint) => ({id, source, type: 'line', layout: {'line-join': 'round', 'line-cap': 'round'}, paint});
  return {
    version: 8,
    sources: {
      states: {type: 'geojson', data: './assets/states.geojson'},
      patches: {type: 'geojson', data: './assets/monotony.geojson', tolerance: .17, maxzoom: 11},
      route: {type: 'geojson', data: geo('LineString', route), tolerance: .04, lineMetrics: true},
      longest: {type: 'geojson', data: geo('LineString', longest), tolerance: .04},
      services: {type: 'geojson', data: features(data.services.map(s => geo('Point', s.coordinates, s)))},
    },
    layers: [
      {id: 'ground', type: 'background', paint: {'background-color': PAPER}},
      line('states', 'states', {'line-color': '#818984', 'line-opacity': .56, 'line-width': .8}),
      {id: 'patch-fill', type: 'fill', source: 'patches', paint: {
        'fill-color': color, 'fill-opacity': ['*', reveal, ['match', ['get', 'band'], 'moderate', BAND_OPACITY.moderate, 'high', BAND_OPACITY.high, BAND_OPACITY.extreme]],
      }},
      line('patch-outline', 'patches', {'line-color': color, 'line-width': .5, 'line-opacity': ['*', reveal, .10]}),
      line('route', 'route', {'line-color': '#a35a17', 'line-width': 1.25, 'line-opacity': .90}),
      line('traversed', 'route', {'line-width': 1.75, 'line-gradient': traveledColor(-1)}),
      line('longest', 'longest', {'line-color': '#6f3a14', 'line-width': 2, 'line-opacity': 0}),
      {id: 'services', source: 'services', type: 'circle', minzoom: 7, layout: {visibility: 'none'}, paint: {
        'circle-color': '#52686b', 'circle-radius': 3.8, 'circle-stroke-color': '#fcf9f2', 'circle-stroke-width': 1,
      }},
    ],
  };
}

function start(data, analysis) {
  const map = new ml.Map({container: 'map', style: style(data, analysis), interactive: true,
    attributionControl: false, bearing: 0, pitch: 8, maxPitch: 8,
    minZoom: 2, maxZoom: 16, fadeDuration: 0, renderWorldCopies: false, pixelRatio: Math.min(devicePixelRatio, 1.6)});
  const dot = document.createElement('span');
  dot.className = 'journey-dot';
  dot.setAttribute('aria-hidden', 'true');
  const traveler = new ml.Marker({element: dot}).setLngLat(position(data, 0));
  const progressAt = routeProgress(data.route);
  let lastProgress = -1;
  const bounds = new ml.LngLatBounds();
  for (const p of data.route) bounds.extend(p.slice(0, 2));
  const controls = ['play', 'replay', 'skip', 'explore', 'seek'];
  const handlers = [map.dragPan, map.scrollZoom, map.doubleClickZoom, map.touchZoomRotate, map.keyboard, map.boxZoom];
  const nav = new ml.NavigationControl({showCompass: false});
  const bandsBySegment = new Map(analysis.regions.flatMap(r => r.segmentIds.map(id => [id, r.band])));
  let mile = 0, playing = false, exploring = false, zero = 0, playbackFrame = 0;
  const light = new Map();
  const stories = analysis.regions.filter(r => STORIES.has(r.start)).map(region => {
    const story = STORIES.get(region.start);
    const notes = story.notes.map(([i, label]) => {
      const values = region.segmentIds.map(id => analysis.segments[id].components[i]);
      return `${label} ${format(values.reduce((a, b) => a + b, 0) / values.length, 0)}${i === 0 ? '/100' : '%'}`;
    });
    return {...region, title: story.title,
      landscape: story.landscape,
      coordinates: position(data, (region.start + region.end) / 2), notes: notes.join(' · ')};
  });
  for (const landmark of LANDMARKS) {
    const sample = analysis.segments[landmark.segment];
    stories.push({...landmark,
      notes: `DMI ${format(sample.score, 0)}/100 · Dominant cover ${format(sample.components[2], 0)}%`});
  }
  stories.sort((a, b) => b.start - a.start);
  const callouts = stories.map(story => {
    const card = document.createElement('article');
    card.title = story.notes;
    for (const [className, value] of [
      ['eyebrow', story.title], ['callout-detail', story.landscape],
    ]) {
      const line = document.createElement('p');
      line.className = className;
      line.textContent = value;
      card.append(line);
    }
    $('story-index').append(card);
    const pin = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    pin.setAttribute('r', '2.5');
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    $('story-leader').append(path, pin);
    return {story, card, path, pin};
  });
  let storyNeedsLayout = true;
  function updateStory() {
    const mapBox = storyNeedsLayout && map.getContainer().getBoundingClientRect();
    for (const {story, card, path, pin} of callouts) {
      const opacity = smooth((mile - story.start) / (data.miles * 500 / DURATION));
      for (const element of [card, path, pin]) {
        element.style.visibility = opacity > 0 ? 'visible' : 'hidden';
        element.style.opacity = opacity;
      }
      if (!storyNeedsLayout) continue;
      const point = map.project(story.coordinates);
      const box = card.getBoundingClientRect();
      const x = box.left + box.width / 2 - mapBox.left;
      path.setAttribute('d', `M ${x} 0 L ${point.x} ${point.y - 4}`);
      pin.setAttribute('cx', point.x);
      pin.setAttribute('cy', point.y);
    }
    storyNeedsLayout = false;
  }
  let lastReadout = -Infinity, ending = false, popup;

  function fit() {
    storyNeedsLayout = true;
    const pad = compact.matches ? 29 : 53;
    const camera = map.cameraForBounds(bounds, {padding: {top: 28, bottom: 34, left: pad, right: pad}, bearing: 0});
    if (camera) map.jumpTo({...camera, pitch: 8, bearing: 0});
  }
  function exploration(on) {
    exploring = on;
    for (const h of handlers) h[on ? 'enable' : 'disable']();
    map.touchZoomRotate.disableRotation();
    map.dragRotate.disable();
    if (on && !map.hasControl(nav)) map.addControl(nav);
    if (!on && map.hasControl(nav)) map.removeControl(nav);
    map.setLayoutProperty('services', 'visibility', on ? 'visible' : 'none');
    $('explore').setAttribute('aria-pressed', String(on));
    $('explore').textContent = on ? 'Poster view' : 'Explore map';
    if (!on) popup?.remove();
  }
  function render(value, now) {
    mile = clamp(value, 0, data.miles);
    const active = analysis.segments[Math.min(analysis.segments.length - 1, Math.floor(mile / 8))];
    traveler.setLngLat(position(data, mile));
    const routeProgress = mile ? progressAt(mile) : -1;
    if (routeProgress !== lastProgress) {
      map.setPaintProperty('traversed', 'line-gradient', traveledColor(routeProgress));
      lastProgress = routeProgress;
    }
    for (const region of analysis.regions) {
      const opacity = Math.round(smooth((mile - region.start) / Math.min(8, region.miles)) * 60) / 60;
      if (opacity === (light.get(region.id) ?? 0)) continue;
      map.setFeatureState({source: 'patches', id: region.id}, {light: opacity});
      light.set(region.id, opacity);
    }
    updateStory();
    const finished = mile >= data.miles;
    if (finished !== ending) {
      ending = finished;
      map.setPaintProperty('longest', 'line-opacity', finished && analysis.longest ? 1 : 0);
      $('result-places').hidden = !finished || !analysis.longest;
      $('subtitle').textContent = finished ? 'Even boredom can be mapped.' : 'How boring is the drive from St. Louis to Denver?';
    }
    const place = nearestPlace(data, mile);
    const distance = format(mile);
    if (finished || now === undefined || now - lastReadout >= 85) {
      lastReadout = now ?? -Infinity;
      $('traveled').textContent = distance;
      $('place').textContent = place;
      $('monotony').textContent = active.score === null ? '—' : format(active.score, 0);
      $('seek').value = mile;
      $('seek').setAttribute('aria-valuetext', `${distance} miles traveled, near ${place}`);
    }
  }
  function pause() {
    playing = false;
    cancelAnimationFrame(playbackFrame);
    $('play').textContent = 'Play';
  }
  function advance(now) {
    if (!playing) return;
    render((now - zero) / DURATION * data.miles, now);
    if (mile >= data.miles) pause();
    else playbackFrame = requestAnimationFrame(advance);
  }
  function play(restart = false) {
    pause();
    if (exploring) { exploration(false); fit(); }
    if (restart || mile >= data.miles) render(0);
    zero = performance.now() - mile / data.miles * DURATION;
    playing = true;
    $('play').textContent = 'Pause';
    playbackFrame = requestAnimationFrame(advance);
  }
  function marker(coords, label, name, offset) {
    const element = document.createElement('span');
    element.className = label;
    element.textContent = name;
    if (label.includes('endpoint-symbol')) element.setAttribute('aria-hidden', 'true');
    new ml.Marker({element, offset}).setLngLat(coords).addTo(map);
  }
  function profile() {
    const canvas = $('profile'), w = canvas.clientWidth, h = canvas.clientHeight;
    canvas.width = w * 2;
    canvas.height = h * 2;
    const ctx = canvas.getContext('2d');
    ctx.scale(2, 2);
    for (const s of analysis.segments) {
      const bar = h * s.score / 100;
      const band = bandsBySegment.get(s.id);
      ctx.fillStyle = band ? bandSwatch(band) : '#a7a9a0';
      ctx.fillRect(s.start / data.miles * w, h - bar, Math.max(1, (s.end - s.start) / data.miles * w - .45), bar);
    }
  }
  map.on('error', event => console.error(event.error));
  map.once('load', () => {
    fit();
    exploration(false);
    for (const band of Object.keys(BAND_COLORS)) {
      document.querySelector(`.${band}-key`).style.backgroundColor = bandSwatch(band);
    }
    $('gap-value').textContent = analysis.longest
      ? format(analysis.longest.miles, Number.isInteger(analysis.longest.miles) ? 0 : 1) : '—';
    if (analysis.longest) {
      const {startPlace, endPlace} = analysis.longest;
      const place = startPlace.endsWith(', KS') && endPlace.endsWith(', CO')
        ? 'Western Kansas into Colorado' : startPlace;
      $('result-caption').textContent = `Longest high-monotony stretch · ${place}`;
      $('result-places').textContent = `${analysis.longest.startPlace} → ${analysis.longest.endPlace}`;
    }
    $('seek').max = data.miles;
    controls.forEach(id => $(id).disabled = false);
    $('status').textContent = '';
    for (const [label, coords] of [['Colorado', [-103.9, 40.34]], ['Kansas', [-98.97, 40.35]], ['Missouri', [-92.5, 40.25]]])
      marker(coords, 'state-label', label, [0, compact.matches ? -24 : 0]);
    for (const p of data.places) {
      const name = p.name.split(',')[0];
      if (!CITY_LABELS.has(name) || name === 'Topeka') continue;
      const destination = name === 'Denver';
      if (destination || name === 'St. Louis') {
        const coordinates = position(data, destination ? data.miles : 0);
        marker(coordinates, `endpoint-symbol ${destination ? 'destination' : 'origin'}`, '', [0, 0]);
        const inset = compact.matches ? (destination ? 8 : -10) : 0;
        marker(coordinates, 'city-label endpoint', name, [inset, destination ? -24 : 24]);
      } else {
        marker(p.coordinates, 'city-label secondary', name, [0, 16]);
      }
    }
    traveler.addTo(map);
    $('play').onclick = () => playing ? pause() : play();
    $('replay').onclick = () => play(true);
    $('skip').onclick = () => {
      pause();
      if (exploring) { exploration(false); fit(); }
      render(data.miles);
      const calloutPanel = $('story-index');
      const calloutBounds = calloutPanel.getBoundingClientRect();
      if (calloutBounds.top < 0 || calloutBounds.bottom > window.innerHeight) {
        calloutPanel.scrollIntoView({block: 'nearest', behavior: 'instant'});
      }
    };
    $('explore').onclick = () => {
      pause();
      exploration(!exploring);
      if (!exploring) fit();
      render(mile);
    };
    $('seek').oninput = event => {
      pause();
      if (exploring) { exploration(false); fit(); }
      render(Number(event.target.value));
    };
    map.on('move', () => { if (exploring) { storyNeedsLayout = true; updateStory(); } });
    map.on('resize', () => { storyNeedsLayout = true; if (!exploring) fit(); if (!playing) render(mile); });
    map.on('click', event => {
      if (!exploring) return;
      const story = stories.find(s => map.project(s.coordinates).dist(event.point) <= 13);
      if (story) {
        popup?.remove();
        popup = new ml.Popup().setLngLat(story.coordinates).setText(`${story.title} · ${story.notes}`).addTo(map);
        return;
      }
      const hit = map.queryRenderedFeatures(event.point, {layers: ['services', 'patch-fill', 'route']})
        .find(f => f.layer.id !== 'patch-fill' || light.get(f.id) > 0);
      if (!hit) return;
      const value = hit.layer.id === 'services'
        ? `${hit.properties.name} · Westbound fuel access at mile ${format(hit.properties.mile)}`
        : hit.layer.id === 'patch-fill'
          ? `${analysis.regions[hit.id].band.replace(/^./, c => c.toUpperCase())} monotony · ${format(analysis.regions[hit.id].miles)} mi`
          : `I-70 westbound · ${format(data.miles)} miles`;
      popup?.remove();
      popup = new ml.Popup().setLngLat(event.lngLat).setText(value).addTo(map);
    });
    profile();
    new ResizeObserver(profile).observe($('profile'));
    render(0);
    if (!reducedMotion.matches) play();
    else pause();
  });
}

Promise.all([getJSON('./assets/journey.json'), getJSON('./assets/monotony.json')])
  .then(([data, analysis]) => start(data, analysis)).catch(error => {
    console.error(error);
    $('status').textContent = 'The map could not start. Open the local HTTP preview.';
  });
