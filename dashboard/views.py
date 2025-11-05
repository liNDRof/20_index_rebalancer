import json
import traceback
import threading
import time
import logging
from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.utils.translation import gettext as _
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db import transaction
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_POST

from trader.btceth_trader import BTCETH_CMC20_Trader
from .models import UserProfile, TraderSession, TradeHistory

# Configure logging - use specialized loggers
logger = logging.getLogger('general')
api_logger = logging.getLogger('api')
trade_logger = logging.getLogger('trades')


# Thread management for each user
user_trader_threads = {}  # {user_id: thread}


def parse_bool(value, default=False):
    """Safely parse boolean-like values from various inputs"""
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        value = value.strip().lower()
        if value in {'1', 'true', 'yes', 'on'}:
            return True
        if value in {'0', 'false', 'no', 'off'}:
            return False
        return default
    try:
        return bool(int(value))
    except (TypeError, ValueError):
        return default


def get_or_create_profile(user):
    """Get or create user profile"""
    profile, created = UserProfile.objects.get_or_create(user=user)
    return profile


def get_or_create_session(user):
    """Get or create trader session for user"""
    session, created = TraderSession.objects.get_or_create(user=user)
    return session


def create_user_trader(user):
    """Create trader instance with user's credentials"""
    profile = get_or_create_profile(user)

    if not profile.has_binance_credentials():
        raise ValueError("Please configure your Binance API credentials in your profile first.")

    api_key, api_secret = profile.get_binance_credentials()

    trader = BTCETH_CMC20_Trader(
        binance_api_key=api_key,
        binance_api_secret=api_secret,
        cmc_api_key=profile.cmc_api_key,
        update_interval=profile.default_interval
    )

    return trader


# ============================================
# Authentication Views
# ============================================

def login_view(request):
    """User login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            response = redirect('dashboard:index')
            response.set_cookie('is_logged_in', 'true', max_age=3600*24*7)
            return response
        else:
            return render(request, 'dashboard/login.html', {
                'error': _('Invalid username or password')
            })

    return render(request, 'dashboard/login.html')


def register_view(request):
    """User registration"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Validation
        if not username or not email or not password1 or not password2:
            return render(request, 'dashboard/register.html', {
                'error': _('Please fill in all fields')
            })

        if password1 != password2:
            return render(request, 'dashboard/register.html', {
                'error': _('Passwords do not match')
            })

        if User.objects.filter(username=username).exists():
            return render(request, 'dashboard/register.html', {
                'error': _('This username already exists')
            })

        if User.objects.filter(email=email).exists():
            return render(request, 'dashboard/register.html', {
                'error': _('This email is already registered')
            })

        # Create user and profile
        with transaction.atomic():
            user = User.objects.create_user(username=username, email=email, password=password1)
            UserProfile.objects.create(user=user)
            TraderSession.objects.create(user=user)

        # Auto login
        login(request, user)
        response = redirect('dashboard:profile')  # Redirect to profile to set API keys
        response.set_cookie('is_logged_in', 'true', max_age=3600 * 24 * 7)
        return response

    return render(request, 'dashboard/register.html')


def logout_view(request):
    """User logout"""
    # Stop trader if running
    if request.user.is_authenticated:
        stop_user_trader(request.user)

    logout(request)
    response = redirect('dashboard:login')
    response.delete_cookie('is_logged_in')
    return response


# ============================================
# Profile Management
# ============================================

