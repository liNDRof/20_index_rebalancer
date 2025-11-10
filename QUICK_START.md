# Quick Start Guide - PythonAnywhere Deployment

## TL;DR - Essential Steps

### 1. Push Code to Git
```bash
git add .
git commit -m "Prepare for PythonAnywhere deployment"
git push origin main
```

### 2. On PythonAnywhere - Clone and Setup
```bash
# In PythonAnywhere Bash console
cd ~
git clone YOUR_GIT_REPO_URL 20_index_rebalancer
cd 20_index_rebalancer
mkvirtualenv --python=/usr/bin/python3.10 crypto_env
pip install -r requirements.txt
```

### 3. Create .env File
```bash
nano .env
```

Paste this (replace with your values):
```env
SECRET_KEY=your-generated-secret-key-here
DEBUG=False
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...
DOMAIN=https://CryptoIndex.pythonanywhere.com
```

Generate SECRET_KEY:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Setup Database
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

### 5. Configure Web App

**Web Tab → Add new web app → Manual configuration → Python 3.10**

**WSGI Configuration:**
- Click WSGI config file link
- Delete everything
- Copy content from `pythonanywhere_wsgi.py`
- Replace `CryptoIndex` with YOUR username
- Save

**Virtual Environment:**
- Enter: `/home/YOUR_USERNAME/.virtualenvs/crypto_env`

**Static Files:**
- URL: `/static/` → Directory: `/home/YOUR_USERNAME/20_index_rebalancer/staticfiles`
- URL: `/media/` → Directory: `/home/YOUR_USERNAME/20_index_rebalancer/media`

### 6. Reload and Test

- Click green **Reload** button
- Visit: `https://YOUR_USERNAME.pythonanywhere.com`
- Test login, registration, payments

### 7. Configure Stripe Webhook

- Stripe Dashboard → Developers → Webhooks
- Add endpoint: `https://YOUR_USERNAME.pythonanywhere.com/subscription/webhook/`
- Select events: checkout, invoice, subscription events
- Copy signing secret → Add to .env as STRIPE_WEBHOOK_SECRET
- Reload web app

## Done! 🎉

Your app should now be live at: `https://YOUR_USERNAME.pythonanywhere.com`

---

## Troubleshooting

**Error 500?** → Check error log (Web tab → Log files)

**Static files not loading?** → Run `python manage.py collectstatic` again

**Import errors?** → Check virtual environment is activated: `workon crypto_env`

**Still issues?** → See full `DEPLOYMENT_GUIDE.md`
