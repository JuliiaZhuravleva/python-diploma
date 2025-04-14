from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from backend.models import Shop
from backend.services.import_service import ImportService


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

        # Импортируем данные магазина
        result = ImportService.import_shop_data(url, request.user.id)

        if result['status']:
            return Response({"status": True, "message": result['message']})
        else:
            return Response(
                {"status": False, "error": result['error']},
                status=status.HTTP_400_BAD_REQUEST
            )
