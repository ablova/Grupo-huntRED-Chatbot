from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'authentication'

urlpatterns = [
    # Autenticación JWT
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    
    # Registro y perfil
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('user-info/', views.user_info, name='user_info'),
    
    # Gestión de contraseñas
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # Administración (solo admin)
    path('login-attempts/', views.LoginAttemptsView.as_view(), name='login_attempts'),
] 