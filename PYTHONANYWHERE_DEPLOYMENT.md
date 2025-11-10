# Semi-Automated PythonAnywhere Deployment Guide

This guide will help you deploy your Django application to PythonAnywhere with **semi-automation**.

## Why "Semi-Automated"?

While I've provided automation scripts, certain steps still require your manual intervention because:
1. Security: You need to provide credentials securely
2. Initial setup: Some one-time configurations need manual verification
3. API limitations: PythonAnywhere's API doesn't expose all features

## Prerequisites

✅ PythonAnywhere account (Hacker plan or higher for SSH/custom domains)
✅ GitHub repository with your code
✅ PythonAnywhere API token
✅ Basic command line knowledge

---

## Method 1: Using the Automated Deployment Script (Recommended)

### Step 1: Get Your PythonAnywhere API Token

1. Log into PythonAnywhere
2. Go to: **Account** → **API Token** tab
3. Click **"Create a new API token"**
4. Copy the token (you'll need it in the next step)

### Step 2: Configure Your Deployment

1. **Copy the environment file:**
   ```bash
   cp .env.pythonanywhere.example .env.pythonanywhere
   ```

2. **Edit `.env.pythonanywhere`** with your actual values:
   ```bash
   nano .env.pythonanywhere
   ```

   Fill in:
   - `PYTHONANYWHERE_USERNAME`: Your PythonAnywhere username
   - `PYTHONANYWHERE_API_TOKEN`: The token you just created
   - `PYTHONANYWHERE_DOMAIN`: Your domain (e.g., `username.pythonanywhere.com`)
   - `GITHUB_REPO_URL`: Your GitHub repository URL

### Step 3: Install Dependencies

```bash
pip install requests python-dotenv
```

### Step 4: Run the Deployment Script

```bash
python deploy_to_pythonanywhere.py
```

The script will:
- ✓ Create/update your webapp
- ✓ Clone your code from GitHub
- ✓ Set up virtual environment
- ✓ Install dependencies
- ✓ Run migrations
- ✓ Collect static files
- ✓ Configure and reload your app

### Step 5: Manual Configuration (Required)

Even with the script, you need to **manually** configure the WSGI file:

1. Go to PythonAnywhere **Web** tab
2. Click on your webapp
3. Click the **WSGI configuration file** link
4. Replace the contents with:

```python
import os
import sys

# Add your project directory to the sys.path
project_home = '/home/YOUR_USERNAME/20_index_rebalancer'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['DJANGO_SETTINGS_MODULE'] = 'crypto_trader.settings'

# Load environment variables from .env file
from pathlib import Path
env_file = Path(project_home) / '.env'
if env_file.exists():
    from dotenv import load_dotenv
    load_dotenv(env_file)

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

5. Replace `YOUR_USERNAME` with your actual username
6. Click **Save**
7. Click **Reload** button at the top

---

## Method 2: Manual Deployment (Full Control)

If you prefer full manual control, follow the guide in `DEPLOYMENT_GUIDE.md`.

---

## Post-Deployment Checklist

After deployment (automated or manual), verify:

- [ ] Navigate to your site URL - does it load?
- [ ] Test the admin panel: `https://yourdomain.com/admin/`
- [ ] Check the **Logs** section in PythonAnywhere Web tab for errors
- [ ] Test key functionality of your application

---

## Updating Your Deployed Application

For subsequent updates after initial deployment:

### Using the script:
```bash
python deploy_to_pythonanywhere.py
```

### Manually:
1. SSH into PythonAnywhere or use Bash console
2. Run:
   ```bash
   cd ~/20_index_rebalancer
   git pull
   source venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```
3. Click **Reload** in the Web tab

---

## Troubleshooting

### Error: "Invalid API token"
- Regenerate your API token on PythonAnywhere
- Update `.env.pythonanywhere`

### Error: "ModuleNotFoundError"
- Check that virtualenv path is correctly set in Web tab
- Ensure all requirements are installed

### Static files not loading
- Verify static files mapping in Web tab
- Check that `STATIC_ROOT` in settings.py matches the path

### Database errors
- Ensure migrations have run: `python manage.py migrate`
- Check database credentials in `.env`

### "DisallowedHost" error
- Add your domain to `ALLOWED_HOSTS` in `settings.py`

---

## Environment Variables on PythonAnywhere

Create a `.env` file in your project directory on PythonAnywhere:

```bash
# In PythonAnywhere Bash console:
cd ~/20_index_rebalancer
nano .env
```

Add your environment variables:
```
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourusername.pythonanywhere.com

# Database
DATABASE_URL=your-database-url

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Add other variables as needed
```

---

## Security Best Practices

1. ✅ **Never commit** `.env` or `.env.pythonanywhere` to Git
2. ✅ Use **strong, unique** SECRET_KEY
3. ✅ Set `DEBUG=False` in production
4. ✅ Use HTTPS (comes free with PythonAnywhere)
5. ✅ Regularly update dependencies
6. ✅ Keep API tokens secure

---

## Cost Considerations

- **Free tier**: Limited, HTTP only, no SSH
- **Hacker ($5/month)**:
  - HTTPS
  - SSH access
  - Custom domains
  - More CPU time
- **Web Dev ($12/month)**: Increased resources

**Recommendation**: Start with Hacker plan for production apps.

---

## Need Help?

- PythonAnywhere Forums: https://www.pythonanywhere.com/forums/
- PythonAnywhere Help: https://help.pythonanywhere.com/
- Check error logs in Web tab → Logs section

---

## What's Automated vs. Manual

### ✅ Automated (via script):
- Creating webapp
- Cloning/updating code
- Setting up virtualenv
- Installing dependencies
- Running migrations
- Collecting static files
- Reloading webapp

### ⚠️ Still Manual:
- Getting API token
- Editing WSGI configuration file
- Setting environment variables
- Initial domain/SSL setup
- Stripe webhook configuration

---

Good luck with your deployment! 🚀
