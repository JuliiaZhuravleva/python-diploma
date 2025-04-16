from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from backend.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter

User = get_user_model()


class ProductDetailViewTestCase(TestCase):
    """
    Тестирование представления для детальной информации о товаре.
    """

    def setUp(self):
        """
        Подготовка тестовых данных.
        """
        self.client = APIClient()

        # Создание тестового магазина
        self.shop = Shop.objects.create(
            name='Test Shop',
            state=True
        )

        # Создание тестовой категории
        self.category = Category.objects.create(name='Test Category')
        self.category.shops.add(self.shop)

        # Создание тестового продукта
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category
        )

        # Создание тестовой информации о продукте
        self.product_info = ProductInfo.objects.create(
            product=self.product,
            shop=self.shop,
            external_id=1,
            model='Test Model',
            price=100,
            price_rrc=120,
            quantity=10
        )

        # Создание тестовых параметров
        self.parameter1 = Parameter.objects.create(name='Color')
        self.parameter2 = Parameter.objects.create(name='Size')

        # Создание тестовых значений параметров
        self.product_parameter1 = ProductParameter.objects.create(
            product_info=self.product_info,
            parameter=self.parameter1,
            value='Red'
        )

        self.product_parameter2 = ProductParameter.objects.create(
            product_info=self.product_info,
            parameter=self.parameter2,
            value='Large'
        )

        # URL для доступа к деталям товара
        self.product_detail_url = f'/api/v1/products/{self.product_info.id}'

    def test_get_product_detail_success(self):
        """
        Тестирование успешного получения деталей товара.
        """
        response = self.client.get(self.product_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем основные поля товара
        self.assertEqual(response.data['id'], self.product_info.id)
        self.assertEqual(response.data['model'], self.product_info.model)
        self.assertEqual(response.data['price'], self.product_info.price)
        self.assertEqual(response.data['price_rrc'], self.product_info.price_rrc)
        self.assertEqual(response.data['quantity'], self.product_info.quantity)

        # Проверяем информацию о товаре
        self.assertEqual(response.data['product']['name'], self.product.name)
        self.assertEqual(response.data['product']['category']['name'], self.category.name)

        # Проверяем информацию о магазине
        self.assertEqual(response.data['shop']['name'], self.shop.name)

        # Проверяем параметры товара
        self.assertEqual(len(response.data['product_parameters']), 2)
        parameter_values = {param['parameter']['name']: param['value'] for param in response.data['product_parameters']}
        self.assertEqual(parameter_values['Color'], 'Red')
        self.assertEqual(parameter_values['Size'], 'Large')

    def test_get_nonexistent_product(self):
        """
        Тестирование запроса несуществующего товара.
        """
        # Находим максимальный ID продукта в базе и добавляем 100,
        # чтобы гарантировать, что такого ID точно не существует
        max_id = ProductInfo.objects.all().order_by('-id').first().id if ProductInfo.objects.exists() else 0
        nonexistent_id = max_id + 100

        # URL для несуществующего товара
        nonexistent_url = f'/api/v1/products/{nonexistent_id}'

        response = self.client.get(nonexistent_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['status'])
        self.assertEqual(response.data['error'], "Товар не найден")

        # Проверяем, что товар не существует в базе
        self.assertFalse(ProductInfo.objects.filter(id=nonexistent_id).exists())
