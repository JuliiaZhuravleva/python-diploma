from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from backend.models import Shop, Category
from backend.api.serializers import ShopSerializer, CategorySerializer


# Импорты системы документации
from backend.api.docs import crud_endpoint


class ShopView(APIView):
    """
    Представление для получения списка магазинов.
    """
    permission_classes = [AllowAny]

    @crud_endpoint(
        operation='list',
        resource='shops',
        summary="Получить список магазинов",
        description="Возвращает список всех активных магазинов в системе",
        requires_auth=False,
        responses={200: ShopSerializer(many=True)}
    )
    def get(self, request):
        """
        Получение списка активных магазинов.
        """
        shops = Shop.objects.filter(state=True)
        serializer = ShopSerializer(shops, many=True)
        return Response(serializer.data)


class CategoryView(APIView):
    """
    Представление для получения списка категорий товаров.
    """
    permission_classes = [AllowAny]

    @crud_endpoint(
        operation='list',
        resource='categories',
        summary="Получить список категорий",
        description="Возвращает список всех доступных категорий товаров",
        requires_auth=False,
        responses={200: CategorySerializer(many=True)}
    )
    def get(self, request):
        """
        Получение списка всех категорий.
        """
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)