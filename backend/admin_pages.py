from django.urls import path
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count, Sum, F
from django.utils import timezone
from datetime import timedelta


@staff_member_required
def admin_dashboard(request):
    """
    Представление для общей панели администратора с ключевыми показателями.
    """
    # Импортируем модели здесь, а не на уровне модуля
    from .models import Order, User, Shop, Product

    # Статистика пользователей
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()

    # Статистика заказов
    total_orders = Order.objects.exclude(state='basket').count()

    # Заказы за последний месяц
    month_ago = timezone.now() - timedelta(days=30)
    recent_orders = Order.objects.filter(dt__gte=month_ago).exclude(state='basket')

    # Статистика по статусам
    orders_by_status = Order.objects.exclude(state='basket').values('state').annotate(count=Count('id'))

    # Популярные товары
    popular_products = Product.objects.annotate(
        order_count=Count('product_info__ordered_items')
    ).order_by('-order_count')[:5]

    # Подготовка контекста для шаблона
    context = {
        'title': 'Административная панель',
        'total_users': total_users,
        'active_users': active_users,
        'total_orders': total_orders,
        'recent_orders_count': recent_orders.count(),
        'orders_by_status': orders_by_status,
        'popular_products': popular_products,
    }

    return render(request, 'admin/dashboard.html', context)


@staff_member_required
def admin_import_export(request):
    """
    Представление для страницы импорта/экспорта данных.
    """
    # Импортируем модели здесь
    from .models import Shop

    shops = Shop.objects.all()

    context = {
        'title': 'Импорт и экспорт данных',
        'shops': shops,
    }

    return render(request, 'admin/import_export.html', context)


# URL-паттерны для админ-страниц
admin_urls = [
    path('dashboard/', admin_dashboard, name='admin-dashboard'),
    path('import-export/', admin_import_export, name='admin-import-export'),
]