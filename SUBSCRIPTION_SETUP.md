# 💎 Subscription System Setup Guide

## Overview
The subscription system has been fully prepared for the $10/month rebalancing feature. All infrastructure is in place, ready for payment integration.

## What's Been Implemented

### ✅ 1. Database Models (models.py)
**New UserProfile Fields:**
- `subscription_status`: Current status (free, active, expired, cancelled)
- `subscription_start_date`: When subscription started
- `subscription_end_date`: When subscription expires
- `payment_provider`: Payment gateway (stripe, paypal, etc.)
- `payment_customer_id`: Customer ID from payment provider
- `payment_subscription_id`: Subscription ID from payment provider
- `trial_used`: Has user used their free trial?
- `trial_end_date`: When trial expires

**Helper Methods:**
- `has_active_subscription()`: Check if subscription is active
- `get_subscription_days_remaining()`: Days left in subscription/trial
- `start_free_trial(days=7)`: Start 7-day free trial
- `activate_subscription(days=30)`: Activate paid subscription
- `cancel_subscription()`: Cancel subscription
- `get_subscription_status_display_info()`: Get status details

### ✅ 2. Access Control (decorators.py)
**New Decorators:**
- `@subscription_required`: Strict subscription check
- `@trial_or_subscription_required`: Allow trial OR subscription
- `@admin_only`: Admin-only access

**Applied to Views:**
- `start_trader()` - Requires subscription/trial
- `manual_rebalance()` - Requires subscription/trial
- `set_next_rebalance_time()` - Requires subscription/trial

### ✅ 3. Subscription Management Views (views.py)
**New Endpoints:**
- `/subscription/` - Subscription management page
- `/subscription/start-trial/` - Start 7-day free trial
- `/subscription/cancel/` - Cancel subscription
- `/subscription/status/` - API endpoint for status

### ✅ 4. User Interface
**Subscription Page** (`subscription.html`):
- Beautiful crypto-themed pricing cards
- Free trial card (7 days)
- Premium subscription card ($10/month)
- Feature comparison
- Payment integration placeholder

**Dashboard Integration**:
- Subscription status banner on main dashboard
- Real-time status updates
- Visual indicators (trial/active/expired)
- "Subscribe Now" / "Upgrade" CTAs
- Navigation menu link to subscription page

**Admin Interface**:
- Enhanced user profile admin
- Subscription status tracking
- Payment details management
- Trial status monitoring

### ✅ 5. Routes (urls.py)
All subscription routes configured and ready.

## Migration Required

**IMPORTANT:** You need to run the migration to add subscription fields to the database:

```bash
# Use the correct Python path from your SWEEP.md
/home/kali/PyCharmMiscProject/.venv/bin/python /home/kali/PyCharmMiscProject/20_index_rebalancer/manage.py makemigrations dashboard
/home/kali/PyCharmMiscProject/.venv/bin/python /home/kali/PyCharmMiscProject/20_index_rebalancer/manage.py migrate
```

## How It Works Now

### Free Trial Flow
1. New user registers
2. User visits `/subscription/` page
3. Clicks "Start Free Trial"
4. Gets 7 days of full access
5. Can use all rebalancing features

### Subscription Enforcement
1. User tries to use rebalancing features
2. System checks subscription status
3. If no active subscription/trial → Redirect to subscription page
4. If active → Allow access

### UI Feedback
- Banner shows subscription status on dashboard
- Green = Active subscription
- Blue = Trial active
- Red = Expired/No subscription

## Next Steps: Payment Integration

When you're ready to add payment processing, you need to:

### Option 1: Stripe Integration
```python
# Install Stripe
pip install stripe

# In views.py - add payment handling
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

def create_checkout_session(request):
    session = stripe.checkout.Session.create(
        customer_email=request.user.email,
        payment_method_types=['card'],
        line_items=[{
            'price': 'price_xxxxx',  # Your Stripe price ID
            'quantity': 1,
        }],
        mode='subscription',
        success_url=request.build_absolute_uri('/subscription/success/'),
        cancel_url=request.build_absolute_uri('/subscription/'),
    )
    return redirect(session.url)

def stripe_webhook(request):
    # Handle subscription events
    # - customer.subscription.created
    # - customer.subscription.updated
    # - customer.subscription.deleted
    # - invoice.payment_succeeded
    # - invoice.payment_failed
    pass
```

