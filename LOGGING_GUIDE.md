# Comprehensive Logging System Guide

## Overview

This crypto trading system now has a **comprehensive multi-file logging system** that tracks every aspect of the application. You will **always know where mistakes happen** by checking the appropriate log files.

## 🎯 Log Files Location

All logs are stored in: `/home/kali/PyCharmMiscProject/20_index_rebalancer/logs/`

The system creates **8 specialized log files**:

### 1. **general.log** - General Application Logs
- Application startup/shutdown
- General information messages
- System initialization

**Example:**
```
2025-11-04 10:15:23 [    INFO] general - ================================================================================
2025-11-04 10:15:23 [    INFO] general - LOGGING SYSTEM INITIALIZED
2025-11-04 10:15:23 [    INFO] general - Log directory: /home/kali/PyCharmMiscProject/20_index_rebalancer/logs
2025-11-04 10:15:23 [    INFO] general - ================================================================================
```

### 2. **api.log** - API Communication
- All Binance API calls
- CoinMarketCap API requests
- API responses and status codes
- Portfolio fetches

**Example:**
```
2025-11-04 10:16:45 [    INFO] api - Fetching all Binance balances...
2025-11-04 10:16:46 [    INFO] api - Successfully fetched balances: 5 assets, total=$1234.56
2025-11-04 10:17:00 [    INFO] api - Fetching CMC Top 20 allocation data...
2025-11-04 10:17:01 [   DEBUG] api - Calling CoinMarketCap API: https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest
2025-11-04 10:17:02 [    INFO] api - CMC allocation calculated: BTC=52.30%, ETH=47.70%
```

### 3. **trades.log** - All Trading Operations
- Manual rebalances
- Automatic rebalances
- Market orders (BUY/SELL)
- Convert operations
- Order confirmations
- Trade results

**Example:**
```
2025-11-04 10:20:15 [    INFO] trades - ================================================================================
2025-11-04 10:20:15 [    INFO] trades - [username] MANUAL REBALANCE STARTED
2025-11-04 10:20:15 [    INFO] trades - ================================================================================
2025-11-04 10:20:16 [    INFO] trades - [username] Step 1: Creating trader instance...
2025-11-04 10:20:16 [    INFO] trades - [username] ✓ Trader instance created
2025-11-04 10:20:17 [    INFO] trades - ============================================================
2025-11-04 10:20:17 [    INFO] trades - MARKET ORDER: BUY 0.01500000 BTC for USDC
2025-11-04 10:20:17 [    INFO] trades - Dry run: False
2025-11-04 10:20:18 [    INFO] trades - ✅ Order executed successfully: 12345678
2025-11-04 10:20:18 [    INFO] trades -   Executed quantity: 0.01500000 BTC
2025-11-04 10:20:18 [    INFO] trades -   Quote quantity: 500.00 USDC
2025-11-04 10:20:18 [    INFO] trades - ============================================================
```

### 4. **errors.log** - All Errors and Exceptions
- All exceptions with full traceback
- API errors
- Database errors
- Missing credentials
- Failed operations

**Example:**
```
2025-11-04 10:25:30 [   ERROR] errors - ==========================================================================
2025-11-04 10:25:30 [   ERROR] errors - UNHANDLED EXCEPTION
2025-11-04 10:25:30 [   ERROR] errors - ==========================================================================
2025-11-04 10:25:30 [   ERROR] errors - Exception Type: BinanceAPIException
2025-11-04 10:25:30 [   ERROR] errors - Exception Message: APIError(code=-1121): Invalid symbol
2025-11-04 10:25:30 [   ERROR] errors - Request: POST /en/manual_rebalance/
2025-11-04 10:25:30 [   ERROR] errors - User: testuser
2025-11-04 10:25:30 [   ERROR] errors - IP: 127.0.0.1
2025-11-04 10:25:30 [   ERROR] errors - ==========================================================================
2025-11-04 10:25:30 [   ERROR] errors - Traceback:
Traceback (most recent call last):
  File "/path/to/trader.py", line 123, in execute_market_order
    order = self.client.order_market_buy(symbol=pair, quantity=quantity)
binance.exceptions.BinanceAPIException: APIError(code=-1121): Invalid symbol
2025-11-04 10:25:30 [   ERROR] errors - ==========================================================================
```

### 5. **requests.log** - HTTP Request Tracking
- All HTTP requests (method, path, user, IP)
- Response status codes
- Request duration
- Success/failure status

