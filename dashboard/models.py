from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from cryptography.fernet import Fernet


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

    # Index Selection - NEW FIELDS
    index_base = models.CharField(
        max_length=10,
        choices=[
            ('cmc20', 'CMC20'),
            ('cmc100', 'CMC100'),
        ],
        default='cmc20',
        help_text="Base index to use (CMC20 or CMC100)"
    )

    index_type = models.CharField(
        max_length=10,
        default='top2',
        help_text="Index type (top2, top5, top10, top20 for CMC20; top30-top100 for CMC100)"
    )

    # Subscription Management
    subscription_status = models.CharField(
        max_length=20,
        choices=[
            ('free', 'Free Trial'),
            ('active', 'Active Subscription'),
            ('expired', 'Expired'),
            ('cancelled', 'Cancelled'),
        ],
        default='free',
        help_text="Current subscription status"
    )
    subscription_start_date = models.DateTimeField(null=True, blank=True, help_text="When subscription started")
    subscription_end_date = models.DateTimeField(null=True, blank=True, help_text="When subscription expires")

    # Payment tracking (for future payment integration)
    payment_provider = models.CharField(max_length=50, blank=True, null=True, help_text="e.g., stripe, paypal")
    payment_customer_id = models.CharField(max_length=255, blank=True, null=True,
                                           help_text="Customer ID from payment provider")
    payment_subscription_id = models.CharField(max_length=255, blank=True, null=True,
                                               help_text="Subscription ID from payment provider")

    # Free trial
    trial_used = models.BooleanField(default=False, help_text="Has user used their free trial?")
    trial_end_date = models.DateTimeField(null=True, blank=True, help_text="When trial expires")

    # Timestamps - ADDED BACK
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    cmc_index_type = models.CharField(
        max_length=10,
        choices=[
            ('CMC20', 'Top 20 Index'),
            ('CMC100', 'Top 100 Index'),
        ],
        default='CMC20',
        help_text="Which CoinMarketCap index to follow"
    )

    auto_convert_dust = models.BooleanField(
        default=True,
        help_text="Automatically convert small balances (<$5) to target assets"
    )

    min_trade_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=5.00,
        help_text="Minimum value for market orders (USD)"
    )

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

    def get_index_display(self):
        """Get human-readable index configuration"""
        return f"{self.index_base.upper()} - {self.index_type.upper()}"

    # Subscription Management Methods
    def has_active_subscription(self):
        """Check if user has an active subscription or valid trial"""
        if self.subscription_status == 'active':
            # Check if subscription hasn't expired
            if self.subscription_end_date and self.subscription_end_date > timezone.now():
                return True
        elif self.subscription_status == 'free':
            # Check if trial hasn't expired
            if self.trial_end_date and self.trial_end_date > timezone.now():
                return True
        return False

    def get_subscription_days_remaining(self):
        """Get number of days remaining in subscription/trial"""
        if self.subscription_status == 'active' and self.subscription_end_date:
            delta = self.subscription_end_date - timezone.now()
            return max(0, delta.days)
        elif self.subscription_status == 'free' and self.trial_end_date:
            delta = self.trial_end_date - timezone.now()
            return max(0, delta.days)
        return 0

    def start_free_trial(self, trial_days=7):
        """Start free trial period"""
        if self.trial_used:
            return False

        self.subscription_status = 'free'
        self.trial_used = True
        self.trial_end_date = timezone.now() + timedelta(days=trial_days)
        self.save()
        return True

    def activate_subscription(self, duration_days=30, subscription_id=None, provider=None):
        """Activate paid subscription (called after payment)"""
        now = timezone.now()

        # If already has active subscription, extend it
        if self.subscription_status == 'active' and self.subscription_end_date and self.subscription_end_date > now:
            self.subscription_end_date += timedelta(days=duration_days)
        else:
            # New subscription
            self.subscription_start_date = now
            self.subscription_end_date = now + timedelta(days=duration_days)

        self.subscription_status = 'active'

        # Update payment provider details if provided
        if subscription_id:
            self.payment_subscription_id = subscription_id
        if provider:
            self.payment_provider = provider

        self.save()
        return True

    def cancel_subscription(self):
        """Cancel subscription (will remain active until end date)"""
        self.subscription_status = 'cancelled'
        self.save()

    def expire_subscription(self):
        """Mark subscription as expired"""
        self.subscription_status = 'expired'
        self.save()

    def get_subscription_status_display_info(self):
        """Get human-readable subscription status info"""
        if self.has_active_subscription():
            days_left = self.get_subscription_days_remaining()
            if self.subscription_status == 'free':
                return {
                    'status': 'trial',
                    'message': f'Free trial - {days_left} days remaining',
                    'days_remaining': days_left,
                    'is_active': True
                }
            else:
                return {
                    'status': 'active',
                    'message': f'Active subscription - {days_left} days remaining',
                    'days_remaining': days_left,
                    'is_active': True
                }
        else:
            return {
                'status': self.subscription_status,
                'message': 'No active subscription',
                'days_remaining': 0,
                'is_active': False
            }


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


