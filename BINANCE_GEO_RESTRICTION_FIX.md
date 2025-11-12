# Binance Geographic Restriction - Solutions

## Problem

You're encountering this error:
```
APIError(code=0): Service unavailable from a restricted location according to 'b. Eligibility' in https://www.binance.com/en/terms
```

This occurs because Binance blocks API access from certain geographic regions, including:
- **United States** (except Binance.US)
- **China**
- **Cuba, Iran, Syria, North Korea, Crimea**
- **Ontario, Canada**
- Some **EU locations**

## 🌍 Universal Solution: Works for ALL Users

**Your application now supports BOTH Binance.com AND Binance.US!**

Simply choose your exchange in **Trading Settings**:
- 🇺🇸 **US Residents** → Select "Binance.US"
- 🌍 **International Users** → Select "Binance.com"

The app will automatically connect to the correct API endpoint for your location!

---

## Solutions Implemented

I've implemented **multiple solutions** for you:

### Solution 1: Choose Your Exchange (🆕 NEW - For US Users!) 🇺🇸

**What is it?**
- The app now supports **both Binance.com AND Binance.US**
- You simply select which exchange you want to use in settings
- No code changes needed - it's all automatic!

**How to set it up:**

#### For US Residents (must use Binance.US):

1. **Create Binance.US Account:**
   - Visit https://www.binance.us/
   - Register an account (US residents only)
   - Complete KYC verification

2. **Get Binance.US API Keys:**
   - Go to https://www.binance.us/user/account/api
   - Create new API key
   - Save the API Key and Secret

3. **Configure in Your App:**
   - Go to **Trading Settings** in your dashboard
   - Select **"🇺🇸 Binance.US (United States only)"** from the exchange dropdown
   - Go to **Profile** and enter your **Binance.US API keys**
   - Save settings

4. **That's it!** Your bot will now connect to `api.binance.us`

#### For International Users (use Binance.com):

1. **Keep Binance.com Account:**
   - Your existing Binance.com account works
   - Keep your existing API keys

2. **Configure in Your App:**
   - Go to **Trading Settings** in your dashboard
   - Select **"🌍 Binance.com (International)"** from the exchange dropdown
   - Make sure your Binance.com API keys are in your profile
   - Choose one of the options below (Testnet or Proxy) if needed

**Pros:**
- ✅ Works for BOTH US and international users
- ✅ No proxy or VPN needed
- ✅ Official, compliant solution
- ✅ One-click exchange selection

**Cons:**
- ❌ US users must use Binance.US (different platform than Binance.com)
- ❌ Binance.US has fewer trading pairs than Binance.com
- ❌ Binance.US and Binance.com have separate accounts/funds

**Important Notes:**
- 🇺🇸 US residents **cannot** use Binance.com legally - you must use Binance.US
- 🌍 International users **cannot** access Binance.US - it's US-only
- Each exchange requires **separate API keys** from that specific platform
- You cannot transfer funds between Binance.com and Binance.US

---

### Solution 2: Use Binance Testnet (Recommended for Development/Testing) ✅

**What is it?**
- Binance provides a test environment at `testnet.binance.vision`
- Free to use, no geographic restrictions
- Perfect for development and testing
- Uses fake money (test assets)

**How to set it up:**

1. **Get Testnet API Keys:**
   - Visit https://testnet.binance.vision/
   - Log in with your GitHub account
   - Generate API keys (these are different from production keys!)

2. **Enable Testnet in your application:**
   - Go to **Trading Settings** in your dashboard
   - Check the box **"🧪 Use Binance Testnet"**
   - Enter your **testnet API keys** in your profile
   - Save settings

3. **That's it!** Your bot will now connect to `testnet.binance.vision` instead of production

**Pros:**
- ✅ No geographic restrictions
- ✅ Free to use
- ✅ Safe for testing (no real money)
- ✅ Same API as production

**Cons:**
- ❌ Test assets only (not real trading)
- ❌ Lower liquidity on testnet
- ❌ Some pairs may not work due to lack of orders

---

### Solution 3: Use SOCKS5 Proxy (For International Users on Binance.com) 🔒

