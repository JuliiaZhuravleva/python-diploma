from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings

from backend.models import Order, OrderItem, Shop
from backend.api.serializers import OrderSerializer


class IsAdminUser(permissions.BasePermission):
    """
    Пользовательское разрешение для проверки, что пользователь является администратором.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class AdminOrdersView(APIView):
    """
    Представление для административного управления заказами.

    GET: Получает список всех заказов в системе.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        Получение списка всех заказов для администратора.
        """
        orders = Order.objects.exclude(
            state='basket'
        ).prefetch_related(
            'ordered_items__product_info__product',
            'ordered_items__product_info__shop',
            'ordered_items__product_info__product_parameters__parameter'
        ).select_related('contact', 'user').order_by('-dt')

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)


class AdminOrderDetailView(APIView):
    """
    Представление для получения и обновления деталей заказа администратором.

    GET: Получает детали конкретного заказа.
    PUT: Обновляет статус заказа.
    """
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        """
        Получение деталей конкретного заказа.
        """
        try:
            order = Order.objects.filter(
                id=pk
            ).prefetch_related(
                'ordered_items__product_info__product',
                'ordered_items__product_info__shop',
                'ordered_items__product_info__product_parameters__parameter'
            ).select_related('contact', 'user').first()

            if not order:
                return Response(
                    {"status": False, "error": "Заказ не найден"},
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = OrderSerializer(order)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"status": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def put(self, request, pk):
        """
        Обновление статуса заказа администратором.

        Ожидаемый формат данных:
        {
            "state": "confirmed"  # Новый статус заказа
        }

        Доступные статусы:
        - new - новый заказ
        - confirmed - подтвержден
        - assembled - собран
        - sent - отправлен
        - delivered - доставлен
        - canceled - отменен
        """
        try:
            new_status = request.data.get('state')
            if not new_status:
                return Response(
                    {"status": False, "error": "Не указан новый статус заказа"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            valid_statuses = ['new', 'confirmed', 'assembled', 'sent', 'delivered', 'canceled']
            if new_status not in valid_statuses:
                return Response(
                    {"status": False, "error": f"Недопустимый статус. Допустимые статусы: {', '.join(valid_statuses)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Получаем заказ
            order = Order.objects.filter(id=pk).select_related('user', 'contact').first()
            if not order:
                return Response(
                    {"status": False, "error": "Заказ не найден"},
                    status=status.HTTP_404_NOT_FOUND
                )

            old_status = order.state

            # Если заказ отменяют, то возвращаем товары в наличие
            if new_status == 'canceled' and old_status != 'canceled':
                with transaction.atomic():
                    order_items = OrderItem.objects.filter(order=order).select_related('product_info')

                    for item in order_items:
                        product_info = item.product_info
                        # Увеличиваем количество товара в магазине
                        product_info.quantity += item.quantity
                        product_info.save()

            # Обновляем статус заказа
            order.state = new_status
            order.save()

            # Отправляем уведомление клиенту об изменении статуса заказа
            self.send_order_status_notification(order, old_status)

            serializer = OrderSerializer(order)
            return Response(
                {"status": True, "message": f"Статус заказа изменен на {new_status}", "data": serializer.data},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"status": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def send_order_status_notification(self, order, old_status):
        """
        Отправка email-уведомления клиенту при изменении статуса заказа.
        """
        status_display = {
            'new': 'Новый',
            'confirmed': 'Подтвержден',
            'assembled': 'Собран',
            'sent': 'Отправлен',
            'delivered': 'Доставлен',
            'canceled': 'Отменен'
        }

        message = f"""
        Здравствуйте, {order.user.first_name}!

        Статус Вашего заказа №{order.id} от {order.dt.strftime('%d.%m.%Y %H:%M')} был изменен с 
        "{status_display.get(old_status, old_status)}" на "{status_display.get(order.state, order.state)}".

        """

        if order.state == 'canceled':
            message += "К сожалению, Ваш заказ был отменен. Если у Вас есть вопросы, свяжитесь с нашей службой поддержки."
        elif order.state == 'confirmed':
            message += "Ваш заказ подтвержден и передан в обработку. Мы сообщим Вам, когда он будет собран."
        elif order.state == 'assembled':
            message += "Ваш заказ собран и готов к отправке. Скоро он будет передан в службу доставки."
        elif order.state == 'sent':
            message += "Ваш заказ передан в службу доставки. Ожидайте доставку в ближайшее время."
        elif order.state == 'delivered':
            message += "Ваш заказ доставлен. Спасибо за покупку!"

        message += f"""

        Детали заказа:
        Дата заказа: {order.dt.strftime('%d.%m.%Y %H:%M')}
        Адрес доставки: {order.contact.city}, {order.contact.street}, д. {order.contact.house}
        {"корп. " + order.contact.structure if order.contact.structure else ""}
        {"стр. " + order.contact.building if order.contact.building else ""}
        {"кв. " + order.contact.apartment if order.contact.apartment else ""}

        Телефон для связи: {order.contact.phone}

        С уважением,
        Команда поддержки
        """

        send_mail(
            subject=f'Изменение статуса заказа №{order.id}',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            fail_silently=False,
        )
