// static/js/dashboard.js
console.log('FatigueAI Dashboard loaded');

// ─── Auth-aware fetch wrapper ────────────────────────────────────────────────
// Wraps native fetch to detect 401 auth errors and redirect to /login.
// Prevents silent JSON parse failures when the session expires mid-use.
async function authFetch(url, options = {}) {
  const resp = await fetch(url, options);
  if (resp.status === 401) {
    console.warn('[AUTH] Session expired. Redirecting to /login...');
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  return resp;
}

// ─── Toast Notification System ──────────────────────────────────────────────
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  let icon = 'ℹ️';
  if (type === 'success') icon = '✅';
  if (type === 'error') icon = '❌';
  if (type === 'warning') icon = '⚠️';

  toast.innerHTML = `
    <span class="toast-icon">${icon}</span>
    <span class="toast-content">${message}</span>
    <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
  `;

  container.appendChild(toast);
  
  setTimeout(() => toast.classList.add('show'), 50);

  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 400);
  }, 4000);
}
window.showToast = showToast;
// ──────────────────────────────────────────────────────────────────────────────


const MAX_POINTS = 30;
let wpmData         = [];
let errorData       = [];
let labelData       = [];

// Globally accessible Chart instances for resetting
let wpmChart, errChart, fatigueHistoryChart;

// ─── Feature 2: Fatigue history data ────────────────────────────────────────
// fatigueScoreData  → numeric score (0-100) per poll point
// fatigueLabelData  → shared time labels with the ring gauge poll (every 2s)
// fatigueBgColors   → per-point background colour (green/yellow/red)
// fatigueBorderColors → per-point border colour
let fatigueScoreData   = [];
let fatigueLabelData   = [];
let fatigueBgColors    = [];
let fatigueBorderColors= [];
let blinkData          = [];
let yawnData           = [];
let confidenceData     = [];
let productivityData   = [];
let concentrationData  = [];
let currentTab         = 'fatigue';

// Cache values for optimization
let lastLogRowId       = null;
let lastCharsCount     = -1;
let lastWpmValue       = -1;
let lastErrorsCount    = -1;

// ──────────────────────────────────────────────────────────────────────────────

// ─── Feature 1: Break Alert state ─────────────────────────────────────────────
// alertShown   → true while the overlay is visible (prevents duplicate triggers)
// alertSnoozed → true for 5 minutes after user clicks "Snooze"
// prevLevel    → last known fatigue level, used to detect transitions to HIGH
let alertShown   = false;
let alertSnoozed = false;
let prevLevel    = '';

/** Show the break alert overlay */
function showBreakAlert() {
  if (alertShown || alertSnoozed) return; // don't double-show
  const overlay = document.getElementById('breakAlertOverlay');
  if (overlay) {
    overlay.style.display = 'flex';
    alertShown = true;
  }
}

/** Dismiss: hide the overlay. Won't re-appear until fatigue drops then rises again. */
function dismissAlert() {
  const overlay = document.getElementById('breakAlertOverlay');
  if (overlay) overlay.style.display = 'none';
  alertShown   = false;
  prevLevel    = ''; // reset so alert can fire again if fatigue re-escalates
}

/** Snooze: hide for 5 minutes then re-arm automatically */
function snoozeAlert() {
  const overlay = document.getElementById('breakAlertOverlay');
  if (overlay) overlay.style.display = 'none';
  alertShown   = false;
  alertSnoozed = true;
  setTimeout(() => { alertSnoozed = false; }, 5 * 60 * 1000); // 5 minutes
}
// ──────────────────────────────────────────────────────────────────────────────

// ─── Feature 3: Reset Session ────────────────────────────────────────────────
/** Show the Reset confirmation modal */
function showResetModal() {
  const overlay = document.getElementById('resetModalOverlay');
  if (overlay) {
    overlay.style.display = 'flex';
  }
}

/** Dismiss the Reset confirmation modal */
function dismissResetModal() {
  const overlay = document.getElementById('resetModalOverlay');
  if (overlay) {
    overlay.style.display = 'none';
  }
}

/** Show the Research Analytics Report modal */
async function showReportModal() {
  const overlay = document.getElementById('reportModalOverlay');
  if (overlay) {
    overlay.style.display = 'flex';
    await loadResearchReport();
  }
}

/** Dismiss the Research Analytics Report modal */
function dismissReportModal() {
  const overlay = document.getElementById('reportModalOverlay');
  if (overlay) {
    overlay.style.display = 'none';
  }
}

