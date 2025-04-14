from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from backend.models import Shop
from backend.api.serializers import ShopSerializer


class ShopView(APIView):
    """
    Представление для получения списка магазинов.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Получение списка активных магазинов.
        """
        shops = Shop.objects.filter(state=True)
        serializer = ShopSerializer(shops, many=True)
        return Response(serializer.data)