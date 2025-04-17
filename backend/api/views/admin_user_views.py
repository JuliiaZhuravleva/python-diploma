from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.contrib.auth import get_user_model
from django.db import transaction

from backend.api.serializers import UserSerializer
from backend.api.views.admin_views import IsAdminUser

User = get_user_model()


class AdminUsersView(APIView):
    """
    Представление для административного управления пользователями.

    GET: Получает список всех пользователей в системе.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        """
        Получение списка всех пользователей.

        Query parameters:
        - active: true/false - фильтр по активности пользователя
        - type: buyer/shop - фильтр по типу пользователя
        """
        users_queryset = User.objects.all()

        # Применяем фильтры
        active_filter = request.query_params.get('active')
        if active_filter:
            is_active = active_filter.lower() == 'true'
            users_queryset = users_queryset.filter(is_active=is_active)

        type_filter = request.query_params.get('type')
        if type_filter and type_filter in ['buyer', 'shop']:
            users_queryset = users_queryset.filter(type=type_filter)

        serializer = UserSerializer(users_queryset, many=True)
        return Response(serializer.data)


class AdminUserDetailView(APIView):
    """
    Представление для получения и обновления информации о пользователе администратором.

    GET: Получает детальную информацию о пользователе.
    PUT: Обновляет информацию о пользователе.
    """
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        """
        Получение детальной информации о пользователе.
        """
        try:
            user = User.objects.get(id=pk)
            serializer = UserSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(
                {"status": False, "error": "Пользователь не найден"},
                status=status.HTTP_404_NOT_FOUND
            )

    def put(self, request, pk):
        """
        Обновление информации о пользователе администратором.
        """
        try:
            user = User.objects.get(id=pk)

            # Обновляем информацию о пользователе
            serializer = UserSerializer(user, data=request.data, partial=True)

            if serializer.is_valid():
                # Если передан новый пароль, хешируем его
                password = request.data.get('password')
                if password:
                    user.set_password(password)

                # Сохраняем изменения
                serializer.save()

                return Response(
                    {"status": True, "message": "Информация о пользователе обновлена", "data": serializer.data},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"status": False, "errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except User.DoesNotExist:
            return Response(
                {"status": False, "error": "Пользователь не найден"},
                status=status.HTTP_404_NOT_FOUND
            )
