"use strict";

const map = document.querySelector("#map");
const panel = document.querySelector("#panel");
const details = document.querySelector("#details");
const tooltip = document.querySelector("#tooltip");
const title = document.querySelector("#panel-title");
const close = document.querySelector("#close");
const motion = window.matchMedia("(prefers-reduced-motion: reduce)");
let selected;

function element(tag, text, parent) {
  const node = document.createElement(tag);
  node.textContent = text;
  parent.append(node);
  return node;
}

function countLabel(count) {
  return `${count} listed club${count === 1 ? "" : "s"}`;
}

function populate(cell, records) {
  tooltip.hidden = true;
  const selection = records[cell.dataset.h3];
  const count = Number(cell.dataset.count);
  if (!selection || selection.provider_count !== count || selection.clubs.length !== count) {
    throw new Error(`Club count mismatch for ${cell.dataset.h3}`);
  }
  selected?.removeAttribute("aria-pressed");
  selected = cell;
  cell.setAttribute("aria-pressed", "true");
  title.textContent = countLabel(count);
  details.replaceChildren();
  for (const club of selection.clubs) {
    const section = element("section", "", details);
    const heading = element("h3", "", section);
    if (club.website) {
      const link = element("a", club.name, heading);
      link.href = club.website;
    } else {
      heading.textContent = club.name;
    }
    element("p", [club.city, club.state].filter(Boolean).join(", "), section);
  }
  panel.hidden = false;
  details.scrollTop = 0;
  close.focus({preventScroll: true});
}

function dismiss() {
  if (panel.hidden) return;
  panel.hidden = true;
  selected.removeAttribute("aria-pressed");
  selected.focus({preventScroll: true});
}

function reveal(svg) {
  svg.dataset.reveal = "complete";
  if (motion.matches) return;
  const cells = [...svg.querySelectorAll(".club-cell")];
  for (const cell of cells) cell.style.opacity = "0";
  svg.dataset.reveal = "waiting";
  requestAnimationFrame(() => requestAnimationFrame(() => {
    svg.dataset.reveal = "running";
    const startTime = document.timeline.currentTime;
    const animations = cells.map(cell => {
      const color = cell.style.getPropertyValue("--final");
      const fade = [
        {opacity:0, fill:color, easing:"ease-out"},
        {opacity:.94, fill:`color-mix(in srgb,${color},#F6F2E7 27%)`, offset:.32, easing:"ease-out"},
        {opacity:1, fill:color},
      ];
      const animation = cell.animate(fade, {delay:Number(cell.dataset.start), duration:Number(cell.dataset.duration),
        fill:"both"});
      animation.startTime = startTime;
      return animation;
    });
    function finish() {
      for (const cell of cells) cell.style.removeProperty("opacity");
      for (const animation of animations) animation.cancel();
      svg.dataset.reveal = "complete";
      motion.removeEventListener("change", change);
    }
    function change(event) {
      if (event.matches) finish();
    }
    motion.addEventListener("change", change);
    if (motion.matches) finish();
    Promise.allSettled(animations.map(animation => animation.finished)).then(finish);
  }));
}

