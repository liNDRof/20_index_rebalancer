# 🚀 Crypto Index Rebalancer

A Django-based cryptocurrency portfolio rebalancing application with multi-user support and real-time trading capabilities.

## 📁 Project Structure

```
20_index_rebalancer/
├── crypto_trader/          # Django project configuration
│   ├── settings.py        # Main settings
│   ├── urls.py           # URL routing
│   ├── middleware.py     # Custom middleware
│   └── logging_config.py # Logging configuration
│
├── dashboard/             # Main application
│   ├── models.py         # UserProfile, TraderSession, TradeHistory
│   ├── views.py          # View logic (multi-user support)
│   ├── urls.py           # Dashboard URLs
│   ├── admin.py          # Django admin configuration
│   ├── templates/        # HTML templates
│   │   └── dashboard/
│   │       ├── base.html      # Base template with navbar
│   │       ├── index.html     # Main dashboard
│   │       ├── login.html     # Login page
│   │       ├── register.html  # Registration page
│   │       └── profile.html   # User profile & settings
│   ├── static/           # Static assets (CSS, JS)
│   │   └── dashboard/
│   │       ├── dashboard.js       # Main dashboard functionality
│   │       ├── dashboard.css      # Base styles
│   │       ├── crypto-theme.css   # Crypto-themed design
│   │       ├── crypto-effects.js  # Visual effects
│   │       └── i18n-switch.js    # Language switcher
│   └── migrations/       # Database migrations
│
├── trader/               # Trading logic
│   └── btceth_trader.py # BTCETH_CMC20_Trader class
│
├── locale/              # Internationalization (i18n)
│   ├── en/             # English translations
│   └── uk/             # Ukrainian translations
│
├── logs/               # Application logs (auto-generated)
│   ├── api.log
│   ├── debug.log
│   ├── errors.log
│   ├── trades.log
│   ├── general.log
│   ├── requests.log
│   ├── performance.log
│   └── user_activity.log
│
├── manage.py           # Django management script
├── db.sqlite3          # SQLite database
├── requirements.txt    # Python dependencies
├── .gitignore         # Git ignore patterns
└── SWEEP.md           # Development notes
```

## 🎯 Features

- ✅ **Multi-user Support** - Each user has isolated trading sessions
- ✅ **Binance Integration** - Real-time trading via Binance API
- ✅ **Portfolio Rebalancing** - Automated BTC/ETH rebalancing based on CMC Top 20
- ✅ **Real-time Dashboard** - Live portfolio updates and trading status
- ✅ **Internationalization** - English and Ukrainian language support
- ✅ **Modern Crypto Theme** - Professional blockchain-inspired UI
- ✅ **Secure Authentication** - User registration and encrypted API credentials

## 🚀 Quick Start

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Run Migrations**
```bash
python manage.py migrate
```

3. **Create Superuser** (optional)
```bash
python manage.py createsuperuser
```

4. **Run Development Server**
```bash
python manage.py runserver
```

5. **Access Application**
- Dashboard: http://localhost:8000/
- Admin Panel: http://localhost:8000/admin/

## 🔧 Configuration

### User Profile Setup
1. Register a new account
2. Navigate to Profile page
3. Add your Binance API credentials:
   - API Key
   - API Secret
4. Credentials are encrypted before storage

### Trading Configuration
Edit `trader/btceth_trader.py` to adjust:
- Rebalancing interval
- Target allocation percentages
- Trading pairs
- Risk parameters

## 📊 Models

### UserProfile
- Stores encrypted Binance API credentials
- Links to Django User model

### TraderSession
- Tracks active trading sessions per user
- Stores session state and configuration

### TradeHistory
- Records all executed trades
- Includes timestamp, symbol, type, quantity, price

## 🎨 UI/UX

The application features a modern cryptocurrency theme with:
- Glassmorphism effects
- Animated backgrounds
- Real-time data updates
- Responsive design
- Multi-language support

## 📝 Logging

Structured logging across multiple files:
- `api.log` - API calls and responses
- `trades.log` - Trade execution records
- `errors.log` - Error tracking
- `debug.log` - Debug information
- `general.log` - General application logs

## 🔐 Security

- Encrypted API credentials using Django's cryptography
- CSRF protection enabled
- Session-based authentication
- Secure password hashing

## 🛠️ Technologies

- **Backend**: Django 5.0+
- **Trading**: CCXT library
- **Frontend**: Vanilla JavaScript, CSS
- **Database**: SQLite (default)
- **API**: Binance REST API

## 📄 License

This project is for educational and personal use.

## ⚠️ Disclaimer

Cryptocurrency trading carries risk. This software is provided as-is without any guarantees. Always test with small amounts first and never invest more than you can afford to lose.