@login_required
def profile_view(request):
    """User profile management"""
    profile = get_or_create_profile(request.user)
    message = None
    error = None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_credentials':
            binance_api_key = request.POST.get('binance_api_key', '').strip()
            binance_api_secret = request.POST.get('binance_api_secret', '').strip()
            cmc_api_key = request.POST.get('cmc_api_key', '').strip()

            try:
                if binance_api_key and binance_api_secret:
                    profile.set_binance_credentials(binance_api_key, binance_api_secret)

                if cmc_api_key:
                    profile.cmc_api_key = cmc_api_key

                profile.save()
                message = _('API credentials updated successfully')
            except ValidationError as e:
                error = str(e)
            except Exception as e:
                error = f"Error: {str(e)}"

        elif action == 'update_settings':
            try:
                default_interval = int(request.POST.get('default_interval', 3600))
                auto_rebalance = request.POST.get('auto_rebalance') == 'on'

                profile.default_interval = max(60, default_interval)  # Minimum 60 seconds
                profile.auto_rebalance = auto_rebalance
                profile.save()

                message = _('Settings updated successfully')
            except Exception as e:
                error = f"Error: {str(e)}"

        elif action == 'update_email':
            new_email = request.POST.get('email', '').strip()
            if new_email:
                request.user.email = new_email
                request.user.save()
                message = _('Email updated')

    return render(request, 'dashboard/profile.html', {
        'profile': profile,
        'has_credentials': profile.has_binance_credentials(),
        'message': message,
        'error': error
    })


# ============================================
# Dashboard View
# ============================================

@login_required
def index(request):
    """Main dashboard"""
    profile = get_or_create_profile(request.user)
    session = get_or_create_session(request.user)

    # Check if user has configured API credentials
    if not profile.has_binance_credentials():
        return render(request, 'dashboard/index.html', {
            'error': _('Please configure your Binance API credentials in your profile first.'),
            'needs_setup': True,
            'session': session,
        })

    return render(request, 'dashboard/index.html', {
        'session': session,
        'needs_setup': False,
    })


# ============================================
# Trader Control
# ============================================

def stop_user_trader(user):
    """Stop trader for specific user"""
    user_id = user.id
    if user_id in user_trader_threads:
        # Signal thread to stop
        session = get_or_create_session(user)
        session.is_running = False
        session.next_run_time = None
        session.save()

        # Wait a bit for thread to finish
        thread = user_trader_threads.get(user_id)
        if thread and thread.is_alive():
            thread.join(timeout=2)

        # Clean up
        user_trader_threads.pop(user_id, None)


def user_trader_loop(user_id):
    """Background trader loop for specific user"""
    try:
        user = User.objects.get(id=user_id)
        profile = get_or_create_profile(user)
        session = get_or_create_session(user)

        # Create trader with user credentials
        trader = create_user_trader(user)
        interval = profile.default_interval

        while session.is_running:
            # Refresh session from DB
            session.refresh_from_db()
            profile.refresh_from_db()
            interval = max(60, profile.default_interval)

            if not session.is_running:
                break

            try:
                print(f"🔁 [{user.username}] Starting rebalance...")

                # Get portfolio
                balances, total = trader.get_all_binance_balances()
                session.last_portfolio = balances
                session.save()

                # Execute rebalance
                rebalance_result = trader.execute_portfolio_rebalance(dry_run=session.dry_run_mode)

                # Save result
                session.last_rebalance_result = rebalance_result if rebalance_result else {"note": "no result"}
                session.last_run_time = datetime.now()
                session.next_run_time = datetime.now() + timedelta(seconds=interval)
                session.save()

                # Save to trade history
                TradeHistory.objects.create(
                    user=user,
                    trade_type='rebalance',
                    dry_run=session.dry_run_mode,
                    trade_data=rebalance_result if rebalance_result else {},
                    success=True
                )

                print(f"✅ [{user.username}] Rebalance completed")

            except Exception as e:
                print(f"❌ [{user.username}] Error: {e}")
                traceback.print_exc()

                error_data = {"error": str(e), "trace": traceback.format_exc()}
                session.last_rebalance_result = error_data
                session.save()

                TradeHistory.objects.create(
                    user=user,
                    trade_type='rebalance',
                    dry_run=session.dry_run_mode,
                    trade_data=error_data,
                    success=False,
                    error_message=str(e)
                )

            # Wait for next cycle
            print(f"😴 [{user.username}] Waiting {interval} seconds...")
            time.sleep(interval)

        print(f"⛔ [{user.username}] Trader loop stopped")

    except Exception as e:
        print(f"❌ [{user.username}] Fatal error in trader loop: {e}")
        traceback.print_exc()


