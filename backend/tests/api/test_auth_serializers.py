from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.exceptions import ErrorDetail

from backend.models import ConfirmEmailToken
from django_rest_passwordreset.models import ResetPasswordToken
from backend.api.serializers import (
    UserRegistrationSerializer,
    ConfirmEmailSerializer,
    UserLoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)

User = get_user_model()


class UserRegistrationSerializerTest(TestCase):
    """
    Тесты для UserRegistrationSerializer.
    """

    def test_valid_registration(self):
        """
        Проверка, что валидные данные для регистрации проходят валидацию.
        """
        # Создаем тестовые данные
        data = {
            'email': 'new_user@example.com',
            'password': 'SecurePassword123!',
            'password_confirm': 'SecurePassword123!',
            'first_name': 'John',
            'last_name': 'Doe',
            'company': 'Test Company',
            'position': 'Test Position'
        }

        # Создаем сериализатор
        serializer = UserRegistrationSerializer(data=data)

        # Проверяем, что валидация проходит успешно
        self.assertTrue(serializer.is_valid())

        # Проверяем, что в validated_data есть правильные данные
        self.assertEqual(serializer.validated_data['email'], 'new_user@example.com')
        self.assertEqual(serializer.validated_data['first_name'], 'John')
        self.assertEqual(serializer.validated_data['last_name'], 'Doe')

    def test_passwords_dont_match(self):
        """
        Проверка, что разные пароли вызывают ошибку валидации.
        """
        # Создаем тестовые данные с разными паролями
        data = {
            'email': 'new_user@example.com',
            'password': 'SecurePassword123!',
            'password_confirm': 'DifferentPassword123!',
            'first_name': 'John',
            'last_name': 'Doe'
        }

        # Создаем сериализатор
        serializer = UserRegistrationSerializer(data=data)

        # Проверяем, что валидация не проходит
        self.assertFalse(serializer.is_valid())

        # Проверяем, что ошибка связана с несовпадением паролей
        self.assertIn('password_confirm', serializer.errors)

    def test_weak_password(self):
        """
        Проверка, что слабый пароль вызывает ошибку валидации.
        """
        # Создаем тестовые данные со слабым паролем
        data = {
            'email': 'new_user@example.com',
            'password': '123',  # Слабый пароль
            'password_confirm': '123',
            'first_name': 'John',
            'last_name': 'Doe'
        }

        # Создаем сериализатор
        serializer = UserRegistrationSerializer(data=data)

        # Проверяем, что валидация не проходит
        self.assertFalse(serializer.is_valid())

        # Проверяем, что ошибка связана с паролем
        self.assertIn('password', serializer.errors)

    def test_existing_email(self):
        """
        Проверка, что существующий email вызывает ошибку валидации.
        """
        # Создаем пользователя
        User.objects.create_user(
            email='existing@example.com',
            password='ExistingPassword123!',
            is_active=True
        )

        # Создаем тестовые данные с существующим email
        data = {
            'email': 'existing@example.com',  # Существующий email
            'password': 'SecurePassword123!',
            'password_confirm': 'SecurePassword123!',
            'first_name': 'John',
            'last_name': 'Doe'
        }

        # Создаем сериализатор
        serializer = UserRegistrationSerializer(data=data)

        # Создаем пользователя с помощью сериализатора
        if serializer.is_valid():
            with self.assertRaises(Exception):
                serializer.save()  # Должно вызвать исключение, т.к. email уже существует

    def test_without_password_confirm(self):
        """
        Проверка, что регистрация без password_confirm проходит успешно (для совместимости с Postman)
        """
        # Создаем тестовые данные без password_confirm
        data = {
            'email': 'new_user2@example.com',
            'password': 'SecurePassword123!',
            'first_name': 'John',
            'last_name': 'Doe',
            'company': 'Test Company',
            'position': 'Test Position'
        }

        # Создаем сериализатор
        serializer = UserRegistrationSerializer(data=data)

        # Проверяем, что валидация проходит успешно
        self.assertTrue(serializer.is_valid())


