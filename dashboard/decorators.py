"""
Decorators for subscription management
"""
from functools import wraps
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext as _


def subscription_required(view_func):
    """
    Decorator to check if user has active subscription before allowing access to rebalance features.
    Returns JSON error for AJAX requests, redirects to subscription page for regular requests.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': _('Authentication required')
                }, status=401)
            return redirect('login')

        # Get user profile
        try:
            profile = request.user.profile
        except:
            # Create profile if doesn't exist
            from dashboard.models import UserProfile
            profile = UserProfile.objects.create(user=request.user)

        # Check subscription status
        if not profile.has_active_subscription():
            subscription_info = profile.get_subscription_status_display_info()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': _('Active subscription required to use rebalancing features'),
                    'subscription_required': True,
                    'subscription_info': subscription_info
                }, status=403)
            else:
                messages.error(request, _('You need an active subscription to use rebalancing features. Subscribe for $10/month to unlock this feature.'))
                return redirect('subscription')

        # User has active subscription, proceed
        return view_func(request, *args, **kwargs)

    return wrapper


def trial_or_subscription_required(view_func):
    """
    Decorator that allows access with either active trial or subscription.
    More lenient than subscription_required.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': _('Authentication required')
                }, status=401)
            return redirect('login')

        try:
            profile = request.user.profile
        except:
            from dashboard.models import UserProfile
            profile = UserProfile.objects.create(user=request.user)

        # Check if user has active subscription OR valid trial
        if not profile.has_active_subscription():
            # Offer free trial if not used
            if not profile.trial_used:
                profile.start_free_trial(trial_days=7)
                messages.success(request, _('Free 7-day trial activated! Enjoy full access to all features.'))
                return view_func(request, *args, **kwargs)

            # No trial available and no subscription
            subscription_info = profile.get_subscription_status_display_info()

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': _('Your trial has expired. Subscribe for $10/month to continue using rebalancing features.'),
                    'subscription_required': True,
                    'subscription_info': subscription_info
                }, status=403)
            else:
                messages.error(request, _('Your trial has expired. Subscribe for $10/month to continue.'))
                return redirect('subscription')

        return view_func(request, *args, **kwargs)

    return wrapper


def admin_only(view_func):
    """
    Decorator to restrict access to admin users only.
    Useful for subscription management endpoints.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'error', 'message': 'Authentication required'}, status=401)

        if not request.user.is_staff and not request.user.is_superuser:
            return JsonResponse({'status': 'error', 'message': 'Admin access required'}, status=403)

        return view_func(request, *args, **kwargs)

    return wrapper