**Example:**
```
2025-11-04 10:30:00 [    INFO] requests - >>> REQUEST | GET /en/status/ | User: testuser | IP: 127.0.0.1
2025-11-04 10:30:00 [    INFO] requests - <<< RESPONSE | GET /en/status/ | User: testuser | Status: 200 (SUCCESS) | Duration: 0.125s
2025-11-04 10:30:15 [    INFO] requests - >>> REQUEST | POST /en/manual_rebalance/ | User: testuser | IP: 127.0.0.1
2025-11-04 10:30:18 [    INFO] requests - <<< RESPONSE | POST /en/manual_rebalance/ | User: testuser | Status: 200 (SUCCESS) | Duration: 3.245s
```

### 6. **performance.log** - Slow Request Warnings
- Requests taking longer than 2 seconds
- Performance bottlenecks
- Slow API calls

**Example:**
```
2025-11-04 10:35:00 [WARNING] performance - ⚠️  SLOW REQUEST | POST /en/manual_rebalance/ | User: testuser | Duration: 5.234s | Status: 200 | Threshold: 2.0s
```

### 7. **user_activity.log** - User Actions
- Login/Logout
- Registration
- Profile changes
- Trading operations
- Timer settings

**Example:**
```
2025-11-04 10:40:00 [    INFO] user_activity - 👤 USER ACTIVITY | User: testuser | Action: POST /en/login/ | IP: 127.0.0.1
2025-11-04 10:40:15 [    INFO] user_activity - 👤 USER ACTIVITY | User: testuser | Action: POST /en/profile/ | IP: 127.0.0.1
2025-11-04 10:40:30 [    INFO] user_activity - 👤 USER ACTIVITY | User: testuser | Action: POST /en/manual_rebalance/ | IP: 127.0.0.1
```

### 8. **debug.log** - Detailed Debug Information
- Detailed variable values
- Function entry/exit
- Request/response bodies
- Internal state changes

**Example:**
```
2025-11-04 10:45:00 [   DEBUG] debug [views.py:202] - Initializing BTCETH_CMC20_Trader...
2025-11-04 10:45:00 [   DEBUG] debug [views.py:225] - Creating Binance client...
2025-11-04 10:45:00 [   DEBUG] debug [views.py:227] - Binance client created successfully
2025-11-04 10:45:00 [   DEBUG] debug [views.py:235] - Trader initialized with update_interval=3600s, stablecoins=11
2025-11-04 10:45:01 [   DEBUG] debug [views.py:312] - Balance details: {'BTC': {'free': 0.015, 'locked': 0.0, 'total': 0.015, 'usdc_value': 500.0}, ...}
```

---

## 🔍 How to Use the Logs to Find Mistakes

### Problem: Portfolio Not Loading

**Check these logs in order:**
1. **browser console** (F12) - Look for JavaScript errors
2. **requests.log** - Verify request was made and response status
3. **api.log** - Check if Binance API call succeeded
4. **errors.log** - Look for any exceptions
5. **debug.log** - See detailed data flow

**Example Investigation:**
```bash
# 1. Check if request was made
tail -f logs/requests.log | grep "refresh_portfolio"

# 2. Check API calls
tail -f logs/api.log | grep "Binance"

# 3. Check for errors
tail -f logs/errors.log
```

### Problem: Trading Operation Failed

**Check these logs:**
1. **trades.log** - See complete trade execution flow
2. **errors.log** - Look for Binance API errors
3. **api.log** - Check API communication

**Example Investigation:**
```bash
# See recent trades
tail -n 100 logs/trades.log

# Filter by username
grep "username" logs/trades.log

# Check for failed orders
grep "ERROR" logs/trades.log
```

### Problem: Slow Performance

**Check:**
1. **performance.log** - Identify slow requests
2. **requests.log** - See request durations

**Example:**
```bash
# See all slow requests
cat logs/performance.log

# Monitor performance in real-time
tail -f logs/performance.log
```

### Problem: User Can't Login

**Check:**
1. **user_activity.log** - See login attempts
2. **errors.log** - Check for authentication errors
3. **requests.log** - Verify login request received

---

## 📊 Log File Features

### Automatic Rotation
- Each log file has a **maximum size of 10MB** (20MB for debug.log)
- When limit reached, file is renamed to `.log.1`, `.log.2`, etc.
- System keeps **5 backup files** (10 for trades and errors)
- Old backups are automatically deleted

### Example:
```
logs/
├── trades.log          (current, 8MB)
├── trades.log.1        (10MB, previous)
├── trades.log.2        (10MB, older)
├── trades.log.3        (10MB, older)
└── trades.log.4        (10MB, oldest)
```