/** Fetch data from /api/research-report and populate the modal overlay card metrics */
async function loadResearchReport() {
  try {
    const resp = await authFetch('/api/research-report');
    const data = await resp.json();
    
    // Dataset Telemetry
    document.getElementById('repTotalRows').textContent = data.total_records;
    document.getElementById('repAvgWpm').textContent = data.avg_wpm;
    document.getElementById('repAvgErrors').textContent = data.avg_errors;
    document.getElementById('repTotalBlinks').textContent = data.total_blinks;
    document.getElementById('repTotalYawns').textContent = data.total_yawns;
    
    // Pearson Correlation Matrix
    const wpmCorr = data.correlations.wpm_vs_fatigue;
    const blinkCorr = data.correlations.blinks_vs_fatigue;
    
    document.getElementById('corrWpm').textContent = (wpmCorr >= 0 ? '+' : '') + wpmCorr.toFixed(3);
    document.getElementById('corrBlinks').textContent = (blinkCorr >= 0 ? '+' : '') + blinkCorr.toFixed(3);
    
    // Model Output Profile
    const lowPct = data.fatigue_distribution.LOW || 0.0;
    const medPct = data.fatigue_distribution.MEDIUM || 0.0;
    const highPct = data.fatigue_distribution.HIGH || 0.0;
    
    document.getElementById('distLowPct').textContent = `${lowPct.toFixed(1)}%`;
    document.getElementById('distMediumPct').textContent = `${medPct.toFixed(1)}%`;
    document.getElementById('distHighPct').textContent = `${highPct.toFixed(1)}%`;
    
    // Animate bars
    document.getElementById('distLowBar').style.width = `${lowPct}%`;
    document.getElementById('distMediumBar').style.width = `${medPct}%`;
    document.getElementById('distHighBar').style.width = `${highPct}%`;
    
  } catch (err) {
    console.error('Failed to load research report:', err);
  }
}

// Bind to window for global templates visibility
window.showReportModal = showReportModal;
window.dismissReportModal = dismissReportModal;
window.loadResearchReport = loadResearchReport;


/** Call backend API to reset, clear UI, and reset charts */
async function executeReset() {
  try {
    const resp = await authFetch('/api/reset', { method: 'POST' });
    const data = await resp.json();
    if (data.status === 'ok') {
      dismissResetModal();

      // 1. Clear all frontend data arrays
      wpmData.length = 0;
      errorData.length = 0;
      labelData.length = 0;
      fatigueScoreData.length = 0;
      fatigueLabelData.length = 0;
      fatigueBgColors.length = 0;
      fatigueBorderColors.length = 0;
      blinkData.length = 0;
      yawnData.length = 0;
      confidenceData.length = 0;
      productivityData.length = 0;
      concentrationData.length = 0;
      concentrationData.length = 0;

      // Reset cache keys
      lastLogRowId = null;
      lastCharsCount = -1;
      lastWpmValue = -1;
      lastErrorsCount = -1;

      // 2. Re-render charts as empty
      if (wpmChart) wpmChart.update();
      if (errChart) errChart.update();
      if (fatigueHistoryChart) fatigueHistoryChart.update();

      // 3. Reset dashboard numerical labels immediately
      document.getElementById('statWpm').textContent = '0';
      document.getElementById('statErrors').textContent = '0';
      document.getElementById('statElapsed').textContent = '0';
      document.getElementById('statChars').textContent = '0';

      // 4. Reset fatigue level ring gauge
      updateRing(0, 'Low');

      // 5. Reset Alert State transitions
      prevLevel = '';
      alertShown = false;
      alertSnoozed = false;

      // 6. Reset XAI Reasoning elements immediately
      const prodVal = document.getElementById('xaiProductivityVal');
      if (prodVal) {
        prodVal.textContent = 'GOOD';
        prodVal.className = 'metric-value text-green';
      }
      const prodScore = document.getElementById('xaiProductivityScore');
      if (prodScore) prodScore.textContent = 'Score: 100.0';
      const concScore = document.getElementById('xaiConcentrationScore');
      if (concScore) {
        concScore.textContent = '100.0';
        concScore.className = 'metric-value text-blue';
      }
      const trend = document.getElementById('xaiTrend');
      if (trend) {
        trend.textContent = 'STABLE';
        trend.className = 'metric-value text-yellow';
      }
      const reasonsList = document.getElementById('xaiReasonsList');
      if (reasonsList) reasonsList.innerHTML = '<li>Start typing to initiate diagnostics...</li>';

      // 7. Reset Logs Table immediately and toggle empty state overlay
      const tableBody = document.getElementById('logsTableBody');
      const tableContainer = document.getElementById('logsTableContainer');
      const logsEmptyState = document.getElementById('logsEmptyState');
      if (tableBody) {
        tableBody.innerHTML = '';
      }
      if (tableContainer) tableContainer.style.display = 'none';
      if (logsEmptyState) logsEmptyState.style.display = 'flex';

      // 8. Reset ML Prediction Card elements
      updateMlRing('LOW', 0);
      const mlModel = document.getElementById('mlModelVal');
      if (mlModel) mlModel.textContent = 'Model: Decision Tree B (Multimodal)';
      const mlStatus = document.getElementById('mlStatusBadge');
      if (mlStatus) {
        mlStatus.textContent = 'Idle';
        mlStatus.className = 'card-badge badge-blue';
      }
      const mlReasons = document.getElementById('mlReasonsBox');
      if (mlReasons) mlReasons.innerHTML = '<strong>🔍 ML Reasoning:</strong> Waiting for typing telemetry...';

      // 9. Reset Webcam Card elements and show empty state
      const blinkEl = document.getElementById('webcamBlinks');
      const yawnEl = document.getElementById('webcamYawns');
      const apertureEl = document.getElementById('webcamAperture');
      const mouthEl = document.getElementById('webcamMouth');
      const webcamBadge = document.getElementById('webcamStatusBadge');
      if (blinkEl) blinkEl.textContent = '0';
      if (yawnEl) yawnEl.textContent = '0';
      if (apertureEl) apertureEl.textContent = '0.0';
      if (mouthEl) mouthEl.textContent = '0.0';
      if (webcamBadge) {
        webcamBadge.textContent = 'Initializing…';
        webcamBadge.className = 'card-badge badge-gray';
      }
    }
  } catch (e) {
    console.error('Reset request failed:', e);
  }
}
// ──────────────────────────────────────────────────────────────────────────────



