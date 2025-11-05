/**
 * DASHBOARD FUNCTIONALITY - Crypto Trading Platform
 * Handles portfolio updates, timer management, rebalancing operations
 */

(function() {
  'use strict';

  // ========================================
  // GLOBAL STATE
  // ========================================
  const DashboardState = {
    remaining: 0,
    defaultInterval: 3600, // 1 hour default
    timerPaused: false,
    timerInterval: null,
    lastPortfolioValue: 0,
    isRebalancing: false
  };

  // ========================================
  // CONFIGURATION
  // ========================================
  const Config = {
    autoRefreshInterval: 10000, // 10 seconds
    portfolioUpdateDelay: 500,
    animationDuration: 1000,
    flashDuration: 500
  };

  // ========================================
  // PORTFOLIO MANAGEMENT
  // ========================================
  async function fetchStatus(updatePortfolio = false) {
    try {
      console.log('[Dashboard] Fetching status...', { updatePortfolio });
      const statusUrl = document.body.getAttribute('data-status-url');
      if (!statusUrl) {
        console.error('[Dashboard] Status URL not found');
        return;
      }

      const res = await fetch(statusUrl);
      console.log('[Dashboard] Response status:', res.status);

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();
      console.log('[Dashboard] Data received:', data);

      // Update timer if not paused
      if (!DashboardState.timerPaused && data.remaining !== null) {
        DashboardState.remaining = data.remaining;
        console.log('[Dashboard] Timer updated:', DashboardState.remaining);
      }

      // Update portfolio display
      if (updatePortfolio && data.portfolio) {
        console.log('[Dashboard] Updating portfolio table');
        updatePortfolioTable(data.portfolio);
      }

      // Update rebalance log
      if (data.rebalance && Object.keys(data.rebalance).length > 0) {
        console.log('[Dashboard] Updating rebalance log');
        updateRebalanceLog(data.rebalance);
      }

      return data;
    } catch (err) {
      console.error('[Dashboard] Error fetching status:', err);
      showNotification('Failed to fetch status: ' + err.message, 'error');
    }
  }

  function updatePortfolioTable(portfolio) {
    console.log('[Dashboard] updatePortfolioTable called with:', portfolio);

    const tbody = document.querySelector('#portfolio tbody');
    if (!tbody) {
      console.error('[Dashboard] Portfolio table body not found');
      return;
    }

    // Clear existing rows
    tbody.innerHTML = '';

    let totalValue = 0;
    let itemCount = 0;

    // Add portfolio items
    for (const [symbol, info] of Object.entries(portfolio)) {
      console.log(`[Dashboard] Processing ${symbol}:`, info);
      itemCount++;

      let balanceText = "";
      let usdcValue = 0;

      if (typeof info === "object" && info !== null) {
        const free = parseFloat(info.free || 0);
        const locked = parseFloat(info.locked || 0);
        const total = free + locked;
        usdcValue = parseFloat(info.usdc_value || 0);
        totalValue += usdcValue;

        balanceText = `${total.toFixed(6)} (${getTranslation('free')}: ${free.toFixed(6)})`;
      } else {
        balanceText = info;
      }

      // Create row with animation
      const row = document.createElement('tr');
      row.style.opacity = '0';
      row.innerHTML = `
        <td><strong class="coin-symbol">${symbol}</strong></td>
        <td>${balanceText}</td>
        <td class="crypto-price">$${usdcValue.toFixed(2)}</td>
      `;
      tbody.appendChild(row);

      // Animate row appearance
      setTimeout(() => {
        row.style.transition = 'opacity 0.5s ease';
        row.style.opacity = '1';
      }, itemCount * 50);
    }

    console.log(`[Dashboard] Added ${itemCount} items, total: $${totalValue.toFixed(2)}`);

    // Add total row
    const totalRow = document.createElement('tr');
    totalRow.innerHTML = `
      <td><strong>${getTranslation('total')}</strong></td>
      <td>-</td>
      <td><strong class="crypto-price total-value">$${totalValue.toFixed(2)}</strong></td>
    `;
    tbody.appendChild(totalRow);

    // Animate total value change
    if (DashboardState.lastPortfolioValue !== 0) {
      const totalValueElement = totalRow.querySelector('.total-value');
      if (totalValue > DashboardState.lastPortfolioValue) {
        if (window.CryptoEffects) {
          window.CryptoEffects.flashPrice(totalValueElement, true);
        }
      } else if (totalValue < DashboardState.lastPortfolioValue) {
        if (window.CryptoEffects) {
          window.CryptoEffects.flashPrice(totalValueElement, false);
        }
      }
    }

    DashboardState.lastPortfolioValue = totalValue;
  }

  function updateRebalanceLog(rebalanceData) {
    const logElement = document.getElementById('rebalanceLog');
    if (!logElement) return;

    const formattedJson = JSON.stringify(rebalanceData, null, 2);
    logElement.textContent = formattedJson;

    // Syntax highlighting for JSON
    highlightJSON(logElement);
  }

  function highlightJSON(element) {
    const text = element.textContent;
    const highlighted = text
      .replace(/"([^"]+)":/g, '<span class="json-key">"$1":</span>')
      .replace(/: "([^"]+)"/g, ': <span class="json-string">"$1"</span>')
      .replace(/: (\d+\.?\d*)/g, ': <span class="json-number">$1</span>')
      .replace(/: (true|false)/g, ': <span class="json-boolean">$1</span>');

    element.innerHTML = highlighted;
  }

  // ========================================
  // TIMER MANAGEMENT
  // ========================================
  function updateTimerDisplay() {
    const timerElement = document.getElementById('timer');
    if (!timerElement) return;

    if (DashboardState.remaining <= 0) {
      timerElement.textContent = getTranslation('rebalanceTimeReached');
      timerElement.style.background = 'linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.2) 100%)';
    } else {
      const d = Math.floor(DashboardState.remaining / 86400);
      const h = Math.floor((DashboardState.remaining % 86400) / 3600);
      const m = Math.floor((DashboardState.remaining % 3600) / 60);
      const s = DashboardState.remaining % 60;

      timerElement.textContent = `${getTranslation('remaining')}: ${d}d ${h}h ${m}m ${s}s`;
      timerElement.style.background = 'linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%)';
    }
  }

  function startTimer() {
    if (DashboardState.timerInterval) {
      clearInterval(DashboardState.timerInterval);
    }

    DashboardState.timerInterval = setInterval(() => {
      if (!DashboardState.timerPaused && DashboardState.remaining > 0) {
        DashboardState.remaining--;
        updateTimerDisplay();

        if (DashboardState.remaining === 0) {
          onTimerEnd();
        }
      }
    }, 1000);
  }

  async function onTimerEnd() {
    const timerElement = document.getElementById('timer');
    if (timerElement) {
      timerElement.textContent = getTranslation('rebalancingInProgress');
    }

    try {
      await performRebalance();
      await fetchStatus(true);
    } catch (e) {
      console.error('[Dashboard] Rebalance error:', e);
      showNotification(getTranslation('rebalanceError') + ': ' + e.message, 'error');
    }

    DashboardState.remaining = DashboardState.defaultInterval;
    updateTimerDisplay();
  }

  // ========================================
  // REBALANCING OPERATIONS
  // ========================================
  async function performRebalance() {
    if (DashboardState.isRebalancing) {
      console.log('[Dashboard] Rebalance already in progress');
      return;
    }

    DashboardState.isRebalancing = true;
    const rebalanceUrl = document.body.getAttribute('data-rebalance-url');

    try {
      const res = await fetch(rebalanceUrl);
      const data = await res.json();
      return data;
    } finally {
      DashboardState.isRebalancing = false;
    }
  }

  async function manualRebalance() {
    const confirmed = confirm(getTranslation('executeRebalance'));
    if (!confirmed) return;

    const btn = document.getElementById('rebalanceBtn');
    if (!btn) return;

    btn.disabled = true;
    btn.textContent = getTranslation('rebalancing');

    try {
      const data = await performRebalance();

      if (data.status === "ok") {
        showNotification(getTranslation('rebalanceCompleted'), 'success');

        // Launch confetti on success
        if (window.CryptoEffects) {
          window.CryptoEffects.launchConfetti({
            count: 50,
            duration: 2000
          });
        }

        await fetchStatus(true);
      } else {
        showNotification(getTranslation('error') + ': ' + (data.error || 'Unknown error'), 'error');
      }
    } catch (err) {
      console.error('[Dashboard] Rebalance error:', err);
      showNotification(getTranslation('rebalanceFailed'), 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = getTranslation('rebalanceNow');
    }
  }

  async function refreshPortfolio() {
    const btn = document.getElementById('refreshBtn');
    if (!btn) return;

    btn.disabled = true;
    btn.textContent = getTranslation('refreshing');

    try {
      const refreshUrl = document.body.getAttribute('data-refresh-url');
      const res = await fetch(refreshUrl);
      const data = await res.json();

      if (data.status === "ok") {
        updatePortfolioTable(data.portfolio || {});
        showNotification(getTranslation('portfolioRefreshed'), 'success');
      } else {
        showNotification(getTranslation('error') + ': ' + (data.error || 'Unknown error'), 'error');
      }
    } catch (err) {
      console.error('[Dashboard] Refresh error:', err);
      showNotification(getTranslation('refreshFailed'), 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = getTranslation('refreshPortfolio');
    }
  }

  // ========================================
  // TIMER CONTROLS
  // ========================================
  function toggleTimer() {
    DashboardState.timerPaused = !DashboardState.timerPaused;
    const btn = document.getElementById('stopBtn');

    if (btn) {
      if (DashboardState.timerPaused) {
        btn.textContent = getTranslation('startTimer');
        btn.style.background = 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)';
      } else {
        btn.textContent = getTranslation('stopTimer');
        btn.style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
      }
    }
  }

  function saveDefaultInterval() {
    const d = Number(document.getElementById('defDays')?.value) || 0;
    const h = Number(document.getElementById('defHours')?.value) || 0;
    const m = Number(document.getElementById('defMinutes')?.value) || 0;
    const s = Number(document.getElementById('defSeconds')?.value) || 0;

    DashboardState.defaultInterval = d * 86400 + h * 3600 + m * 60 + s;

    showNotification(
      `${getTranslation('newDefaultInterval')}: ${DashboardState.defaultInterval} ${getTranslation('sec')}`,
      'success'
    );
  }

  function setNextRebalance() {
    const d = Number(document.getElementById('nextDays')?.value) || 0;
    const h = Number(document.getElementById('nextHours')?.value) || 0;
    const m = Number(document.getElementById('nextMinutes')?.value) || 0;
    const s = Number(document.getElementById('nextSeconds')?.value) || 0;

    DashboardState.remaining = d * 86400 + h * 3600 + m * 60 + s;
    updateTimerDisplay();
    startTimer();

    showNotification(
      `${getTranslation('nextRebalanceIn')} ${DashboardState.remaining} ${getTranslation('sec')}`,
      'info'
    );
  }

  // ========================================
  // NOTIFICATIONS
  // ========================================
  function showNotification(message, type = 'info') {
    // Check if notification container exists, if not create it
    let container = document.getElementById('notification-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'notification-container';
      container.style.cssText = `
        position: fixed;
        top: 80px;
        right: 20px;
        z-index: 10000;
        max-width: 400px;
      `;
      document.body.appendChild(container);
    }

    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
      padding: 16px 20px;
      margin-bottom: 10px;
      border-radius: 12px;
      box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
      background: white;
      border-left: 4px solid;
      animation: slideInRight 0.3s ease;
      display: flex;
      align-items: center;
      gap: 12px;
      font-weight: 500;
    `;

    // Set border color based on type
    const colors = {
      success: '#22c55e',
      error: '#ef4444',
      warning: '#f59e0b',
      info: '#3b82f6'
    };
    notification.style.borderLeftColor = colors[type] || colors.info;

    // Add icon
    const icons = {
      success: '✓',
      error: '✕',
      warning: '⚠',
      info: 'ℹ'
    };
    const icon = document.createElement('span');
    icon.textContent = icons[type] || icons.info;
    icon.style.cssText = `
      width: 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 50%;
      background: ${colors[type] || colors.info};
      color: white;
      font-weight: bold;
      flex-shrink: 0;
    `;

    const text = document.createElement('span');
    text.textContent = message;
    text.style.flex = '1';

    notification.appendChild(icon);
    notification.appendChild(text);
    container.appendChild(notification);

    // Auto remove after 5 seconds
    setTimeout(() => {
      notification.style.animation = 'slideOutRight 0.3s ease';
      setTimeout(() => notification.remove(), 300);
    }, 5000);

    // Add CSS animation if not exists
    if (!document.getElementById('notification-style')) {
      const style = document.createElement('style');
      style.id = 'notification-style';
      style.textContent = `
        @keyframes slideInRight {
          from {
            transform: translateX(400px);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        @keyframes slideOutRight {
          from {
            transform: translateX(0);
            opacity: 1;
          }
          to {
            transform: translateX(400px);
            opacity: 0;
          }
        }
      `;
      document.head.appendChild(style);
    }
  }

  // ========================================
  // INTERNATIONALIZATION HELPER
  // ========================================
  function getTranslation(key) {
    const translations = window.DashboardTranslations || {};
    return translations[key] || key;
  }

  // ========================================
  // EVENT LISTENERS
  // ========================================
  function attachEventListeners() {
    // Stop/Start Timer
    const stopBtn = document.getElementById('stopBtn');
    if (stopBtn) {
      stopBtn.addEventListener('click', toggleTimer);
    }

    // Save Default Interval
    const saveDefaultBtn = document.getElementById('saveDefaultIntervalBtn');
    if (saveDefaultBtn) {
      saveDefaultBtn.addEventListener('click', saveDefaultInterval);
    }

    // Set Next Rebalance
    const setNextBtn = document.getElementById('setNextRebalanceBtn');
    if (setNextBtn) {
      setNextBtn.addEventListener('click', setNextRebalance);
    }

    // Manual Rebalance
    const rebalanceBtn = document.getElementById('rebalanceBtn');
    if (rebalanceBtn) {
      rebalanceBtn.addEventListener('click', manualRebalance);
    }

    // Refresh Portfolio
    const refreshBtn = document.getElementById('refreshBtn');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', refreshPortfolio);
    }
  }

  // ========================================
  // INITIALIZATION
  // ========================================
  async function initDashboard() {
    console.log('[Dashboard] Initializing...');

    // Attach event listeners
    attachEventListeners();

    // First, try to refresh portfolio from API
    try {
      const refreshUrl = document.body.getAttribute('data-refresh-url');
      if (refreshUrl) {
        console.log('[Dashboard] Fetching fresh portfolio...');
        const refreshRes = await fetch(refreshUrl);
        const refreshData = await refreshRes.json();

        if (refreshData.status === "ok") {
          console.log('[Dashboard] Portfolio refreshed successfully');
          updatePortfolioTable(refreshData.portfolio || {});
        } else {
          console.warn('[Dashboard] Refresh failed, falling back to status');
          await fetchStatus(true);
        }
      }
    } catch (err) {
      console.error('[Dashboard] Refresh error:', err);
      await fetchStatus(true);
    }

    // Load last rebalance results
    try {
      const statusData = await fetchStatus(false);
      if (statusData?.rebalance && Object.keys(statusData.rebalance).length > 0) {
        updateRebalanceLog(statusData.rebalance);
      }
    } catch (err) {
      console.error('[Dashboard] Error fetching status:', err);
    }

    // Start timer
    DashboardState.remaining = DashboardState.defaultInterval;
    updateTimerDisplay();
    startTimer();

    // Auto-refresh portfolio periodically
    setInterval(() => fetchStatus(true), Config.autoRefreshInterval);

    console.log('[Dashboard] Initialization complete');
  }

  // ========================================
  // START ON DOM READY
  // ========================================
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboard);
  } else {
    initDashboard();
  }

  // ========================================
  // EXPORT TO GLOBAL SCOPE
  // ========================================
  window.Dashboard = {
    fetchStatus,
    updatePortfolioTable,
    manualRebalance,
    refreshPortfolio,
    showNotification,
    state: DashboardState
  };

})();
