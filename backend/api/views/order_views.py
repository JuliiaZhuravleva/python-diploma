from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import transaction
from django.db.models import F, Sum, Prefetch

from backend.models import Order, OrderItem, Contact
from backend.api.serializers import OrderSerializer, OrderItemSerializer
from backend.tasks import send_order_confirmation_email

# Импорты для системы документации
from backend.api.docs import (
    crud_endpoint,
    get_success_response,
    get_error_response,
    ORDER_EXAMPLES
)


class OrderView(APIView):
    """
    Представление для работы с заказами пользователя.

    Позволяет получать список заказов и создавать новые заказы.
    """
    permission_classes = [permissions.IsAuthenticated]

    @crud_endpoint(
        operation='list',
        resource='orders',
        summary="Получить список заказов",
        description="Возвращает список всех заказов текущего пользователя",
        responses={200: OrderSerializer(many=True)}
    )
    def get(self, request):
        """Получение списка заказов пользователя."""
        orders = Order.objects.filter(
            user=request.user,
        ).exclude(
            state='basket'
        ).prefetch_related(
            'ordered_items__product_info__product',
            'ordered_items__product_info__shop',
            'contact'
        ).annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product_info__price'))
        ).order_by('-dt')

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    @crud_endpoint(
        operation='create',
        resource='orders',
        summary="Создать заказ",
        description="Оформляет заказ из корзины с указанным адресом доставки",
        examples=[ORDER_EXAMPLES['order_create_request']],
        responses={
            201: get_success_response("Заказ успешно создан", with_data=True),
            400: get_error_response("Корзина пуста или не найдена"),
            404: get_error_response("Контакт не найден")
        }
    )
    def post(self, request):
        """Создание заказа из корзины."""
        contact_id = request.data.get('contact')

        if not contact_id:
            return Response({
                'status': False,
                'error': 'Не указан адрес доставки'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем существование контакта
        try:
            contact = Contact.objects.get(id=contact_id, user=request.user, is_deleted=False)
        except Contact.DoesNotExist:
            return Response({
                'status': False,
                'error': 'Контакт не найден или был удален'
            }, status=status.HTTP_404_NOT_FOUND)

        # Получаем корзину
        try:
            basket = Order.objects.filter(user=request.user, state='basket').first()
            if not basket:
                return Response({
                    'status': False,
                    'error': 'Корзина не найдена'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Order.DoesNotExist:
            return Response({
                'status': False,
                'error': 'Корзина не найдена'
            }, status=status.HTTP_400_BAD_REQUEST)

        if basket.ordered_items.count() == 0:
            return Response({
                'status': False,
                'error': 'Корзина пуста'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем, что все товары из активных магазинов
        inactive_items = basket.ordered_items.filter(product_info__shop__state=False)
        if inactive_items.exists():
            return Response({
                'status': False,
                'error': 'Магазины не принимают заказы'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Проверяем достаточность количества товаров
        for item in basket.ordered_items.all():
            if item.product_info.quantity < item.quantity:
                return Response({
                    'status': False,
                    'error': f'Недостаточное количество товара {item.product_info.product.name}'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Создаем заказ
        with transaction.atomic():
            basket.contact = contact
            basket.state = 'new'
            basket.save()

            # Списываем товар со склада
            for order_item in basket.ordered_items.all():
                product_info = order_item.product_info
                if product_info.quantity >= order_item.quantity:
                    product_info.quantity -= order_item.quantity
                    product_info.save()
                else:
                    # Если товара недостаточно, откатываем транзакцию
                    raise ValueError(f"Недостаточное количество товара {product_info.product.name}")

            # Отправляем email подтверждения
            send_order_confirmation_email.delay(basket.id)

        serializer = OrderSerializer(basket)
        return Response({
            'status': True,
            'message': 'Заказ успешно оформлен',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class OrderDetailView(APIView):
    """
    Представление для работы с детальной информацией о заказе.
    """
    permission_classes = [permissions.IsAuthenticated]

    @crud_endpoint(
        operation='read',
        resource='orders',
        summary="Получить детали заказа",
        description="Возвращает подробную информацию о конкретном заказе",
        responses={
            200: OrderSerializer,
            404: get_error_response("Заказ не найден")
        }
    )
    def get(self, request, pk):
        """Получение детальной информации о заказе."""
        try:
            order = Order.objects.prefetch_related(
                'ordered_items__product_info__product',
                'ordered_items__product_info__shop',
                'contact'
            ).get(id=pk, user=request.user)
        except Order.DoesNotExist:
            return Response({
                'status': False,
                'error': 'Заказ не найден'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = OrderSerializer(order)
        return Response(serializer.data)

    @crud_endpoint(
        operation='update',
        resource='orders',
        summary="Обновить статус заказа",
        description="Позволяет отменить заказ (только для заказов в статусе 'new')",
        responses={
            200: get_success_response("Статус заказа обновлен"),
            400: get_error_response("Невозможно изменить статус заказа"),
            404: get_error_response("Заказ не найден")
        }
    )
    def put(self, request, pk):
        """Обновление статуса заказа."""
        try:
            order = Order.objects.get(id=pk, user=request.user)
        except Order.DoesNotExist:
            return Response({
                'status': False,
                'error': 'Заказ не найден'
            }, status=status.HTTP_404_NOT_FOUND)

        # Проверяем, что заказ в статусе "new"
        if order.state != 'new':
            return Response(
                {"status": False, "error": "Отменить можно только новый заказ"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем действие
        action = request.data.get('action')
        if action != 'cancel':
            return Response(
                {"status": False, "error": "Неизвестное действие. Допустимое действие: 'cancel'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Начинаем транзакцию для отмены заказа
        with transaction.atomic():
            # Возвращаем товары в наличие
            order_items = OrderItem.objects.filter(order=order).select_related('product_info')

            for item in order_items:
                product_info = item.product_info
                # Увеличиваем количество товара в магазине
                product_info.quantity += item.quantity
                product_info.save()

            # Меняем статус заказа на 'canceled'
            order.state = 'canceled'
            order.save()

        serializer = OrderSerializer(order)
        return Response(
            {"status": True, "message": "Заказ отменен", "data": serializer.data},
            status=status.HTTP_200_OK
        )