const TIPS = {
  Low:    '✅ You\'re in great shape! Typing smoothly with minimal errors.',
  Medium: '⚠️ Some signs of fatigue. Consider a short 5-minute break.',
  High:   '🔴 High fatigue detected. Take a break, hydrate, and rest your eyes.'
};

// ─── Chart setup ─────────────────────────────────────────────────
function makeChartOptions(label, borderColor, bgColor) {
  return {
    type: 'line',
    data: {
      labels: labelData,
      datasets: [{
        label,
        data: label === 'WPM' ? wpmData : errorData,
        borderColor,
        backgroundColor: bgColor,
        fill: true,
        tension: 0.45,
        pointRadius: 2,
        pointHoverRadius: 5,
        borderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 400 },
      scales: {
        x: {
          ticks: { color: '#7a8399', font: { size: 10 }, maxTicksLimit: 6 },
          grid: { color: 'rgba(255,255,255,0.04)' }
        },
        y: {
          beginAtZero: true,
          ticks: { color: '#7a8399', font: { size: 11 } },
          grid: { color: 'rgba(255,255,255,0.04)' }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1a2035',
          titleColor: '#e8ecf4',
          bodyColor: '#7a8399',
          borderColor: 'rgba(255,255,255,0.08)',
          borderWidth: 1,
        }
      }
    }
  };
}

// ─── Ring gauge helpers ───────────────────────────────────────────
const CIRCUMFERENCE = 2 * Math.PI * 55; // r=55

function updateRing(score, level) {
  const ring      = document.getElementById('ringFill');
  const ringScore = document.getElementById('ringScore');
  const label     = document.getElementById('fatigueLabel');
  const sub       = document.getElementById('fatigueSub');
  const badge     = document.getElementById('fatigueBadge');
  const tip       = document.getElementById('fatigueTip');

  if (!ring) return;

  const offset = CIRCUMFERENCE - (score / 100) * CIRCUMFERENCE;
  ring.style.strokeDasharray  = CIRCUMFERENCE;
  ring.style.strokeDashoffset = offset;

  // Colour classes
  const cls = `level-${level.toLowerCase()}`;
  ring.className    = `ring-fill ${cls}`;
  ringScore.className = `ring-score ${cls}`;
  label.className   = `fatigue-text ${cls}`;

  ringScore.textContent = score;
  label.textContent     = level;
  badge.textContent     = level;
  sub.textContent       = score === 0
    ? 'Start typing to begin analysis'
    : `Fatigue score: ${score}/100`;

  if (tip) {
    tip.innerHTML = `<strong>💡 Tip:</strong> ${TIPS[level] || ''}`;
  }
}

// ─── ML Ring gauge helper ──────────────────────────────────────────
function updateMlRing(level, confidence) {
  const ring = document.getElementById('mlRingFill');
  const ringConf = document.getElementById('mlConfidenceVal');
  const label = document.getElementById('mlPredictLabel');
  const badge = document.getElementById('mlStatusBadge');
  
  if (!ring) return;
  
  const lvlLower = level.toLowerCase();
  const confScore = Math.round(confidence * 100);
  const offset = CIRCUMFERENCE - (confScore / 100) * CIRCUMFERENCE;
  
  ring.style.strokeDasharray = CIRCUMFERENCE;
  ring.style.strokeDashoffset = offset;
  
  // Apply theme color classes matching the level
  const cls = `level-${lvlLower}`;
  ring.className = `ring-fill ${cls}`;
  ringConf.className = `ring-score ${cls}`;
  label.className = `fatigue-text ${cls}`;
  
  ringConf.textContent = `${confScore}%`;
  label.textContent = level.toUpperCase();
  
  if (badge) {
    badge.textContent = 'Active';
    badge.className = 'card-badge badge-blue';
  }
}

// ─── Animate a counter ───────────────────────────────────────────
function animateTo(el, target) {
  if (!el) return;
  const current = parseFloat(el.textContent) || 0;
  const diff    = target - current;
  if (Math.abs(diff) < 0.5) { el.textContent = target; return; }
  el.textContent = (current + diff * 0.3).toFixed(target % 1 !== 0 ? 1 : 0);
}

// ─── Theme Management ───────────────────────────────────────────
function setTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
  
  const icon = document.getElementById('themeToggleIcon');
  if (icon) {
    icon.textContent = theme === 'dark' ? '🌙' : '☀️';
  }
  
  updateChartColorsForTheme(theme);
}

