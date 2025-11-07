"""
Comprehensive Logging Configuration for Crypto Trading System
This creates multiple specialized log files to track different aspects of the system.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging():
    """
    Setup comprehensive logging system with multiple specialized loggers.

    Log Files Created:
    - logs/general.log - General application logs
    - logs/api.log - Binance/CoinMarketCap API calls
    - logs/trades.log - All trading operations
    - logs/errors.log - All errors and exceptions
    - logs/requests.log - HTTP requests
    - logs/performance.log - Performance metrics
    - logs/user_activity.log - User actions
    - logs/debug.log - Detailed debug information
    """

    # Create logs directory
    log_dir = Path(__file__).parent.parent / 'logs'
    log_dir.mkdir(exist_ok=True)

    # Common formatter with timestamp, level, logger name, and message
    detailed_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)8s] %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Extra detailed formatter for debug logs
    debug_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)8s] %(name)s [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # ============================================
    # 1. GENERAL LOGGER - General application logs
    # ============================================
    general_logger = logging.getLogger('general')
    general_logger.setLevel(logging.INFO)
    general_handler = RotatingFileHandler(
        log_dir / 'general.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    general_handler.setFormatter(detailed_formatter)
    general_logger.addHandler(general_handler)

    # Also log to console
    # Wrap sys.stdout with UTF-8 encoding to handle emoji characters on Windows
    import sys
    import io

    # Create a UTF-8 wrapper for stdout to handle emoji characters
    # This prevents UnicodeEncodeError on Windows (cp1251 encoding)
    try:
        # Try to reconfigure stdout to UTF-8 (Python 3.7+)
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            console_stream = sys.stdout
        else:
            # Fallback for older Python versions
            console_stream = io.TextIOWrapper(
                sys.stdout.buffer,
                encoding='utf-8',
                errors='replace',
                line_buffering=True
            )
    except (AttributeError, io.UnsupportedOperation):
        # If stdout doesn't have buffer (e.g., in some test environments)
        # use default stdout but set errors='replace' in the formatter
        console_stream = sys.stdout

    console_handler = logging.StreamHandler(console_stream)
    console_handler.setFormatter(detailed_formatter)
    general_logger.addHandler(console_handler)

    # ============================================
    # 2. API LOGGER - Binance/CoinMarketCap API calls
    # ============================================
    api_logger = logging.getLogger('api')
    api_logger.setLevel(logging.INFO)
    api_handler = RotatingFileHandler(
        log_dir / 'api.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    api_handler.setFormatter(detailed_formatter)
    api_logger.addHandler(api_handler)
    api_logger.addHandler(console_handler)  # Also to console

    # ============================================
    # 3. TRADES LOGGER - All trading operations
    # ============================================
    trade_logger = logging.getLogger('trades')
    trade_logger.setLevel(logging.INFO)
    trade_handler = RotatingFileHandler(
        log_dir / 'trades.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10,  # Keep more trade logs
        encoding='utf-8'
    )
    trade_handler.setFormatter(detailed_formatter)
    trade_logger.addHandler(trade_handler)
    trade_logger.addHandler(console_handler)  # Also to console

    # ============================================
    # 4. ERRORS LOGGER - All errors and exceptions
    # ============================================
    error_logger = logging.getLogger('errors')
    error_logger.setLevel(logging.WARNING)
    error_handler = RotatingFileHandler(
        log_dir / 'errors.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=10,  # Keep more error logs
        encoding='utf-8'
    )
    error_handler.setFormatter(detailed_formatter)
    error_logger.addHandler(error_handler)
    error_logger.addHandler(console_handler)  # Also to console

    # ============================================
    # 5. REQUESTS LOGGER - HTTP requests
    # ============================================
    request_logger = logging.getLogger('requests')
    request_logger.setLevel(logging.INFO)
    request_handler = RotatingFileHandler(
        log_dir / 'requests.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    request_handler.setFormatter(detailed_formatter)
    request_logger.addHandler(request_handler)
    request_logger.addHandler(console_handler)  # Also to console

    # ============================================
    # 6. PERFORMANCE LOGGER - Performance metrics
    # ============================================
    perf_logger = logging.getLogger('performance')
    perf_logger.setLevel(logging.INFO)
    perf_handler = RotatingFileHandler(
        log_dir / 'performance.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    perf_handler.setFormatter(detailed_formatter)
    perf_logger.addHandler(perf_handler)
    perf_logger.addHandler(console_handler)  # Also to console

    # ============================================
    # 7. USER ACTIVITY LOGGER - User actions
    # ============================================
    activity_logger = logging.getLogger('user_activity')
    activity_logger.setLevel(logging.INFO)
    activity_handler = RotatingFileHandler(
        log_dir / 'user_activity.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    activity_handler.setFormatter(detailed_formatter)
    activity_logger.addHandler(activity_handler)
    activity_logger.addHandler(console_handler)  # Also to console

    # ============================================
    # 8. DEBUG LOGGER - Detailed debug information
    # ============================================
    debug_logger = logging.getLogger('debug')
    debug_logger.setLevel(logging.DEBUG)
    debug_handler = RotatingFileHandler(
        log_dir / 'debug.log',
        maxBytes=20*1024*1024,  # 20MB
        backupCount=3,
        encoding='utf-8'
    )
    debug_handler.setFormatter(debug_formatter)
    debug_logger.addHandler(debug_handler)

    # ============================================
    # Configure Django's logger
    # ============================================
    django_logger = logging.getLogger('django')
    django_logger.setLevel(logging.INFO)

    # Prevent propagation to avoid duplicate logs
    for logger_name in ['general', 'api', 'trades', 'errors', 'requests',
                        'performance', 'user_activity', 'debug']:
        logging.getLogger(logger_name).propagate = False

    # Log that logging system is initialized
    general_logger.info("=" * 80)
    general_logger.info("LOGGING SYSTEM INITIALIZED")
    general_logger.info(f"Log directory: {log_dir}")
    general_logger.info("=" * 80)

    return {
        'general': general_logger,
        'api': api_logger,
        'trades': trade_logger,
        'errors': error_logger,
        'requests': request_logger,
        'performance': perf_logger,
        'user_activity': activity_logger,
        'debug': debug_logger,
    }
