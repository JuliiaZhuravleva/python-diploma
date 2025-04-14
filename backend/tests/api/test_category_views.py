from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from backend.models import Category, Shop
from django.contrib.auth import get_user_model

User = get_user_model()


class CategoryViewTestCase(TestCase):
    """
    Тестирование представления для списка категорий.
    """

    def setUp(self):
        """
        Подготовка тестовых данных.
        """
        self.client = APIClient()

        # Создание тестового пользователя
        self.user = User.objects.create_user(
            email='shop@example.com',
            password='password123',
            is_active=True,
            type='shop'
        )

        # Создание тестового магазина
        self.shop = Shop.objects.create(
            name='Test Shop',
            user=self.user,
            state=True
        )

        # Создание тестовых категорий
        self.category1 = Category.objects.create(name='Category 1')
        self.category2 = Category.objects.create(name='Category 2')

        # Связь категорий с магазином
        self.category1.shops.add(self.shop)
        self.category2.shops.add(self.shop)

    def test_get_categories_list(self):
        """
        Тестирование получения списка категорий.
        """
        response = self.client.get('/api/v1/categories')

        # Проверяем успешный ответ
        self.assertEqual(response.status_code, 200)

        # Проверяем, что в ответе все категории
        self.assertEqual(len(response.data), 2)
        category_names = [item['name'] for item in response.data]
        self.assertIn('Category 1', category_names)
        self.assertIn('Category 2', category_names)