from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from backend.models import ProductInfo
from backend.api.serializers import ProductInfoSerializer



# Импорты системы документации
from backend.api.docs import (
    crud_endpoint,
    api_endpoint
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