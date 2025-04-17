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

        # Создание тестового активного магазина
        self.active_shop = Shop.objects.create(
            name='Active Shop',
            state=True
        )

        # Создание тестового неактивного магазина
        self.inactive_shop = Shop.objects.create(
            name='Inactive Shop',
            state=False
        )

        # Создание тестовой категории
        self.category = Category.objects.create(name='Test Category')
        self.category.shops.add(self.active_shop)
        self.category.shops.add(self.inactive_shop)

        # Создание тестового продукта
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category
        )

        # Создание тестовой информации о продукте в активном магазине
        self.active_product_info = ProductInfo.objects.create(
            product=self.product,
            shop=self.active_shop,
            external_id=1,
            model='Active Test Model',
            price=100,
            price_rrc=120,
            quantity=10
        )

        # Создание тестовой информации о продукте в неактивном магазине
        self.inactive_product_info = ProductInfo.objects.create(
            product=self.product,
            shop=self.inactive_shop,
            external_id=2,
            model='Inactive Test Model',
            price=90,
            price_rrc=110,
            quantity=5
        )

        # Создание тестовых параметров
        self.parameter1 = Parameter.objects.create(name='Color')
        self.parameter2 = Parameter.objects.create(name='Size')

        # Создание тестовых значений параметров для активного продукта
        self.product_parameter1 = ProductParameter.objects.create(
            product_info=self.active_product_info,
            parameter=self.parameter1,
            value='Red'
        )

        self.product_parameter2 = ProductParameter.objects.create(
            product_info=self.active_product_info,
            parameter=self.parameter2,
            value='Large'
        )

        # Создание тестовых значений параметров для неактивного продукта
        self.product_parameter3 = ProductParameter.objects.create(
            product_info=self.inactive_product_info,
            parameter=self.parameter1,
            value='Blue'
        )

        # URL для доступа к деталям товаров
        self.active_product_detail_url = f'/api/v1/products/{self.active_product_info.id}'
        self.inactive_product_detail_url = f'/api/v1/products/{self.inactive_product_info.id}'

    def test_get_active_product_detail_success(self):
        """
        Тестирование успешного получения деталей товара из активного магазина.
        """
        response = self.client.get(self.active_product_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем основные поля товара
        self.assertEqual(response.data['id'], self.active_product_info.id)
        self.assertEqual(response.data['model'], self.active_product_info.model)
        self.assertEqual(response.data['price'], self.active_product_info.price)
        self.assertEqual(response.data['price_rrc'], self.active_product_info.price_rrc)
        self.assertEqual(response.data['quantity'], self.active_product_info.quantity)

        # Проверяем информацию о товаре
        self.assertEqual(response.data['product']['name'], self.product.name)
        self.assertEqual(response.data['product']['category']['name'], self.category.name)

        # Проверяем информацию о магазине
        self.assertEqual(response.data['shop']['name'], self.active_shop.name)

        # Проверяем параметры товара
        self.assertEqual(len(response.data['product_parameters']), 2)
        parameter_values = {param['parameter']['name']: param['value'] for param in response.data['product_parameters']}
        self.assertEqual(parameter_values['Color'], 'Red')
        self.assertEqual(parameter_values['Size'], 'Large')

    def test_get_inactive_product_detail_failure(self):
        """
        Тестирование неудачного получения деталей товара из неактивного магазина.
        Ожидается ошибка 404, так как товары из неактивных магазинов не должны быть доступны.
        """
        response = self.client.get(self.inactive_product_detail_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['status'])
        self.assertIn("не найден", response.data['error'])

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
        self.assertIn("не найден", response.data['error'])