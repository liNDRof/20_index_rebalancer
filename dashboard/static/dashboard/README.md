# Crypto Trading Platform - Theme & Styling Guide

## 📁 File Structure

```
dashboard/static/dashboard/
├── crypto-theme.css       # Main theme stylesheet (base styles, components)
├── dashboard.css          # Dashboard-specific styles (portfolio, charts, controls)
├── crypto-effects.js      # Visual effects & animations library
├── dashboard.js           # Dashboard functionality (portfolio, timer, rebalancing)
├── i18n-switch.js        # Language switching functionality
└── README.md             # This file
```

## 🎨 CSS Files Overview

### 1. **crypto-theme.css** - Main Theme Stylesheet
The foundation of the cryptocurrency theme with modern design elements.

**Features:**
- ✨ Animated gradient backgrounds
- 🌌 Particle/blockchain network effects
- 💎 Glassmorphism design (transparent, blurred backgrounds)
- 🎯 Smooth animations and transitions
- 📱 Fully responsive design
- 🎨 Consistent color palette and spacing

**Key Components:**
- Global reset and base styles
- Navigation bar with sticky positioning
- Card and block components with hover effects
- Button variants (primary, success, warning, danger)
- Form inputs with focus animations
- Alert boxes (success, warning, error, info)
- Loading animations and spinners
- Utility classes for spacing, flex, etc.

**Color Palette:**
```css
--primary-blue: #3b82f6
--primary-purple: #8b5cf6
--primary-orange: #f59e0b
--success-green: #22c55e
--warning-yellow: #f59e0b
--error-red: #ef4444
```

### 2. **dashboard.css** - Dashboard-Specific Styles
Specialized styles for trading dashboard features.

**Features:**
- 📊 Portfolio table with gradient headers
- ⏱️ Timer controls with custom inputs
- 📈 Trading statistics cards
- 💰 Cryptocurrency price displays
- 📜 Code/log viewer with syntax highlighting
- 🔄 Trade history timeline
- 📱 Mobile-optimized layouts

**Key Components:**
- Dashboard title with rotating gradient effect
- Timer controls with glassmorphism
- Portfolio table with hover animations
- Price flash effects (green up, red down)
- Rebalance log with custom scrollbar
- Coin icon styles (BTC, ETH, USDC, etc.)

## 🚀 JavaScript Files Overview

### 3. **crypto-effects.js** - Visual Effects Library
Advanced animations and interactive effects for the platform.

**Available Effects:**

#### CryptoParticles
Animated particle network background with connecting lines.
```javascript
new CryptoEffects.CryptoParticles('myCanvas', {
  particleCount: 50,
  particleSpeed: 0.5,
  connectionDistance: 150
});
```

#### CryptoTicker
Animated cryptocurrency price ticker.
```javascript
new CryptoEffects.CryptoTicker('tickerElement', ['BTC', 'ETH', 'BNB']);
```

#### Number Counter Animation
Smooth number transitions.
```javascript
CryptoEffects.animateCounter(element, targetValue, duration, decimals);
```

#### Interactive Effects
```javascript
// Add glow on hover
CryptoEffects.addGlowEffect('.card', 'rgba(59, 130, 246, 0.5)');

// 3D tilt effect
CryptoEffects.addTiltEffect('.block', maxTilt);

// Ripple effect on click
CryptoEffects.addRippleEffect('button');

// Scroll reveal animations
new CryptoEffects.ScrollReveal('.block', { delay: 100 });

// Price flash animations
CryptoEffects.flashPrice(element, isIncrease);

// Typing effect
CryptoEffects.typeWriter(element, text, speed);

// Confetti celebration
CryptoEffects.launchConfetti({ count: 100, duration: 3000 });
```

### 4. **dashboard.js** - Core Dashboard Functionality
Manages portfolio updates, timer, and trading operations.

**Features:**
- 📊 Real-time portfolio updates
- ⏱️ Countdown timer with auto-rebalance
- 🔄 Manual and automatic rebalancing
- 🔔 Toast notifications
- 🌐 Multi-language support
- 💾 State management

**Key Functions:**
```javascript
// Fetch portfolio status
Dashboard.fetchStatus(updatePortfolio);

// Update portfolio display
Dashboard.updatePortfolioTable(portfolio);

// Manual rebalance
Dashboard.manualRebalance();

// Refresh portfolio
Dashboard.refreshPortfolio();

// Show notification
Dashboard.showNotification(message, type);
```

**Configuration:**
- Auto-refresh every 10 seconds
- Smooth animations on updates
- Price change flash effects
- Confetti on successful trades

## 📋 Integration Guide

### Basic Setup

1. **Add CSS files to your HTML:**
```html
<head>
  <link rel="stylesheet" href="{% static 'dashboard/crypto-theme.css' %}">
  <link rel="stylesheet" href="{% static 'dashboard/dashboard.css' %}">
</head>
```

2. **Add JavaScript files before closing body:**
```html
<body>
  <!-- Your content -->

  <script src="{% static 'dashboard/i18n-switch.js' %}"></script>
  <script src="{% static 'dashboard/crypto-effects.js' %}"></script>
  <script src="{% static 'dashboard/dashboard.js' %}"></script>
</body>
```

3. **Add required data attributes to body:**
```html
<body
  data-status-url="{% url 'dashboard:status' %}"
  data-rebalance-url="{% url 'dashboard:manual_rebalance' %}"
  data-refresh-url="{% url 'dashboard:refresh_portfolio' %}">
```