@login_required
@require_POST
def start_trader(request):
    """Start trader for current user"""
    user = request.user
    session = get_or_create_session(user)

    try:
        # Verify credentials
        create_user_trader(user)  # This will raise error if no credentials

        if session.is_running:
            return JsonResponse({'status': 'already_running'})

        # Start trader thread
        session.is_running = True
        profile = get_or_create_profile(user)
        session.next_run_time = datetime.now() + timedelta(seconds=max(60, profile.default_interval))
        session.save()

        thread = threading.Thread(target=user_trader_loop, args=(user.id,), daemon=True)
        thread.start()

        user_trader_threads[user.id] = thread

        remaining = max(0, int((session.next_run_time - datetime.now()).total_seconds())) if session.next_run_time else None

        return JsonResponse({
            'status': 'started',
            'remaining': remaining,
            'default_interval': profile.default_interval
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)})


@login_required
@require_POST
def stop_trader(request):
    """Stop trader for current user"""
    stop_user_trader(request.user)
    session = get_or_create_session(request.user)
    profile = get_or_create_profile(request.user)
    return JsonResponse({
        'status': 'stopped',
        'remaining': 0,
        'default_interval': profile.default_interval,
        'is_running': session.is_running
    })


# ============================================
# Status & Data
# ============================================

@login_required
def get_status(request):
    """Get current status for user"""
    logger.info(f"[{request.user.username}] ========== get_status called ==========")
    profile = get_or_create_profile(request.user)
    session = get_or_create_session(request.user)

    remaining = None
    if session.next_run_time:
        remaining = max(0, int((session.next_run_time - datetime.now()).total_seconds()))
        logger.info(f"[{request.user.username}] Next run time: {session.next_run_time}, remaining: {remaining}s")

    logger.info(f"[{request.user.username}] Session data:")
    logger.info(f"  - is_running: {session.is_running}")
    logger.info(f"  - dry_run_mode: {session.dry_run_mode}")
    logger.info(f"  - last_portfolio type: {type(session.last_portfolio)}")
    logger.info(f"  - last_portfolio: {session.last_portfolio}")
    logger.info(f"  - portfolio_items: {len(session.last_portfolio) if session.last_portfolio else 0}")
    logger.info(f"  - last_rebalance_result: {session.last_rebalance_result}")
    logger.info(f"  - rebalance_data items: {len(session.last_rebalance_result) if session.last_rebalance_result else 0}")

    response_data = {
        'is_running': session.is_running,
        'remaining': remaining,
        'portfolio': session.last_portfolio,
        'rebalance': session.last_rebalance_result,
        'dry_run_mode': session.dry_run_mode,
        'default_interval': profile.default_interval,
        'next_run_time': session.next_run_time.isoformat() if session.next_run_time else None,
        'last_run_time': session.last_run_time.isoformat() if session.last_run_time else None,
    }

    logger.info(f"[{request.user.username}] Returning response: {response_data}")
    logger.info(f"[{request.user.username}] ========== get_status END ==========")

    return JsonResponse(response_data)