window.toggleTheme = function() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  setTheme(next);
};

function updateChartColorsForTheme(theme) {
  const gridColor = theme === 'dark' ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.05)';
  const labelColor = theme === 'dark' ? '#7a8399' : '#475569';
  const tooltipBg = theme === 'dark' ? '#1a2035' : '#ffffff';
  const tooltipTitle = theme === 'dark' ? '#e8ecf4' : '#1e293b';
  const tooltipBody = theme === 'dark' ? '#7a8399' : '#475569';
  const tooltipBorder = theme === 'dark' ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)';

  const charts = [wpmChart, errChart, fatigueHistoryChart];
  charts.forEach(chart => {
    if (!chart) return;
    
    if (chart.options.scales) {
      if (chart.options.scales.x) {
        if (chart.options.scales.x.ticks) chart.options.scales.x.ticks.color = labelColor;
        if (chart.options.scales.x.grid) chart.options.scales.x.grid.color = gridColor;
      }
      if (chart.options.scales.y) {
        if (chart.options.scales.y.ticks) chart.options.scales.y.ticks.color = labelColor;
        if (chart.options.scales.y.grid) chart.options.scales.y.grid.color = gridColor;
      }
    }
    
    if (chart.options.plugins && chart.options.plugins.tooltip) {
      chart.options.plugins.tooltip.backgroundColor = tooltipBg;
      chart.options.plugins.tooltip.titleColor = tooltipTitle;
      chart.options.plugins.tooltip.bodyColor = tooltipBody;
      chart.options.plugins.tooltip.borderColor = tooltipBorder;
      chart.options.plugins.tooltip.borderWidth = 1;
    }
    
    chart.update();
  });
}

// Immediately evaluate theme before chart creation to avoid flicker
const savedTheme = localStorage.getItem('theme');
const systemDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
const defaultTheme = savedTheme || (systemDark ? 'dark' : 'light');
document.documentElement.setAttribute('data-theme', defaultTheme);

