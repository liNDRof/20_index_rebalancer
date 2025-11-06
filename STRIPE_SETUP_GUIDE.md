# 🔐 Stripe Payment Integration Setup Guide

## 📋 Overview

This guide will walk you through setting up Stripe payment integration for your crypto rebalancing subscription system. The integration is **100% complete** and ready to use - you just need to configure your Stripe account.

---

## ✅ What's Already Implemented

- ✅ Stripe SDK installed and configured
- ✅ Payment checkout flow
- ✅ Webhook handlers for subscription events
- ✅ Customer portal for subscription management
- ✅ Automatic subscription status updates
- ✅ Success/cancel payment pages
- ✅ All UI integrated with beautiful design

---

## 🚀 Step-by-Step Setup

### Step 1: Create a Stripe Account

1. Go to [https://stripe.com](https://stripe.com)
2. Click "Start now" to create an account
3. Complete the sign-up process
4. You'll start in **Test Mode** (recommended for initial setup)

### Step 2: Get Your API Keys

1. Log in to [Stripe Dashboard](https://dashboard.stripe.com)
2. Click **Developers** in the top menu
3. Click **API keys** in the left sidebar
4. You'll see two keys:
   - **Publishable key** (starts with `pk_test_...`)
   - **Secret key** (starts with `sk_test_...`) - Click "Reveal test key"

**Important:** Keep the Secret key private!

### Step 3: Create Your Product (Monthly Subscription)

1. In Stripe Dashboard, click **Products** in the left sidebar
2. Click **+ Add product**
3. Fill in the details:
   - **Name:** `Crypto Rebalancer Premium`
   - **Description:** `Monthly subscription for automated crypto portfolio rebalancing`
   - **Pricing model:** Select "Standard pricing"
   - **Price:** `10.00`
   - **Billing period:** `Monthly`
   - **Currency:** `USD`
4. Click **Save product**
5. **Copy the Price ID** (starts with `price_...`) - you'll need this!

### Step 4: Set Up Webhook Endpoint

Webhooks allow Stripe to notify your app about subscription events (payments, cancellations, etc.)

#### 4.1 For Local Development (Testing)

You'll need to expose your local server to the internet. Use **Stripe CLI** (recommended):

**Install Stripe CLI:**
```bash
# On Linux
wget https://github.com/stripe/stripe-cli/releases/download/v1.19.4/stripe_1.19.4_linux_x86_64.tar.gz
tar -xvf stripe_1.19.4_linux_x86_64.tar.gz
sudo mv stripe /usr/local/bin/
```

**Forward webhooks to your local server:**
```bash
stripe login
stripe listen --forward-to localhost:8000/dashboard/stripe/webhook/
```

This will output a webhook signing secret starting with `whsec_...` - **copy this!**

#### 4.2 For Production (Live Server)

1. In Stripe Dashboard, click **Developers** → **Webhooks**
2. Click **+ Add endpoint**
3. Enter your webhook URL:
   ```
   https://yourdomain.com/dashboard/stripe/webhook/
   ```
4. Select events to listen to:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Click **Add endpoint**
6. Click on the webhook you just created
7. Click **Reveal** next to "Signing secret" and **copy it**

### Step 5: Configure Environment Variables

1. **Copy the example file:**
   ```bash
   cd /home/kali/PycharmProjects/20_index_rebalancer
   cp .env.example .env
   ```

2. **Edit the .env file** with your credentials:
   ```bash
   nano .env
   ```

3. **Fill in your Stripe credentials:**
   ```env
   STRIPE_PUBLISHABLE_KEY=pk_test_51Abc123...
   STRIPE_SECRET_KEY=sk_test_51Abc123...
   STRIPE_WEBHOOK_SECRET=whsec_abc123...
   STRIPE_PRICE_ID=price_1Abc123...
   DOMAIN=http://localhost:8000
   ```

4. **Save and close** (Ctrl+X, then Y, then Enter)

### Step 6: Run Your Application

1. **Make sure you have migrations ready:**
   ```bash
   python manage.py makemigrations dashboard
   python manage.py migrate
   ```

2. **Start the Django server:**
   ```bash
   python manage.py runserver
   ```

3. **If using Stripe CLI for webhooks, start the listener** (in a separate terminal):
   ```bash
   stripe listen --forward-to localhost:8000/dashboard/stripe/webhook/
   ```

---

## 🧪 Testing the Integration

### Test the Subscription Flow

1. **Register a new user** or log in
2. Go to the **Subscription** page (💎 icon in navigation)
3. Click **"Subscribe Now"** on the Premium card
4. You'll be redirected to Stripe Checkout
5. Use a **test card number:**
   - Card: `4242 4242 4242 4242`
   - Expiry: Any future date (e.g., `12/34`)
   - CVC: Any 3 digits (e.g., `123`)
   - ZIP: Any 5 digits (e.g., `12345`)
6. Complete the payment
7. You'll be redirected back with a success message
8. Your subscription should now be **Active**!

### Test Subscription Management

1. When you have an active subscription, click **"Manage Subscription"**
2. You'll be taken to Stripe's Customer Portal
3. Here you can:
   - Update payment method
   - View invoices
   - Cancel subscription
   - Update billing information

### Test Webhooks

1. Make sure Stripe CLI is running: `stripe listen --forward-to ...`
2. In Stripe CLI terminal, you'll see webhook events as they happen
3. Try:
   - Subscribing (should see `customer.subscription.created`)
   - Waiting for renewal (should see `invoice.payment_succeeded`)
   - Canceling (should see `customer.subscription.deleted`)

### Test Cards for Different Scenarios

Stripe provides test cards for various scenarios:

- **Successful payment:** `4242 4242 4242 4242`
- **Declined payment:** `4000 0000 0000 0002`
- **Requires authentication:** `4000 0025 0000 3155`
- **Insufficient funds:** `4000 0000 0000 9995`

Full list: [https://stripe.com/docs/testing](https://stripe.com/docs/testing)

---

## 🌐 Going Live (Production)

### When You're Ready for Real Payments:

1. **Switch Stripe to Live Mode:**
   - In Stripe Dashboard, toggle from "Test mode" to "Live mode"
   - Get your **Live API keys** (starts with `pk_live_` and `sk_live_`)

2. **Create Live Product:**
   - Create the same product in Live mode
   - Get the Live Price ID

3. **Set up Live Webhook:**
   - Add webhook endpoint with your production URL
   - Get the Live webhook secret

4. **Update .env with Live credentials:**
   ```env
   STRIPE_PUBLISHABLE_KEY=pk_live_...
   STRIPE_SECRET_KEY=sk_live_...
   STRIPE_WEBHOOK_SECRET=whsec_live_...
   STRIPE_PRICE_ID=price_live_...
   DOMAIN=https://yourdomain.com
   ```

5. **Complete Stripe Account Verification:**
   - Provide business details
   - Set up bank account for payouts
   - Complete identity verification

6. **Enable HTTPS:**
   - Your production site **must use HTTPS** for Stripe
   - Use Let's Encrypt for free SSL certificates

---

## 🔍 How It Works

### Subscription Flow

1. **User clicks "Subscribe Now"**
   → Creates Stripe Checkout Session
   → Redirects to Stripe payment page

2. **User enters payment details**
   → Stripe processes payment securely
   → Creates subscription in Stripe

3. **Payment successful**
   → Stripe sends webhook to your server
   → Your app activates subscription in database
   → User redirected back to success page

4. **Monthly renewals**
   → Stripe automatically charges customer
   → Sends webhook on successful payment
   → Your app extends subscription period

5. **Cancellation**
   → User clicks "Manage Subscription"
   → Cancels in Stripe Customer Portal
   → Stripe sends webhook
   → Your app marks subscription as cancelled

### Webhook Events Handled

- `customer.subscription.created` - New subscription started
- `customer.subscription.updated` - Subscription status changed
- `customer.subscription.deleted` - Subscription cancelled
- `invoice.payment_succeeded` - Payment successful (monthly renewal)
- `invoice.payment_failed` - Payment failed

---

## 🛠️ Troubleshooting

### "Stripe is not configured"

- Check that your `.env` file exists and has all the required variables
- Make sure you copied `.env.example` to `.env`
- Verify the keys start with the correct prefix (`pk_`, `sk_`, `whsec_`, `price_`)

### Webhooks not working

- **Local development:** Make sure Stripe CLI is running
- **Production:** Check webhook URL is correct and accessible via HTTPS
- Check webhook signing secret matches your `.env`
- Look at webhook logs in Stripe Dashboard → Developers → Webhooks

### Subscription not activating

- Check Django logs for webhook errors
- Verify webhook secret is correct
- Make sure the webhook URL is accessible (not behind authentication)

### Payment page doesn't open

- Check browser console for errors
- Verify `STRIPE_PRICE_ID` is correct
- Make sure Stripe SDK is loaded properly

---

## 📚 Additional Resources

- [Stripe Documentation](https://stripe.com/docs)
- [Stripe Testing Guide](https://stripe.com/docs/testing)
- [Stripe Webhooks Guide](https://stripe.com/docs/webhooks)
- [Stripe Customer Portal](https://stripe.com/docs/billing/subscriptions/integrating-customer-portal)

---

## 💡 Quick Commands Reference

```bash
# Copy environment file
cp .env.example .env

# Edit environment file
nano .env

# Run migrations
python manage.py makemigrations dashboard
python manage.py migrate

# Start Django server
python manage.py runserver

# Start Stripe webhook listener (for local testing)
stripe listen --forward-to localhost:8000/dashboard/stripe/webhook/

# Test webhook
stripe trigger customer.subscription.created
```

---

## ✅ Verification Checklist

Before going live, verify:

- [ ] Stripe account created
- [ ] API keys obtained (test or live)
- [ ] Product created with $10/month price
- [ ] Price ID copied
- [ ] Webhook endpoint configured
- [ ] Webhook secret obtained
- [ ] `.env` file created and filled
- [ ] Environment variables loaded correctly
- [ ] Django migrations applied
- [ ] Test subscription works end-to-end
- [ ] Webhooks are being received
- [ ] Customer portal accessible
- [ ] Success/cancel pages work
- [ ] For production: HTTPS enabled
- [ ] For production: Live keys configured
- [ ] For production: Business verification complete

---

**You're all set! 🎉**

The payment system is fully implemented and ready to accept subscriptions once you complete the Stripe configuration above.
