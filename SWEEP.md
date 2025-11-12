# Crypto Index Rebalancer - Development Guide

## Project Setup

### Virtual Environment
This project uses the virtual environment located at:
```bash
/home/kali/PycharmProjects/20_index_rebalancer/.venv
```

### Dependencies Installation
Install required Python packages:
```bash
/home/kali/PycharmProjects/20_index_rebalancer/.venv/bin/pip install django python-binance requests python-dotenv pysocks cryptography
```

**Note:** `pysocks` is required for SOCKS5 proxy support (to bypass Binance geographic restrictions).

### System Dependencies
Install GNU gettext tools (required for translations):
```bash
sudo apt-get install -y gettext
```

## Common Commands

### Compile Translation Messages
After updating .po translation files, compile them:
```bash
/home/kali/PycharmProjects/20_index_rebalancer/.venv/bin/python /home/kali/PycharmProjects/20_index_rebalancer/manage.py compilemessages
```

### Run Development Server
Start the Django development server:
```bash
/home/kali/PycharmProjects/20_index_rebalancer/.venv/bin/python /home/kali/PycharmProjects/20_index_rebalancer/manage.py runserver
```

The server will be available at: http://127.0.0.1:8000/

### Make Migrations
```bash
/home/kali/PycharmProjects/20_index_rebalancer/.venv/bin/python /home/kali/PycharmProjects/20_index_rebalancer/manage.py makemigrations
```

### Apply Migrations
```bash
/home/kali/PycharmProjects/20_index_rebalancer/.venv/bin/python /home/kali/PycharmProjects/20_index_rebalancer/manage.py migrate
```

## Translation System

### Supported Languages
- English (en) - Default language
- Ukrainian (uk)

### Translation Files Location
- English: `locale/en/LC_MESSAGES/django.po` → `django.mo`
- Ukrainian: `locale/uk/LC_MESSAGES/django.po` → `django.mo`

### Update Translations
1. Edit the `.po` files in `locale/*/LC_MESSAGES/`
2. Run `compilemessages` command (see above)
3. Restart the Django server

## Binance Geographic Restrictions

### Problem
Binance blocks API access from certain locations (US, China, etc.). The app now supports multiple solutions:

### Solutions Available
1. **Binance.US Support** - For US users, select "Binance.US" in Trading Settings
2. **Testnet Mode** - For testing, use Binance Testnet (no geo restrictions)
3. **SOCKS5 Proxy** - For international users on restricted servers, route through proxy
4. **PythonAnywhere EU Cluster** - Deploy to eu.pythonanywhere.com instead of US cluster

### Documentation
- Complete guide: `BINANCE_GEO_RESTRICTION_FIX.md`
- PythonAnywhere deployment: `PYTHONANYWHERE_DEPLOYMENT.md`

### Configuration
Users can configure connection settings in the dashboard:
- **Trading Settings** → Choose exchange (Binance.com or Binance.US)
- **Trading Settings** → Enable testnet mode
- **Trading Settings** → Configure SOCKS5 proxy

## Notes
- Always compile translation messages after cloning the repository or updating .po files
- The project uses gettext for internationalization (i18n)
- Environment variables are stored in `.env` file

- Database migrations include geo-restriction bypass features (migrations 0006 and 0007)
