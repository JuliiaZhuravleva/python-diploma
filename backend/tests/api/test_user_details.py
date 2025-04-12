from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()


class UserDetailsTestCase(TestCase):
    """
    Тесты для API работы с информацией о пользователе.
    """

    def setUp(self):
        """
        Подготовка тестового окружения.
        """
        self.client = APIClient()
        self.details_url = reverse('api:user-details')

        # Создаем пользователя
        self.user = User.objects.create_user(
            email='test@example.com',
            password='ValidPass123!',
            first_name='Test',
            last_name='User',
            company='Test Company',
            position='Developer',
            is_active=True
        )

        # Создаем токен для пользователя
        self.token = Token.objects.create(user=self.user)

        # Аутентифицируем клиент
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_get_user_details(self):
        """
        Тестирование получения информации о пользователе.
        """
        response = self.client.get(self.details_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что данные пользователя корректны
        self.assertEqual(response.data['email'], self.user.email)
        self.assertEqual(response.data['first_name'], self.user.first_name)
        self.assertEqual(response.data['last_name'], self.user.last_name)
        self.assertEqual(response.data['company'], self.user.company)
        self.assertEqual(response.data['position'], self.user.position)

    def test_update_user_details(self):
        """
        Тестирование обновления информации о пользователе.
        """
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'company': 'Updated Company',
            'position': 'Senior Developer'
        }

        response = self.client.post(self.details_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что данные пользователя обновлены
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, update_data['first_name'])
        self.assertEqual(self.user.last_name, update_data['last_name'])
        self.assertEqual(self.user.company, update_data['company'])
        self.assertEqual(self.user.position, update_data['position'])

    def test_update_password(self):
        """
        Тестирование обновления пароля пользователя.
        """
        new_password = 'NewPassword123!'
        update_data = {'password': new_password}

        response = self.client.post(self.details_url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что пароль обновлен
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))

    def test_unauthorized_access(self):
        """
        Тестирование доступа к информации пользователя без аутентификации.
        """
        # Удаляем учетные данные клиента
        self.client.credentials()

        response = self.client.get(self.details_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TokenAuthenticationTestCase(TestCase):
    """
    Тесты для аутентификации по токену.
    """

    def setUp(self):
        """
        Подготовка тестового окружения.
        """
        self.client = APIClient()
        self.test_auth_url = reverse('api:test-auth')

        # Создаем пользователя
        self.user = User.objects.create_user(
            email='test@example.com',
            password='ValidPass123!',
            is_active=True
        )

        # Создаем токен для пользователя
        self.token = Token.objects.create(user=self.user)

    def test_token_authentication_success(self):
        """
        Тестирование успешной аутентификации по токену.
        """
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        response = self.client.get(self.test_auth_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'You are authenticated')

    def test_token_authentication_failure(self):
        """
        Тестирование неудачной аутентификации по токену.
        """
        # Неверный токен
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid-token')
        response = self.client.get(self.test_auth_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Без токена
        self.client.credentials()
        response = self.client.get(self.test_auth_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)