/**
 * AGIMS v2.0 — Frontend
 *
 * PRN list is fetched dynamically from the backend on connection.
 * No hardcoded PRN IDs — works with any dataset.
 */

const WS_URL  = 'ws://localhost:8000/ws/live';
const API_URL = 'http://localhost:8000';
const MAX_PTS = 80;

// ── Palette (cycles for many PRNs) ───────────────────────────────────────────
const PALETTE = [
  '#00e5ff','#00ff9d','#ffc400','#ff2d55','#b24bff',
  '#ff9f40','#4bc0c0','#9966ff','#ff6384','#36a2eb',
  '#ffcd56','#4bc0c0','#c9cbcf','#7dff91','#f77fbe',
  '#a1c4fd','#fd9853','#b8f7d4'
];

// ── State ─────────────────────────────────────────────────────────────────────
let ws           = null;
let simRunning   = false;
let detCount     = 0;
let lastAlert    = '';
let PRN_IDS      = [];          // populated from backend init message
let selectedPRNs = new Set();
let prnColorMap  = {};          // prn → color string
let prnIndexMap  = {};          // prn → dataset index in charts
const chartRefs  = {};

const $ = id => document.getElementById(id);

// ── Clock ─────────────────────────────────────────────────────────────────────
setInterval(() => { $('clock').textContent = new Date().toLocaleTimeString('en-GB'); }, 1000);

// ── Dynamic PRN setup (called once we get backend init) ───────────────────────
function initPRNs(prnIds) {
  PRN_IDS = prnIds;
  prnIds.forEach((prn, i) => {
    prnColorMap[prn]  = PALETTE[i % PALETTE.length];
    prnIndexMap[prn]  = i;
    selectedPRNs.add(prn);
  });
  buildPRNSelector();
  buildPRNMonitors();
  buildCharts();
}

// ── PRN selector ──────────────────────────────────────────────────────────────
function buildPRNSelector() {
  const grid = $('prnSelector');
  grid.innerHTML = '';
  PRN_IDS.forEach(prn => {
    const id  = `pcb-${prn}`;
    const cb  = document.createElement('input');
    cb.type = 'checkbox'; cb.id = id; cb.className = 'prn-cb'; cb.checked = true;
    cb.addEventListener('change', () => cb.checked ? selectedPRNs.add(prn) : selectedPRNs.delete(prn));
    const lbl = document.createElement('label');
    lbl.htmlFor = id; lbl.className = 'prn-lbl'; lbl.textContent = `${prn}`;
    grid.append(cb, lbl);
  });

  $('selAllBtn').onclick = () => PRN_IDS.forEach(prn => {
    selectedPRNs.add(prn);
    const cb = $(`pcb-${prn}`); if (cb) cb.checked = true;
  });
  $('selNoneBtn').onclick = () => PRN_IDS.forEach(prn => {
    selectedPRNs.delete(prn);
    const cb = $(`pcb-${prn}`); if (cb) cb.checked = false;
  });

  $('prnCount').textContent = `${PRN_IDS.length}`;
}

// ── PRN monitor cards ─────────────────────────────────────────────────────────
function buildPRNMonitors() {
  const grid = $('prnMonitors');
  grid.innerHTML = '';
  PRN_IDS.forEach(prn => {
    const col = prnColorMap[prn];
    grid.insertAdjacentHTML('beforeend', `
      <div class="prn-mon" id="mon-${prn}">
        <div class="mon-hdr">
          <span class="mon-id mono" style="color:${col}">PRN ${prn}</span>
          <span class="badge b-low" id="badge-${prn}">LOW</span>
        </div>
        <div class="mon-pct" id="pct-${prn}" style="color:var(--green)">0%</div>
        <div class="mon-lvl" id="mlvl-${prn}">—</div>
      </div>`);
  });
}

