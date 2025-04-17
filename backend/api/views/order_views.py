from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from backend.models import Order, Contact, OrderItem, Shop
from backend.api.serializers import OrderSerializer


class OrderView(APIView):
    """
    Представление для работы с заказами пользователя.

    GET: Получает список заказов пользователя.
    POST: Оформляет заказ из корзины.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Получение списка заказов пользователя.
        """
        orders = Order.objects.filter(
            user=request.user
        ).exclude(
            state='basket'
        ).prefetch_related(
            'ordered_items__product_info__product',
            'ordered_items__product_info__shop',
            'ordered_items__product_info__product_parameters__parameter'
        ).select_related('contact').order_by('-dt')

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        """
        Оформление заказа из корзины.

        Ожидаемый формат данных:
        {
            "id": 1,        # ID корзины
            "contact": 2     # ID контакта для доставки
        }
        """
        order_id = request.data.get('id')
        contact_id = request.data.get('contact')

        if not order_id or not contact_id:
            return Response(
                {"status": False, "error": "Не указаны обязательные поля (id, contact)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем наличие корзины
        try:
            order = Order.objects.get(
                id=order_id,
                user=request.user,
                state='basket'
            )
        except Order.DoesNotExist:
            return Response(
                {"status": False, "error": "Корзина не найдена"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверяем наличие контакта и что он не помечен как удаленный
        try:
            contact = Contact.objects.get(
                id=contact_id,
                user=request.user,
                is_deleted=False  # Проверка, что контакт не удален
            )
        except Contact.DoesNotExist:
            return Response(
                {"status": False, "error": "Контакт не найден или был удален"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Оформляем заказ
        with transaction.atomic():
            # Сначала проверяем активность всех магазинов
            # Получаем уникальные магазины из товаров в корзине
            shop_ids = OrderItem.objects.filter(order=order).values_list(
                'product_info__shop_id', flat=True
            ).distinct()

            # Проверяем активность магазинов одним запросом
            inactive_shops = Shop.objects.filter(
                id__in=shop_ids,
                state=False
            ).values_list('name', flat=True)

            if inactive_shops:
                # Формируем сообщение об ошибке с перечислением неактивных магазинов
                shops_str = ", ".join(inactive_shops)
                return Response(
                    {"status": False,
                     "error": f"Невозможно оформить заказ, так как следующие магазины не принимают заказы: {shops_str}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Теперь проверяем количество товаров в магазинах
            order_items = OrderItem.objects.filter(order=order).select_related('product_info')

            for item in order_items:
                product_info = item.product_info

                # Проверяем, хватает ли товара на складе
                if product_info.quantity < item.quantity:
                    return Response(
                        {"status": False,
                         "error": f"Недостаточное количество товара {product_info.product.name} в магазине"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Вычитаем количество из остатков
            for item in order_items:
                product_info = item.product_info
                product_info.quantity -= item.quantity
                product_info.save()

            # Меняем статус заказа
            order.state = 'new'
            order.contact = contact
            order.save()

            # Отправляем email с подтверждением заказа
            self.send_order_confirmation(order)

        # Получаем обновленные данные заказа
        order = Order.objects.filter(id=order.id).prefetch_related(
            'ordered_items__product_info__product',
            'ordered_items__product_info__shop',
            'ordered_items__product_info__product_parameters__parameter'
        ).select_related('contact').first()

        serializer = OrderSerializer(order)
        return Response(
            {"status": True, "message": "Заказ успешно оформлен", "data": serializer.data},
            status=status.HTTP_200_OK
        )

    def send_order_confirmation(self, order):
        """
        Отправка email с подтверждением заказа.
        """
        total_sum = order.get_total_cost()
        items = []

        for item in order.ordered_items.all():
            items.append(
                f"- {item.product_info.product.name}: {item.quantity} шт. x {item.product_info.price} руб. "
                f"= {item.quantity * item.product_info.price} руб."
            )

        message = f"""
        Здравствуйте, {order.user.first_name}!

        Ваш заказ №{order.id} от {order.dt.strftime('%d.%m.%Y %H:%M')} успешно оформлен.

        Состав заказа:
        {"".join(items)}

        Общая сумма заказа: {total_sum} руб.

        Адрес доставки:
        {order.contact.city}, {order.contact.street}, д. {order.contact.house},
        {'корп. ' + order.contact.structure if order.contact.structure else ''}
        {'стр. ' + order.contact.building if order.contact.building else ''}
        {'кв. ' + order.contact.apartment if order.contact.apartment else ''}

        Телефон для связи: {order.contact.phone}

        Спасибо за заказ!
        """

        send_mail(
            subject=f'Подтверждение заказа №{order.id}',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            fail_silently=False,
        )


class OrderDetailView(APIView):
    """
    Представление для получения и обновления деталей заказа.

    GET: Получает детали конкретного заказа.
    PUT: Обновляет статус заказа.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        """
        Получение деталей конкретного заказа.
        """
        try:
            order = Order.objects.filter(
                id=pk,
                user=request.user
            ).prefetch_related(
                'ordered_items__product_info__product',
                'ordered_items__product_info__shop',
                'ordered_items__product_info__product_parameters__parameter'
            ).select_related('contact').first()

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
        Отмена заказа пользователем.

        Пользователь может отменить только свой заказ и только в статусе "new".
        При отмене заказа товары возвращаются в наличие магазинов.

        Ожидаемый формат данных:
        {
            "action": "cancel"  # Действие - отмена заказа
        }
        """
        try:
            # Получаем заказ пользователя
            order = Order.objects.get(id=pk, user=request.user)

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
                {"status": True, "message": "Заказ успешно отменен", "data": serializer.data},
                status=status.HTTP_200_OK
            )
        except Order.DoesNotExist:
            return Response(
                {"status": False, "error": "Заказ не найден"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"status": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

