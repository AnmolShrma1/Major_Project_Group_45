// AGIMS Frontend Application
// WebSocket and UI management

const CONFIG = {
    WS_URL: 'ws://localhost:8000/ws/live',
    API_BASE: 'http://localhost:8000',
    MAX_FEED_ITEMS: 20,
    MAX_CHART_POINTS: 50,
    NUM_PRNS: 8
};

// Global state
let ws = null;
let charts = {};
let selectedPRNs = new Set([1, 2, 3]);
let chartData = {
    risk: {},
    cn0: {},
    do: {},
    tcd: {}
};
let detectionCount = 0;
let lastAlert = 0;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeUI();
    initializeCharts();
    connectWebSocket();
    fetchStatus();
});

// ============ WebSocket Management ============

function connectWebSocket() {
    updateConnectionStatus('connecting');
    
    ws = new WebSocket(CONFIG.WS_URL);
    
    ws.onopen = () => {
        console.log('✓ WebSocket connected');
        updateConnectionStatus('connected');
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'status') {
            updateSystemStatus(data.data);
        } else {
            handleLiveData(data);
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateConnectionStatus('error');
    };
    
    ws.onclose = () => {
        console.log('✗ WebSocket disconnected');
        updateConnectionStatus('disconnected');
        
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
            if (document.visibilityState === 'visible') {
                connectWebSocket();
            }
        }, 3000);
    };
}

function updateConnectionStatus(status) {
    const indicator = document.getElementById('connectionStatus');
    const text = document.getElementById('connectionText');
    
    indicator.className = 'status-indicator';
    
    switch(status) {
        case 'connected':
            indicator.classList.add('connected');
            text.textContent = 'Connected';
            break;
        case 'connecting':
            text.textContent = 'Connecting...';
            break;
        case 'disconnected':
            text.textContent = 'Disconnected';
            break;
        case 'error':
            text.textContent = 'Connection Error';
            break;
    }
}

// ============ UI Initialization ============

function initializeUI() {
    // PRN selector checkboxes
    const prnSelector = document.getElementById('prnSelector');
    for (let i = 1; i <= CONFIG.NUM_PRNS; i++) {
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `prn${i}`;
        checkbox.className = 'prn-checkbox';
        checkbox.value = i;
        checkbox.checked = selectedPRNs.has(i);
        checkbox.addEventListener('change', handlePRNSelection);
        
        const label = document.createElement('label');
        label.htmlFor = `prn${i}`;
        label.className = 'prn-label';
        label.textContent = `PRN ${i}`;
        
        prnSelector.appendChild(checkbox);
        prnSelector.appendChild(label);
    }
    
    // PRN monitor cards
    const prnMonitors = document.getElementById('prnMonitors');
    for (let i = 1; i <= CONFIG.NUM_PRNS; i++) {
        const monitor = createPRNMonitor(i);
        prnMonitors.appendChild(monitor);
    }
    
    // Button event listeners
    document.getElementById('startBtn').addEventListener('click', startSimulation);
    document.getElementById('stopBtn').addEventListener('click', stopSimulation);
    document.getElementById('demoBtn').addEventListener('click', startDemoMode);
    document.getElementById('attackStartBtn').addEventListener('click', startAttack);
    document.getElementById('attackStopBtn').addEventListener('click', stopAttack);
    
    // Intensity slider
    const slider = document.getElementById('attackIntensity');
    slider.addEventListener('input', (e) => {
        document.getElementById('intensityValue').textContent = e.target.value;
    });
}

function createPRNMonitor(prn) {
    const div = document.createElement('div');
    div.className = 'prn-monitor normal';
    div.id = `monitor-prn${prn}`;
    div.innerHTML = `
        <div class="prn-monitor-header">
            <span class="prn-id">PRN ${prn}</span>
            <span class="risk-badge low">LOW</span>
        </div>
        <div class="prn-risk-score">0.00</div>
        <div class="prn-status" style="font-size: 0.75rem; color: var(--text-secondary); text-align: center;">
            Normal
        </div>
    `;
    return div;
}

// ============ Chart Initialization ============

function initializeCharts() {
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: true,
        animation: {
            duration: 0
        },
        scales: {
            x: {
                display: true,
                grid: { color: 'rgba(255,255,255,0.1)' },
                ticks: { color: '#a0a8c5' }
            },
            y: {
                display: true,
                grid: { color: 'rgba(255,255,255,0.1)' },
                ticks: { color: '#a0a8c5' }
            }
        },
        plugins: {
            legend: {
                display: true,
                labels: { color: '#a0a8c5' }
            }
        }
    };
    
    // Risk Score Chart
    charts.risk = new Chart(document.getElementById('riskChart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: {
            ...chartOptions,
            scales: {
                ...chartOptions.scales,
                y: { ...chartOptions.scales.y, min: 0, max: 1 }
            }
        }
    });
    
    // CN0 Chart
    charts.cn0 = new Chart(document.getElementById('cn0Chart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: chartOptions
    });
    
    // Doppler Chart
    charts.do = new Chart(document.getElementById('doChart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: chartOptions
    });
    
    // TCD Chart
    charts.tcd = new Chart(document.getElementById('tcdChart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: []
        },
        options: chartOptions
    });
}