@login_required
def refresh_portfolio(request):
    """Fetch fresh portfolio data from Binance"""
    logger.info(f"[{request.user.username}] ========== refresh_portfolio called ==========")
    user = request.user
    session = get_or_create_session(user)
    profile = get_or_create_profile(user)

    logger.info(f"[{request.user.username}] User profile:")
    logger.info(f"  - has_binance_credentials: {profile.has_binance_credentials()}")
    logger.info(f"  - cmc_api_key: {'set' if profile.cmc_api_key else 'not set'}")
    logger.info(f"  - default_interval: {profile.default_interval}")

    try:
        # Create trader with user credentials
        logger.info(f"[{request.user.username}] Creating trader instance...")
        trader = create_user_trader(user)
        logger.info(f"[{request.user.username}] Trader instance created successfully")

        # Fetch portfolio from Binance
        logger.info(f"[{request.user.username}] Calling trader.get_all_binance_balances()...")
        balances, total = trader.get_all_binance_balances()

        logger.info(f"[{request.user.username}] Portfolio fetched successfully:")
        logger.info(f"  - Number of assets: {len(balances)}")
        logger.info(f"  - Total value: ${total}")
        logger.info(f"  - Balances data: {balances}")

        # Save to session
        logger.info(f"[{request.user.username}] Saving portfolio to session...")
        session.last_portfolio = balances
        session.save()
        logger.info(f"[{request.user.username}] Portfolio saved to session")

        response_data = {
            "status": "ok",
            "portfolio": balances,
            "total_value": total
        }
        logger.info(f"[{request.user.username}] Returning response: {response_data}")
        logger.info(f"[{request.user.username}] ========== refresh_portfolio END (SUCCESS) ==========")

        return JsonResponse(response_data)

    except ValueError as e:
        # Missing credentials
        logger.error(f"[{request.user.username}] ========== CREDENTIALS ERROR ==========")
        logger.error(f"[{request.user.username}] Missing credentials: {e}")
        logger.error(f"[{request.user.username}] ========== refresh_portfolio END (ERROR) ==========")
        return JsonResponse({
            "status": "error",
            "error": str(e),
            "error_type": "credentials"
        }, status=400)

    except Exception as e:
        logger.error(f"[{request.user.username}] ========== API ERROR ==========")
        logger.error(f"[{request.user.username}] Error fetching portfolio: {e}")
        logger.error(f"[{request.user.username}] Exception type: {type(e).__name__}")
        logger.error(f"[{request.user.username}] Traceback:")
        logger.error(traceback.format_exc())
        logger.error(f"[{request.user.username}] ========== refresh_portfolio END (ERROR) ==========")
        return JsonResponse({
            "status": "error",
            "error": str(e),
            "error_type": "api_error"
        }, status=500)


@login_required
@require_POST
def manual_rebalance(request):
    """Manual rebalance for current user"""
    trade_logger.info(f"{'='*80}")
    trade_logger.info(f"[{request.user.username}] MANUAL REBALANCE STARTED")
    trade_logger.info(f"{'='*80}")

    user = request.user
    session = get_or_create_session(user)
    profile = get_or_create_profile(user)

    try:
        # Create trader with user credentials
        trade_logger.info(f"[{request.user.username}] Step 1: Creating trader instance...")
        trader = create_user_trader(user)
        trade_logger.info(f"[{request.user.username}] ✓ Trader instance created")

        # Get portfolio
        trade_logger.info(f"[{request.user.username}] Step 2: Fetching portfolio from Binance...")
        balances, total = trader.get_all_binance_balances()
        session.last_portfolio = balances
        session.save()
        trade_logger.info(f"[{request.user.username}] ✓ Portfolio fetched:")
        trade_logger.info(f"[{request.user.username}]   - Assets: {len(balances)}")
        trade_logger.info(f"[{request.user.username}]   - Total value: ${total:.2f}")
        for symbol, info in balances.items():
            if isinstance(info, dict):
                trade_logger.info(f"[{request.user.username}]   - {symbol}: {info.get('free', 0)} (${info.get('usdc_value', 0):.2f})")

        # Execute rebalance
        is_dry_run = session.dry_run_mode
        trade_logger.info(f"[{request.user.username}] Step 3: Executing rebalance...")
        trade_logger.info(f"[{request.user.username}]   - Mode: {'DRY RUN (TEST)' if is_dry_run else 'LIVE TRADING'}")

        rebalance_result = trader.execute_portfolio_rebalance(dry_run=is_dry_run)

        # Save result
        session.last_rebalance_result = rebalance_result if rebalance_result else {"note": "no result"}
        session.last_run_time = datetime.now()
        if session.is_running:
            session.next_run_time = datetime.now() + timedelta(seconds=max(60, profile.default_interval))
        else:
            session.next_run_time = None
        session.save()

        trade_logger.info(f"[{request.user.username}] ✓ Rebalance completed successfully")
        trade_logger.info(f"[{request.user.username}] Result summary:")
        if isinstance(rebalance_result, dict):
            for key, value in rebalance_result.items():
                trade_logger.info(f"[{request.user.username}]   - {key}: {value}")

        # Save to history
        TradeHistory.objects.create(
            user=user,
            trade_type='manual',
            dry_run=session.dry_run_mode,
            trade_data=rebalance_result if rebalance_result else {},
            success=True
        )

        trade_logger.info(f"{'='*80}")
        trade_logger.info(f"[{request.user.username}] MANUAL REBALANCE COMPLETED - SUCCESS")
        trade_logger.info(f"{'='*80}")

        return JsonResponse({
            "status": "ok",
            "rebalance": rebalance_result if rebalance_result else {"note": "no result"},
            "dry_run": session.dry_run_mode
        })

    except Exception as e:
        logger.error(f"[{request.user.username}] Error during manual rebalance: {e}")
        logger.error(traceback.format_exc())

        error_data = {"error": str(e), "trace": traceback.format_exc()}

        session.last_rebalance_result = error_data
        session.save()

        TradeHistory.objects.create(
            user=user,
            trade_type='manual',
            dry_run=session.dry_run_mode,
            trade_data=error_data,
            success=False,
            error_message=str(e)
        )

        return JsonResponse({"status": "error", "error": str(e)})


