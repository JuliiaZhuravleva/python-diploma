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
            contact = Contact.objects.get(id=contact_id, user=request.user)
        except Contact.DoesNotExist:
            return Response({
                'status': False,
                'error': 'Контакт не найден'
            }, status=status.HTTP_404_NOT_FOUND)

        # Получаем корзину
        try:
            basket = Order.objects.get(user=request.user, state='basket')
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

        # Создаем заказ
        with transaction.atomic():
            basket.contact = contact
            basket.state = 'new'
            basket.save()

            # Отправляем email подтверждения
            send_order_confirmation_email.delay(basket.id)

        serializer = OrderSerializer(basket)
        return Response({
            'status': True,
            'message': 'Заказ успешно создан',
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
    def get(self, request, order_id):
        """Получение детальной информации о заказе."""
        try:
            order = Order.objects.prefetch_related(
                'ordered_items__product_info__product',
                'ordered_items__product_info__shop',
                'contact'
            ).get(id=order_id, user=request.user)
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
    def put(self, request, order_id):
        """Обновление статуса заказа."""
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response({
                'status': False,
                'error': 'Заказ не найден'
            }, status=status.HTTP_404_NOT_FOUND)

        new_state = request.data.get('state')

        # Пользователь может только отменить свой заказ
        if new_state == 'canceled' and order.state == 'new':
            order.state = 'canceled'
            order.save()

            return Response({
                'status': True,
                'message': 'Заказ отменен'
            })
        else:
            return Response({
                'status': False,
                'error': 'Невозможно изменить статус заказа'
            }, status=status.HTTP_400_BAD_REQUEST)