// ── Charts ────────────────────────────────────────────────────────────────────
function buildCharts() {
  const mkDatasets = (hidden_after = 5) => PRN_IDS.map((prn, i) => ({
    label: `PRN ${prn}`,
    data: [],
    borderColor: prnColorMap[prn],
    backgroundColor: prnColorMap[prn] + '14',
    borderWidth: 1.5,
    pointRadius: 0,
    tension: 0.35,
    hidden: i >= hidden_after,
  }));

  const baseOpts = {
    responsive: true, maintainAspectRatio: true,
    animation: { duration: 0 },
    plugins: { legend: { display: false } },
    scales: {
      x: { display: false },
      y: { grid: { color: '#172030' }, ticks: { color: '#4a5578', font: { family: 'Share Tech Mono', size: 10 } } }
    }
  };

  chartRefs.risk = new Chart($('riskChart').getContext('2d'), {
    type: 'line',
    data: { labels: [], datasets: mkDatasets(6) },
    options: {
      ...baseOpts,
      plugins: { legend: { display: true, labels: { color: '#5a6480', font: { family: 'Share Tech Mono', size: 10 }, boxWidth: 12, padding: 8 } } },
      scales: { ...baseOpts.scales, y: { ...baseOpts.scales.y, min: 0, max: 1 } }
    }
  });
  chartRefs.cn0 = new Chart($('cn0Chart').getContext('2d'), { type:'line', data:{ labels:[], datasets: mkDatasets(4) }, options: baseOpts });
  chartRefs.do  = new Chart($('doChart').getContext('2d'),  { type:'line', data:{ labels:[], datasets: mkDatasets(4) }, options: baseOpts });
  chartRefs.tcd = new Chart($('tcdChart').getContext('2d'), { type:'line', data:{ labels:[], datasets: mkDatasets(4) }, options: baseOpts });
}

// ── Push data into charts ─────────────────────────────────────────────────────
let lastChartUpdate = 0;
function pushChart(prn, ts, risk, cn0, doVal, tcd) {
  const idx   = prnIndexMap[prn];
  const label = ts.toFixed(1);
  if (idx === undefined) return;

  const push = (chart, val) => {
    const ds = chart.data.datasets[idx];
    if (!ds) return;
    ds.data.push(val);
    if (ds.data.length > MAX_PTS) ds.data.shift();
  };

  push(chartRefs.risk, risk);
  push(chartRefs.cn0,  cn0);
  push(chartRefs.do,   doVal);
  push(chartRefs.tcd,  tcd);

  // Shared labels on risk chart (only update once per sweep)
  if (prn === PRN_IDS[0]) {
    const lbs = chartRefs.risk.data.labels;
    lbs.push(label);
    if (lbs.length > MAX_PTS) lbs.shift();
    ['cn0','do','tcd'].forEach(k => {
      const c = chartRefs[k].data.labels;
      c.push(label); if (c.length > MAX_PTS) c.shift();
    });
  }

  // Throttle: batch chart redraws to once per 300ms
  const now = Date.now();
  if (now - lastChartUpdate > 300) {
    lastChartUpdate = now;
    Object.values(chartRefs).forEach(c => c.update('none'));
  }
}

// ── PRN monitor update ────────────────────────────────────────────────────────
function updateMonitor(prn, risk, threat) {
  const level = (threat && threat.threat_level) || 'LOW';
  const pct   = Math.round(risk * 100);
  const mon   = $(`mon-${prn}`); if (!mon) return;

  const classMap = { LOW:'normal', MEDIUM:'medium', HIGH:'high', CRITICAL:'critical' };
  const badgeCls = { LOW:'b-low', MEDIUM:'b-medium', HIGH:'b-high', CRITICAL:'b-critical' };
  const colors   = { LOW:'var(--green)', MEDIUM:'var(--amber)', HIGH:'var(--red)', CRITICAL:'var(--red)' };

  mon.className = `prn-mon ${classMap[level] || 'normal'}`;
  const badge   = $(`badge-${prn}`);
  badge.className     = `badge ${badgeCls[level] || 'b-low'}`;
  badge.textContent   = level;
  const pctEl = $(`pct-${prn}`);
  pctEl.style.color   = colors[level];
  pctEl.textContent   = `${pct}%`;
  $(`mlvl-${prn}`).textContent = threat ? threat.mitre_tactic.substring(0,22) + '…' : '—';
}

