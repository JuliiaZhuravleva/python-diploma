from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from backend.models import Shop

User = get_user_model()


class ShopViewTestCase(TestCase):
    """
    Тестирование представления для списка магазинов.
    """

    def setUp(self):
        """
        Подготовка тестовых данных.
        """
        self.client = APIClient()

        # Создание тестовых пользователей
        self.user1 = User.objects.create_user(
            email='shop1@example.com',
            password='password123',
            is_active=True,
            type='shop'
        )

        self.user2 = User.objects.create_user(
            email='shop2@example.com',
            password='password123',
            is_active=True,
            type='shop'
        )

        # Создание тестовых магазинов
        self.shop1 = Shop.objects.create(
            name='Test Shop 1',
            user=self.user1,
            state=True
        )

        self.shop2 = Shop.objects.create(
            name='Test Shop 2',
            user=self.user2,
            state=False  # неактивный магазин
        )

    def test_get_shops_list(self):
        """
        Тестирование получения списка активных магазинов.
        """
        response = self.client.get('/api/v1/shops')

        # Проверяем успешный ответ
        self.assertEqual(response.status_code, 200)

        # Проверяем, что в ответе только активные магазины
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Shop 1')