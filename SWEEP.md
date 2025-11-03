# Crypto Index Rebalancer - Development Guide

## Project Setup

### Virtual Environment
This project uses the virtual environment located at:
```bash
/home/kali/PyCharmMiscProject/.venv
```

### Dependencies Installation
Install required Python packages:
```bash
/home/kali/PyCharmMiscProject/.venv/bin/pip install django python-binance requests python-dotenv
```

### System Dependencies
Install GNU gettext tools (required for translations):
```bash
sudo apt-get install -y gettext
```

## Common Commands

### Compile Translation Messages
After updating .po translation files, compile them:
```bash
/home/kali/PyCharmMiscProject/.venv/bin/python /home/kali/PyCharmMiscProject/20_index_rebalancer/manage.py compilemessages
```

### Run Development Server
Start the Django development server:
```bash
/home/kali/PyCharmMiscProject/.venv/bin/python /home/kali/PyCharmMiscProject/20_index_rebalancer/manage.py runserver
```

The server will be available at: http://127.0.0.1:8000/

### Make Migrations
```bash
/home/kali/PyCharmMiscProject/.venv/bin/python /home/kali/PyCharmMiscProject/20_index_rebalancer/manage.py makemigrations
```

### Apply Migrations
```bash
/home/kali/PyCharmMiscProject/.venv/bin/python /home/kali/PyCharmMiscProject/20_index_rebalancer/manage.py migrate
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

## Notes
- Always compile translation messages after cloning the repository or updating .po files
- The project uses gettext for internationalization (i18n)
- Environment variables are stored in `.env` file