// ============ Data Handling ============

function handleLiveData(data) {
    const { prn, timestamp, risk_score, attack_detected, raw_features, current_attack } = data;
    
    // Update PRN monitor
    updatePRNMonitor(prn, risk_score, attack_detected);
    
    // Update charts if PRN is selected
    if (selectedPRNs.has(prn)) {
        updateCharts(prn, timestamp, risk_score, raw_features);
    }
    
    // Update live feed
    addFeedItem(prn, risk_score, attack_detected, current_attack);
    
    // Show alert if attack detected
    if (attack_detected && Date.now() - lastAlert > 5000) {
        showAlert(prn, risk_score);
        lastAlert = Date.now();
        detectionCount++;
        document.getElementById('detectionCount').textContent = detectionCount;
    }
}

function updatePRNMonitor(prn, riskScore, attackDetected) {
    const monitor = document.getElementById(`monitor-prn${prn}`);
    if (!monitor) return;
    
    const scoreDisplay = monitor.querySelector('.prn-risk-score');
    const badge = monitor.querySelector('.risk-badge');
    const status = monitor.querySelector('.prn-status');
    
    scoreDisplay.textContent = riskScore.toFixed(2);
    
    // Update class and badge
    monitor.className = 'prn-monitor';
    if (riskScore >= 0.7) {
        monitor.classList.add('attack');
        badge.className = 'risk-badge high';
        badge.textContent = 'HIGH';
        status.textContent = 'Attack Detected!';
    } else if (riskScore >= 0.4) {
        monitor.classList.add('suspicious');
        badge.className = 'risk-badge medium';
        badge.textContent = 'MEDIUM';
        status.textContent = 'Suspicious';
    } else {
        monitor.classList.add('normal');
        badge.className = 'risk-badge low';
        badge.textContent = 'LOW';
        status.textContent = 'Normal';
    }
}

function updateCharts(prn, timestamp, riskScore, features) {
    const timeLabel = timestamp.toFixed(1);
    
    // Initialize data arrays if needed
    if (!chartData.risk[prn]) {
        const color = getColorForPRN(prn);
        
        chartData.risk[prn] = [];
        chartData.cn0[prn] = [];
        chartData.do[prn] = [];
        chartData.tcd[prn] = [];
        
        // Add dataset to each chart
        charts.risk.data.datasets.push({
            label: `PRN ${prn}`,
            data: chartData.risk[prn],
            borderColor: color,
            backgroundColor: color + '20',
            borderWidth: 2,
            tension: 0.4
        });
        
        charts.cn0.data.datasets.push({
            label: `PRN ${prn}`,
            data: chartData.cn0[prn],
            borderColor: color,
            backgroundColor: color + '20',
            borderWidth: 2,
            tension: 0.4
        });
        
        charts.do.data.datasets.push({
            label: `PRN ${prn}`,
            data: chartData.do[prn],
            borderColor: color,
            backgroundColor: color + '20',
            borderWidth: 2,
            tension: 0.4
        });
        
        charts.tcd.data.datasets.push({
            label: `PRN ${prn}`,
            data: chartData.tcd[prn],
            borderColor: color,
            backgroundColor: color + '20',
            borderWidth: 2,
            tension: 0.4
        });
    }
    
    // Add data points
    chartData.risk[prn].push({ x: timeLabel, y: riskScore });
    chartData.cn0[prn].push({ x: timeLabel, y: features.CN0 });
    chartData.do[prn].push({ x: timeLabel, y: features.DO });
    chartData.tcd[prn].push({ x: timeLabel, y: features.TCD });
    
    // Limit data points
    if (chartData.risk[prn].length > CONFIG.MAX_CHART_POINTS) {
        chartData.risk[prn].shift();
        chartData.cn0[prn].shift();
        chartData.do[prn].shift();
        chartData.tcd[prn].shift();
    }
    
    // Update chart labels
    if (!charts.risk.data.labels.includes(timeLabel)) {
        charts.risk.data.labels.push(timeLabel);
        charts.cn0.data.labels.push(timeLabel);
        charts.do.data.labels.push(timeLabel);
        charts.tcd.data.labels.push(timeLabel);
        
        if (charts.risk.data.labels.length > CONFIG.MAX_CHART_POINTS) {
            charts.risk.data.labels.shift();
            charts.cn0.data.labels.shift();
            charts.do.data.labels.shift();
            charts.tcd.data.labels.shift();
        }
    }
    
    // Update charts
    charts.risk.update('none');
    charts.cn0.update('none');
    charts.do.update('none');
    charts.tcd.update('none');
}

