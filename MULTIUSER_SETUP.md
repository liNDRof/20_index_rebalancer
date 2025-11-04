# Multi-User Trading System - Setup Guide

## Overview

The system now supports **multiple users simultaneously**, each with their own:
- **Binance API credentials** (encrypted and stored securely)
- **Trading sessions** (independent trader threads)
- **Portfolio data** (separate balances and history)
- **Trade history** (individual transaction records)
- **Settings** (custom rebalance intervals, auto-trading preferences)

## Database Models

### 1. UserProfile
Stores user-specific configuration:
- Encrypted Binance API key and secret (using Fernet encryption)
- Optional CoinMarketCap API key
- Default rebalance interval
- Auto-rebalance toggle

### 2. TraderSession
Tracks active trading sessions per user:
- Running status
- Next/last run times
- Portfolio snapshot
- Last rebalance results
- Dry run mode toggle

### 3. TradeHistory
Records all trading activity:
- Trade type (manual/auto rebalance)
- Dry run flag
- Trade data (JSON)
- Success/error status
- Timestamps

## How It Works

### User Registration & Login

1. **Register**: Users create an account at `/register/`
   - Username, email, and password required
   - Automatically creates UserProfile and TraderSession

2. **Login**: Users authenticate at `/login/`
   - Session-based authentication
   - Redirects to dashboard

3. **Profile Setup**: After registration, users configure API credentials at `/profile/`
   - Enter Binance API key and secret (encrypted before storage)
   - Set default rebalance interval
   - Enable/disable auto-rebalancing

### Trading Flow

1. **Dashboard Access**: Each user sees only their own data
   - Personal portfolio balances
   - Individual timer settings
   - User-specific trade history

2. **Independent Trader Threads**:
   - Each user gets their own background thread
   - Threads run simultaneously without interference
   - Stored in `user_trader_threads` dictionary keyed by user ID

3. **Credential Security**:
   - API keys encrypted using Fernet (symmetric encryption)
   - Encryption key derived from Django SECRET_KEY + user ID
   - Decrypted only when needed for API calls

4. **Session Isolation**:
   - Each user's session is completely independent
   - One user stopping trading doesn't affect others
   - Database queries filtered by user

## API Endpoints

All endpoints require authentication (`@login_required`):

- `GET /` - Dashboard (shows setup warning if no API credentials)
- `GET /profile/` - Manage API credentials and settings
- `POST /start/` - Start trader for current user
- `POST /stop/` - Stop trader for current user
- `GET /status/` - Get current user's session status
- `POST /manual_rebalance/` - Execute immediate rebalance
- `POST /update_default_interval/` - Update rebalance interval
- `POST /set_next_rebalance_time/` - Set next run time
- `POST /toggle_dry_run/` - Switch between test/live mode

## Security Features

1. **Encrypted Storage**:
   - Binance API credentials encrypted with Fernet
   - Unique encryption key per user

2. **Authentication Required**:
   - All trading endpoints require login
   - Session-based authentication
   - Auto-redirect to login if not authenticated

3. **User Isolation**:
   - Users can only access their own data
   - Database queries filtered by request.user
   - Thread management separated by user ID

## Running the System

### Initial Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (optional, for admin access)
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### User Workflow

1. **Register**: Go to `http://localhost:8000/register/`
2. **Setup API Keys**: After registration, configure Binance API credentials
3. **Start Trading**: Return to dashboard and start the timer
4. **Monitor**: Check portfolio updates and rebalance results

### Multiple Users

- Each user can login simultaneously
- Each has independent trading sessions
- No interference between users
- Database handles concurrent access

## Translation Support

The system is fully translated into Ukrainian:
- All authentication messages
- Dashboard interface
- Error messages
- Success notifications

To switch languages, use the language selector in the UI.

## Database Schema

```
User (Django built-in)
  ├── UserProfile (1-to-1)
  │   ├── binance_api_key_encrypted
  │   ├── binance_api_secret_encrypted
  │   ├── cmc_api_key
  │   ├── default_interval
  │   └── auto_rebalance
  │
  ├── TraderSession (1-to-1)
  │   ├── is_running
  │   ├── next_run_time
  │   ├── last_run_time
  │   ├── last_portfolio (JSON)
  │   ├── last_rebalance_result (JSON)
  │   └── dry_run_mode
  │
  └── TradeHistory (1-to-many)
      ├── trade_type
      ├── dry_run
      ├── trade_data (JSON)
      ├── success
      └── error_message
```

## Notes

- **Thread Safety**: Each user has their own thread and lock
- **Database**: SQLite works for development; use PostgreSQL for production
- **Encryption**: Keep Django SECRET_KEY secure - it's used for encryption
- **API Keys**: Never commit API keys to version control
- **Testing**: Use dry_run mode to test without real trades

## Troubleshooting

### "Please configure your Binance API credentials"
- Go to Profile and enter your API credentials
- Make sure both API key and secret are provided

### Trader not starting
- Check that API credentials are valid
- Verify Binance API permissions
- Check console for error messages

### Multiple users seeing each other's data
- This shouldn't happen - all views are filtered by request.user
- If it occurs, check that @login_required decorator is present

## Future Enhancements

Potential improvements:
- Password reset functionality
- Email verification
- API key validation before saving
- Trade notifications (email/webhook)
- Performance analytics per user
- Multi-exchange support