// ─── Init ────────────────────────────────────────────────────────
async function initCharts() {
  const ctxWPM = document.getElementById('wpmChart').getContext('2d');
  const ctxErr = document.getElementById('errorChart').getContext('2d');

  wpmChart = new Chart(ctxWPM, makeChartOptions(
    'WPM',
    '#6c63ff',
    'rgba(108,99,255,0.15)'
  ));

  errChart = new Chart(ctxErr, makeChartOptions(
    'Errors',
    '#ff6b9d',
    'rgba(255,107,157,0.12)'
  ));

  // ── Feature 2: Fatigue History Chart ──────────────────────────────────────
  // This chart uses per-point colours: green for Low, yellow for Medium, red for High.
  // We store arrays of colours alongside the numeric score data.
  const ctxFH = document.getElementById('fatigueHistoryChart').getContext('2d');
  fatigueHistoryChart = new Chart(ctxFH, {
    type: 'line',
    data: {
      labels: fatigueLabelData,
      datasets: [{
        label: 'Fatigue Score',
        data: fatigueScoreData,
        // Per-point dot colours are set dynamically (see updateFatigueHistory)
        pointBackgroundColor: fatigueBgColors,
        pointBorderColor:     fatigueBorderColors,
        pointRadius: 5,
        pointHoverRadius: 7,
        borderColor: 'rgba(255,255,255,0.15)',  // faint connecting line
        backgroundColor: 'transparent',
        fill: false,
        tension: 0.4,
        borderWidth: 1.5,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 500 },
      scales: {
        x: {
          ticks: { color: '#7a8399', font: { size: 10 }, maxTicksLimit: 8 },
          grid: { color: 'rgba(255,255,255,0.04)' }
        },
        y: {
          min: 0, max: 100,
          ticks: {
            color: '#7a8399', font: { size: 11 },
            // Show human labels instead of numbers
            callback: v => v === 25 ? 'Low' : v === 50 ? 'Med' : v === 75 ? 'High' : ''
          },
          grid: { color: 'rgba(255,255,255,0.04)' }
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1a2035',
          titleColor: '#e8ecf4',
          bodyColor: '#7a8399',
          borderColor: 'rgba(255,255,255,0.08)',
          borderWidth: 1,
          callbacks: {
            // Show "Low / Medium / High" in tooltip instead of raw number
            label: ctx => {
              const s = ctx.parsed.y;
              const lv = s <= 25 ? 'Low' : s <= 50 ? 'Medium' : 'High';
              return `Fatigue: ${lv} (${s})`;
            }
          }
        }
      }
    }
  });

  /** Push a new point into the fatigue history chart */
  function updateFatigueHistory(score, level, blinks, yawns, confidence, productivity, concentration) {
    const now   = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const color = level === 'Low' ? '#00e5a0' : level === 'Medium' ? '#ffd166' : '#ff4757';

    if (fatigueLabelData.length >= MAX_POINTS) {
      fatigueLabelData.shift();
      fatigueScoreData.shift();
      fatigueBgColors.shift();
      fatigueBorderColors.shift();
      blinkData.shift();
      yawnData.shift();
      confidenceData.shift();
      productivityData.shift();
      concentrationData.shift();
    }
    fatigueLabelData.push(now);
    fatigueScoreData.push(score);
    fatigueBgColors.push(color);
    fatigueBorderColors.push(color);
    blinkData.push(blinks || 0);
    yawnData.push(yawns || 0);
    confidenceData.push(Math.round((confidence || 0) * 100));
    productivityData.push(productivity || 0.0);
    concentrationData.push(concentration || 100.0);

    refreshHistoryChart();
  }

  window.switchHistoryTab = function(tab) {
    currentTab = tab;

    // Toggle active styling on buttons
    const buttons = document.querySelectorAll('.analytics-tabs .tab-btn');
    buttons.forEach(btn => {
      if (btn.getAttribute('onclick').includes(tab)) {
        btn.classList.add('active');
        btn.style.color = 'var(--text)';
      } else {
        btn.classList.remove('active');
        btn.style.color = 'var(--muted)';
      }
    });

    refreshHistoryChart();
  };

  function refreshHistoryChart() {
    if (!fatigueHistoryChart) return;

    const titleEl = document.getElementById('historyChartTitle');
    const legendEl = document.getElementById('historyLegend');

    if (currentTab === 'fatigue') {
      if (titleEl) titleEl.textContent = 'Fatigue Score History';
      if (legendEl) legendEl.style.display = 'flex';
      
      fatigueHistoryChart.data.datasets = [{
        label: 'Fatigue Score',
        data: fatigueScoreData,
        pointBackgroundColor: fatigueBgColors,
        pointBorderColor:     fatigueBorderColors,
        pointRadius: 5,
        pointHoverRadius: 7,
        borderColor: 'rgba(255,255,255,0.15)',
        backgroundColor: 'transparent',
        fill: false,
        tension: 0.4,
        borderWidth: 1.5,
      }];
      
      fatigueHistoryChart.options.scales.y = {
        min: 0, max: 100,
        ticks: {
          color: '#7a8399', font: { size: 11 },
          callback: v => v === 25 ? 'Low' : v === 50 ? 'Med' : v === 75 ? 'High' : ''
        },
        grid: { color: 'rgba(255,255,255,0.04)' }
      };
      
      fatigueHistoryChart.options.plugins.tooltip.callbacks.label = ctx => {
        const s = ctx.parsed.y;
        const lv = s <= 25 ? 'Low' : s <= 50 ? 'Medium' : 'High';
        return `Fatigue: ${lv} (${s})`;
      };
    }
    else if (currentTab === 'webcam') {
      if (titleEl) titleEl.textContent = 'Webcam Telemetry (Blinks & Yawns)';
      if (legendEl) legendEl.style.display = 'none';

      fatigueHistoryChart.data.datasets = [
        {
          label: 'Blinks',
          data: blinkData,
          borderColor: '#00e5a0',
          backgroundColor: 'rgba(0, 229, 160, 0.1)',
          fill: true,
          tension: 0.4,
          borderWidth: 2,
          pointRadius: 3,
        },
        {
          label: 'Yawns',
          data: yawnData,
          borderColor: '#ffd166',
          backgroundColor: 'rgba(255, 209, 102, 0.1)',
          fill: true,
          tension: 0.4,
          borderWidth: 2,
          pointRadius: 3,
        }
      ];

      fatigueHistoryChart.options.scales.y = {
        min: 0,
        ticks: { color: '#7a8399', font: { size: 11 }, precision: 0 },
        grid: { color: 'rgba(255,255,255,0.04)' }
      };

      fatigueHistoryChart.options.plugins.tooltip.callbacks.label = ctx => {
        return `${ctx.dataset.label}: ${ctx.parsed.y}`;
      };
    }
    else if (currentTab === 'confidence') {
      if (titleEl) titleEl.textContent = 'ML Model Confidence Trends';
      if (legendEl) legendEl.style.display = 'none';

      fatigueHistoryChart.data.datasets = [{
        label: 'Confidence (%)',
        data: confidenceData,
        borderColor: '#00d4ff',
        backgroundColor: 'rgba(0, 212, 255, 0.15)',
        fill: true,
        tension: 0.45,
        borderWidth: 2,
        pointRadius: 4,
        pointBackgroundColor: '#00d4ff',
      }];

      fatigueHistoryChart.options.scales.y = {
        min: 0, max: 100,
        ticks: { color: '#7a8399', font: { size: 11 } },
        grid: { color: 'rgba(255,255,255,0.04)' }
      };

      fatigueHistoryChart.options.plugins.tooltip.callbacks.label = ctx => {
        return `Confidence: ${ctx.parsed.y}%`;
      };
    }
    else if (currentTab === 'productivity') {
      if (titleEl) titleEl.textContent = 'Productivity vs Concentration Dynamics';
      if (legendEl) legendEl.style.display = 'none';

      fatigueHistoryChart.data.datasets = [
        {
          label: 'Productivity Score',
          data: productivityData,
          borderColor: '#6c63ff',
          backgroundColor: 'rgba(108, 99, 255, 0.05)',
          fill: false,
          tension: 0.4,
          borderWidth: 2,
          pointRadius: 3,
        },
        {
          label: 'Concentration Score',
          data: concentrationData,
          borderColor: '#ff6b9d',
          backgroundColor: 'rgba(255, 107, 157, 0.05)',
          fill: false,
          tension: 0.4,
          borderWidth: 2,
          pointRadius: 3,
        }
      ];

      fatigueHistoryChart.options.scales.y = {
        min: 0, max: 100,
        ticks: { color: '#7a8399', font: { size: 11 } },
        grid: { color: 'rgba(255,255,255,0.04)' }
      };

      fatigueHistoryChart.options.plugins.tooltip.callbacks.label = ctx => {
        return `${ctx.dataset.label}: ${ctx.parsed.y}`;
      };
    }

    fatigueHistoryChart.update();
  }
  // ──────────────────────────────────────────────────────────────────────────

  // ── Poll stats every second ──
  setInterval(async () => {
    try {
      const resp = await authFetch('/api/stats');
      const data = await resp.json();
      const now  = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

      // Update stat cards
      animateTo(document.getElementById('statWpm'),     data.wpm);
      animateTo(document.getElementById('statErrors'),  data.errors);
      animateTo(document.getElementById('statElapsed'), data.elapsed);
      animateTo(document.getElementById('statChars'),   data.chars);

      // Cache check: only update charts if stats have actually changed
      if (data.chars !== lastCharsCount || data.wpm !== lastWpmValue || data.errors !== lastErrorsCount) {
        lastCharsCount = data.chars;
        lastWpmValue = data.wpm;
        lastErrorsCount = data.errors;

        // Update charts
        if (labelData.length >= MAX_POINTS) {
          labelData.shift(); wpmData.shift(); errorData.shift();
        }
        labelData.push(now);
        wpmData.push(data.wpm);
        errorData.push(data.errors);

        if (wpmChart) wpmChart.update();
        if (errChart) errChart.update();
      }
    } catch (e) {
      console.error('Stats fetch failed:', e);
    }
  }, 1000);

  // ── Poll fatigue and advanced stats every 2 seconds ──
  setInterval(async () => {
    try {
      // 1. Fetch Fatigue Ring Gauge stats
      const resp = await authFetch('/api/fatigue');
      const data = await resp.json();
      updateRing(data.score, data.fatigue);

      // ── Trigger break alert on HIGH fatigue ──
      if (data.fatigue === 'High' && prevLevel !== 'High') {
        showBreakAlert();
      }
      prevLevel = data.fatigue;

      // 2. Fetch Explainable AI
      const explainResp = await authFetch('/api/explain');
      const explainData = await explainResp.json();
      
      const prodValEl = document.getElementById('xaiProductivityVal');
      const prodScoreEl = document.getElementById('xaiProductivityScore');
      const concScoreEl = document.getElementById('xaiConcentrationScore');
      const trendEl = document.getElementById('xaiTrend');
      const reasonsListEl = document.getElementById('xaiReasonsList');
      
      if (prodValEl) {
        prodValEl.textContent = explainData.productivity_level;
        prodValEl.className = 'metric-value ' + 
          (explainData.productivity_level === 'EXCELLENT' ? 'text-green' : 
           explainData.productivity_level === 'GOOD' ? 'text-blue' : 'text-red');
      }
      if (prodScoreEl) {
        prodScoreEl.textContent = `Score: ${explainData.productivity_score}`;
      }
      if (concScoreEl) {
        concScoreEl.textContent = explainData.concentration_score;
        concScoreEl.className = 'metric-value ' + 
          (explainData.concentration_score >= 80 ? 'text-green' : 
           explainData.concentration_score >= 60 ? 'text-yellow' : 'text-red');
      }
      if (trendEl) {
        trendEl.textContent = explainData.trend;
        trendEl.className = 'metric-value ' + 
          (explainData.trend === 'FALLING' ? 'text-green' : 
           explainData.trend === 'STABLE' ? 'text-yellow' : 'text-red');
      }
      
      if (reasonsListEl) {
        reasonsListEl.innerHTML = '';
        explainData.reasons.forEach(reason => {
          const li = document.createElement('li');
          li.textContent = reason;
          reasonsListEl.appendChild(li);
        });
      }

      // 3. Fetch Webcam metrics
      let blinks = 0;
      let yawns = 0;
      try {
        const webcamResp = await authFetch('/api/webcam-status');
        const webcamData = await webcamResp.json();
        blinks = webcamData.blink_count;
        yawns = webcamData.yawn_count;
        
        // Update webcam metrics on UI
        const blinkEl = document.getElementById('webcamBlinks');
        const yawnEl = document.getElementById('webcamYawns');
        const apertureEl = document.getElementById('webcamAperture');
        const mouthEl = document.getElementById('webcamMouth');
        const webcamBadge = document.getElementById('webcamStatusBadge');
        
        if (blinkEl) blinkEl.textContent = webcamData.blink_count;
        if (yawnEl) yawnEl.textContent = webcamData.yawn_count;
        if (apertureEl) apertureEl.textContent = webcamData.eye_aperture.toFixed(2);
        if (mouthEl) mouthEl.textContent = webcamData.mouth_stretch.toFixed(2);
        
        const emptyStateEl = document.getElementById('webcamEmptyState');
        const webcamStreamEl = document.getElementById('webcamStream');

        if (webcamBadge) {
          if (webcamData.is_active) {
            if (emptyStateEl) emptyStateEl.style.display = 'none';
            if (webcamStreamEl) webcamStreamEl.style.display = 'block';
            if (webcamData.face_detected) {
              webcamBadge.textContent = `Active (${webcamData.fps} FPS)`;
              webcamBadge.className = 'card-badge badge-green';
            } else {
              webcamBadge.textContent = 'No Face';
              webcamBadge.className = 'card-badge badge-yellow';
            }
          } else {
            if (emptyStateEl) {
              emptyStateEl.style.display = 'flex';
              const titleEl = emptyStateEl.querySelector('.empty-title');
              const descEl = emptyStateEl.querySelector('.empty-desc');
              if (webcamData.cloud_mode) {
                if (titleEl) titleEl.textContent = 'Webcam Offline (Cloud Mode)';
                if (descEl) descEl.textContent = 'Physical camera sensors are disabled in cloud environments. FatigueAI has automatically activated simulated physiological telemetry and the Random Forest fallback model.';
              } else {
                if (titleEl) titleEl.textContent = 'Webcam Offline / Locked';
                if (descEl) descEl.textContent = 'Connect a USB camera or allow browser permissions to track physical landmark telemetry.';
              }
            }
            if (webcamStreamEl) webcamStreamEl.style.display = 'none';
            webcamBadge.textContent = 'Inactive';
            webcamBadge.className = 'card-badge badge-gray';
          }
        }
      } catch (webcamErr) {
        console.error('Webcam status fetch failed:', webcamErr);
      }

      // 4. Fetch SQLite logs and update session logs table & fatigue history
      const logsResp = await authFetch('/api/logs');
      const logsData = await logsResp.json();
      
      const tableBody = document.getElementById('logsTableBody');
      const tableContainer = document.getElementById('logsTableContainer');
      const logsEmptyState = document.getElementById('logsEmptyState');

      if (tableBody) {
        if (logsData.length === 0) {
          if (tableContainer) tableContainer.style.display = 'none';
          if (logsEmptyState) logsEmptyState.style.display = 'flex';
          lastLogRowId = null;
        } else {
          if (tableContainer) tableContainer.style.display = 'block';
          if (logsEmptyState) logsEmptyState.style.display = 'none';

          const latestLog = logsData[0];
          const latestId = latestLog.id;

          if (latestId !== lastLogRowId) {
            lastLogRowId = latestId;

            // Update Logs Table
            tableBody.innerHTML = '';
            logsData.forEach(log => {
              const tr = document.createElement('tr');
              
              let timeStr = log.timestamp;
              if (timeStr && timeStr.includes(' ')) {
                timeStr = timeStr.split(' ')[1];
              }
              
              const prodLevel = log.productivity_score >= 80 ? 'EXCELLENT' : 
                                log.productivity_score >= 50 ? 'GOOD' : 'NEEDS BREAK';
              const prodClass = log.productivity_score >= 80 ? 'prod-excellent' : 
                                log.productivity_score >= 50 ? 'prod-good' : 'prod-break';
              
              const fatigueClass = log.fatigue_level.toLowerCase();
              
              tr.innerHTML = `
                <td>${timeStr || 'N/A'}</td>
                <td>${log.wpm}</td>
                <td>${log.errors}</td>
                <td>${Math.round(log.session_duration)}s</td>
                <td><span class="badge-pill level-${fatigueClass}">${log.fatigue_score}</span></td>
                <td><span class="badge-pill level-${fatigueClass}">${log.fatigue_level}</span></td>
                <td><span class="badge-pill ${prodClass}">${prodLevel}</span></td>
              `;
              tableBody.appendChild(tr);
            });

            // Trigger push & update to history charts using values directly from SQL
            updateFatigueHistory(
              latestLog.fatigue_score,
              latestLog.fatigue_level,
              latestLog.blink_count || 0,
              latestLog.yawn_count || 0,
              latestLog.predict_confidence || 1.0,
              latestLog.productivity_score || 0.0,
              latestLog.concentration_score || 100.0
            );
          }
        }
      }

      // 5. Fetch ML Fatigue predictions
      try {
        const mlResp = await authFetch('/api/predict-fatigue');
        const mlData = await mlResp.json();
        
        updateMlRing(mlData.fatigue_level, mlData.confidence);
        
        const reasonsBox = document.getElementById('mlReasonsBox');
        if (reasonsBox && mlData.reasoning) {
          let reasonsHTML = '<strong>🔍 ML Reasoning:</strong><br>';
          if (mlData.reasoning.length === 0) {
            reasonsHTML += 'All physical/behavioral traits are normal.';
          } else {
            reasonsHTML += '<ul style="list-style-type:none; padding-left:0; margin-top:5px; margin-bottom:0;">';
            mlData.reasoning.forEach(r => {
              reasonsHTML += `<li style="font-size:11px; margin-bottom:4px; padding-left:12px; position:relative; color:var(--muted);">⚡ ${r}</li>`;
            });
            reasonsHTML += '</ul>';
          }
          reasonsBox.innerHTML = reasonsHTML;
        }
      } catch (mlErr) {
        console.error('ML prediction fetch failed:', mlErr);
      }

    } catch (e) {
      console.error('Fatigue fetch failed:', e);
    }
  }, 2000);

  // ── Pre-populate history graphs from SQL DB logs on startup ──
  try {
    const logsResp = await authFetch('/api/logs');
    const logsData = await logsResp.json();
    if (logsData && logsData.length > 0) {
      const historicalLogs = [...logsData].reverse().slice(-MAX_POINTS);
      
      historicalLogs.forEach(log => {
        let timeStr = log.timestamp;
        if (timeStr && timeStr.includes(' ')) {
          timeStr = timeStr.split(' ')[1];
        }
        
        const color = log.fatigue_level === 'Low' ? '#00e5a0' : 
                      log.fatigue_level === 'Medium' ? '#ffd166' : '#ff4757';
        
        fatigueLabelData.push(timeStr);
        fatigueScoreData.push(log.fatigue_score);
        fatigueBgColors.push(color);
        fatigueBorderColors.push(color);
        blinkData.push(log.blink_count || 0);
        yawnData.push(log.yawn_count || 0);
        confidenceData.push(Math.round((log.predict_confidence || 1.0) * 100));
        productivityData.push(log.productivity_score || 0.0);
        concentrationData.push(log.concentration_score || 100.0);
      });
      
      refreshHistoryChart();
    }
  } catch (err) {
    console.error('Failed to pre-populate logs from DB:', err);
  }

  // Initialize toggle icon state and synchronize chart colors on load
  setTheme(defaultTheme);

  // ── Retrieve startup diagnostics ──
  try {
    const diagResp = await authFetch('/api/diagnostics');
    const diagData = await diagResp.json();
    if (diagData.status === 'ok') {
      const startup = diagData.startup_validation;
      if (!startup.model_ok) {
        showToast('ML classifier binary missing: falling back to keyboard heuristics.', 'warning');
      }
      if (!startup.webcam_ok) {
        showToast('Webcam hardware offline: physiological telemetry is inactive.', 'warning');
      }
    }
  } catch (err) {
    console.error('Failed to load system diagnostics:', err);
  }
}

// ─── Presentation Mode ────────────────────────────────────────────────────────
function togglePresentationMode() {
  document.body.classList.toggle('presentation-mode');
  const isPres = document.body.classList.contains('presentation-mode');
  const btn = document.getElementById('btnPresentationNavbar');
  if (btn) {
    if (isPres) {
      btn.innerHTML = '<span class="btn-reset-icon">📺</span> Exit Presentation';
      btn.style.borderColor = 'var(--accent3)';
      btn.style.color = 'var(--accent3)';
      showToast('Recruiter Presentation Mode Enabled', 'success');
    } else {
      btn.innerHTML = '<span class="btn-reset-icon">📺</span> Presentation Mode';
      btn.style.borderColor = 'var(--accent2)';
      btn.style.color = 'var(--accent2)';
      showToast('Recruiter Presentation Mode Disabled', 'info');
    }
  }
  
  // Resize charts to refit new layout widths
  setTimeout(() => {
    if (wpmChart) wpmChart.resize();
    if (errChart) errChart.resize();
    if (fatigueHistoryChart) fatigueHistoryChart.resize();
  }, 300);
}
window.togglePresentationMode = togglePresentationMode;

// ─── Dismiss Page Loader on Resource Load Complete ───────────────────────────
window.addEventListener('load', () => {
  const loader = document.getElementById('page-loader');
  if (loader) {
    loader.style.opacity = '0';
    setTimeout(() => {
      loader.style.display = 'none';
    }, 500);
  }
});

window.addEventListener('DOMContentLoaded', initCharts);
