from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _

from backend.admin_pages import admin_dashboard, admin_import_export


class OrderServiceAdminSite(AdminSite):
    # Заголовок сайта
    site_header = _('Система управления заказами')
    # Название сайта
    site_title = _('Административная панель')
    # Текст на главной странице
    index_title = _('Добро пожаловать в административную панель')

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('dashboard/', self.admin_view(admin_dashboard), name='dashboard'),
            path('import-export/', self.admin_view(admin_import_export), name='import-export'),
        ]
        return custom + urls


# Создаем экземпляр AdminSite
admin_site = OrderServiceAdminSite(name='order_service_admin')


def setup_admin_site():
    """
    Настройка административного сайта.
    Эта функция должна вызываться после того, как все приложения загружены.
    """
    # Импортируем все модели и административные классы
    from django.contrib.auth.models import Group
    from backend.models import (
        User, Shop, Category, Product, ProductInfo, Parameter,
        ProductParameter, Contact, Order, OrderItem, ConfirmEmailToken
    )
    from backend.admin import (
        UserAdmin, ShopAdmin, CategoryAdmin, ProductAdmin,
        ProductInfoAdmin, ContactAdmin, OrderAdmin
    )

    # Регистрируем модели в нашем административном сайте
    admin_site.register(User, UserAdmin)
    admin_site.register(Shop, ShopAdmin)
    admin_site.register(Category, CategoryAdmin)
    admin_site.register(Product, ProductAdmin)
    admin_site.register(ProductInfo, ProductInfoAdmin)
    admin_site.register(Parameter)
    admin_site.register(Contact, ContactAdmin)
    admin_site.register(Order, OrderAdmin)
    admin_site.register(ConfirmEmailToken)
    admin_site.register(Group)