from django.urls import path
from . import views

app_name = 'referrals'

urlpatterns = [
    path('', views.referral_dashboard, name='dashboard'),
    path('create/', views.create_referral, name='create'),
    path('<int:referral_id>/', views.referral_detail, name='detail'),
    path('<int:referral_id>/validate/', views.validate_referral, name='validate'),
    path('<int:referral_id>/reject/', views.reject_referral, name='reject'),
    path('stats/', views.referral_stats, name='stats'),
    path('search/', views.search_referrals, name='search'),
] 