4. **Define translations for JavaScript:**
```html
<script>
  window.DashboardTranslations = {
    'free': '{% trans "free" %}',
    'total': '{% trans "TOTAL" %}',
    'remaining': '{% trans "Remaining" %}',
    'rebalanceNow': '{% trans "Rebalance now" %}',
    // ... add more translations
  };
</script>
```

### Required HTML Structure

#### Portfolio Table
```html
<table id="portfolio">
  <thead>
    <tr>
      <th>Asset</th>
      <th>Balance</th>
      <th>Value (USDC)</th>
    </tr>
  </thead>
  <tbody>
    <!-- Will be populated by JavaScript -->
  </tbody>
</table>
```

#### Timer Controls
```html
<div class="timer-controls">
  <div class="input-group">
    <label>Days <input id="nextDays" type="number" min="0" value="0"></label>
    <label>Hours <input id="nextHours" type="number" min="0" value="0"></label>
    <label>Minutes <input id="nextMinutes" type="number" min="0" value="10"></label>
    <label>Seconds <input id="nextSeconds" type="number" min="0" value="0"></label>
  </div>
  <button id="setNextRebalanceBtn">Set time</button>
  <button id="stopBtn">Stop timer</button>
  <div class="timer-info" id="timer">Until next rebalance: ...</div>
</div>
```

#### Action Buttons
```html
<button id="rebalanceBtn">Rebalance now</button>
<button id="refreshBtn">Refresh portfolio</button>
```

#### Rebalance Log
```html
<pre id="rebalanceLog">Waiting for data...</pre>
```

## 🎯 Component Usage Examples

### Cards with Auto-Effects
```html
<div class="card">
  <h2>My Card Title</h2>
  <p>Card content here</p>
</div>
```
Automatically gets:
- Hover lift effect
- Glow on hover
- Glassmorphism background

### Buttons with Ripple
```html
<button class="btn-primary">Primary Action</button>
<button class="btn-success">Success Action</button>
<button class="btn-warning">Warning Action</button>
<button class="btn-danger">Danger Action</button>
```
Automatically gets ripple effect on click.

### Alert Boxes
```html
<div class="alert-box alert-success">
  <h2>Success!</h2>
  <p>Operation completed successfully.</p>
</div>

<div class="alert-box alert-warning">
  <h2>Warning</h2>
  <p>Please review your settings.</p>
</div>

<div class="alert-box alert-error">
  <h2>Error</h2>
  <p>Something went wrong.</p>
</div>
```

### Portfolio Stats
```html
<div class="portfolio-stats">
  <div class="stat-card">
    <h3>Total Value</h3>
    <div class="value">$12,345.67</div>
  </div>
  <div class="stat-card">
    <h3>24h Change</h3>
    <div class="value">+5.2%</div>
  </div>
</div>
```

## 🎨 Customization

### Changing Colors
Edit CSS variables in `crypto-theme.css`:
```css
:root {
  --primary-blue: #your-color;
  --primary-purple: #your-color;
  /* etc. */
}
```

### Adjusting Animations
Modify animation durations:
```css
@keyframes floatParticles {
  /* Adjust timing and keyframes */
}
```

### Custom Effects
Add your own effects in `crypto-effects.js`:
```javascript
window.CryptoEffects.myCustomEffect = function() {
  // Your effect code
};
```

## 📱 Responsive Breakpoints

- **Desktop:** > 768px (full features)
- **Tablet:** 481px - 768px (adjusted layouts)
- **Mobile:** ≤ 480px (stacked layouts, simplified views)

## 🔧 Browser Compatibility

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

**Features used:**
- CSS Grid & Flexbox
- CSS Custom Properties (variables)
- Backdrop Filter (glassmorphism)
- Intersection Observer API
- Fetch API
- ES6+ JavaScript

## 🐛 Troubleshooting

### Styles not applying
1. Check CSS file paths in template
2. Verify static files are being served
3. Clear browser cache
4. Run `python manage.py collectstatic`

### JavaScript not working
1. Check browser console for errors
2. Verify data-* attributes on body
3. Ensure elements have correct IDs
4. Check network tab for failed requests

### Animations laggy
1. Reduce particle count in effects
2. Disable backdrop-filter on low-end devices
3. Use `will-change` CSS property sparingly

## 📚 Additional Resources

- [CSS Gradient Generator](https://cssgradient.io/)
- [Glassmorphism Generator](https://hype4.academy/tools/glassmorphism-generator)
- [Color Palette Tools](https://coolors.co/)

## 🎉 Features Showcase

### Automatic Features (No Code Required)
✅ Ripple effects on all buttons
✅ Glow effects on cards
✅ Scroll reveal animations
✅ Responsive layouts
✅ Smooth transitions

### Interactive Features (JavaScript)
✅ Real-time portfolio updates
✅ Countdown timer with auto-rebalance
✅ Toast notifications
✅ Price flash animations
✅ Confetti celebrations

### Design Features
✅ Gradient backgrounds with animations
✅ Glassmorphism effects
✅ Custom scrollbars
✅ Syntax highlighting for JSON
✅ Coin-specific icons and colors

---

**Version:** 1.0.0
**Last Updated:** 2024
**License:** MIT
**Author:** Crypto Trading Platform Team
