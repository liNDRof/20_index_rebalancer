from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('start/', views.start_trader, name='start_trader'),
    path('stop/', views.stop_trader, name='stop_trader'),
    path('status/', views.get_status, name='status'),
    path('refresh_portfolio/', views.refresh_portfolio, name='refresh_portfolio'),
    path('update_default_interval/', views.update_default_interval, name='update_default_interval'),
    path('set_next_rebalance_time/', views.set_next_rebalance_time, name='set_next_rebalance_time'),
    path('manual_rebalance/', views.manual_rebalance, name='manual_rebalance'),
    path('toggle_dry_run/', views.toggle_dry_run, name='toggle_dry_run'),
]
