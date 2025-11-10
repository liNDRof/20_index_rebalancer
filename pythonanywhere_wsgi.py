"""
WSGI config for crypto_trader project on PythonAnywhere.

This file should be copied to your PythonAnywhere WSGI configuration file.
You can find it at: Web tab -> Code section -> WSGI configuration file

IMPORTANT: Update the paths below to match your PythonAnywhere username!
Replace 'CryptoIndex' with your actual PythonAnywhere username.
"""

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