function addFeedItem(prn, riskScore, attackDetected, currentAttack) {
    const feed = document.getElementById('liveFeed');
    const item = document.createElement('div');
    item.className = attackDetected ? 'feed-item detection' : 'feed-item';
    
    const now = new Date();
    const timeStr = now.toLocaleTimeString();
    
    const message = attackDetected 
        ? `⚠️ ATTACK DETECTED on PRN ${prn} (Risk: ${(riskScore * 100).toFixed(0)}%)`
        : `✓ PRN ${prn} normal (Risk: ${(riskScore * 100).toFixed(0)}%)`;
    
    item.innerHTML = `
        <div class="feed-time">${timeStr}</div>
        <div class="feed-message">${message}</div>
        ${currentAttack !== 'none' ? `<div style="font-size: 0.75rem; color: var(--warning); margin-top: 0.25rem;">Active: ${currentAttack}</div>` : ''}
    `;
    
    feed.insertBefore(item, feed.firstChild);
    
    // Limit feed items
    while (feed.children.length > CONFIG.MAX_FEED_ITEMS) {
        feed.removeChild(feed.lastChild);
    }
}

// ============ API Calls ============

async function startSimulation() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ demo_mode: false })
        });
        
        if (response.ok) {
            updateButtonStates(true);
            clearCharts();
            detectionCount = 0;
            document.getElementById('detectionCount').textContent = '0';
        }
    } catch (error) {
        console.error('Error starting simulation:', error);
    }
}

async function stopSimulation() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/stop`, {
            method: 'POST'
        });
        
        if (response.ok) {
            updateButtonStates(false);
        }
    } catch (error) {
        console.error('Error stopping simulation:', error);
    }
}

async function startDemoMode() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ demo_mode: true })
        });
        
        if (response.ok) {
            updateButtonStates(true);
            clearCharts();
            detectionCount = 0;
            document.getElementById('detectionCount').textContent = '0';
            addFeedItem(0, 0, false, 'Demo Mode Started');
        }
    } catch (error) {
        console.error('Error starting demo mode:', error);
    }
}

async function startAttack() {
    const attackType = document.getElementById('attackType').value;
    const intensity = parseFloat(document.getElementById('attackIntensity').value);
    const prns = Array.from(selectedPRNs);
    
    try {
        const response = await fetch(`${CONFIG.API_BASE}/attack/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                attack_type: attackType,
                prns: prns.length > 0 ? prns : null,
                intensity: intensity
            })
        });
        
        if (response.ok) {
            document.getElementById('attackStopBtn').disabled = false;
        }
    } catch (error) {
        console.error('Error starting attack:', error);
    }
}

async function stopAttack() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/attack/stop`, {
            method: 'POST'
        });
        
        if (response.ok) {
            document.getElementById('attackStopBtn').disabled = true;
        }
    } catch (error) {
        console.error('Error stopping attack:', error);
    }
}

async function fetchStatus() {
    try {
        const response = await fetch(`${CONFIG.API_BASE}/status`);
        const data = await response.json();
        updateSystemStatus(data);
    } catch (error) {
        console.error('Error fetching status:', error);
    }
}

// ============ UI Updates ============

function updateSystemStatus(status) {
    document.getElementById('simStatus').textContent = 
        status.simulation_running ? 'Running' : 'Stopped';
    
    document.getElementById('modelStatus').textContent = 
        status.model_loaded ? 'Loaded (Stub)' : 'Not Loaded';
    
    document.getElementById('attackStatus').textContent = 
        status.attack_active ? status.attack_type.toUpperCase() : 'None';
    
    updateButtonStates(status.simulation_running);
}

function updateButtonStates(running) {
    document.getElementById('startBtn').disabled = running;
    document.getElementById('stopBtn').disabled = !running;
    document.getElementById('demoBtn').disabled = running;
    document.getElementById('attackStartBtn').disabled = !running;
}

function handlePRNSelection(e) {
    const prn = parseInt(e.target.value);
    if (e.target.checked) {
        selectedPRNs.add(prn);
    } else {
        selectedPRNs.delete(prn);
    }
}

function clearCharts() {
    chartData.risk = {};
    chartData.cn0 = {};
    chartData.do = {};
    chartData.tcd = {};
    
    charts.risk.data.labels = [];
    charts.risk.data.datasets = [];
    charts.cn0.data.labels = [];
    charts.cn0.data.datasets = [];
    charts.do.data.labels = [];
    charts.do.data.datasets = [];
    charts.tcd.data.labels = [];
    charts.tcd.data.datasets = [];
    
    charts.risk.update();
    charts.cn0.update();
    charts.do.update();
    charts.tcd.update();
}

function showAlert(prn, riskScore) {
    const modal = document.getElementById('alertModal');
    const message = document.getElementById('alertMessage');
    
    message.textContent = `High-risk activity detected on PRN ${prn} with confidence ${(riskScore * 100).toFixed(0)}%. Review system immediately.`;
    
    modal.classList.add('show');
}

function closeAlert() {
    const modal = document.getElementById('alertModal');
    modal.classList.remove('show');
}

// ============ Utility Functions ============

function getColorForPRN(prn) {
    const colors = [
        '#00d4ff', '#ff6b9d', '#00ff88', '#ffaa00',
        '#7b2cbf', '#ff3366', '#00ffff', '#ff9500'
    ];
    return colors[(prn - 1) % colors.length];
}

// Periodic status updates
setInterval(fetchStatus, 5000);