from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from backend.models import ConfirmEmailToken

User = get_user_model()


class EmailConfirmationTestCase(TestCase):
    """
    Тесты для API подтверждения email пользователя.
    """

    def setUp(self):
        """
        Подготовка тестового окружения.
        """
        self.client = APIClient()
        self.confirm_url = reverse('api:user-register-confirm')

        # Создаем неактивного пользователя
        self.user = User.objects.create_user(
            email='test@example.com',
            password='ValidPass123!',
            is_active=False
        )

        # Создаем токен для подтверждения email
        self.token = ConfirmEmailToken.objects.create(user=self.user)

        # Тестовые данные для подтверждения
        self.confirmation_data = {
            'email': self.user.email,
            'token': self.token.key
        }

    def test_email_confirmation_success(self):
        """
        Тестирование успешного подтверждения email.
        """
        response = self.client.post(self.confirm_url, self.confirmation_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что пользователь активирован
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

        # Проверяем, что токен удален
        self.assertFalse(ConfirmEmailToken.objects.filter(key=self.token.key).exists())

    def test_email_confirmation_invalid_token(self):
        """
        Тестирование подтверждения email с неверным токеном.
        """
        invalid_data = self.confirmation_data.copy()
        invalid_data['token'] = 'invalid-token'

        response = self.client.post(self.confirm_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Проверяем, что пользователь остался неактивным
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_email_confirmation_invalid_email(self):
        """
        Тестирование подтверждения email с неверным email.
        """
        invalid_data = self.confirmation_data.copy()
        invalid_data['email'] = 'wrong@example.com'

        response = self.client.post(self.confirm_url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Проверяем, что пользователь остался неактивным
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)


class PasswordResetTestCase(TestCase):
    """
    Тесты для API сброса пароля.
    """

    def setUp(self):
        """
        Подготовка тестового окружения.
        """
        self.client = APIClient()
        self.reset_request_url = reverse('api:password-reset-request')
        self.reset_confirm_url = reverse('api:password-reset-confirm')

        # Создаем активного пользователя
        self.user = User.objects.create_user(
            email='test@example.com',
            password='OldPassword123!',
            is_active=True
        )

    def test_password_reset_request_success(self):
        """
        Тестирование успешного запроса на сброс пароля.
        """
        response = self.client.post(self.reset_request_url, {'email': self.user.email}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что создан токен для сброса пароля
        self.assertTrue(ConfirmEmailToken.objects.filter(user=self.user).exists())

    def test_password_reset_request_nonexistent_email(self):
        """
        Тестирование запроса на сброс пароля с несуществующим email.
        """
        response = self.client.post(self.reset_request_url, {'email': 'nonexistent@example.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_confirm_success(self):
        """
        Тестирование успешного подтверждения сброса пароля.
        """
        # Создаем токен для сброса пароля
        token = ConfirmEmailToken.objects.create(user=self.user)

        # Данные для подтверждения сброса пароля
        confirm_data = {
            'email': self.user.email,
            'token': token.key,
            'password': 'NewPassword123!'
        }

        response = self.client.post(self.reset_confirm_url, confirm_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что пароль изменен
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(confirm_data['password']))

        # Проверяем, что токен удален
        self.assertFalse(ConfirmEmailToken.objects.filter(key=token.key).exists())

    def test_password_reset_confirm_invalid_token(self):
        """
        Тестирование подтверждения сброса пароля с неверным токеном.
        """
        confirm_data = {
            'email': self.user.email,
            'token': 'invalid-token',
            'password': 'NewPassword123!'
        }

        response = self.client.post(self.reset_confirm_url, confirm_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Проверяем, что пароль не изменен
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password(confirm_data['password']))