// ── Threat banner ─────────────────────────────────────────────────────────────
function updateBanner(threat, decision) {
  const banner = $('threatBanner');
  if (!threat || !decision || threat.threat_level === 'LOW') {
    banner.classList.add('hidden'); return;
  }
  banner.classList.remove('hidden');
  banner.className = `threat-banner${threat.threat_level === 'CRITICAL' ? ' critical' : ''}`;
  $('bannerLevel').textContent    = `${threat.threat_level} THREAT`;
  $('bannerDecision').textContent = decision.final_decision;
  $('bannerAction').textContent   = decision.recommended_action;
}
window.closeBanner = () => $('threatBanner').classList.add('hidden');

// ── Data source badge ─────────────────────────────────────────────────────────
function setSource(mode) {
  const b = $('dataSourceBadge');
  const t = $('dataSourceText');
  b.className = `ds-badge ${mode}`;
  t.textContent = { real:'● REAL GNSS', dataset:'◆ DATASET', simulated:'○ SIMULATED' }[mode] || mode.toUpperCase();
  $('sourceMode').textContent = mode.toUpperCase();
}

// ── Alert overlay ─────────────────────────────────────────────────────────────
function showAlert(threat, decision) {
  const level = threat.threat_level;
  if (level === lastAlert && level !== 'CRITICAL') return;
  lastAlert = level;
  $('alertLevel').textContent = level;
  $('alertLevel').style.color = level === 'CRITICAL' ? 'var(--red)' : 'var(--amber)';
  $('alertMsg').textContent   = decision.final_decision;
  $('alertAction').textContent= decision.recommended_action;
  $('alertOverlay').classList.remove('hidden');
}
window.closeAlert = () => { $('alertOverlay').classList.add('hidden'); lastAlert = ''; };

// ── Feed ──────────────────────────────────────────────────────────────────────
function feed(msg, type = 'info') {
  const el = document.createElement('div');
  el.className = `feed-item ${type}`;
  el.innerHTML = `<div class="feed-time mono">${new Date().toLocaleTimeString('en-GB')}</div>
                  <div class="feed-msg">${msg}</div>`;
  const f = $('liveFeed');
  f.prepend(el);
  while (f.children.length > 80) f.lastChild.remove();
}

// ── Simulation status ─────────────────────────────────────────────────────────
function setSimStatus(running) {
  simRunning = running;
  $('startBtn').disabled      = running;
  $('stopBtn').disabled       = !running;
  $('attackStartBtn').disabled= !running;
  $('simStatus').textContent  = running ? 'RUNNING' : 'STOPPED';
  $('simStatus').className    = running ? 'tag tag-on' : 'tag tag-off';
  if (!running) $('threatBanner').classList.add('hidden');
}

