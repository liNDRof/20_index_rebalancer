# PythonAnywhere Deployment Checklist

Use this checklist to ensure you've completed all steps for deployment.

## Pre-Deployment (Local)

- [ ] All code tested locally
- [ ] Requirements.txt updated with exact versions
- [ ] .gitignore configured properly
- [ ] Sensitive data removed from code
- [ ] Git repository pushed to GitHub/GitLab
- [ ] Stripe account set up with live keys
- [ ] PythonAnywhere account created

## PythonAnywhere Setup

- [ ] Code uploaded (via Git or Files tab)
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] .env file created with all variables
- [ ] SECRET_KEY generated and added to .env
- [ ] DEBUG=False set in .env
- [ ] STRIPE keys (live) added to .env
- [ ] DOMAIN set to your PythonAnywhere URL

## Database Setup

- [ ] Migrations run (`python manage.py migrate`)
- [ ] Superuser created (`python manage.py createsuperuser`)
- [ ] Test data created if needed

## Web App Configuration

- [ ] Web app created (Manual configuration)
- [ ] WSGI file configured (copied from pythonanywhere_wsgi.py)
- [ ] Virtual environment path set
- [ ] Static files mapping: `/static/` → `/home/USERNAME/20_index_rebalancer/staticfiles`
- [ ] Media files mapping: `/media/` → `/home/USERNAME/20_index_rebalancer/media`
- [ ] Static files collected (`python manage.py collectstatic`)

## Production Settings

- [ ] ALLOWED_HOSTS configured correctly
- [ ] HTTPS security settings enabled
- [ ] STATIC_ROOT path correct for PythonAnywhere
- [ ] MEDIA_ROOT path correct for PythonAnywhere

## Stripe Configuration

- [ ] Webhook endpoint created in Stripe dashboard
- [ ] Webhook URL: `https://USERNAME.pythonanywhere.com/subscription/webhook/`
- [ ] Webhook events selected (checkout, invoice, subscription)
- [ ] Webhook secret added to .env
- [ ] Payment flow tested

## Testing

- [ ] Homepage loads without errors
- [ ] Admin panel accessible
- [ ] User registration works
- [ ] User login works
- [ ] Trial activation works
- [ ] Subscription payment flow works
- [ ] Static files loading (CSS/JS)
- [ ] No errors in error log

## Security

- [ ] DEBUG = False in production
- [ ] SECRET_KEY is unique and secret
- [ ] .env file not committed to Git
- [ ] HTTPS enabled (paid account only)
- [ ] Security headers configured

## Post-Deployment

- [ ] Monitor error logs for issues
- [ ] Test all critical functionality
- [ ] Set up database backup routine
- [ ] Document any custom configuration
- [ ] Configure scheduled tasks (if needed)

## Optional Enhancements

- [ ] Custom domain configured
- [ ] Email notifications configured
- [ ] Error monitoring (Sentry, etc.)
- [ ] Performance monitoring
- [ ] Database backup automation

---

## Quick Commands Reference

```bash
# Activate virtual environment
workon crypto_env

# Update code from Git
cd ~/20_index_rebalancer
git pull origin main

# Install/update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser

# View error logs
tail -f /var/log/USERNAME.pythonanywhere.com.error.log

# Django shell (for debugging)
python manage.py shell
```

Remember to reload your web app after making changes!
