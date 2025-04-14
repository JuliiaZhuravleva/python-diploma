from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from backend.models import (
    Shop, Category, Product, ProductInfo, Parameter, ProductParameter
)

User = get_user_model()


class ProductViewTestCase(TestCase):
    """
    Тестирование представления для списка товаров.
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
        self.category1 = Category.objects.create(name='Electronics')
        self.category2 = Category.objects.create(name='Clothing')

        # Связь категорий с магазином
        self.category1.shops.add(self.shop)
        self.category2.shops.add(self.shop)

        # Создание тестовых продуктов
        self.product1 = Product.objects.create(
            name='Smartphone',
            category=self.category1
        )
        self.product2 = Product.objects.create(
            name='Laptop',
            category=self.category1
        )
        self.product3 = Product.objects.create(
            name='T-Shirt',
            category=self.category2
        )

        # Создание тестовой информации о продуктах
        self.product_info1 = ProductInfo.objects.create(
            product=self.product1,
            shop=self.shop,
            model='iPhone 13',
            external_id=1001,
            quantity=10,
            price=1000,
            price_rrc=1200
        )
        self.product_info2 = ProductInfo.objects.create(
            product=self.product2,
            shop=self.shop,
            model='MacBook Pro',
            external_id=1002,
            quantity=5,
            price=2000,
            price_rrc=2200
        )
        self.product_info3 = ProductInfo.objects.create(
            product=self.product3,
            shop=self.shop,
            model='Cotton T-Shirt',
            external_id=1003,
            quantity=20,
            price=15,
            price_rrc=20
        )

        # Создание тестовых параметров
        self.parameter1 = Parameter.objects.create(name='Color')
        self.parameter2 = Parameter.objects.create(name='Size')

        # Создание тестовых значений параметров
        ProductParameter.objects.create(
            product_info=self.product_info1,
            parameter=self.parameter1,
            value='Black'
        )
        ProductParameter.objects.create(
            product_info=self.product_info1,
            parameter=self.parameter2,
            value='6.1 inch'
        )
        ProductParameter.objects.create(
            product_info=self.product_info2,
            parameter=self.parameter1,
            value='Silver'
        )
        ProductParameter.objects.create(
            product_info=self.product_info3,
            parameter=self.parameter1,
            value='White'
        )
        ProductParameter.objects.create(
            product_info=self.product_info3,
            parameter=self.parameter2,
            value='M'
        )

    def test_get_products_list(self):
        """
        Тестирование получения списка всех товаров.
        """
        response = self.client.get('/api/v1/products')

        # Проверяем успешный ответ
        self.assertEqual(response.status_code, 200)

        # Проверяем, что в ответе все товары
        self.assertEqual(response.data['count'], 3)

        # Проверяем наличие результатов
        self.assertTrue('results' in response.data)
        self.assertEqual(len(response.data['results']), 3)

    def test_filter_products_by_category(self):
        """
        Тестирование фильтрации товаров по категории.
        """
        # Фильтрация по категории Electronics
        response = self.client.get(f'/api/v1/products?category_id={self.category1.id}')

        # Проверяем успешный ответ
        self.assertEqual(response.status_code, 200)

        # Проверяем, что в ответе только товары из категории Electronics
        self.assertEqual(response.data['count'], 2)

        # Проверяем, что в результатах только товары из нужной категории
        product_names = [item['product']['name'] for item in response.data['results']]
        self.assertIn('Smartphone', product_names)
        self.assertIn('Laptop', product_names)
        self.assertNotIn('T-Shirt', product_names)

    def test_filter_products_by_search(self):
        """
        Тестирование поиска товаров по названию.
        """
        # Поиск по строке 'phone'
        response = self.client.get('/api/v1/products?search=phone')

        # Проверяем успешный ответ
        self.assertEqual(response.status_code, 200)

        # Проверяем, что в ответе только товары, содержащие 'phone' в названии
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['product']['name'], 'Smartphone')