**What is it?**
- Routes your API traffic through a server in an **allowed location** (Europe, Asia, etc.)
- Allows you to access production Binance from restricted locations
- Requires a proxy server or VPS

**How to set it up:**

#### Step 1: Get a Proxy Server

**Option A: Rent a VPS and Set Up Your Own Proxy (Recommended)**

1. Rent a VPS in Europe or Asia (e.g., Hetzner, DigitalOcean, Vultr)
   - **Hetzner Cloud**: €4-5/month - https://www.hetzner.com
   - **DigitalOcean**: $6/month - https://www.digitalocean.com
   - **Vultr**: $6/month - https://www.vultr.com
   - Location: Choose **Germany, Netherlands, UK, Singapore, Japan**

2. Install Dante SOCKS5 proxy on Ubuntu/Debian:
   ```bash
   sudo apt update
   sudo apt install dante-server
   ```

3. Configure Dante (`/etc/danted.conf`):
   ```
   logoutput: /var/log/danted.log
   internal: eth0 port = 1080
   external: eth0
   socksmethod: username none

   client pass {
     from: 0.0.0.0/0 to: 0.0.0.0/0
     log: connect disconnect error
   }

   socks pass {
     from: 0.0.0.0/0 to: 0.0.0.0/0
     log: connect disconnect error
   }
   ```

4. Start the proxy:
   ```bash
   sudo systemctl start danted
   sudo systemctl enable danted
   ```

**Option B: Use Commercial Proxy Service**
- proxy-seller.com
- proxyrack.com
- smartproxy.com
- Make sure they support **SOCKS5** protocol

#### Step 2: Configure Proxy in Your Application

1. Go to **Trading Settings** in your dashboard
2. Check the box **"🔒 Use SOCKS5 Proxy"**
3. Enter your proxy details:
   - **Proxy Host**: Your VPS IP or proxy hostname (e.g., `123.45.67.89` or `proxy.example.com`)
   - **Proxy Port**: Typically `1080` for SOCKS5
   - **Username/Password**: If your proxy requires authentication (optional)
4. Save settings

**Pros:**
- ✅ Access production Binance API
- ✅ Real trading with real assets
- ✅ Bypass geographic restrictions

**Cons:**
- ❌ Costs money (VPS or proxy service)
- ❌ Requires setup
- ❌ Adds slight latency

---

## How to Choose?

| Your Situation | Recommended Solution |
|----------------|---------------------|
| 🇺🇸 US Resident | **Select "Binance.US" exchange** |
| 🌍 International User | **Select "Binance.com" exchange** |
| Just testing/developing the bot | **Use Testnet** |
| International user on restricted server (e.g., PythonAnywhere US cluster) | **Use Proxy or migrate to EU cluster** |
| Want to test before real trading | **Use Testnet first, then switch to production** |

### PythonAnywhere-Specific Recommendations:

| PythonAnywhere Cluster | User Location | Solution |
|------------------------|---------------|----------|
| **US Cluster** (www.pythonanywhere.com) | 🇺🇸 US Resident | ✅ Use Binance.US (no proxy needed) |
| **US Cluster** | 🌍 International | ⚠️ Migrate to EU cluster OR use proxy |
| **EU Cluster** (eu.pythonanywhere.com) | 🇺🇸 US Resident | ✅ Use Binance.US (works fine) |
| **EU Cluster** | 🌍 International | ✅ Use Binance.com (no proxy needed) |

---

## Technical Details

### What Changed in the Code?

1. **UserProfile Model** - Added new fields:
   - `binance_exchange` - Select between Binance.com or Binance.US
   - `use_testnet` - Toggle testnet mode
   - `use_proxy` - Toggle proxy usage
   - `proxy_host`, `proxy_port`, `proxy_user`, `proxy_pass_encrypted` - Proxy configuration

2. **Trader Class** - Now accepts:
   - `binance_tld='com'` or `'us'` - Connects to api.binance.com or api.binance.us
   - `use_testnet=True` - Connects to testnet.binance.vision
   - `proxy_config` - Dictionary with proxy settings

