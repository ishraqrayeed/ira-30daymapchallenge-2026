// Mode flags indicate involvement. Events flagged for both modes appear once
// in each applicable filtered view and once in the combined view.
const modeSelect = document.getElementById('mode-filter');
const scopeLabel = document.getElementById('map-scope');
const originalLayers = deckInstance.props.layers;
const allCrashPoints = originalLayers.find(layer => layer.id === 'crash-points');

modeSelect.addEventListener('change', () => {
  const mode = modeSelect.value;
  const filtered = allCrashPoints.props.data.filter(record =>
    mode === 'all' || (mode === 'pedestrian' && record.pedestrian) ||
    (mode === 'bicycle' && record.bicycle)
  );
  deckInstance.setProps({
    layers: originalLayers.map(layer => layer.id === 'crash-points'
      ? allCrashPoints.clone({data: filtered}) : layer)
  });
  scopeLabel.textContent = 'Crashes resulting in fatal or serious injury · ' + scopeLabel.dataset.period;
});