class ConfirmEmailSerializerTest(TestCase):
    """
    Тестирование сериализатора для подтверждения email.
    """

    def setUp(self):
        # Создаем пользователя
        self.user = User.objects.create_user(
            email='test@example.com',
            password='SecurePass123!',
            is_active=False
        )

        # Создаем токен подтверждения
        self.token = ConfirmEmailToken.objects.create(user=self.user)

        self.valid_data = {
            'email': self.user.email,
            'token': self.token.key
        }

    def test_valid_confirmation_data(self):
        """
        Проверка, что валидные данные проходят валидацию.
        """
        serializer = ConfirmEmailSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['user'], self.user)
        self.assertEqual(serializer.validated_data['confirm_token'], self.token)

    def test_invalid_token(self):
        """
        Проверка, что неверный токен вызывает ошибку валидации.
        """
        invalid_data = self.valid_data.copy()
        invalid_data['token'] = 'invalid-token'

        serializer = ConfirmEmailSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('token', serializer.errors)

    def test_wrong_email(self):
        """
        Проверка, что неверный email вызывает ошибку валидации.
        """
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'wrong@example.com'

        serializer = ConfirmEmailSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('token', serializer.errors)


class UserLoginSerializerTest(TestCase):
    """
    Тестирование сериализатора для входа пользователей.
    """

    def setUp(self):
        # Создаем активного пользователя
        self.active_user = User.objects.create_user(
            email='active@example.com',
            password='SecurePass123!',
            is_active=True
        )

        # Создаем неактивного пользователя
        self.inactive_user = User.objects.create_user(
            email='inactive@example.com',
            password='SecurePass123!',
            is_active=False
        )

        self.valid_data = {
            'email': self.active_user.email,
            'password': 'SecurePass123!'
        }

    def test_valid_login_data(self):
        """
        Проверка, что валидные данные активного пользователя проходят валидацию.
        """
        serializer = UserLoginSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['user'], self.active_user)

    def test_inactive_user(self):
        """
        Проверка, что неактивный пользователь не может войти.
        """
        data = {
            'email': self.inactive_user.email,
            'password': 'SecurePass123!'
        }

        serializer = UserLoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_wrong_password(self):
        """
        Проверка, что неверный пароль вызывает ошибку валидации.
        """
        invalid_data = self.valid_data.copy()
        invalid_data['password'] = 'WrongPass123!'

        serializer = UserLoginSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_nonexistent_user(self):
        """
        Проверка, что несуществующий email вызывает ошибку валидации.
        """
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'nonexistent@example.com'

        serializer = UserLoginSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)


class PasswordResetRequestSerializerTest(TestCase):
    """
    Тестирование сериализатора для запроса сброса пароля.
    """

    def setUp(self):
        # Создаем активного пользователя
        self.active_user = User.objects.create_user(
            email='active@example.com',
            password='SecurePass123!',
            is_active=True
        )

        # Создаем неактивного пользователя
        self.inactive_user = User.objects.create_user(
            email='inactive@example.com',
            password='SecurePass123!',
            is_active=False
        )

    def test_valid_reset_request(self):
        """
        Проверка, что запрос сброса пароля для активного пользователя проходит валидацию.
        """
        serializer = PasswordResetRequestSerializer(data={'email': self.active_user.email})
        self.assertTrue(serializer.is_valid())

    def test_inactive_user_reset_request(self):
        """
        Проверка, что запрос сброса пароля для неактивного пользователя вызывает ошибку.
        """
        serializer = PasswordResetRequestSerializer(data={'email': self.inactive_user.email})
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_nonexistent_user_reset_request(self):
        """
        Проверка, что запрос сброса пароля для несуществующего пользователя вызывает ошибку.
        """
        serializer = PasswordResetRequestSerializer(data={'email': 'nonexistent@example.com'})
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)


