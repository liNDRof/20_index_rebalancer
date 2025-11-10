# PythonAnywhere Deployment Guide for Crypto Index Rebalancer

This guide will walk you through deploying your Django crypto trading application to PythonAnywhere.

## Prerequisites

- A PythonAnywhere account (Free or Paid)
- Git repository with your code (GitHub, GitLab, or Bitbucket)
- Stripe account for payments
- Binance API credentials (for your users)

---

## Step-by-Step Deployment

### 1. Sign Up for PythonAnywhere

1. Go to [www.pythonanywhere.com](https://www.pythonanywhere.com)
2. Sign up for an account (choose the username `CryptoIndex` or update all references to your chosen username)
3. Choose a plan:
   - **Free tier**: Good for testing (limited to HTTP, no HTTPS)
   - **Paid tier**: Required for HTTPS and custom domains (Recommended for production with Stripe)

### 2. Upload Your Code to PythonAnywhere

#### Option A: Using Git (Recommended)

1. Open a **Bash console** in PythonAnywhere (Consoles tab → Bash)

2. Clone your repository:
```bash
cd ~
git clone https://github.com/yourusername/yourrepo.git 20_index_rebalancer
cd 20_index_rebalancer
```

#### Option B: Upload Files Manually

1. Go to the **Files** tab
2. Create directory: `20_index_rebalancer`
3. Upload all your project files

### 3. Set Up Virtual Environment

In the Bash console:

```bash
cd ~/20_index_rebalancer

# Create virtual environment with Python 3.10 (or your preferred version)
mkvirtualenv --python=/usr/bin/python3.10 crypto_env

# Activate it (should happen automatically)
workon crypto_env

# Install dependencies
pip install -r requirements.txt
```

### 4. Configure Environment Variables

1. Create a `.env` file in your project directory:

```bash
cd ~/20_index_rebalancer
nano .env
```

2. Add the following content (replace with your actual values):

```env
# Django Settings
SECRET_KEY=your-super-secret-key-here-generate-a-new-one
DEBUG=False

# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_live_your_publishable_key
STRIPE_SECRET_KEY=sk_live_your_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
STRIPE_PRICE_ID=price_your_monthly_price_id

# Domain Configuration
DOMAIN=https://CryptoIndex.pythonanywhere.com
```

3. Save and exit (Ctrl+X, then Y, then Enter)

**Important:** Generate a new SECRET_KEY using this Python command:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Set Up the Database

Run migrations to create your database:

```bash
cd ~/20_index_rebalancer
python manage.py migrate
```

Create a superuser account:

```bash
python manage.py createsuperuser
```

Follow the prompts to create your admin account.

### 6. Collect Static Files

Collect all static files into the `staticfiles` directory:

```bash
python manage.py collectstatic --noinput
```

### 7. Configure the Web App

1. Go to the **Web** tab in PythonAnywhere
2. Click **"Add a new web app"**
3. Choose **"Manual configuration"** (NOT Django wizard)
4. Select **Python 3.10** (or your preferred version)

### 8. Configure WSGI File

1. In the **Web** tab, scroll to the **Code** section
2. Click on the **WSGI configuration file** link
3. Delete all the existing content
4. Copy the content from `pythonanywhere_wsgi.py` in your project
5. **Important:** Replace `CryptoIndex` with your actual PythonAnywhere username
6. Save the file

The WSGI file should look like this:

```python
import os
import sys

# Add your project directory to the sys.path
project_home = '/home/CryptoIndex/20_index_rebalancer'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variable to use production settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'crypto_trader.settings_production'

# Load environment variables from .env file
from pathlib import Path
env_file = Path(project_home) / '.env'
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

# Import Django application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 9. Configure Virtual Environment

1. In the **Web** tab, scroll to the **Virtualenv** section
2. Enter the path to your virtual environment:
```
/home/CryptoIndex/.virtualenvs/crypto_env
```
(Replace `CryptoIndex` with your username)

### 10. Configure Static Files

1. In the **Web** tab, scroll to the **Static files** section
2. Add a new static files mapping:
   - **URL**: `/static/`
   - **Directory**: `/home/CryptoIndex/20_index_rebalancer/staticfiles`

3. Add another mapping for media files:
   - **URL**: `/media/`
   - **Directory**: `/home/CryptoIndex/20_index_rebalancer/media`

(Replace `CryptoIndex` with your username)

### 11. Reload Your Web App

1. Scroll to the top of the **Web** tab
2. Click the big green **"Reload"** button
3. Wait a few seconds for the app to reload

### 12. Test Your Application

1. Visit your site: `https://yourusername.pythonanywhere.com`
2. Test the following:
   - Homepage loads correctly
   - Login functionality works
   - Admin panel works (`/admin/`)
   - User registration
   - Trial activation
   - Stripe payment integration

### 13. Configure Stripe Webhooks

1. Go to your [Stripe Dashboard](https://dashboard.stripe.com)
2. Navigate to **Developers** → **Webhooks**
3. Click **"Add endpoint"**
4. Enter your webhook URL:
```
https://yourusername.pythonanywhere.com/subscription/webhook/
```
5. Select events to listen to:
   - `checkout.session.completed`
   - `invoice.paid`
   - `invoice.payment_failed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
6. Copy the **Signing secret** and add it to your `.env` file as `STRIPE_WEBHOOK_SECRET`
7. Reload your web app

---

## Important Production Checklist

- [ ] **SECRET_KEY**: Generated a new random secret key
- [ ] **DEBUG**: Set to `False` in `.env`
- [ ] **ALLOWED_HOSTS**: Configured in `settings_production.py`
- [ ] **Database**: Migrations applied and superuser created
- [ ] **Static files**: Collected successfully
- [ ] **Stripe keys**: Using LIVE keys (not test keys)
- [ ] **Stripe webhooks**: Configured and tested
- [ ] **.env file**: Created with all required variables
- [ ] **HTTPS**: Enabled (requires paid PythonAnywhere account)
- [ ] **Binance API**: Users enter their own API keys (not hardcoded)

---

## Updating Your Application

When you need to update your code:

1. Open a Bash console:
```bash
cd ~/20_index_rebalancer
git pull origin main  # or your branch name
```

2. Activate virtual environment and update dependencies:
```bash
workon crypto_env
pip install -r requirements.txt --upgrade
```

3. Run migrations if models changed:
```bash
python manage.py migrate
```

4. Collect static files if they changed:
```bash
python manage.py collectstatic --noinput
```

5. Reload the web app from the **Web** tab

---

## Troubleshooting

### Check Error Logs

1. Go to the **Web** tab
2. Scroll to **Log files** section
3. Check:
   - **Error log**: Shows Python errors
   - **Server log**: Shows request logs

### Common Issues

**Issue: "DisallowedHost" error**
- Solution: Check `ALLOWED_HOSTS` in `settings_production.py`

**Issue: Static files not loading**
- Solution: Run `python manage.py collectstatic` and check static files mapping

**Issue: Database errors**
- Solution: Run `python manage.py migrate` again

**Issue: ModuleNotFoundError**
- Solution: Activate virtual environment and reinstall requirements

**Issue: 500 Internal Server Error**
- Solution: Check error logs, ensure `.env` file exists with all variables

### View Real-time Logs

In a Bash console:
```bash
tail -f /var/log/yourusername.pythonanywhere.com.error.log
```

---

## Security Best Practices

1. **Never commit sensitive data**:
   - `.env` file is in `.gitignore`
   - Don't hardcode API keys in code

2. **Use environment variables** for all sensitive configuration

3. **Regular backups**:
   - Backup your database regularly
   - Download `db.sqlite3` from Files tab

4. **Monitor logs** regularly for suspicious activity

5. **Keep dependencies updated**:
```bash
pip list --outdated
pip install --upgrade package-name
```

6. **Use HTTPS** (requires paid account):
   - Essential for Stripe payments
   - Protects user data

---

## Free Tier Limitations

If using the free tier, be aware:
- ✅ Can run Django applications
- ✅ Can use SQLite database
- ❌ **No HTTPS** (HTTP only)
- ❌ **Limited CPU/bandwidth**
- ❌ **App sleeps after inactivity**
- ❌ **Cannot use Stripe** (requires HTTPS)

**Recommendation**: Use a paid plan ($5/month minimum) for production with Stripe.

---

## Support

- **PythonAnywhere Help**: [help.pythonanywhere.com](https://help.pythonanywhere.com)
- **PythonAnywhere Forums**: [www.pythonanywhere.com/forums](https://www.pythonanywhere.com/forums)
- **Django Documentation**: [docs.djangoproject.com](https://docs.djangoproject.com)

---

## Next Steps After Deployment

1. **Test thoroughly** in production
2. **Set up monitoring** (optional: use services like Sentry)
3. **Configure backup strategy**
4. **Set up custom domain** (optional, requires paid account)
5. **Enable automated tasks** for rebalancing (use PythonAnywhere scheduled tasks)

---

## Scheduled Tasks (Optional)

PythonAnywhere allows you to schedule tasks. For example, to run rebalancing automatically:

1. Go to **Tasks** tab
2. Add a new scheduled task
3. Set the time and command:
```bash
cd /home/CryptoIndex/20_index_rebalancer && /home/CryptoIndex/.virtualenvs/crypto_env/bin/python manage.py your_management_command
```

---

Good luck with your deployment! 🚀
