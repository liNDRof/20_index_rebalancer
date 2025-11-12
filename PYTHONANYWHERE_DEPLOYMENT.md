# PythonAnywhere Deployment Guide

## 🚀 Your App Now Works for EVERYONE!

Your crypto index rebalancer now supports:
- 🇺🇸 **US users** via Binance.US
- 🌍 **International users** via Binance.com
- 🧪 **Testnet** for development
- 🔒 **Proxy** for advanced users

---

## Step-by-Step Deployment on PythonAnywhere

### Step 1: Upload Your Code

```bash
# On PythonAnywhere Bash console:
cd ~
git clone <your-repo-url> 20_index_rebalancer
# OR upload files manually via Files tab
```

### Step 2: Create Virtual Environment

```bash
cd ~/20_index_rebalancer
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install django python-binance requests python-dotenv pysocks cryptography
```

**Important:** Install `pysocks` for proxy support!

### Step 4: Configure Environment Variables

Create `.env` file in your project root:

```bash
nano ~/20_index_rebalancer/.env
```

Add:
```env
SECRET_KEY=your-django-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-username.pythonanywhere.com
DATABASE_URL=sqlite:///db.sqlite3

# Optional - if you want default values
BINANCE_API_KEY=
BINANCE_API_SECRET=
CMC_API_KEY=
```

Save with `Ctrl+X`, then `Y`, then `Enter`.

### Step 5: Run Migrations

```bash
source ~/20_index_rebalancer/venv/bin/activate
cd ~/20_index_rebalancer
python manage.py migrate
```

You should see:
```
Applying dashboard.0006_userprofile_proxy_host_and_more... OK
Applying dashboard.0007_userprofile_binance_exchange... OK
```

### Step 6: Create Superuser

```bash
python manage.py createsuperuser
```

Follow prompts to create your admin account.

### Step 7: Collect Static Files

```bash
python manage.py collectstatic --noinput
```

### Step 8: Configure Web App on PythonAnywhere

1. Go to **Web** tab
2. Click **Add a new web app**
3. Choose **Manual configuration** (not Django wizard)
4. Choose **Python 3.10** (or your Python version)

#### Configure Source Code:

- **Source code**: `/home/your-username/20_index_rebalancer`
- **Working directory**: `/home/your-username/20_index_rebalancer`

#### Configure Virtualenv:

- **Virtualenv**: `/home/your-username/20_index_rebalancer/venv`

#### Configure WSGI File:

Click on the WSGI configuration file link and replace contents with:

```python
import os
import sys

# Add your project directory to the sys.path
path = '/home/your-username/20_index_rebalancer'
if path not in sys.path:
    sys.path.insert(0, path)

# Set environment variable for Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'crypto_trader.settings'

# Activate virtualenv
activate_this = '/home/your-username/20_index_rebalancer/venv/bin/activate_this.py'
# Note: activate_this.py may not exist in newer Python versions, so check first
try:
    with open(activate_this) as f:
        exec(f.read(), {'__file__': activate_this})
except FileNotFoundError:
    pass

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

**Replace `your-username` with your actual PythonAnywhere username!**

#### Configure Static Files:

In the **Static files** section, add:

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/your-username/20_index_rebalancer/staticfiles` |
| `/media/` | `/home/your-username/20_index_rebalancer/media` |

### Step 9: Reload Web App

Click the green **Reload** button at the top.

---

## 🌍 Configure for Your Location

### Option A: US Resident on ANY PythonAnywhere Cluster ✅

