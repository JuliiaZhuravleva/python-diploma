from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
import csv
from django.http import HttpResponse
import yaml
import io

from backend.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter


class ExportProductsView(APIView):
    """
    Представление для экспорта товаров в различных форматах.

    GET: Экспортирует товары магазина в выбранном формате (CSV, YAML).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Экспорт товаров магазина.

        Query parameters:
        - format: csv или yaml (по умолчанию yaml)
        - shop_id: ID магазина (если не указан, пытается найти магазин пользователя)
        """
        # Проверяем права доступа (должен быть администратор или владелец магазина)
        user = request.user
        shop_id = request.query_params.get('shop_id')

        # Если указан shop_id, проверяем права
        if shop_id:
            shop = Shop.objects.filter(id=shop_id).first()
            if not shop:
                return Response(
                    {"status": False, "error": "Магазин не найден"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Если пользователь не администратор и не владелец магазина
            if not user.is_staff and (not hasattr(user, 'shop') or user.shop.id != shop.id):
                return Response(
                    {"status": False, "error": "У вас нет прав на экспорт данных этого магазина"},
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            # Если не указан shop_id, пытаемся найти магазин пользователя
            shop = Shop.objects.filter(user=user).first()
            if not shop:
                return Response(
                    {"status": False, "error": "Не указан ID магазина, и пользователь не связан с магазином"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Получаем формат экспорта
        export_format = request.query_params.get('format', 'yaml').lower()

        if export_format == 'csv':
            return self.export_csv(shop)
        elif export_format == 'yaml':
            return self.export_yaml(shop)
        else:
            return Response(
                {"status": False, "error": "Неподдерживаемый формат. Доступные форматы: csv, yaml"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def export_csv(self, shop):
        """
        Экспорт товаров магазина в формате CSV.
        """
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{shop.name}_products.csv"'

        writer = csv.writer(response)
        writer.writerow(['id', 'category', 'model', 'name', 'price', 'price_rrc', 'quantity', 'parameters'])

        products = ProductInfo.objects.filter(
            shop=shop
        ).prefetch_related('product', 'product_parameters__parameter').select_related('product__category')

        for product_info in products:
            parameters = {}
            for param in product_info.product_parameters.all():
                parameters[param.parameter.name] = param.value

            writer.writerow([
                product_info.external_id,
                product_info.product.category.id,
                product_info.model,
                product_info.product.name,
                product_info.price,
                product_info.price_rrc,
                product_info.quantity,
                str(parameters)
            ])

        return response

    def export_yaml(self, shop):
        """
        Экспорт товаров магазина в формате YAML.
        """
        products = ProductInfo.objects.filter(
            shop=shop
        ).prefetch_related('product', 'product_parameters__parameter').select_related('product__category')

        # Структура для YAML
        data = {
            'shop': shop.name,
            'categories': [],
            'goods': []
        }

        # Добавляем категории
        categories = {}
        for product_info in products:
            category = product_info.product.category
            if category.id not in categories:
                categories[category.id] = category.name
                data['categories'].append({
                    'id': category.id,
                    'name': category.name
                })

        # Добавляем товары
        for product_info in products:
            # Собираем параметры товара
            parameters = {}
            for param in product_info.product_parameters.all():
                parameters[param.parameter.name] = param.value

            data['goods'].append({
                'id': product_info.external_id,
                'category': product_info.product.category.id,
                'model': product_info.model,
                'name': product_info.product.name,
                'price': product_info.price,
                'price_rrc': product_info.price_rrc,
                'quantity': product_info.quantity,
                'parameters': parameters
            })

        # Преобразуем в YAML
        yaml_data = yaml.dump(data, allow_unicode=True, sort_keys=False)

        # Возвращаем как файл для скачивания
        response = HttpResponse(yaml_data, content_type='application/x-yaml')
        response['Content-Disposition'] = f'attachment; filename="{shop.name}_products.yaml"'

        return response
