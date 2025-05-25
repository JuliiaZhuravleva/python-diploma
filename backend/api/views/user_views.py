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

# Импорты новой системы документации
from backend.api.docs import (
    auth_endpoint,
    crud_endpoint,
    api_endpoint,
    get_success_response,
    get_error_response,
    AUTH_EXAMPLES,
    ORDER_EXAMPLES
)
from drf_spectacular.utils import OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes


class UserRegisterView(APIView):
    """
    Представление для регистрации новых пользователей в системе.

    Создает нового пользователя на основе предоставленных данных,
    генерирует токен подтверждения и отправляет его на указанный email.
    """
    permission_classes = [permissions.AllowAny]

    @auth_endpoint(
        operation='register',
        summary="Регистрация нового пользователя",
        description="Создает нового пользователя в системе и отправляет email для подтверждения адреса",
        request=UserRegistrationSerializer,
        responses={
            201: get_success_response(
                "Пользователь успешно зарегистрирован. Проверьте email для подтверждения.",
                with_data=False
            )
        }
    )
    def post(self, request):
        """
        Регистрирует нового пользователя.

        Принимает данные пользователя, создает новую учетную запись,
        генерирует токен подтверждения и отправляет его на указанный email.
        """
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
    Представление для подтверждения email пользователя.

    Активирует учетную запись пользователя после проверки токена подтверждения.
    """
    permission_classes = [permissions.AllowAny]

    @auth_endpoint(
        operation='confirm_email',
        summary="Подтверждение email пользователя",
        description="Активирует учетную запись пользователя после проверки токена подтверждения",
        request=ConfirmEmailSerializer,
        responses={
            200: get_success_response("Email успешно подтвержден. Теперь вы можете войти в систему.")
        }
    )
    def post(self, request):
        """
        Подтверждает email пользователя.

        Проверяет токен подтверждения и активирует учетную запись пользователя.
        """
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
    Представление для входа пользователя в систему.

    Аутентифицирует пользователя и возвращает токен доступа.
    """
    permission_classes = [permissions.AllowAny]

    @auth_endpoint(
        operation='login',
        summary="Вход пользователя в систему",
        description="Аутентифицирует пользователя по email и паролю, возвращает токен доступа",
        request=UserLoginSerializer,
        responses={
            200: api_endpoint(
                tags=['Auth'],
                summary="Успешная авторизация",
                description="Возвращает токен и данные пользователя",
                examples=[AUTH_EXAMPLES['login_success']]
            )
        }
    )
    def post(self, request):
        """
        Выполняет вход пользователя в систему.

        Проверяет учетные данные и возвращает токен для дальнейшей авторизации.
        """
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
    Представление для работы с данными пользователя.

    Позволяет получать и обновлять информацию о текущем пользователе.
    """
    permission_classes = [permissions.IsAuthenticated]

    @crud_endpoint(
        operation='read',
        resource='user',
        summary="Получить данные пользователя",
        description="Возвращает информацию о текущем авторизованном пользователе",
        responses={200: UserSerializer}
    )
    def get(self, request):
        """Получение данных текущего пользователя."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @crud_endpoint(
        operation='update',
        resource='user',
        summary="Обновить данные пользователя",
        description="Обновляет информацию о текущем пользователе. Поддерживает частичное обновление.",
        request=UserSerializer,
        responses={
            200: get_success_response("Данные пользователя обновлены", with_data=True)
        }
    )
    def post(self, request):
        """Обновление данных пользователя."""
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
    Представление для запроса сброса пароля.

    Отправляет email с токеном для сброса пароля.
    """
    permission_classes = [permissions.AllowAny]

    @auth_endpoint(
        operation='reset_password',
        summary="Запрос сброса пароля",
        description="Отправляет email с инструкциями для сброса пароля",
        request=PasswordResetRequestSerializer,
        responses={
            200: get_success_response("Инструкции по сбросу пароля отправлены на ваш email")
        }
    )
    def post(self, request):
        """
        Обрабатывает запрос на сброс пароля.

        Создает токен сброса и отправляет его на email пользователя.
        """
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
    Представление для подтверждения сброса пароля.

    Устанавливает новый пароль пользователю.
    """
    permission_classes = [permissions.AllowAny]

    @auth_endpoint(
        operation='confirm_reset',
        summary="Подтверждение сброса пароля",
        description="Устанавливает новый пароль пользователю после проверки токена",
        request=PasswordResetConfirmSerializer,
        responses={
            200: get_success_response("Пароль успешно изменен. Теперь вы можете войти в систему с новым паролем.")
        }
    )
    def post(self, request):
        """
        Подтверждает сброс пароля и устанавливает новый.

        Проверяет токен и устанавливает новый пароль пользователю.
        """
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
    Представление для работы с контактной информацией пользователя.

    Позволяет управлять адресами доставки и контактными данными.
    """
    permission_classes = [permissions.IsAuthenticated]

    @crud_endpoint(
        operation='list',
        resource='contacts',
        summary="Получить список контактов",
        description="Возвращает список контактов пользователя",
        responses={200: ContactSerializer(many=True)}
    )
    def get(self, request):
        """Получение списка контактов пользователя."""
        contacts = Contact.objects.filter(user=request.user, is_deleted=False)
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)

    @crud_endpoint(
        operation='create',
        resource='contacts',
        summary="Создать новый контакт",
        description="Добавляет новый адрес доставки для пользователя",
        request=ContactSerializer,
        responses={
            201: get_success_response("Контакт успешно создан", with_data=True)
        },
        examples=[ORDER_EXAMPLES['contact_create_request']]
    )
    def post(self, request):
        """Создание нового контакта."""
        serializer = ContactSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @crud_endpoint(
        operation='update',
        resource='contacts',
        summary="Обновить контакт",
        description="Обновляет существующий контакт пользователя",
        request=ContactSerializer,
        responses={
            200: get_success_response("Контакт успешно обновлен", with_data=True),
            404: get_error_response("Контакт не найден", "404")
        }
    )
    def put(self, request):
        """Обновление существующего контакта."""
        # В запросе должен быть указан id контакта для обновления
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

    @crud_endpoint(
        operation='delete',
        resource='contacts',
        summary="Удалить контакты",
        description="Мягкое удаление контактов пользователя",
        parameters=[
            OpenApiParameter(
                name='items',
                type=OpenApiTypes.STR,
                description='Список ID контактов для удаления, разделенных запятыми',
                required=True,
                examples=[
                    OpenApiExample(
                        "Удаление нескольких контактов",
                        value="1,2,3"
                    )
                ]
            )
        ],
        responses={
            200: get_success_response("Контакты успешно удалены"),
            400: get_error_response("Некорректный формат списка ID")
        }
    )
    def delete(self, request):
        """
        Мягкое удаление контактов (помечает как удаленные).

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
