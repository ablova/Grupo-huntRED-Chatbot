from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('executive/', views.executive_dashboard, name='executive_dashboard'),
] 