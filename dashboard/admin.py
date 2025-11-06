from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, TraderSession, TradeHistory


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fieldsets = (
        ('Subscription', {
            'fields': ('subscription_status', 'subscription_start_date', 'subscription_end_date',
                      'trial_used', 'trial_end_date')
        }),
        ('Payment Integration (Future)', {
            'fields': ('payment_provider', 'payment_customer_id', 'payment_subscription_id'),
            'classes': ('collapse',)
        }),
        ('Binance Credentials', {
            'fields': ('binance_api_key_encrypted', 'binance_api_secret_encrypted')
        }),
        ('CoinMarketCap', {
            'fields': ('cmc_api_key',)
        }),
        ('Settings', {
            'fields': ('default_interval', 'auto_rebalance', 'created_at', 'updated_at')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(TraderSession)
class TraderSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_running', 'dry_run_mode', 'next_run_time', 'last_run_time', 'updated_at')
    list_filter = ('is_running', 'dry_run_mode', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'last_portfolio', 'last_rebalance_result')


@admin.register(TradeHistory)
class TradeHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'trade_type', 'dry_run', 'success', 'created_at')
    list_filter = ('trade_type', 'dry_run', 'success', 'created_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'trade_data', 'error_message')
    ordering = ('-created_at',)
