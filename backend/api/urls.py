from django.urls import path
from backend.api.views.user_views import (
    UserRegisterView, ConfirmEmailView, UserLoginView, UserDetailsView,
    PasswordResetRequestView, PasswordResetConfirmView, ContactViewSet
)
from backend.api.views import TestAuthView

app_name = 'api'

urlpatterns = [
    # Тестовый URL для проверки аутентификации
    path('test-auth/', TestAuthView.as_view(), name='test-auth'),

    # Пользовательские URL
    path('user/register', UserRegisterView.as_view(), name='user-register'),
    path('user/register/confirm', ConfirmEmailView.as_view(), name='user-register-confirm'),
    path('user/login', UserLoginView.as_view(), name='user-login'),
    path('user/details', UserDetailsView.as_view(), name='user-details'),
    path('user/password_reset', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('user/password_reset/confirm', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    path('user/contact', ContactViewSet.as_view(), name='user-contact'),
]