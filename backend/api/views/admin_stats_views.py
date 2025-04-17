from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db.models import Count, Sum, F, Avg, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta

from backend.models import Order, OrderItem, Shop, User, Product, ProductInfo
from backend.api.views.admin_views import IsAdminUser


class AdminStatsView(APIView):
    """
    Представление для получения статистики по заказам и продажам.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        Получение общей статистики по системе.

        Query parameters:
        - period: day, week, month (по умолчанию month)
        """
        period = request.query_params.get('period', 'month')

        if period == 'day':
            start_date = timezone.now() - timedelta(days=1)
        elif period == 'week':
            start_date = timezone.now() - timedelta(weeks=1)
        else:  # month
            start_date = timezone.now() - timedelta(days=30)

        # Общая статистика
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        shops_count = Shop.objects.count()
        active_shops = Shop.objects.filter(state=True).count()

        # Статистика по заказам
        orders = Order.objects.filter(dt__gte=start_date).exclude(state='basket')
        total_orders = orders.count()

        orders_by_status = orders.values('state').annotate(count=Count('id'))

        # Статистика по продажам
        order_items = OrderItem.objects.filter(
            order__dt__gte=start_date,
            order__state__in=['confirmed', 'assembled', 'sent', 'delivered']
        ).select_related('product_info')

        total_sales_amount = order_items.annotate(
            item_total=ExpressionWrapper(
                F('quantity') * F('product_info__price'),
                output_field=DecimalField()
            )
        ).aggregate(total=Sum('item_total'))['total'] or 0

        # Самые популярные товары
        popular_products = ProductInfo.objects.filter(
            ordered_items__order__dt__gte=start_date,
            ordered_items__order__state__in=['confirmed', 'assembled', 'sent', 'delivered']
        ).annotate(
            sold_quantity=Sum('ordered_items__quantity')
        ).order_by('-sold_quantity')[:10]

        # Собираем данные по продажам по дням
        sales_by_day = OrderItem.objects.filter(
            order__dt__gte=start_date,
            order__state__in=['confirmed', 'assembled', 'sent', 'delivered']
        ).annotate(
            date=TruncDate('order__dt'),
            item_total=ExpressionWrapper(
                F('quantity') * F('product_info__price'),
                output_field=DecimalField()
            )
        ).values('date').annotate(
            total=Sum('item_total'),
            orders=Count('order', distinct=True)
        ).order_by('date')

        # Формируем ответ
        response_data = {
            'general': {
                'total_users': total_users,
                'active_users': active_users,
                'shops_count': shops_count,
                'active_shops': active_shops
            },
            'orders': {
                'total_orders': total_orders,
                'by_status': orders_by_status
            },
            'sales': {
                'total_amount': total_sales_amount,
                'by_day': list(sales_by_day),
                'popular_products': [
                    {
                        'id': product.id,
                        'name': product.product.name,
                        'shop': product.shop.name,
                        'sold_quantity': product.sold_quantity
                    } for product in popular_products
                ]
            }
        }

        return Response(response_data)


class AdminCategoriesStatsView(APIView):
    """
    Представление для получения статистики по категориям товаров.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        Получение статистики по категориям.
        """
        # Статистика по категориям
        categories_stats = Product.objects.values(
            'category__id', 'category__name'
        ).annotate(
            products_count=Count('id')
        ).order_by('-products_count')

        # Статистика продаж по категориям
        sales_by_category = OrderItem.objects.filter(
            order__state__in=['confirmed', 'assembled', 'sent', 'delivered']
        ).select_related(
            'product_info__product__category'
        ).values(
            'product_info__product__category__id',
            'product_info__product__category__name'
        ).annotate(
            sold_quantity=Sum('quantity'),
            total_amount=Sum(F('quantity') * F('product_info__price'))
        ).order_by('-total_amount')

        response_data = {
            'categories': list(categories_stats),
            'sales_by_category': list(sales_by_category)
        }

        return Response(response_data)
