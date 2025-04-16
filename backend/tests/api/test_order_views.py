from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from backend.models import Shop, Category, Product, ProductInfo, Order, OrderItem, Contact

User = get_user_model()


class OrderViewTestCase(TestCase):
    """
    Тестирование API для работы с заказами.
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
            first_name='Test',
            last_name='User',
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

        # Создание тестового контакта
        self.contact = Contact.objects.create(
            user=self.user,
            city='Test City',
            street='Test Street',
            house='123',
            phone='+1234567890',
            is_deleted=False
        )

        # Создание тестовой корзины
        self.basket = Order.objects.create(
            user=self.user,
            state='basket'
        )

        # Добавление товара в корзину
        self.order_item = OrderItem.objects.create(
            order=self.basket,
            product_info=self.product_info,
            quantity=2
        )

        # URL для работы с заказами
        self.order_url = '/api/v1/order'
        self.order_detail_url = f'/api/v1/order/{self.basket.id}'

    def test_get_orders_empty(self):
        """
        Тестирование получения пустого списка заказов.
        """
        response = self.client.get(self.order_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # Нет оформленных заказов

    def test_place_order(self):
        """
        Тестирование оформления заказа.
        """
        # Данные для запроса
        data = {
            'id': self.basket.id,
            'contact': self.contact.id
        }

        response = self.client.post(self.order_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertEqual(response.data['message'], "Заказ успешно оформлен")

        # Проверяем, что заказ оформлен
        self.basket.refresh_from_db()
        self.assertEqual(self.basket.state, 'new')
        self.assertEqual(self.basket.contact, self.contact)

        # Проверяем, что количество товара уменьшилось
        self.product_info.refresh_from_db()
        self.assertEqual(self.product_info.quantity, 8)  # 10 - 2 = 8

    def test_place_order_insufficient_quantity(self):
        """
        Тестирование оформления заказа с недостаточным количеством товара.
        """
        # Уменьшаем количество товара в магазине
        self.product_info.quantity = 1
        self.product_info.save()

        # Данные для запроса
        data = {
            'id': self.basket.id,
            'contact': self.contact.id
        }

        response = self.client.post(self.order_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn("Недостаточное количество товара", response.data['error'])

    def test_place_order_with_deleted_contact(self):
        """
        Тестирование оформления заказа с удаленным контактом.
        """
        # Помечаем контакт как удаленный
        self.contact.is_deleted = True
        self.contact.save()

        # Данные для запроса
        data = {
            'id': self.basket.id,
            'contact': self.contact.id
        }

        response = self.client.post(self.order_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['status'])
        self.assertEqual(response.data['error'], "Контакт не найден или был удален")

    def test_get_orders_after_place(self):
        """
        Тестирование получения списка заказов после оформления.
        """
        # Оформляем заказ
        self.basket.state = 'new'
        self.basket.contact = self.contact
        self.basket.save()

        response = self.client.get(self.order_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Один оформленный заказ
        self.assertEqual(response.data[0]['id'], self.basket.id)
        self.assertEqual(response.data[0]['state'], 'new')

    def test_get_order_detail(self):
        """
        Тестирование получения деталей заказа.
        """
        # Оформляем заказ
        self.basket.state = 'new'
        self.basket.contact = self.contact
        self.basket.save()

        response = self.client.get(self.order_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.basket.id)
        self.assertEqual(response.data['state'], 'new')
        self.assertEqual(len(response.data['ordered_items']), 1)
        self.assertEqual(response.data['ordered_items'][0]['quantity'], 2)