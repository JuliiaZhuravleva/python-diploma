from django.urls import path

from backend.api.views.basket_views import BasketView
from backend.api.views.order_views import OrderView, OrderDetailView
from backend.api.views.partner_views import PartnerUpdateView, PartnerStateView, PartnerOrdersView
from backend.api.views.product_views import ProductView, ProductDetailView
from backend.api.views.user_views import (
    UserRegisterView, ConfirmEmailView, UserLoginView, UserDetailsView,
    PasswordResetRequestView, PasswordResetConfirmView, ContactViewSet
)
from backend.api.views.shop_views import ShopView, CategoryView
from backend.api.views.admin_views import AdminOrdersView, AdminOrderDetailView
from backend.api.views.export_views import ExportProductsView
from backend.api.views.admin_stats_views import AdminStatsView, AdminCategoriesStatsView
from backend.api.views.admin_user_views import AdminUsersView, AdminUserDetailView
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

    # URL для магазинов
    path('shops', ShopView.as_view(), name='shops'),
    path('categories', CategoryView.as_view(), name='categories'),
    path('products', ProductView.as_view(), name='products'),
    path('products/<int:pk>', ProductDetailView.as_view(), name='product-detail'),

    # URL для корзины и заказов
    path('basket', BasketView.as_view(), name='basket'),
    path('order', OrderView.as_view(), name='order'),
    path('order/<int:pk>', OrderDetailView.as_view(), name='order-detail'),

    # URL для партнеров (магазинов)
    path('partner/update', PartnerUpdateView.as_view(), name='partner-update'),
    path('partner/state', PartnerStateView.as_view(), name='partner-state'),
    path('partner/orders', PartnerOrdersView.as_view(), name='partner-orders'),

    # URL для администратора
    path('admin/orders', AdminOrdersView.as_view(), name='admin-orders'),
    path('admin/orders/<int:pk>', AdminOrderDetailView.as_view(), name='admin-order-detail'),
    path('admin/users', AdminUsersView.as_view(), name='admin-users'),
    path('admin/users/<int:pk>', AdminUserDetailView.as_view(), name='admin-user-detail'),

    # URL для экспорта товаров
    path('partner/export', ExportProductsView.as_view(), name='partner-export'),

    # URL для статистики
    path('admin/stats', AdminStatsView.as_view(), name='admin-stats'),
    path('admin/stats/categories', AdminCategoriesStatsView.as_view(), name='admin-categories-stats')
]