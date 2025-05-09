from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
import json
from backend.models import Shop, Category, Product, ProductInfo, Order, OrderItem

User = get_user_model()


class BasketViewAdvancedTestCase(TestCase):
    """
    Расширенные тесты для представления корзины (BasketView).
    Фокусируется на граничных случаях и обработке ошибок.
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

        # Аутентификация пользователя
        self.client.force_authenticate(user=self.user)

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

        # URL для работы с корзиной
        self.basket_url = '/api/v1/basket'

    def test_parse_items_data_with_invalid_json(self):
        """
        Тестирование обработки невалидных данных JSON при добавлении товаров в корзину.
        """
        # Данные с невалидным JSON
        data = {
            'items': '{invalid json'
        }

        response = self.client.post(self.basket_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn('Неверный формат данных', response.data['error'])

    def test_post_with_missing_items(self):
        """
        Тестирование добавления товаров в корзину без указания товаров.
        """
        # Пустые данные
        data = {}

        response = self.client.post(self.basket_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn('Не указаны товары', response.data['error'])

    def test_post_with_missing_product_info_or_quantity(self):
        """
        Тестирование добавления товаров в корзину с отсутствующими полями product_info или quantity.
        """
        # Данные без product_info
        data = {
            'items': json.dumps([
                {
                    'quantity': 2
                }
            ])
        }

        response = self.client.post(self.basket_url, data)

        # Проверяем, что запрос завершился с ошибкой
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])

        # Данные без quantity
        data = {
            'items': json.dumps([
                {
                    'product_info': self.product_info.id
                }
            ])
        }

        response = self.client.post(self.basket_url, data)

        # Проверяем, что запрос завершился с ошибкой
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])

    def test_post_with_nonexistent_product_info(self):
        """
        Тестирование добавления несуществующего товара в корзину.
        """
        # Данные с несуществующим product_info
        data = {
            'items': json.dumps([
                {
                    'product_info': 9999,  # Несуществующий ID
                    'quantity': 2
                }
            ])
        }

        response = self.client.post(self.basket_url, data)

        # Проверяем, что запрос завершился с ошибкой
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn('Не удалось добавить товары', response.data['error'])

    def test_put_with_nonexistent_order_item(self):
        """
        Тестирование обновления несуществующей позиции в корзине.
        """
        # Создаем корзину
        basket = Order.objects.create(user=self.user, state='basket')

        # Данные с несуществующим order_item
        data = {
            'items': json.dumps([
                {
                    'id': 9999,  # Несуществующий ID
                    'quantity': 3
                }
            ])
        }

        response = self.client.put(self.basket_url, data)

        # Проверяем, что запрос завершился с ошибкой
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn('Позиция с ID 9999 не найдена', response.data['error'])

    def test_put_with_invalid_quantity(self):
        """
        Тестирование обновления количества товара в корзине с некорректным значением.
        """
        # Создаем корзину и добавляем товар
        basket = Order.objects.create(user=self.user, state='basket')
        order_item = OrderItem.objects.create(
            order=basket,
            product_info=self.product_info,
            quantity=1
        )

        # Данные с количеством, превышающим доступное
        data = {
            'items': json.dumps([
                {
                    'id': order_item.id,
                    'quantity': 20  # Больше, чем есть в наличии (10)
                }
            ])
        }

        response = self.client.put(self.basket_url, data)

        # Проверяем, что запрос завершился с ошибкой
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn('Недостаточное количество товара', response.data['error'])

    def test_delete_with_invalid_items_format(self):
        """
        Тестирование удаления товаров из корзины с некорректным форматом items.
        """
        # Данные с невалидным форматом items
        data = {
            'items': 'abc,def'  # Нечисловые ID
        }

        response = self.client.delete(self.basket_url, data)

        # Проверяем, что запрос завершился с ошибкой
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn('Неверный формат списка ID', response.data['error'])

    def test_delete_without_items(self):
        """
        Тестирование удаления товаров из корзины без указания items.
        """
        # Пустые данные
        data = {}

        response = self.client.delete(self.basket_url, data)

        # Проверяем, что запрос завершился с ошибкой
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn('Не указаны товары', response.data['error'])

    def test_get_nonexistent_basket(self):
        """
        Тестирование получения несуществующей корзины.
        """
        # Удаляем все корзины пользователя, если они есть
        Order.objects.filter(user=self.user, state='basket').delete()

        response = self.client.get(self.basket_url)

        # Проверяем, что запрос завершился успешно, но корзина пуста
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['status'])
        self.assertEqual(response.data['error'], 'Корзина пуста')
        