class PasswordResetConfirmSerializerTest(TestCase):
    """
    Тестирование сериализатора для подтверждения сброса пароля.
    """
    def setUp(self):
        """
        Создаем тестового пользователя и токен для тестов.
        """
        self.user = User.objects.create_user(
            email='test@example.com',
            password='TestPassword123!',
            is_active=True
        )

        # Создаем токен для сброса пароля
        self.token = ConfirmEmailToken.objects.create(user=self.user)

    def test_valid_reset_confirmation(self):
        """
        Проверка, что валидные данные для сброса пароля проходят валидацию.
        """
        # Создаем тестовые данные с реальным токеном
        data = {
            'email': 'test@example.com',
            'token': self.token.key,
            'password': 'NewSecurePassword123!',
            'password_confirm': 'NewSecurePassword123!'
        }

        # Создаем сериализатор
        serializer = PasswordResetConfirmSerializer(data=data)

        # Проверяем, что валидация проходит успешно
        self.assertTrue(serializer.is_valid())

        # Проверяем, что в validated_data есть правильные данные
        self.assertEqual(serializer.validated_data['user'], self.user)
        self.assertEqual(serializer.validated_data['reset_token'], self.token)

    def test_passwords_dont_match(self):
        """
        Проверка, что разные пароли вызывают ошибку валидации.
        """
        # Создаем тестовые данные с реальным токеном
        data = {
            'email': 'test@example.com',
            'token': self.token.key,
            'password': 'NewSecurePassword123!',
            'password_confirm': 'DifferentPassword123!'
        }

        # Создаем сериализатор
        serializer = PasswordResetConfirmSerializer(data=data)

        # Проверяем, что валидация не проходит
        self.assertFalse(serializer.is_valid())

        # Проверяем, что ошибка связана с несовпадением паролей
        self.assertIn('password_confirm', serializer.errors)

    def test_invalid_token(self):
        """
        Проверка, что недействительный токен вызывает ошибку валидации.
        """
        # Создаем тестовые данные с некорректным токеном
        data = {
            'email': 'test@example.com',
            'token': 'invalid_token',
            'password': 'NewSecurePassword123!',
            'password_confirm': 'NewSecurePassword123!'
        }

        # Создаем сериализатор
        serializer = PasswordResetConfirmSerializer(data=data)

        # Проверяем, что валидация не проходит
        self.assertFalse(serializer.is_valid())

        # Проверяем, что ошибка связана с токеном
        self.assertIn('token', serializer.errors)

    def test_weak_password(self):
        """
        Проверка, что слабый пароль вызывает ошибку валидации.
        """
        # Создаем тестовые данные с реальным токеном
        data = {
            'email': 'test@example.com',
            'token': self.token.key,
            'password': '123',  # Слабый пароль
            'password_confirm': '123'
        }

        # Создаем сериализатор
        serializer = PasswordResetConfirmSerializer(data=data)

        # Проверяем, что валидация не проходит
        self.assertFalse(serializer.is_valid())

        # Проверяем, что ошибка связана с паролем
        self.assertIn('password', serializer.errors)

    def test_inactive_user(self):
        """
        Проверка, что неактивный пользователь вызывает ошибку валидации.
        """
        # Деактивируем пользователя
        self.user.is_active = False
        self.user.save()

        # Создаем тестовые данные с реальным токеном
        data = {
            'email': 'test@example.com',
            'token': self.token.key,
            'password': 'NewSecurePassword123!',
            'password_confirm': 'NewSecurePassword123!'
        }

        # Создаем сериализатор
        serializer = PasswordResetConfirmSerializer(data=data)

        # Проверяем, что валидация не проходит
        self.assertFalse(serializer.is_valid())

        # Проверяем, что ошибка связана с неактивным пользователем
        self.assertIn('email', serializer.errors)

