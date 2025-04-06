from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


class ApiInfrastructureTestCase(TestCase):
    """
    Тестирование базовой инфраструктуры API.

    Проверяет, что REST Framework корректно настроен и работает со стандартными методами
    аутентификации и авторизации.
    """

    def setUp(self):
        """
        Подготовка тестовых данных.
        """
        self.client = APIClient()

        # Создание тестового пользователя
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password123',
            is_active=True
        )

    def test_authentication_required(self):
        """
        Тестирование требования аутентификации для защищенных эндпоинтов.
        """
        # Запрос к защищенному эндпоинту без аутентификации
        response = self.client.get('/api/v1/test-auth/')

        # Ожидаем 401 Unauthorized
        self.assertEqual(response.status_code, 401)

        # Теперь аутентифицируемся и повторим запрос
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/v1/test-auth/')

        # Ожидаем 200 OK
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], "You are authenticated")