### Option 2: PayPal Integration
```python
# Install PayPal SDK
pip install paypalrestsdk

# Configure and create subscriptions
# Handle webhooks for payment events
```

### Webhook Endpoints Needed
```python
# urls.py
path('subscription/stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
path('subscription/paypal/webhook/', views.paypal_webhook, name='paypal_webhook'),
path('subscription/success/', views.subscription_success, name='subscription_success'),
path('subscription/failed/', views.subscription_failed, name='subscription_failed'),
```

### Environment Variables Needed
```bash
# .env
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxx
STRIPE_SECRET_KEY=sk_test_xxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxx

# OR for PayPal
PAYPAL_CLIENT_ID=xxxxx
PAYPAL_CLIENT_SECRET=xxxxx
PAYPAL_MODE=sandbox  # or 'live'
```

## Testing Subscription System

### Manual Testing (Without Payment)
```python
# In Django shell or admin panel
from django.contrib.auth.models import User
from dashboard.models import UserProfile

user = User.objects.get(username='testuser')
profile = user.profile

# Test free trial
profile.start_free_trial(trial_days=7)

# Test activation (simulate payment)
profile.activate_subscription(duration_days=30)

# Check status
print(profile.has_active_subscription())
print(profile.get_subscription_status_display_info())
```

### Automated Testing
Create tests in `dashboard/tests.py`:
```python
from django.test import TestCase
from django.contrib.auth.models import User
from dashboard.models import UserProfile

class SubscriptionTestCase(TestCase):
    def test_free_trial(self):
        user = User.objects.create_user('test', 'test@test.com', 'pass')
        profile = user.profile

        self.assertFalse(profile.trial_used)
        self.assertTrue(profile.start_free_trial())
        self.assertTrue(profile.has_active_subscription())
        self.assertTrue(profile.trial_used)
```

## Pricing Model

**Current Setup:**
- Free Trial: 7 days
- Premium: $10/month (30 days)

**Easy to Modify:**
```python
# For annual pricing
profile.activate_subscription(duration_days=365)  # $100/year

# For quarterly
profile.activate_subscription(duration_days=90)   # $25/quarter
```

## Admin Management

Admins can:
1. View all user subscriptions in Django admin
2. Manually activate/deactivate subscriptions
3. Grant trial extensions
4. View payment provider details
5. Track subscription metrics

## Security Considerations

✅ Implemented:
- Decorator-based access control
- Session-based authentication
- CSRF protection on forms

🔒 TODO when adding payments:
- Webhook signature verification
- PCI compliance (handled by Stripe/PayPal)
- Secure storage of payment IDs
- HTTPS enforcement in production

## Features Locked Behind Subscription

Currently protected features:
1. ✅ Start automated trading (`start_trader`)
2. ✅ Manual rebalancing (`manual_rebalance`)
3. ✅ Setting next rebalance time (`set_next_rebalance_time`)

Unprotected features (still free):
- View dashboard
- View portfolio
- Configure API keys
- View trade history
- Dry run mode testing

## Subscription Expiry Handling

The system automatically:
- Checks subscription status on each protected action
- Displays days remaining
- Shows upgrade prompts when trial ends
- Blocks access when expired

**Recommended:** Add a cron job to check and expire subscriptions:
```python
# management/commands/expire_subscriptions.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from dashboard.models import UserProfile

class Command(BaseCommand):
    def handle(self, *args, **options):
        expired = UserProfile.objects.filter(
            subscription_status='active',
            subscription_end_date__lt=timezone.now()
        )
        for profile in expired:
            profile.expire_subscription()
            print(f"Expired subscription for {profile.user.username}")
```

## Summary

🎉 **The subscription system is 100% ready!**

You can:
- ✅ Accept users and let them start free trials
- ✅ Enforce subscription requirements
- ✅ Display subscription status
- ✅ Manage subscriptions in admin
- ⏳ Add payment integration when ready

No payment integration yet, but all the infrastructure is in place. When you're ready to monetize, you just need to:
1. Choose payment provider (Stripe recommended)
2. Add webhook handlers
3. Update subscription page with payment buttons
4. Test and go live! 🚀