// ── WebSocket ─────────────────────────────────────────────────────────────────
function connect() {
  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    $('wsDot').className = 'ws-dot on';
    $('wsText').textContent = 'ONLINE';
    feed('Connected to AGIMS backend', 'info');
  };

  ws.onclose = () => {
    $('wsDot').className = 'ws-dot';
    $('wsText').textContent = 'OFFLINE';
    feed('Disconnected — retrying in 3s…', 'warn');
    setTimeout(connect, 3000);
  };

  ws.onerror = () => feed('WebSocket error', 'warn');

  ws.onmessage = evt => {
    let msg;
    try { msg = JSON.parse(evt.data); } catch { return; }

    // ── Init / status ─────────────────────────────────────────
    if (msg.type === 'init' || msg.type === 'status') {
      const d = msg.data;
      // Build PRN UI from server-provided list (only once)
      if (d.prn_ids && PRN_IDS.length === 0) {
        initPRNs(d.prn_ids);
        feed(`Backend ready — ${d.prn_ids.length} PRNs, source: ${d.data_source}`, 'info');
      }
      setSimStatus(d.simulation_running);
      $('modelStatus').textContent  = d.model_loaded ? (d.model_type || 'LOADED') : 'STUB';
      $('attackStatus').textContent = d.attack_active ? (d.attack_type || '').toUpperCase() : 'NONE';
      if (d.data_source) setSource(d.data_source);
      return;
    }

    if (msg.type === 'ping') return;

    // ── Live data point ───────────────────────────────────────
    const { prn, timestamp, risk_score, attack_detected,
            raw_features: feat, current_attack, data_source,
            threat, decision } = msg;

    if (!selectedPRNs.has(prn) || PRN_IDS.length === 0) return;

    pushChart(prn, timestamp, risk_score, feat.CN0, feat.DO, feat.TCD);
    updateMonitor(prn, risk_score, threat);

    if (threat && (threat.threat_level === 'HIGH' || threat.threat_level === 'CRITICAL')) {
      updateBanner(threat, decision);
    }

    if (attack_detected) {
      detCount++;
      $('detCount').textContent = detCount;
      feed(`PRN ${prn} | ${threat.threat_level} | ${Math.round(risk_score*100)}% | ${current_attack}`,
           threat.threat_level === 'CRITICAL' ? 'critical' : 'warn');
    }

    if (decision && decision.alert_flag) showAlert(threat, decision);
    if (data_source) setSource(data_source);
  };
}

// ── Controls ──────────────────────────────────────────────────────────────────
$('startBtn').addEventListener('click', async () => {
  const r = await fetch(`${API_URL}/start`, { method:'POST',
    headers:{'Content-Type':'application/json'}, body: JSON.stringify({demo_mode:false}) });
  if (r.ok) { setSimStatus(true); feed('Simulation started', 'info'); }
  else       { const e = await r.json(); feed(`Start failed: ${e.detail}`, 'warn'); }
});

$('stopBtn').addEventListener('click', async () => {
  await fetch(`${API_URL}/stop`, { method:'POST' });
  setSimStatus(false); feed('Simulation stopped', 'info');
});

$('demoBtn').addEventListener('click', async () => {
  if (simRunning) await fetch(`${API_URL}/stop`, { method:'POST' });
  const r = await fetch(`${API_URL}/start`, { method:'POST',
    headers:{'Content-Type':'application/json'}, body: JSON.stringify({demo_mode:true}) });
  if (r.ok) { setSimStatus(true); feed('Demo mode started — cycling attack patterns', 'info'); }
});

$('attackIntensity').addEventListener('input', e => {
  $('intensityVal').textContent = parseFloat(e.target.value).toFixed(1);
});

$('attackStartBtn').addEventListener('click', async () => {
  const type      = $('attackType').value;
  if (type === 'none') { feed('Select an attack type first', 'warn'); return; }
  const prns      = [...selectedPRNs];
  const intensity = parseFloat($('attackIntensity').value);
  const r = await fetch(`${API_URL}/attack/start`, { method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify({attack_type: type, prns, intensity}) });
  if (r.ok) {
    $('attackStopBtn').disabled = false;
    $('attackStatus').textContent = type.toUpperCase();
    $('attackStatus').className = 'tag tag-atk';
    feed(`Attack STARTED: ${type} | PRNs [${prns.join(',')}] | intensity ${intensity}`, 'warn');
  } else {
    const e = await r.json(); feed(`Attack failed: ${e.detail}`, 'warn');
  }
});

$('attackStopBtn').addEventListener('click', async () => {
  await fetch(`${API_URL}/attack/stop`, { method:'POST' });
  $('attackStopBtn').disabled = true;
  $('attackStatus').textContent = 'NONE';
  $('attackStatus').className = 'tag';
  $('threatBanner').classList.add('hidden');
  lastAlert = '';
  feed('Attack CLEARED', 'info');
});

// ── Boot ──────────────────────────────────────────────────────────────────────
connect();
feed('AGIMS v2.0 initialised', 'info');

window.closeAlert = function () {
    const overlay = document.getElementById('alertOverlay');

    if (overlay) {
        overlay.classList.add('hidden');
    }

    console.log("Alert acknowledged");
};
