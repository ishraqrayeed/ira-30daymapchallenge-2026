// Run with: node tests/test_map_controls.js
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const script = fs.readFileSync(path.join(__dirname, '../templates/map-controls.js'), 'utf8');
const records = [
  {id: 'pedestrian', pedestrian: true, bicycle: false},
  {id: 'bicycle', pedestrian: false, bicycle: true},
  {id: 'both', pedestrian: true, bicycle: true}
];
let listener;
let updated;
const select = {value: 'all', addEventListener: (event, callback) => {listener = callback;}};
const scope = {textContent: '', dataset: {period: '2021–2025'}};
const layer = {
  id: 'crash-points', props: {data: records},
  clone: props => ({id: 'crash-points', props})
};
const context = {
  document: {getElementById: id => id === 'mode-filter' ? select : scope},
  deckInstance: {props: {layers: [layer]}, setProps: props => {updated = props;}}
};
vm.runInNewContext(script, context);
select.value = 'pedestrian'; listener();
assert.deepEqual(Array.from(updated.layers[0].props.data, r => r.id), ['pedestrian', 'both']);
assert.equal(scope.textContent, 'Crashes resulting in fatal or serious injury · 2021–2025');
select.value = 'bicycle'; listener();
assert.deepEqual(Array.from(updated.layers[0].props.data, r => r.id), ['bicycle', 'both']);
assert.match(scope.textContent, /2021–2025$/);
select.value = 'all'; listener();
assert.equal(updated.layers[0].props.data.length, 3);
assert.equal(records.length, 3, 'Filtering must not mutate the original points');

// Check the actual story export uses an embedded walking-person icon and the
// agreed fatal-crash-involvement scope, without retaining the old map artifact.
const html = fs.readFileSync(path.join(__dirname, '../maps/day01-points/map.html'), 'utf8');
const json = html.match(/const jsonInput = (\{[\s\S]*?\n\});/);
assert.ok(json, 'Export must include deck.gl input');
const config = JSON.parse(json[1]);
const exported = config.layers.find(l => l.id === 'crash-points');
assert.equal(exported['@@type'], 'IconLayer');
assert.equal(exported.sizeUnits, 'pixels');
assert.equal(exported.getIcon, '@@=icon_name');
assert.equal(exported.loadOptions.image.type, 'image');
assert.ok(exported.iconAtlas.startsWith('data:image/svg+xml;base64,'));
assert.ok(exported.data.length > 0);
for (const point of exported.data) {
  assert.equal(point.icon_name, 'pedestrian');
  assert.equal(point.severity, 'Fatal');
  assert.equal(point.pedestrian, true);
}
assert.ok(html.includes('One symbol = one fatal crash'));
assert.ok(!html.includes('id="mode-filter"'));
console.log('Passed: shared filter logic and current fatal-pedestrian-involvement icon export.');