# ============================================
# Settings
# ============================================

@login_required
@require_POST
def update_default_interval(request):
    """Update default rebalance interval"""
    profile = get_or_create_profile(request.user)
    session = get_or_create_session(request.user)

    try:
        if request.content_type == 'application/json':
            payload = json.loads(request.body or '{}')
        else:
            payload = request.POST

        def to_int(value):
            try:
                return int(value)
            except (TypeError, ValueError):
                return 0

        days = to_int(payload.get("days", 0))
        hours = to_int(payload.get("hours", 0))
        minutes = to_int(payload.get("minutes", 0))
        seconds = to_int(payload.get("seconds", 0))

        total_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds
        profile.default_interval = max(60, total_seconds)  # Minimum 60 seconds
        profile.save()

        if session.is_running:
            session.next_run_time = datetime.now() + timedelta(seconds=profile.default_interval)
            session.save(update_fields=['next_run_time', 'is_running', 'updated_at'])

        return JsonResponse({"status": "ok", "default_interval": profile.default_interval})
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)})


@login_required
@require_POST
def set_next_rebalance_time(request):
    """Set next rebalance time"""
    session = get_or_create_session(request.user)

    try:
        if request.content_type == 'application/json':
            payload = json.loads(request.body or '{}')
        else:
            payload = request.POST

        def to_int(value):
            try:
                return int(value)
            except (TypeError, ValueError):
                return 0

        days = to_int(payload.get("days", 0))
        hours = to_int(payload.get("hours", 0))
        minutes = to_int(payload.get("minutes", 0))
        seconds = to_int(payload.get("seconds", 0))

        total_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds
        session.next_run_time = datetime.now() + timedelta(seconds=total_seconds)
        session.save()

        return JsonResponse({
            "status": "ok",
            "next_in": max(0, total_seconds),
            "is_running": session.is_running
        })
    except Exception as e:
        return JsonResponse({"status": "error", "error": str(e)})


@login_required
@require_POST
def toggle_dry_run(request):
    """Toggle dry run mode"""
    session = get_or_create_session(request.user)

    if request.content_type == 'application/json':
        try:
            payload = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            payload = {}
    else:
        payload = request.POST

    mode = payload.get('mode', None)
    if mode == 'real':
        session.dry_run_mode = False
    elif mode == 'test':
        session.dry_run_mode = True
    else:
        session.dry_run_mode = not session.dry_run_mode

    session.save()

    return JsonResponse({
        'status': 'ok',
        'dry_run_mode': session.dry_run_mode,
        'message': _('Test mode') if session.dry_run_mode else _('Real trading mode')
    })