function navigation(svg, records) {
  const {x, y, width, height} = svg.getBBox();
  const padding = 9;
  const home = {x:x-padding, y:y-padding, width:width+2*padding, height:height+2*padding};
  let view = {...home};
  let inverse;
  const pointers = new Map();
  let dragged = false;
  let candidate = null;
  let origin;

  function draw() {
    tooltip.hidden = true;
    svg.setAttribute("viewBox", [view.x, view.y, view.width, view.height].join(" "));
  }
  draw();
  function position(point) {
    return new DOMPoint(point.x, point.y).matrixTransform(inverse);
  }
  function zoom(factor, from, to = from) {
    inverse = svg.getScreenCTM().inverse();
    const p = position(from);
    const q = position(to);
    const ratio = Math.max(home.width / 10, Math.min(home.width, view.width / factor)) / view.width;
    view = {x:p.x-(q.x-view.x)*ratio, y:p.y-(q.y-view.y)*ratio,
            width:view.width*ratio, height:view.height*ratio};
    draw();
  }
  function center() {
    const bounds = svg.getBoundingClientRect();
    return {x:bounds.left+bounds.width/2, y:bounds.top+bounds.height/2};
  }
  svg.setAttribute("tabindex", "0");
  svg.setAttribute("aria-keyshortcuts", "+ - Home ArrowLeft ArrowRight ArrowUp ArrowDown");
  svg.addEventListener("wheel", event => {
    event.preventDefault();
    zoom(Math.exp(-Math.max(-160, Math.min(160, event.deltaY)) * .0035),
         {x:event.clientX, y:event.clientY});
  }, {passive:false});

  const middle = (a,b) => ({x:(a.x+b.x)/2, y:(a.y+b.y)/2});
  const distance = (a,b) => Math.hypot(a.x-b.x, a.y-b.y);
  function showTip(cell, x, y) {
    const box = map.getBoundingClientRect();
    tooltip.textContent = countLabel(Number(cell.dataset.count));
    tooltip.hidden = false;
    tooltip.style.left = `${Math.max(2, Math.min(box.width-tooltip.offsetWidth-2, x-box.left+12))}px`;
    const above = y-box.top-tooltip.offsetHeight-10;
    tooltip.style.top = `${above > 2 ? above : Math.min(box.height-tooltip.offsetHeight-2, y-box.top+12)}px`;
  }
  function hover(event) {
    if (event.pointerType !== "mouse" || pointers.size) return;
    const cell = event.target.closest(".hex-hit");
    if (cell) showTip(cell, event.clientX, event.clientY);
    else tooltip.hidden = true;
  }
  svg.addEventListener("pointerover", hover);
  svg.addEventListener("pointermove", hover);
  svg.addEventListener("pointerleave", () => { tooltip.hidden = true; });
  svg.addEventListener("focusin", event => {
    const cell = event.target.closest(".hex-hit:focus-visible");
    if (!cell) return;
    const rect = cell.getBoundingClientRect();
    showTip(cell, rect.left+rect.width/2, rect.top);
  });
  svg.addEventListener("focusout", () => { tooltip.hidden = true; });
  svg.addEventListener("pointerdown", event => {
    tooltip.hidden = true;
    if (event.button !== 0 || pointers.size >= 2) return;
    const p = {x:event.clientX, y:event.clientY};
    if (!pointers.size) {
      origin = p;
      dragged = false;
      candidate = event.target.closest(".hex-hit");
    } else {
      dragged = true;
    }
    pointers.set(event.pointerId, p);
    svg.setPointerCapture(event.pointerId);
  });
  svg.addEventListener("pointermove", event => {
    if (!pointers.has(event.pointerId)) return;
    const previous = pointers.get(event.pointerId);
    const current = {x:event.clientX, y:event.clientY};
    if (!dragged && distance(origin,current) < 5) return;
    dragged = true;
    svg.classList.add("dragging");
    pointers.set(event.pointerId, current);
    const other = [...pointers].find(([id]) => id !== event.pointerId)?.[1];
    if (other) {
      const before = distance(previous,other);
      const after = distance(current,other);
      if (before > 2 && after > 2) zoom(after/before, middle(previous,other), middle(current,other));
    } else {
      zoom(1, previous, current);
    }
  });
  function release(event) {
    if (!pointers.delete(event.pointerId)) return;
    if (!pointers.size) {
      svg.classList.remove("dragging");
      if (!dragged && candidate && event.type === "pointerup") populate(candidate, records);
      candidate = null;
    }
  }
  svg.addEventListener("pointerup", release);
  svg.addEventListener("pointercancel", release);
  svg.addEventListener("lostpointercapture", release);
  svg.addEventListener("keydown", event => {
    const cell = event.target.closest(".hex-hit");
    if (cell && (event.key === "Enter" || event.key === " ")) {
      event.preventDefault();
      populate(cell, records);
      return;
    }
    const directions = {ArrowLeft:[45,0], ArrowRight:[-45,0], ArrowUp:[0,45], ArrowDown:[0,-45]};
    const position = center();
    const direction = directions[event.key];
    if (direction) {
      zoom(1, position, {x:position.x+direction[0], y:position.y+direction[1]});
    } else if (event.key === "+" || event.key === "=") {
      zoom(1.5, position);
    } else if (event.key === "-") {
      zoom(1/1.5, position);
    } else if (event.key === "Home" || event.key === "0") {
      view = {...home};
      draw();
    } else {
      return;
    }
    event.preventDefault();
  });
}

