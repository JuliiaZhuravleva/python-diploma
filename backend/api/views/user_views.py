from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import authenticate

from backend.models import User, Contact, ConfirmEmailToken
from backend.api.serializers import (
    UserSerializer, UserRegistrationSerializer, UserLoginSerializer,
    ConfirmEmailSerializer, ContactSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer
)
from backend.tasks import send_confirmation_email, send_password_reset_email

from . import ApiResponse


class UserRegisterView(APIView):
    """
    View для регистрации новых пользователей.

    POST: Создает нового пользователя и отправляет email с токеном подтверждения.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)

        if serializer.is_valid():
            # Создаем нового пользователя
            with transaction.atomic():
                user = serializer.save()

                # Создаем токен для подтверждения email
                token, _ = ConfirmEmailToken.objects.get_or_create(user=user)

                # Запуск асинхронной задачи для отправки email
                send_confirmation_email.delay(user.id, token.key)

                return Response({
                    'status': True,
                    'message': 'Пользователь успешно зарегистрирован. Проверьте email для подтверждения.'
                }, status=status.HTTP_201_CREATED)

        return Response({
            'status': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ConfirmEmailView(APIView):
    """
    View для подтверждения email пользователя.

    POST: Активирует пользователя после подтверждения email.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ConfirmEmailSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']
            confirm_token = serializer.validated_data['confirm_token']

            # Активируем пользователя
            user.is_active = True
            user.save()

            # Удаляем токен, так как он больше не нужен
            confirm_token.delete()

            return Response({
                'message': 'Email успешно подтвержден. Теперь вы можете войти в систему.'
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    """
    View для входа пользователя в систему.

    POST: Аутентифицирует пользователя и возвращает токен.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)

            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailsView(APIView):
    """
    View для работы с данными пользователя.

    GET: Возвращает информацию о текущем пользователе.
    POST: Обновляет информацию пользователя.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)

        if serializer.is_valid():
            # Проверяем, есть ли новый пароль
            password = request.data.get('password')
            if password:
                request.user.set_password(password)

            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetRequestView(APIView):
    """
    View для запроса сброса пароля.

    POST: Отправляет email с токеном для сброса пароля.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)

            # Создаем токен для сброса пароля
            token, _ = ConfirmEmailToken.objects.get_or_create(user=user)

            # Запуск асинхронной задачи для отправки email
            send_password_reset_email.delay(user.id, token.key)

            return Response({
                'message': 'Инструкции по сбросу пароля отправлены на ваш email.'
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    View для подтверждения сброса пароля.

    POST: Устанавливает новый пароль пользователю.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']
            token = serializer.validated_data['reset_token']

            # Устанавливаем новый пароль
            user.set_password(serializer.validated_data['password'])
            user.save()

            # Удаляем токен, так как он больше не нужен
            token.delete()

            return Response({
                'status': True,
                'message': 'Пароль успешно изменен. Теперь вы можете войти в систему с новым паролем.'
            }, status=status.HTTP_200_OK)

        return Response({
            'status': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ContactViewSet(APIView):
    """
    View для работы с контактной информацией пользователя.

    GET: Возвращает список контактов пользователя.
    POST: Создает новый контакт.
    PUT: Обновляет существующий контакт.
    DELETE: Мягко удаляет контакты.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        contacts = Contact.objects.filter(user=request.user, is_deleted=False)
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ContactSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        # В запросе должно быть указано id контакта для обновления
        contact_id = request.data.get('id')
        if not contact_id:
            return Response({'error': 'Не указан ID контакта'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            contact = Contact.objects.get(id=contact_id, user=request.user, is_deleted=False)
        except Contact.DoesNotExist:
            return Response({'error': 'Контакт не найден'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ContactSerializer(contact, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """
        Мягкое удаление контактов (пометка как удаленные).

        Ожидаемый формат данных:
        {
            "items": "1,2,3"  # Строка с ID контактов через запятую
        }
        """
        items_str = request.data.get('items')
        if not items_str:
            return Response({'error': 'Не указаны ID контактов для удаления'}, status=status.HTTP_400_BAD_REQUEST)

        # Преобразуем строку с id в список
        try:
            items_ids = [int(item) for item in items_str.split(',')]
        except ValueError:
            return Response({'error': 'Некорректный формат списка ID'}, status=status.HTTP_400_BAD_REQUEST)

        # Получаем контакты пользователя из указанного списка
        contacts = Contact.objects.filter(id__in=items_ids, user=request.user, is_deleted=False)
        deleted_count = contacts.count()

        # Помечаем контакты как удаленные
        contacts.update(is_deleted=True)

        return Response({'message': f'Удалено контактов: {deleted_count}'})