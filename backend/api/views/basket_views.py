import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import transaction
from django.db.models import F
from backend.models import Order, OrderItem, ProductInfo
from backend.api.serializers import OrderSerializer, OrderItemSerializer


class BasketView(APIView):
    """
    Представление для работы с корзиной пользователя.

    GET: Получает текущее содержимое корзины пользователя.
    POST: Добавляет товары в корзину.
    PUT: Обновляет количество товаров в корзине.
    DELETE: Удаляет товары из корзины.
    """
    permission_classes = [permissions.IsAuthenticated]

    def parse_items_data(self, request):
        items_data = request.data.get('items')
        if not items_data:
            return None, Response(
                {"status": False, "error": "Не указаны товары для обработки"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if isinstance(items_data, list):
            return items_data, None

        try:
            items_list = json.loads(items_data)
            return items_list, None
        except (json.JSONDecodeError, TypeError):
            return None, Response(
                {"status": False, "error": "Неверный формат данных"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get(self, request):
        """
        Получение содержимого корзины пользователя.
        """
        basket = Order.objects.filter(
            user=request.user,
            state='basket'
        ).prefetch_related(
            'ordered_items__product_info__product',
            'ordered_items__product_info__shop',
            'ordered_items__product_info__product_parameters__parameter'
        ).first()

        if not basket:
            return Response(
                {"status": False, "error": "Корзина пуста"},
                status=status.HTTP_200_OK
            )

        serializer = OrderSerializer(basket)
        return Response(serializer.data)

    def post(self, request):
        """
        Добавление товаров в корзину.

        Ожидаемый формат данных:
        {
            "items": [
                {
                    "product_info": 1,  # ID информации о товаре
                    "quantity": 2       # Количество
                },
                ...
            ]
        }
        """

        items_list, error_response = self.parse_items_data(request)
        if error_response:
            return error_response

        # Получаем или создаем корзину
        with transaction.atomic():
            basket, _ = Order.objects.get_or_create(
                user=request.user,
                state='basket'
            )

            for item in items_list:
                product_info_id = item.get('product_info')
                quantity = item.get('quantity')

                if not product_info_id or not quantity:
                    continue

                # Проверяем наличие товара
                try:
                    product_info = ProductInfo.objects.select_related('shop').get(id=product_info_id)
                    if product_info.shop.state:
                        # Проверяем наличие достаточного количества товара
                        if product_info.quantity >= quantity:
                            # Ищем существующую позицию в корзине
                            order_item = OrderItem.objects.filter(
                                order=basket,
                                product_info=product_info
                            ).first()

                            if order_item:
                                # Обновляем существующую позицию
                                order_item.quantity = F('quantity') + quantity
                                order_item.save()
                            else:
                                # Создаем новую позицию
                                OrderItem.objects.create(
                                    order=basket,
                                    product_info=product_info,
                                    quantity=quantity
                                )
                        else:
                            return Response(
                                {"status": False,
                                 "error": f"Недостаточное количество товара {product_info.product.name}"},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                    else:
                        return Response(
                            {"status": False, "error": f"Магазин {product_info.shop.name} не принимает заказы"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except ProductInfo.DoesNotExist:
                    return Response(
                        {"status": False, "error": f"Товар с ID {product_info_id} не найден"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Получаем обновленные данные корзины
            basket = Order.objects.filter(id=basket.id).prefetch_related(
                'ordered_items__product_info__product',
                'ordered_items__product_info__shop',
                'ordered_items__product_info__product_parameters__parameter'
            ).first()

        serializer = OrderSerializer(basket)
        return Response(
            {"status": True, "message": "Товары добавлены в корзину", "data": serializer.data},
            status=status.HTTP_201_CREATED
        )

    def put(self, request):
        """
        Обновление количества товаров в корзине.

        Ожидаемый формат данных:
        {
            "items": [
                {
                    "id": 1,          # ID позиции в корзине
                    "quantity": 5      # Новое количество
                },
                ...
            ]
        }
        """

        items_list, error_response = self.parse_items_data(request)
        if error_response:
            return error_response

        # Получаем корзину пользователя
        basket = Order.objects.filter(
            user=request.user,
            state='basket'
        ).prefetch_related('ordered_items').first()

        if not basket:
            return Response(
                {"status": False, "error": "Корзина не найдена"},
                status=status.HTTP_404_NOT_FOUND
            )

        with transaction.atomic():
            for item in items_list:
                order_item_id = item.get('id')
                quantity = item.get('quantity')

                if not order_item_id or not quantity:
                    continue

                try:
                    order_item = OrderItem.objects.get(
                        id=order_item_id,
                        order=basket
                    )

                    # Проверяем наличие достаточного количества товара
                    if order_item.product_info.quantity >= quantity:
                        order_item.quantity = quantity
                        order_item.save()
                    else:
                        return Response(
                            {"status": False,
                             "error": f"Недостаточное количество товара {order_item.product_info.product.name}"},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except OrderItem.DoesNotExist:
                    return Response(
                        {"status": False, "error": f"Позиция с ID {order_item_id} не найдена в корзине"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Получаем обновленные данные корзины
            basket = Order.objects.filter(id=basket.id).prefetch_related(
                'ordered_items__product_info__product',
                'ordered_items__product_info__shop',
                'ordered_items__product_info__product_parameters__parameter'
            ).first()

        serializer = OrderSerializer(basket)
        return Response(
            {"status": True, "message": "Корзина обновлена", "data": serializer.data},
            status=status.HTTP_200_OK
        )

    def delete(self, request):
        """
        Удаление товаров из корзины.

        Ожидаемый формат данных:
        {
            "items": "1,2,3"  # Строка с ID позиций в корзине через запятую
        }
        """
        items_str = request.data.get('items')
        if not items_str:
            return Response(
                {"status": False, "error": "Не указаны товары для удаления"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Преобразуем строку с id в список
        try:
            items_ids = [int(item) for item in items_str.split(',')]
        except ValueError:
            return Response(
                {"status": False, "error": "Неверный формат списка ID"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Получаем корзину пользователя
        basket = Order.objects.filter(
            user=request.user,
            state='basket'
        ).first()

        if not basket:
            return Response(
                {"status": False, "error": "Корзина не найдена"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Удаляем указанные позиции из корзины
        deleted_count, _ = OrderItem.objects.filter(
            order=basket,
            id__in=items_ids
        ).delete()

        # Получаем обновленные данные корзины
        basket = Order.objects.filter(id=basket.id).prefetch_related(
            'ordered_items__product_info__product',
            'ordered_items__product_info__shop',
            'ordered_items__product_info__product_parameters__parameter'
        ).first()

        if basket.ordered_items.count() == 0:
            basket.delete()
            return Response(
                {"status": True, "message": f"Удалено позиций: {deleted_count}. Корзина пуста."},
                status=status.HTTP_200_OK
            )

        serializer = OrderSerializer(basket)
        return Response(
            {"status": True, "message": f"Удалено позиций: {deleted_count}", "data": serializer.data},
            status=status.HTTP_200_OK
        )
