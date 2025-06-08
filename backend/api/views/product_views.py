from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from backend.models import ProductInfo, Product
from backend.api.serializers import ProductSerializer, ProductInfoSerializer



# Импорты системы документации
from backend.api.docs import (
    crud_endpoint,
    api_endpoint, get_success_response, get_error_response
)
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.types import OpenApiTypes

class ProductPagination(PageNumberPagination):
    """
    Класс пагинации для продуктов.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ProductView(APIView):
    """
    Представление для получения списка товаров с возможностью фильтрации.
    """
    permission_classes = [AllowAny]
    pagination_class = ProductPagination

    @crud_endpoint(
        operation='list',
        resource='products',
        summary="Получить список товаров",
        description="Возвращает список товаров с возможностью фильтрации по магазину и категории",
        requires_auth=False,
        parameters=[
            OpenApiParameter(
                name='shop_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID магазина для фильтрации',
                required=False
            ),
            OpenApiParameter(
                name='category_id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='ID категории для фильтрации',
                required=False
            )
        ],
        responses={200: ProductInfoSerializer(many=True)}
    )
    def get(self, request):
        """
        Получение списка товаров с применением фильтров.

        Доступные фильтры:
        - shop_id - ID магазина
        - category_id - ID категории
        - search - поисковый запрос (ищет по названию товара)
        """
        query_params = request.query_params

        # Базовый QuerySet - включает фильтрацию по статусу магазина (только активные)
        queryset = ProductInfo.objects.filter(
            shop__state=True
        ).select_related(
            'product', 'shop'
        ).prefetch_related(
            'product_parameters__parameter'
        ).order_by('id')

        # Применение фильтров
        if query_params.get('shop_id'):
            queryset = queryset.filter(shop_id=query_params.get('shop_id'))

        if query_params.get('category_id'):
            queryset = queryset.filter(product__category_id=query_params.get('category_id'))

        if query_params.get('search'):
            search_term = query_params.get('search')
            queryset = queryset.filter(
                Q(product__name__icontains=search_term) |
                Q(model__icontains=search_term)
            )

        # Применение пагинации
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        serializer = ProductInfoSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)


class ProductDetailView(APIView):
    """
    Представление для получения детальной информации о товаре.
    """
    permission_classes = [AllowAny]

    @crud_endpoint(
        operation='retrieve',
        resource='product',
        summary="Получить детальную информацию о конкретном товаре",
        description="Возвращает детальную информацию о конкретном товаре",
        requires_auth=False,
        responses={200: ProductInfoSerializer(many=False)}
    )
    def get(self, request, pk):
        """
        Получение подробной информации о конкретном товаре.

        Товары из неактивных магазинов не будут доступны.
        """
        try:
            # Также добавляем фильтрацию по статусу магазина
            product_info = ProductInfo.objects.filter(
                pk=pk,
                shop__state=True  # Только из активных магазинов
            ).first()

            if not product_info:
                return Response(
                    {"status": False, "error": "Товар не найден или магазин не активен"},
                    status=status.HTTP_404_NOT_FOUND
                )

            serializer = ProductInfoSerializer(product_info)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"status": False, "error": "Товар не найден"},
                status=status.HTTP_404_NOT_FOUND
            )


class ProductImageUploadView(APIView):
    """
    Представление для загрузки изображения товара.
    """
    permission_classes = [IsAuthenticated]

    @crud_endpoint(
        operation='update',
        resource='product_image',
        summary="Загрузить изображение товара",
        description="Загружает изображение для товара. Автоматически изменяет размер до 400x400 пикселей.",
        responses={
            200: get_success_response("Изображение товара успешно загружено", with_data=True),
            400: get_error_response("Файл image не найден или некорректный формат"),
            404: get_error_response("Товар не найден")
        }
    )
    def post(self, request, product_id):
        """
        Загружает изображение товара.

        Ожидает multipart/form-data с полем 'image' содержащим изображение.
        Поддерживаемые форматы: JPEG, PNG, GIF.
        """
        if 'image' not in request.FILES:
            return Response({
                'status': False,
                'error': 'Файл image не найден'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({
                'status': False,
                'error': 'Товар не найден'
            }, status=status.HTTP_404_NOT_FOUND)

        # Если у товара уже есть изображение, удаляем старые файлы
        old_image_path = None
        if product.image:
            old_image_path = product.image.path

        product.image = request.FILES['image']
        product.save()

        # Принудительно обновляем объект из БД чтобы получить реальный путь к файлу
        product.refresh_from_db()

        # Проверяем, что файл действительно создан
        if product.image and hasattr(product.image, 'path'):
            try:
                import os
                if os.path.exists(product.image.path):
                    from backend.tasks import process_product_image, cleanup_old_images
                    task = process_product_image.delay(product.id)
                else:
                    print(f"Файл не найден: {product.image.path}")
                    task = None
            except Exception as e:
                print(f"Ошибка при проверке файла: {e}")
                task = None
        else:
            task = None

        serializer = ProductSerializer(product)
        response_data = {
            'status': True,
            'message': 'Изображение товара успешно загружено.',
            'product': serializer.data
        }

        if task:
            response_data['message'] += ' Дополнительные размеры обрабатываются в фоновом режиме.'
            response_data['task_id'] = task.id

        return Response(response_data, status=status.HTTP_200_OK)

    @crud_endpoint(
        operation='delete',
        resource='product_image',
        summary="Удалить изображение товара",
        description="Удаляет изображение товара",
        responses={
            200: get_success_response("Изображение товара успешно удалено"),
            404: get_error_response("Товар не найден или у товара нет изображения")
        }
    )
    def delete(self, request, product_id):
        """
        Удаляет изображение товара.
        """
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({
                'status': False,
                'error': 'Товар не найден'
            }, status=status.HTTP_404_NOT_FOUND)

        if not product.image:
            return Response({
                'status': False,
                'error': 'У товара нет изображения'
            }, status=status.HTTP_404_NOT_FOUND)

        # Получаем путь перед удалением
        image_path = product.image.path if product.image else None

        product.image.delete()
        product.image = None
        product.save()

        # Асинхронно удаляем все связанные файлы
        if image_path:
            from backend.tasks import cleanup_old_images
            cleanup_old_images.delay(image_path)

        return Response({
            'status': True,
            'message': 'Изображение товара успешно удалено'
        }, status=status.HTTP_200_OK)