1. Visit `https://your-username.pythonanywhere.com`
2. Log in with your superuser account
3. Go to **Profile**
4. Add your **Binance.US API keys** (from https://www.binance.us/)
5. Go to **Trading Settings**
6. Select **"🇺🇸 Binance.US (United States only)"**
7. Save settings
8. Done! ✅

**No proxy needed! Works on both US and EU clusters!**

---

### Option B: International User on EU Cluster (eu.pythonanywhere.com) ✅

1. Visit `https://your-username.eu.pythonanywhere.com`
2. Log in
3. Go to **Profile**
4. Add your **Binance.com API keys**
5. Go to **Trading Settings**
6. Select **"🌍 Binance.com (International)"**
7. Save settings
8. Done! ✅

**No proxy needed!**

---

### Option C: International User on US Cluster (www.pythonanywhere.com)

#### Recommended: Migrate to EU Cluster

1. Email: **support@pythonanywhere.com**
2. Subject: "Request to migrate to EU cluster"
3. Body:
   ```
   Hi,

   I would like to migrate my PythonAnywhere account to the EU cluster
   (eu.pythonanywhere.com) because my application needs to access Binance.com
   API which blocks US IP addresses.

   Username: your-username

   Thank you!
   ```
4. Wait for migration (usually a few hours)
5. Follow **Option B** above

#### Alternative: Use Proxy (Advanced)

If you can't migrate to EU cluster:

1. **Set up a proxy server** (see BINANCE_GEO_RESTRICTION_FIX.md)
2. In **Trading Settings**:
   - Select **"🌍 Binance.com (International)"**
   - Check **"🔒 Use SOCKS5 Proxy"**
   - Enter proxy details
   - Save settings

---

### Option D: Testing/Development (Any Location) 🧪

1. Go to https://testnet.binance.vision/
2. Log in with GitHub
3. Generate testnet API keys
4. In your app:
   - Go to **Profile** → Enter **testnet API keys**
   - Go to **Trading Settings** → Check **"🧪 Use Binance Testnet"**
   - Save settings
5. Test with fake money!

---

## 🔍 How to Check Your PythonAnywhere Cluster

Run in PythonAnywhere Bash console:

```bash
# Check your location
curl ipinfo.io

# Test Binance.com access
curl https://api.binance.com/api/v3/ping

# Test Binance.US access
curl https://api.binance.us/api/v3/ping
```

**If Binance.com is blocked:**
- You're on US cluster
- Use Binance.US (if US resident) OR migrate to EU cluster

---

## 🐛 Troubleshooting

### "Service unavailable from a restricted location"

**For US users:**
- ✅ Make sure you selected "Binance.US" in Trading Settings
- ✅ Make sure you're using Binance.US API keys (not Binance.com keys)

**For international users:**
- ✅ Make sure you selected "Binance.com" in Trading Settings
- ✅ Check your PythonAnywhere cluster location
- ✅ If on US cluster, migrate to EU or use proxy

### Web app not loading

```bash
# Check error logs in PythonAnywhere Web tab
# Look at Error log and Server log

# Common issues:
# 1. Wrong virtualenv path
# 2. Wrong WSGI configuration
# 3. Missing dependencies
# 4. Database not migrated
```

### Static files not loading

```bash
# Make sure you ran collectstatic
python manage.py collectstatic --noinput

# Check static files mapping in Web tab
# URL: /static/
# Directory: /home/your-username/20_index_rebalancer/staticfiles
```

### "No module named 'binance'"

```bash
# Install in correct virtualenv
source ~/20_index_rebalancer/venv/bin/activate
pip install python-binance pysocks
```

---

## 📊 Running Background Tasks (Scheduled Rebalancing)

PythonAnywhere doesn't allow long-running processes in web apps. For scheduled rebalancing:

### Option 1: Scheduled Tasks (Paid accounts only)

1. Go to **Tasks** tab
2. Create new scheduled task
3. Command: `/home/your-username/20_index_rebalancer/venv/bin/python /home/your-username/20_index_rebalancer/manage.py your_rebalance_command`
4. Set schedule (daily, hourly, etc.)

### Option 2: Manual Rebalancing

- Use the web interface to manually trigger rebalancing
- This works on free accounts

---

## 🔒 Security Best Practices

1. **Never commit `.env` to Git**
   - Add `.env` to `.gitignore`

2. **Use environment variables for secrets**
   - API keys stored encrypted in database
   - Django SECRET_KEY in `.env`

3. **Set DEBUG=False in production**
   - Edit `.env`: `DEBUG=False`

4. **Restrict API key permissions on Binance**
   - Only enable: Read Info, Spot & Margin Trading
   - Disable: Withdrawals

5. **Use IP whitelist on Binance API keys (if possible)**
   - Find PythonAnywhere IP: `curl ifconfig.me`
   - Add to Binance API key restrictions

---

## 🎉 You're Done!

Your crypto index rebalancer is now live and works for users worldwide!

**Test it:**
1. Visit `https://your-username.pythonanywhere.com` (or `.eu.pythonanywhere.com`)
2. Log in
3. Configure your settings
4. Try "Refresh Portfolio"
5. If successful, you're all set! 🚀

---

## 📚 Related Documentation

- Full solution guide: `BINANCE_GEO_RESTRICTION_FIX.md`
- Django commands: `SWEEP.md`
- PythonAnywhere help: https://help.pythonanywhere.com/

---

## 🆘 Need Help?

### Check the server location:
```bash
curl ipinfo.io
```

### Check if Binance works:
```bash
# For Binance.com
curl https://api.binance.com/api/v3/ping

# For Binance.US
curl https://api.binance.us/api/v3/ping

# For Testnet
curl https://testnet.binance.vision/api/v3/ping
```

### View Django logs:
```bash
tail -f ~/20_index_rebalancer/logs/*.log
```

If you need more help, check the PythonAnywhere forums or contact their support!