### Console Output
Some logs are also displayed in the Django server console:
- **general.log** - All messages
- **api.log** - All messages
- **trades.log** - All messages
- **errors.log** - Errors and warnings

---

## 🛠️ Useful Commands

### Real-time Monitoring

```bash
# Monitor all errors
tail -f logs/errors.log

# Monitor trades
tail -f logs/trades.log

# Monitor API calls
tail -f logs/api.log

# Monitor specific user
tail -f logs/user_activity.log | grep "username"

# Monitor multiple files
tail -f logs/trades.log logs/errors.log
```

### Search Logs

```bash
# Find all errors today
grep "$(date +%Y-%m-%d)" logs/errors.log

# Find specific error message
grep -i "binance api" logs/errors.log

# Find user activity
grep "testuser" logs/user_activity.log

# Find slow requests
grep "SLOW REQUEST" logs/performance.log

# Search all logs
grep -r "error keyword" logs/
```

### Analyze Logs

```bash
# Count errors
grep "ERROR" logs/errors.log | wc -l

# Count trades today
grep "$(date +%Y-%m-%d)" logs/trades.log | grep "MARKET ORDER" | wc -l

# See most active users
grep "USER ACTIVITY" logs/user_activity.log | cut -d'|' -f2 | sort | uniq -c | sort -rn

# Average request duration (requires awk)
grep "RESPONSE" logs/requests.log | grep -oP "Duration: \K[0-9.]+" | awk '{sum+=$1; count++} END {print sum/count "s"}'
```

### Clear Old Logs

```bash
# Clear all logs (use with caution!)
rm logs/*.log

# Clear only debug logs
rm logs/debug.log*

# Archive logs before clearing
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
rm logs/*.log
```

---

## 🎨 Log Format

All logs follow this format:
```
YYYY-MM-DD HH:MM:SS [LEVEL   ] logger_name - message
```

**Example:**
```
2025-11-04 10:15:23 [    INFO] general - Application started
2025-11-04 10:15:24 [   DEBUG] debug - Processing request
2025-11-04 10:15:25 [ WARNING] errors - Slow query detected
2025-11-04 10:15:26 [   ERROR] errors - Database connection failed
```

**Log Levels:**
- **DEBUG** - Detailed diagnostic information
- **INFO** - Informational messages
- **WARNING** - Warning messages (potential issues)
- **ERROR** - Error messages (something failed)

---

## 🚀 Quick Troubleshooting Guide

### Issue: "Portfolio not loading"
1. Check browser console: `F12 → Console`
2. Check: `tail -f logs/api.log | grep "balances"`
3. Check: `tail logs/errors.log`

### Issue: "Trade failed"
1. Check: `tail logs/trades.log`
2. Look for: `ERROR` or `failed`
3. Check: `tail logs/errors.log`

### Issue: "Page is slow"
1. Check: `cat logs/performance.log`
2. Look for: `SLOW REQUEST`
3. Check duration in: `logs/requests.log`

### Issue: "Can't login"
1. Check: `tail logs/user_activity.log`
2. Check: `grep "login" logs/errors.log`
3. Check: `grep "login" logs/requests.log`

### Issue: "API error"
1. Check: `tail logs/api.log`
2. Check: `grep "Binance" logs/errors.log`
3. Check credentials in profile

---

## 📝 Best Practices

1. **Monitor logs regularly** - Check `errors.log` daily
2. **Archive old logs** - Compress and backup monthly
3. **Use grep effectively** - Search for specific issues
4. **Check multiple logs** - Issues may span multiple log files
5. **Keep logs secure** - Contains sensitive operation data

---

## 🔧 Configuration

Logging is configured in: `crypto_trader/logging_config.py`

### Adjust Log Levels

Edit `logging_config.py` to change log levels:

```python
# Make debug logs more verbose
debug_logger.setLevel(logging.DEBUG)

# Reduce API logging
api_logger.setLevel(logging.WARNING)
```

### Adjust File Sizes

```python
# Increase max log file size to 50MB
api_handler = RotatingFileHandler(
    log_dir / 'api.log',
    maxBytes=50*1024*1024,  # 50MB instead of 10MB
    backupCount=10  # Keep 10 backups instead of 5
)
```

### Disable Console Output

Remove console handlers if you don't want console output:

```python
# Remove this line to disable console output
general_logger.addHandler(console_handler)
```

---

## 📞 Support

If you can't find the issue in logs:
1. Copy the relevant log section
2. Include timestamp and username
3. Include the error message from `errors.log`
4. Include the trade details from `trades.log` if applicable

**With this logging system, you will ALWAYS know where mistakes happen!** 🎯
