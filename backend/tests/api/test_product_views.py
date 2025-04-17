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

        # Создание тестового активного магазина
        self.active_shop = Shop.objects.create(
            name='Active Shop',
            user=self.user,
            state=True
        )

        # Создание тестового неактивного магазина
        self.inactive_shop = Shop.objects.create(
            name='Inactive Shop',
            state=False
        )

        # Создание тестовых категорий
        self.category1 = Category.objects.create(name='Electronics')
        self.category2 = Category.objects.create(name='Clothing')

        # Связь категорий с магазинами
        self.category1.shops.add(self.active_shop)
        self.category1.shops.add(self.inactive_shop)
        self.category2.shops.add(self.active_shop)
        self.category2.shops.add(self.inactive_shop)

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

        # Создание тестовой информации о продуктах в активном магазине
        self.product_info1 = ProductInfo.objects.create(
            product=self.product1,
            shop=self.active_shop,
            model='iPhone 13',
            external_id=1001,
            quantity=10,
            price=1000,
            price_rrc=1200
        )
        self.product_info2 = ProductInfo.objects.create(
            product=self.product2,
            shop=self.active_shop,
            model='MacBook Pro',
            external_id=1002,
            quantity=5,
            price=2000,
            price_rrc=2200
        )

        # Создание тестовой информации о продуктах в неактивном магазине
        self.inactive_product_info = ProductInfo.objects.create(
            product=self.product3,
            shop=self.inactive_shop,
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
            product_info=self.product_info2,
            parameter=self.parameter1,
            value='Silver'
        )
        ProductParameter.objects.create(
            product_info=self.inactive_product_info,
            parameter=self.parameter1,
            value='White'
        )

    def test_get_products_list(self):
        """
        Тестирование получения списка товаров только из активных магазинов.
        """
        response = self.client.get('/api/v1/products')

        # Проверяем успешный ответ
        self.assertEqual(response.status_code, 200)

        # Проверяем, что в ответе только товары из активных магазинов
        self.assertEqual(response.data['count'], 2)  # Только 2 продукта из активного магазина

        # Проверяем наличие результатов
        self.assertTrue('results' in response.data)

        # Проверяем, что товары из неактивного магазина не включены
        product_models = [item['model'] for item in response.data['results']]
        self.assertIn('iPhone 13', product_models)
        self.assertIn('MacBook Pro', product_models)
        self.assertNotIn('Cotton T-Shirt', product_models)  # Товар из неактивного магазина

    def test_filter_products_by_category(self):
        """
        Тестирование фильтрации товаров по категории (только из активных магазинов).
        """
        # Фильтрация по категории Electronics
        response = self.client.get(f'/api/v1/products?category_id={self.category1.id}')

        # Проверяем успешный ответ
        self.assertEqual(response.status_code, 200)

        # Проверяем, что в ответе только товары из активного магазина в указанной категории
        self.assertEqual(response.data['count'], 2)

        # Проверяем, что в результатах только товары из нужной категории и активного магазина
        product_names = [item['product']['name'] for item in response.data['results']]
        self.assertIn('Smartphone', product_names)
        self.assertIn('Laptop', product_names)

        # Проверка фильтрации по другой категории, товары из которой есть только в неактивном магазине
        response = self.client.get(f'/api/v1/products?category_id={self.category2.id}')
        self.assertEqual(response.data['count'], 0)  # Не должно быть результатов

    def test_filter_products_by_search(self):
        """
        Тестирование поиска товаров по названию (только из активных магазинов).
        """
        # Поиск по строке 'phone'
        response = self.client.get('/api/v1/products?search=phone')

        # Проверяем успешный ответ
        self.assertEqual(response.status_code, 200)

        # Проверяем, что в ответе только товары, содержащие 'phone' в названии
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['product']['name'], 'Smartphone')

        # Поиск по строке из товара в неактивном магазине
        response = self.client.get('/api/v1/products?search=T-Shirt')
        self.assertEqual(response.data['count'], 0)  # Не должно быть результатов