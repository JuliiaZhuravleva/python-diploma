from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
import json
from backend.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Order, OrderItem

User = get_user_model()


class BasketViewTestCase(TestCase):
    """
    Тестирование API для работы с корзиной.
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

    def test_get_empty_basket(self):
        """
        Тестирование получения пустой корзины.
        """
        response = self.client.get(self.basket_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], False)
        self.assertEqual(response.data['error'], "Корзина пуста")

    def test_add_product_to_basket(self):
        """
        Тестирование добавления товара в корзину.
        """
        # Данные для запроса
        data = {
            'items': json.dumps([
                {
                    'product_info': self.product_info.id,
                    'quantity': 2
                }
            ])
        }

        response = self.client.post(self.basket_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['status'])
        self.assertEqual(response.data['message'], "Товары добавлены в корзину")

        # Проверяем, что товар добавлен в корзину
        basket = Order.objects.filter(user=self.user, state='basket').first()
        self.assertIsNotNone(basket)

        basket_items = OrderItem.objects.filter(order=basket)
        self.assertEqual(basket_items.count(), 1)
        self.assertEqual(basket_items.first().product_info.id, self.product_info.id)
        self.assertEqual(basket_items.first().quantity, 2)

    def test_add_product_exceed_quantity(self):
        """
        Тестирование добавления товара в количестве, превышающем остаток.
        """
        # Данные для запроса
        data = {
            'items': json.dumps([
                {
                    'product_info': self.product_info.id,
                    'quantity': 20  # Больше, чем есть в наличии (10)
                }
            ])
        }

        response = self.client.post(self.basket_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn("Недостаточное количество товара", response.data['error'])

    def test_update_basket_item(self):
        """
        Тестирование обновления количества товара в корзине.
        """
        # Сначала добавляем товар в корзину
        basket = Order.objects.create(user=self.user, state='basket')
        order_item = OrderItem.objects.create(
            order=basket,
            product_info=self.product_info,
            quantity=1
        )

        # Данные для запроса обновления
        data = {
            'items': json.dumps([
                {
                    'id': order_item.id,
                    'quantity': 3
                }
            ])
        }

        response = self.client.put(self.basket_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertEqual(response.data['message'], "Корзина обновлена")

        # Проверяем, что количество обновлено
        order_item.refresh_from_db()
        self.assertEqual(order_item.quantity, 3)

    def test_delete_basket_item(self):
        """
        Тестирование удаления товара из корзины.
        """
        # Сначала добавляем товар в корзину
        basket = Order.objects.create(user=self.user, state='basket')
        order_item = OrderItem.objects.create(
            order=basket,
            product_info=self.product_info,
            quantity=1
        )

        # Данные для запроса удаления
        data = {
            'items': str(order_item.id)
        }

        response = self.client.delete(self.basket_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertIn("Удалено позиций: 1", response.data['message'])

        # Проверяем, что товар удален из корзины
        self.assertFalse(OrderItem.objects.filter(id=order_item.id).exists())

    def test_delete_all_basket_items(self):
        """
        Тестирование удаления всех товаров из корзины.
        """
        # Сначала добавляем товар в корзину
        basket = Order.objects.create(user=self.user, state='basket')
        order_item = OrderItem.objects.create(
            order=basket,
            product_info=self.product_info,
            quantity=1
        )

        # Данные для запроса удаления
        data = {
            'items': str(order_item.id)
        }

        response = self.client.delete(self.basket_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertIn("Корзина пуста", response.data['message'])

        # Проверяем, что корзина удалена
        self.assertFalse(Order.objects.filter(id=basket.id).exists())