3. **Settings UI** - New sections:
   - Exchange selector (Binance.com vs Binance.US)
   - Connection settings with easy toggles
   - Smart UI that shows warnings based on your selection

### Python-Binance Library Support

The `python-binance` library natively supports:
- **Testnet**: `Client(api_key, api_secret, testnet=True)`
- **Proxy**: `Client(api_key, api_secret, requests_params={'proxies': {...}})`

---

## Installation Requirements

If you're using a proxy, you may need to install proxy support:

```bash
pip install requests[socks]
# or
pip install pysocks
```

---

## Testing Your Setup

### Test Testnet Connection:
1. Enable testnet in settings
2. Add testnet API keys
3. Click "Refresh Portfolio" on dashboard
4. You should see your testnet balances

### Test Proxy Connection:
1. Enable proxy in settings
2. Enter proxy details
3. Click "Refresh Portfolio" on dashboard
4. Check logs for "Using SOCKS5 proxy: your.proxy.host:1080"

---

## Troubleshooting

### Still getting geo-restriction error?
- ✅ Make sure you're using the correct API keys (testnet keys for testnet, production keys for production)
- ✅ Verify proxy server is in an **allowed location** (not US, China, etc.)
- ✅ Test proxy connection: `curl -x socks5://host:port https://api.binance.com/api/v3/ping`

### Proxy not working?
- ✅ Check firewall allows port 1080 (or your proxy port)
- ✅ Verify proxy service is running: `sudo systemctl status danted`
- ✅ Check proxy logs: `tail -f /var/log/danted.log`

### Testnet issues?
- ✅ Make sure you have testnet API keys from https://testnet.binance.vision/
- ✅ Some trading pairs may not work due to low liquidity on testnet
- ✅ Stick to major pairs like BTCUSDT for testing

---

## Important Security Notes

⚠️ **API Key Security:**
- Your API keys are encrypted in the database
- Never share your API keys
- Use testnet keys for testing, production keys only for live trading
- Set IP restrictions on your Binance API keys when possible

⚠️ **Proxy Security:**
- Use trusted proxy services only
- Consider setting up your own VPS proxy for better security
- Don't use free public proxies for trading

---

## Support Resources

- **Binance Testnet**: https://testnet.binance.vision/
- **Binance Testnet Docs**: https://github.com/binance/binance-spot-api-docs/blob/master/testnet/README.md
- **Dante SOCKS5 Setup**: https://www.inet.no/dante/
- **Python-Binance Docs**: https://python-binance.readthedocs.io/

---

## Migrations Applied

Database migrations have been created and applied:
- `0006_userprofile_proxy_host_and_more.py` - Proxy and testnet support
- `0007_userprofile_binance_exchange.py` - Binance.com / Binance.US selection

You can now access all the new settings through your dashboard!

---

## Quick Start Guide for Different Users

### 🇺🇸 If You're a US Resident:

```bash
1. Go to Trading Settings
2. Select "🇺🇸 Binance.US (United States only)"
3. Go to Profile and enter your Binance.US API keys
4. Done! You can trade on Binance.US
```

### 🌍 If You're International on PythonAnywhere US Cluster:

```bash
Option A (Recommended):
1. Email support@pythonanywhere.com
2. Request migration to eu.pythonanywhere.com
3. Wait for migration
4. Select "🌍 Binance.com" in Trading Settings
5. Done!

Option B (Stay on US cluster):
1. Set up SOCKS5 proxy in Europe/Asia
2. Enable "Use SOCKS5 Proxy" in Trading Settings
3. Enter proxy details
4. Select "🌍 Binance.com" in Trading Settings
5. Done!
```

### 🌍 If You're International on PythonAnywhere EU Cluster:

```bash
1. Go to Trading Settings
2. Select "🌍 Binance.com (International)"
3. Make sure your Binance.com API keys are in Profile
4. Done! No proxy needed
```

### 🧪 If You're Just Testing:

```bash
1. Get testnet keys from https://testnet.binance.vision/
2. Go to Trading Settings
3. Check "Use Binance Testnet"
4. Enter testnet keys in Profile
5. Done! Test with fake money
```
