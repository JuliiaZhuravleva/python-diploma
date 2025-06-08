from django.urls import path

from backend.api.views.basket_views import BasketView
from backend.api.views.celery_views import TaskStatusView
from backend.api.views.order_views import OrderView, OrderDetailView
from backend.api.views.partner_views import PartnerUpdateView, PartnerStateView, PartnerOrdersView
from backend.api.views.product_views import ProductView, ProductDetailView, ProductImageUploadView
from backend.api.views.user_views import (
    UserRegisterView, ConfirmEmailView, UserLoginView, UserDetailsView,
    PasswordResetRequestView, PasswordResetConfirmView, ContactViewSet,
    UserAvatarUploadView
)
from backend.api.views.shop_views import ShopView, CategoryView
from backend.api.views import TestAuthView
from backend.api.views.debug_views import (
    test_zero_division_error,
    test_unhandled_exception,
    test_database_error,
    test_slow_request,
    test_success,
    test_custom_exception
)
from order_service import settings

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
    path('user/avatar', UserAvatarUploadView.as_view(), name='user-avatar'),

    # URL для магазинов
    path('shops', ShopView.as_view(), name='shops'),
    path('categories', CategoryView.as_view(), name='categories'),
    path('products', ProductView.as_view(), name='products'),
    path('products/<int:pk>', ProductDetailView.as_view(), name='product-detail'),
    path('products/<int:product_id>/image', ProductImageUploadView.as_view(), name='product-image'),

    # URL для корзины и заказов
    path('basket', BasketView.as_view(), name='basket'),
    path('order', OrderView.as_view(), name='order'),
    path('order/<int:pk>', OrderDetailView.as_view(), name='order-detail'),

    # URL для партнеров (магазинов)
    path('partner/update', PartnerUpdateView.as_view(), name='partner-update'),
    path('partner/state', PartnerStateView.as_view(), name='partner-state'),
    path('partner/orders', PartnerOrdersView.as_view(), name='partner-orders'),

    # URL для Celery
    path('task/<str:task_id>', TaskStatusView.as_view(), name='task-status'),

    # Debug endpoints для тестирования Sentry (только для разработки)
    ] + ([] if not settings.DEBUG else [
    path('debug/sentry/zero-division/', test_zero_division_error, name='debug-zero-division'),
    path('debug/sentry/unhandled-exception/', test_unhandled_exception, name='debug-unhandled-exception'),
    path('debug/sentry/database-error/', test_database_error, name='debug-database-error'),
    path('debug/sentry/slow-request/', test_slow_request, name='debug-slow-request'),
    path('debug/sentry/success/', test_success, name='debug-success'),
    path('debug/sentry/custom-exception/', test_custom_exception, name='debug-custom-exception'),
])