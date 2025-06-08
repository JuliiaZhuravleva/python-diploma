from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions


class TestAuthView(APIView):
    """
    Тестовый view для проверки аутентификации.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({"message": "You are authenticated"}, status=status.HTTP_200_OK)
