from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from backend.api.serializers import OrderSerializer, OrderItemSerializer, ContactSerializer
from backend.models import Shop, Order
from backend.services.import_service import ImportService
from backend.tasks import import_shop_data_task



class PartnerUpdateView(APIView):
    """
    Представление для обновления прайс-листа партнера (магазина).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Обновление прайс-листа магазина из указанного URL.

        Ожидаемый формат данных:
        {
            "url": "https://example.com/price.yaml"  // URL прайс-листа в формате YAML
        }
        """
        # Проверяем, что пользователь является магазином
        if request.user.type != 'shop':
            return Response(
                {"status": False, "error": "Только пользователи с типом 'магазин' могут обновлять прайс-листы"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Проверяем наличие URL
        url = request.data.get('url')
        if not url:
            return Response(
                {"status": False, "error": "Необходимо указать URL прайс-листа"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Запуск асинхронной задачи для импорта данных
        task = import_shop_data_task.delay(url, request.user.id)

        return Response({
            "status": True,
            "message": "Импорт данных запущен асинхронно. Результат будет доступен позже.",
            "task_id": task.id
        })


class PartnerStateView(APIView):
    """
    Представление для работы с состоянием партнера (магазина).

    GET: Получение текущего статуса магазина.
    POST: Изменение статуса магазина.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Получение текущего статуса магазина пользователя.
        """
        # Проверяем, что пользователь является партнером
        if request.user.type != 'shop':
            return Response(
                {"status": False, "error": "Только пользователи с типом 'магазин' имеют доступ"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            shop = Shop.objects.get(user=request.user)
            return Response({
                "status": True,
                "state": shop.state,
                "name": shop.name,
                "url": shop.url
            })
        except Shop.DoesNotExist:
            return Response(
                {"status": False, "error": "Магазин не найден"},
                status=status.HTTP_404_NOT_FOUND
            )

    def post(self, request):
        """
        Изменение статуса магазина.

        Ожидаемый формат данных:
        {
            "state": "on" или "off"  # Новый статус магазина
        }
        """
        # Проверяем, что пользователь является партнером
        if request.user.type != 'shop':
            return Response(
                {"status": False, "error": "Только пользователи с типом 'магазин' имеют доступ"},
                status=status.HTTP_403_FORBIDDEN
            )

        state_param = request.data.get('state')
        if state_param not in ['on', 'off']:
            return Response(
                {"status": False, "error": "Параметр state должен быть 'on' или 'off'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Преобразуем текстовый параметр в булево значение
        new_state = (state_param == 'on')

        try:
            shop = Shop.objects.get(user=request.user)
            shop.state = new_state
            shop.save()

            return Response({
                "status": True,
                "message": f"Статус магазина изменен на {'включен' if new_state else 'выключен'}"
            })
        except Shop.DoesNotExist:
            return Response(
                {"status": False, "error": "Магазин не найден"},
                status=status.HTTP_404_NOT_FOUND
            )


class PartnerOrdersView(APIView):
    """
    Представление для получения списка заказов партнера (магазина).
    Магазин видит только те позиции заказов, которые содержат его товары.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Получение списка заказов, содержащих товары магазина пользователя.
        Для каждого заказа возвращаются только позиции, относящиеся к данному магазину.
        """
        # Проверяем, что пользователь является партнером
        if request.user.type != 'shop':
            return Response(
                {"status": False, "error": "Только пользователи с типом 'магазин' имеют доступ"},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            shop = Shop.objects.get(user=request.user)

            # Получаем заказы, содержащие товары данного магазина
            orders = Order.objects.filter(
                ordered_items__product_info__shop=shop
            ).exclude(
                state='basket'
            ).prefetch_related(
                'ordered_items__product_info__product',
                'ordered_items__product_info__shop',
                'ordered_items__product_info__product_parameters__parameter'
            ).select_related('contact').distinct().order_by('-dt')

            # Создаем модифицированный список заказов, в котором каждый заказ содержит
            # только позиции, относящиеся к данному магазину
            shop_orders = []

            for order in orders:
                # Фильтруем позиции заказа, оставляя только относящиеся к данному магазину
                shop_items = [
                    item for item in order.ordered_items.all()
                    if item.product_info.shop.id == shop.id
                ]

                # Если в заказе есть позиции от этого магазина
                if shop_items:
                    # Создаем сериализатор для базовой информации о заказе
                    order_data = {
                        'id': order.id,
                        'dt': order.dt,
                        'state': order.state,
                        'contact': ContactSerializer(order.contact).data if order.contact else None,
                        # Включаем только позиции, относящиеся к данному магазину
                        'ordered_items': OrderItemSerializer(shop_items, many=True).data
                    }

                    # Рассчитываем сумму только для товаров данного магазина
                    shop_total = sum(item.quantity * item.product_info.price for item in shop_items)
                    order_data['total_sum'] = shop_total

                    shop_orders.append(order_data)

            return Response(shop_orders)

        except Shop.DoesNotExist:
            return Response(
                {"status": False, "error": "Магазин не найден"},
                status=status.HTTP_404_NOT_FOUND
            )