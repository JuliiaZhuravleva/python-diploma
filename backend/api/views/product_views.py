from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from backend.models import ProductInfo
from backend.api.serializers import ProductInfoSerializer


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

    def get(self, request):
        """
        Получение списка товаров с применением фильтров.

        Доступные фильтры:
        - shop_id - ID магазина
        - category_id - ID категории
        - search - поисковый запрос (ищет по названию товара)
        """
        query_params = request.query_params

        # Базовый QuerySet
        queryset = ProductInfo.objects.all().select_related(
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

    def get(self, request, pk):
        """
        Получение подробной информации о конкретном товаре.
        """
        try:
            product_info = ProductInfo.objects.get(pk=pk)
            serializer = ProductInfoSerializer(product_info)
            return Response(serializer.data)
        except ProductInfo.DoesNotExist:
            return Response(
                {"status": False, "error": "Товар не найден"},
                status=status.HTTP_404_NOT_FOUND
            )
