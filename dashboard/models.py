from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from cryptography.fernet import Fernet
import os


class UserProfile(models.Model):
    """Extended user profile with Binance API credentials"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # Encrypted API credentials
    binance_api_key_encrypted = models.TextField(blank=True, null=True)
    binance_api_secret_encrypted = models.TextField(blank=True, null=True)

    # CoinMarketCap API key (optional, can use default)
    cmc_api_key = models.CharField(max_length=255, blank=True, null=True)

    # Trader settings
    default_interval = models.IntegerField(default=3600, help_text="Default rebalance interval in seconds")
    auto_rebalance = models.BooleanField(default=False, help_text="Enable automatic rebalancing")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile: {self.user.username}"

    def get_encryption_key(self):
        """Get or create encryption key for this user"""
        # Use Django SECRET_KEY + user ID for encryption
        from django.conf import settings
        base_key = settings.SECRET_KEY.encode()
        user_salt = str(self.user.id).encode()
        # Generate a Fernet-compatible key
        import hashlib
        import base64
        key = base64.urlsafe_b64encode(hashlib.sha256(base_key + user_salt).digest())
        return key

    def set_binance_credentials(self, api_key, api_secret):
        """Encrypt and store Binance API credentials"""
        if not api_key or not api_secret:
            raise ValidationError("API key and secret are required")

        cipher = Fernet(self.get_encryption_key())
        self.binance_api_key_encrypted = cipher.encrypt(api_key.encode()).decode()
        self.binance_api_secret_encrypted = cipher.encrypt(api_secret.encode()).decode()

    def get_binance_credentials(self):
        """Decrypt and return Binance API credentials"""
        if not self.binance_api_key_encrypted or not self.binance_api_secret_encrypted:
            return None, None

        try:
            cipher = Fernet(self.get_encryption_key())
            api_key = cipher.decrypt(self.binance_api_key_encrypted.encode()).decode()
            api_secret = cipher.decrypt(self.binance_api_secret_encrypted.encode()).decode()
            return api_key, api_secret
        except Exception as e:
            print(f"Error decrypting credentials: {e}")
            return None, None

    def has_binance_credentials(self):
        """Check if user has configured Binance credentials"""
        return bool(self.binance_api_key_encrypted and self.binance_api_secret_encrypted)


class TraderSession(models.Model):
    """Track active trading sessions for each user"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trader_session')

    # Session state
    is_running = models.BooleanField(default=False)
    next_run_time = models.DateTimeField(null=True, blank=True)
    last_run_time = models.DateTimeField(null=True, blank=True)

    # Last portfolio snapshot (JSON)
    last_portfolio = models.JSONField(default=dict, blank=True)

    # Last rebalance result (JSON)
    last_rebalance_result = models.JSONField(default=dict, blank=True)

    # Dry run mode
    dry_run_mode = models.BooleanField(default=True, help_text="Test mode (no real trades)")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session: {self.user.username} ({'Running' if self.is_running else 'Stopped'})"


class TradeHistory(models.Model):
    """Store trade history for each user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trades')

    # Trade details
    trade_type = models.CharField(max_length=20, choices=[
        ('rebalance', 'Rebalance'),
        ('manual', 'Manual Trade'),
    ])

    dry_run = models.BooleanField(default=True)

    # Trade data (JSON)
    trade_data = models.JSONField(default=dict)

    # Result
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Trade histories"

    def __str__(self):
        return f"{self.user.username} - {self.trade_type} at {self.created_at}"