function describeCoverage(hexes, names) {
  const counts = new Map();
  const ids = new Set();
  for (const cell of Object.values(hexes)) {
    for (const club of cell.clubs) {
      if (!club.state || ids.has(club.club_id)) continue;
      ids.add(club.club_id);
      counts.set(club.state, (counts.get(club.state) ?? 0) + 1);
    }
  }
  const [leader, ...runners] = [...counts]
    .sort(([a, n], [b, m]) => m-n || a.localeCompare(b, "en-US")).slice(0, 3);
  if (leader) {
    const [state, total] = leader;
    const note = document.querySelector("#lead-note");
    const lead = element("span", `${names[state] ?? state} leads the directory with `, note);
    lead.className = "lead";
    element("strong", total.toLocaleString("en-US"), lead);
    lead.append(runners.length ? " listed clubs, followed by " : " listed clubs.");
    for (const [i, [key, count]] of runners.entries()) {
      if (i) note.append(" and ");
      note.append(`${names[key] ?? key} (`);
      element("strong", count.toLocaleString("en-US"), note);
      note.append(")");
    }
    if (runners.length) note.append(".");
    note.hidden = false;
  }
  const stateCount = counts.size - Number(counts.has("DC"));
  const total = [...counts.values()].reduce((sum, count) => sum + count, 0);
  const coverage = `${stateCount === 50 ? "all " : ""}${stateCount} states${counts.has("DC") ? " and D.C." : "."}`;
  document.querySelector("#subtitle").textContent =
    `${total.toLocaleString("en-US")} mapped club locations across ${coverage}`;
}

async function load(path, kind) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Could not read ${path}`);
  return response[kind]();
}

async function initialize() {
  const [art, data] = await Promise.all([
    load("national-r3.svg", "text"),
    load("h3-r3-panel.json", "json"),
  ]);
  const svg = new DOMParser().parseFromString(art, "image/svg+xml").documentElement;
  const legend = document.querySelector("#legend");
  element("span", "Listed clubs per hex", legend);
  const bins = [...JSON.parse(svg.dataset.legend), ["No mapped listings", svg.dataset.land]];
  for (const [name, color] of bins) {
    const item = element("span", "", legend);
    item.className = "legend-item";
    const swatch = element("span", "", item);
    swatch.className = "swatch";
    swatch.style.setProperty("--color", color);
    item.append(name);
  }
  describeCoverage(data.hexes, JSON.parse(svg.dataset.stateNames));
  for (const cell of svg.querySelectorAll(".hex-hit")) {
    cell.setAttribute("tabindex", "0");
    cell.setAttribute("role", "button");
  }
  close.addEventListener("click", dismiss);
  document.addEventListener("keydown", event => { if (event.key === "Escape") dismiss(); });
  reveal(svg);
  map.replaceChildren(svg);
  navigation(svg, data.hexes);
  map.setAttribute("aria-busy", "false");
}

initialize().catch(error => {
  map.setAttribute("aria-busy", "false");
  map.textContent = error.message;
});
