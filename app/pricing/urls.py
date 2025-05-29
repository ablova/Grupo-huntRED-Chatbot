"""
URLs para el módulo de precios.
"""
from django.urls import path
from . import views

app_name = 'pricing'

urlpatterns = [
    # API para aplicar códigos de descuento
    path('api/apply-coupon/', views.apply_coupon, name='apply_coupon'),
    
    # Evaluaciones de equipo
    path('team-evaluation/request/', views.request_team_evaluation, name='request_team_evaluation'),
    path('team-evaluation/<uuid:pk>/', views.team_evaluation_detail, name='team_evaluation_detail'),
    path('team-evaluation/<uuid:pk>/complete/', views.complete_team_evaluation, name='complete_team_evaluation'),
    
    # Gestión de promociones (solo staff)
    path('promotions/', views.promotion_list, name='promotion_list'),
    path('promotions/create/', views.promotion_create, name='promotion_create'),
    path('promotions/<int:pk>/edit/', views.promotion_edit, name='promotion_edit'),
    path('promotions/<int:pk>/delete/', views.promotion_delete, name='promotion_delete'),
    
    # Cupones de descuento
    path('coupons/', views.coupon_list, name='coupon_list'),
    path('coupons/create/', views.coupon_create, name='coupon_create'),
    path('coupons/<int:pk>/', views.coupon_detail, name='coupon_detail'),
    path('coupons/<int:pk>/delete/', views.coupon_delete, name='coupon_delete'),
]
