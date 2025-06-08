from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from social_django.models import UserSocialAuth

User = get_user_model()


class SocialAuthInfoViewTestCase(TestCase):
    """
    Тесты для SocialAuthInfoView.
    """

    def setUp(self):
        """
        Подготовка тестового окружения.
        """
        self.client = APIClient()
        self.url = '/api/v1/social/info/'  # URL напрямую, т.к. он не в namespace api

        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
            is_active=True
        )

    def test_get_social_info_anonymous_json(self):
        """
        Тестирование GET запроса для анонимного пользователя (JSON).
        """
        response = self.client.get(self.url, HTTP_ACCEPT='application/json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.json())
        self.assertIn('providers', response.json())
        self.assertIn('current_user', response.json())

        # Проверяем структуру providers
        providers = response.json()['providers']
        self.assertEqual(len(providers), 2)

        # Проверяем наличие Google и GitHub провайдеров
        provider_names = [p['name'] for p in providers]
        self.assertIn('Google', provider_names)
        self.assertIn('GitHub', provider_names)

        # Для анонимного пользователя current_user должен быть None
        self.assertIsNone(response.json()['current_user'])

    def test_get_social_info_authenticated_json(self):
        """
        Тестирование GET запроса для аутентифицированного пользователя (JSON).
        """
        # Создаем социальную связку для пользователя
        UserSocialAuth.objects.create(
            user=self.user,
            provider='google-oauth2',
            uid='123456789'
        )

        # Аутентифицируем пользователя
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url, HTTP_ACCEPT='application/json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        current_user = response.json()['current_user']
        self.assertIsNotNone(current_user)
        self.assertEqual(current_user['id'], self.user.id)
        self.assertEqual(current_user['email'], self.user.email)
        self.assertEqual(current_user['first_name'], self.user.first_name)
        self.assertEqual(current_user['last_name'], self.user.last_name)
        self.assertTrue(current_user['is_active'])

        # Проверяем социальные аккаунты
        social_accounts = current_user['social_accounts']
        self.assertEqual(len(social_accounts), 1)
        self.assertEqual(social_accounts[0]['provider'], 'google-oauth2')
        self.assertEqual(social_accounts[0]['uid'], '123456789')

    def test_get_social_info_html_response(self):
        """
        Тестирование GET запроса с HTML ответом.
        """
        response = self.client.get(self.url, HTTP_ACCEPT='text/html')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')

        # Проверяем, что в HTML есть ключевые элементы
        content = response.content.decode()
        self.assertIn('Social Auth Test', content)
        self.assertIn('Войти через Google', content)
        self.assertIn('Войти через GitHub', content)
        self.assertIn('Не авторизован', content)  # Анонимный пользователь

    def test_get_social_info_html_authenticated(self):
        """
        Тестирование GET запроса с HTML ответом для аутентифицированного пользователя.
        """
        # Аутентифицируем пользователя
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url, HTTP_ACCEPT='text/html')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        content = response.content.decode()
        self.assertIn('Авторизация успешна!', content)
        self.assertIn('Данные пользователя:', content)
        self.assertIn('Выйти', content)

    def test_get_social_info_multiple_social_accounts(self):
        """
        Тестирование пользователя с несколькими социальными аккаунтами.
        """
        # Создаем несколько социальных связок
        UserSocialAuth.objects.create(
            user=self.user,
            provider='google-oauth2',
            uid='google123'
        )
        UserSocialAuth.objects.create(
            user=self.user,
            provider='github',
            uid='github456'
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url, HTTP_ACCEPT='application/json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        social_accounts = response.json()['current_user']['social_accounts']
        self.assertEqual(len(social_accounts), 2)

        # Проверяем, что оба провайдера присутствуют
        providers = [acc['provider'] for acc in social_accounts]
        self.assertIn('google-oauth2', providers)
        self.assertIn('github', providers)

    def test_providers_structure(self):
        """
        Тестирование структуры провайдеров.
        """
        response = self.client.get(self.url, HTTP_ACCEPT='application/json')

        providers = response.json()['providers']

        # Проверяем Google провайдер
        google_provider = next((p for p in providers if p['name'] == 'Google'), None)
        self.assertIsNotNone(google_provider)
        self.assertEqual(google_provider['provider'], 'google-oauth2')
        self.assertEqual(google_provider['auth_url'], '/auth/login/google-oauth2/')

        # Проверяем GitHub провайдер
        github_provider = next((p for p in providers if p['name'] == 'GitHub'), None)
        self.assertIsNotNone(github_provider)
        self.assertEqual(github_provider['provider'], 'github')
        self.assertEqual(github_provider['auth_url'], '/auth/login/github/')


class SimpleLogoutViewTestCase(TestCase):
    """
    Тесты для SimpleLogoutView.
    """

    def setUp(self):
        """
        Подготовка тестового окружения.
        """
        self.client = APIClient()
        self.logout_url = '/logout/'  # URL напрямую

        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password123',
            is_active=True
        )

    def test_logout_authenticated_user(self):
        """
        Тестирование выхода аутентифицированного пользователя.
        """
        # Входим в систему
        self.client.force_authenticate(user=self.user)

        # Выполняем logout
        response = self.client.get(self.logout_url)

        # Должен быть редирект
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn('/api/v1/social/info/', response['Location'])

    def test_logout_anonymous_user(self):
        """
        Тестирование выхода для анонимного пользователя.
        """
        # Выполняем logout без аутентификации
        response = self.client.get(self.logout_url)

        # Должен быть редирект (logout работает даже для анонимных пользователей)
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertIn('/api/v1/social/info/', response['Location'])

    @patch('backend.api.views.social_views.logout')
    def test_logout_calls_django_logout(self, mock_logout):
        """
        Тестирование, что view корректно вызывает Django logout.
        """
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.logout_url)

        # Проверяем, что logout был вызван
        mock_logout.assert_called_once()

        # Проверяем редирект
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_logout_redirects_to_correct_url(self):
        """
        Тестирование корректного URL редиректа после logout.
        """
        response = self.client.get(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        self.assertEqual(response['Location'], '/api/v1/social/info/')
