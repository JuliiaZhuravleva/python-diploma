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
    Тестирование сериализатора для регистрации пользователей.
    """

    def setUp(self):
        self.valid_user_data = {
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'Test',
            'last_name': 'User',
            'company': 'Test Company',
            'position': 'Developer'
        }

    def test_valid_registration_data(self):
        """
        Проверка, что валидные данные проходят валидацию и создают пользователя.
        """
        serializer = UserRegistrationSerializer(data=self.valid_user_data)
        self.assertTrue(serializer.is_valid())

        user = serializer.save()
        self.assertEqual(user.email, self.valid_user_data['email'])
        self.assertEqual(user.first_name, self.valid_user_data['first_name'])
        self.assertEqual(user.last_name, self.valid_user_data['last_name'])
        self.assertEqual(user.company, self.valid_user_data['company'])
        self.assertEqual(user.position, self.valid_user_data['position'])
        self.assertFalse(user.is_active)  # По умолчанию пользователь неактивен

    def test_passwords_dont_match(self):
        """
        Проверка, что разные пароли вызывают ошибку валидации.
        """
        invalid_data = self.valid_user_data.copy()
        invalid_data['password_confirm'] = 'DifferentPass123!'

        serializer = UserRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password_confirm', serializer.errors)

    def test_weak_password(self):
        """
        Проверка, что слабый пароль вызывает ошибку валидации.
        """
        invalid_data = self.valid_user_data.copy()
        invalid_data['password'] = 'password'
        invalid_data['password_confirm'] = 'password'

        serializer = UserRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_email_required(self):
        """
        Проверка, что email является обязательным полем.
        """
        invalid_data = self.valid_user_data.copy()
        invalid_data.pop('email')

        serializer = UserRegistrationSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)


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

    Примечание: Этот тест требует установки django-rest-passwordreset
    и может потребовать дополнительных настроек в settings.py
    """

    def setUp(self):
        # Создаем активного пользователя
        self.user = User.objects.create_user(
            email='test@example.com',
            password='OldPass123!',
            is_active=True
        )

        # Создаем токен сброса пароля
        # Предполагается, что ResetPasswordToken из django-rest-passwordreset доступен
        self.reset_token = ResetPasswordToken.objects.create(user=self.user)

        self.valid_data = {
            'email': self.user.email,
            'token': self.reset_token.key,
            'password': 'NewSecurePass123!',
            'password_confirm': 'NewSecurePass123!'
        }

    def test_valid_reset_confirmation(self):
        """
        Проверка, что валидные данные для сброса пароля проходят валидацию.
        """
        serializer = PasswordResetConfirmSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['user'], self.user)
        self.assertEqual(serializer.validated_data['reset_token'], self.reset_token)

    def test_passwords_dont_match(self):
        """
        Проверка, что разные пароли вызывают ошибку валидации.
        """
        invalid_data = self.valid_data.copy()
        invalid_data['password_confirm'] = 'DifferentPass123!'

        serializer = PasswordResetConfirmSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password_confirm', serializer.errors)

    def test_weak_password(self):
        """
        Проверка, что слабый пароль вызывает ошибку валидации.
        """
        invalid_data = self.valid_data.copy()
        invalid_data['password'] = 'weak'
        invalid_data['password_confirm'] = 'weak'

        serializer = PasswordResetConfirmSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('password', serializer.errors)

    def test_invalid_token(self):
        """
        Проверка, что неверный токен вызывает ошибку валидации.
        """
        invalid_data = self.valid_data.copy()
        invalid_data['token'] = 'invalid-token'

        serializer = PasswordResetConfirmSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('token', serializer.errors)

    def test_nonexistent_user(self):
        """
        Проверка, что несуществующий email вызывает ошибку валидации.
        """
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'nonexistent@example.com'

        serializer = PasswordResetConfirmSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

    def test_inactive_user(self):
        """
        Проверка, что неактивный email вызывает ошибку валидации.
        """
        self.user.is_active = False
        self.user.save()

        serializer = PasswordResetConfirmSerializer(data=self.valid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('email', serializer.errors)

