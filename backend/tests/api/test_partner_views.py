from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from unittest.mock import patch
from rest_framework import status
from backend.models import Shop, Category, Product, ProductInfo, Order, OrderItem, Contact


User = get_user_model()


class PartnerUpdateViewTest(TestCase):
    """
    Тестирование представления для обновления прайс-листа партнера.
    """

    def setUp(self):
        """
        Подготовка тестовых данных.
        """
        self.client = APIClient()

        # Создание пользователя с типом 'shop'
        self.shop_user = User.objects.create_user(
            email='shop@example.com',
            password='password123',
            is_active=True,
            type='shop'
        )

        # Создание пользователя с типом 'buyer'
        self.buyer_user = User.objects.create_user(
            email='buyer@example.com',
            password='password123',
            is_active=True,
            type='buyer'
        )

        # Создание магазина для shop_user
        self.shop = Shop.objects.create(
            name='Test Shop',
            user=self.shop_user,
            state=True
        )

    @patch('backend.services.import_service.ImportService.import_shop_data')
    def test_update_price_list_success(self, mock_import_shop_data):
        """
        Тестирование успешного обновления прайс-листа.
        """
        # Настройка мока
        mock_import_shop_data.return_value = {
            "status": True,
            "message": "Импорт успешно завершен. Импортировано категорий: 3. Импортировано товаров: 10, параметров: 25"
        }

        # Аутентификация как магазин
        self.client.force_authenticate(user=self.shop_user)

        # Отправка запроса
        response = self.client.post(
            '/api/v1/partner/update',
            {'url': 'https://example.com/shop1.yaml'},
            format='json'
        )

        # Проверка ответа
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['status'])
        self.assertIn('Импорт успешно завершен', response.data['message'])

        # Проверка вызова сервиса
        mock_import_shop_data.assert_called_once_with('https://example.com/shop1.yaml', self.shop_user.id)

    def test_update_price_list_unauthorized(self):
        """
        Тестирование попытки обновления прайс-листа без аутентификации.
        """
        # Запрос без аутентификации
        response = self.client.post(
            '/api/v1/partner/update',
            {'url': 'https://example.com/shop1.yaml'},
            format='json'
        )

        # Проверка ответа
        self.assertEqual(response.status_code, 401)  # Unauthorized

    def test_update_price_list_buyer(self):
        """
        Тестирование попытки обновления прайс-листа пользователем-покупателем.
        """
        # Аутентификация как покупатель
        self.client.force_authenticate(user=self.buyer_user)

        # Отправка запроса
        response = self.client.post(
            '/api/v1/partner/update',
            {'url': 'https://example.com/shop1.yaml'},
            format='json'
        )

        # Проверка ответа
        self.assertEqual(response.status_code, 403)  # Forbidden
        self.assertFalse(response.data['status'])
        self.assertIn('Только пользователи с типом \'магазин\'', response.data['error'])


class PartnerViewsTestCase(TestCase):
    """
    Тестирование расширенных представлений для партнеров (магазинов).
    """

    def setUp(self):
        """
        Подготовка тестовых данных.
        """
        self.client = APIClient()

        # Создание тестового пользователя-магазина
        self.shop_user = User.objects.create_user(
            email='shop@example.com',
            password='password123',
            is_active=True,
            type='shop'
        )

        # Создание тестового пользователя-покупателя
        self.buyer_user = User.objects.create_user(
            email='buyer@example.com',
            password='password123',
            is_active=True,
            type='buyer'
        )

        # Создание тестового магазина
        self.shop = Shop.objects.create(
            name='Test Shop',
            user=self.shop_user,
            state=True
        )

        # Создание второго тестового магазина
        self.shop2_user = User.objects.create_user(
            email='shop2@example.com',
            password='password123',
            is_active=True,
            type='shop'
        )

        self.shop2 = Shop.objects.create(
            name='Test Shop 2',
            user=self.shop2_user,
            state=True
        )

        # Создание тестовой категории
        self.category = Category.objects.create(name='Test Category')
        self.category.shops.add(self.shop)
        self.category.shops.add(self.shop2)

        # Создание тестовых продуктов
        self.product1 = Product.objects.create(
            name='Test Product 1',
            category=self.category
        )

        self.product2 = Product.objects.create(
            name='Test Product 2',
            category=self.category
        )

        # Создание тестовой информации о продуктах
        self.product_info1 = ProductInfo.objects.create(
            product=self.product1,
            shop=self.shop,
            external_id=1,
            model='Model 1',
            price=100,
            price_rrc=120,
            quantity=10
        )

        self.product_info2 = ProductInfo.objects.create(
            product=self.product2,
            shop=self.shop2,
            external_id=2,
            model='Model 2',
            price=200,
            price_rrc=240,
            quantity=5
        )

        # Создание тестового контакта
        self.contact = Contact.objects.create(
            user=self.buyer_user,
            city='Test City',
            street='Test Street',
            house='123',
            phone='+1234567890',
            is_deleted=False
        )

        # Создание тестового заказа с товарами из обоих магазинов
        self.order = Order.objects.create(
            user=self.buyer_user,
            state='new',
            contact=self.contact
        )

        # Добавление товаров в заказ
        self.order_item1 = OrderItem.objects.create(
            order=self.order,
            product_info=self.product_info1,
            quantity=2
        )

        self.order_item2 = OrderItem.objects.create(
            order=self.order,
            product_info=self.product_info2,
            quantity=1
        )

        # Создание второго заказа только с товарами из второго магазина
        self.order2 = Order.objects.create(
            user=self.buyer_user,
            state='new',
            contact=self.contact
        )

        self.order_item3 = OrderItem.objects.create(
            order=self.order2,
            product_info=self.product_info2,
            quantity=3
        )

        # URLs для доступа к API партнеров
        self.partner_state_url = '/api/v1/partner/state'
        self.partner_orders_url = '/api/v1/partner/orders'

    def test_get_partner_state(self):
        """
        Тестирование получения статуса партнера.
        """
        # Аутентификация как магазин
        self.client.force_authenticate(user=self.shop_user)

        response = self.client.get(self.partner_state_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertEqual(response.data['state'], True)
        self.assertEqual(response.data['name'], 'Test Shop')

    def test_get_partner_state_as_buyer(self):
        """
        Тестирование получения статуса партнера пользователем-покупателем.
        """
        # Аутентификация как покупатель
        self.client.force_authenticate(user=self.buyer_user)

        response = self.client.get(self.partner_state_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['status'])

    def test_update_partner_state(self):
        """
        Тестирование обновления статуса партнера.
        """
        # Аутентификация как магазин
        self.client.force_authenticate(user=self.shop_user)

        # Данные для запроса - выключение магазина
        data = {
            'state': 'off'
        }

        response = self.client.post(self.partner_state_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertIn('выключен', response.data['message'])

        # Проверяем, что статус магазина обновился
        self.shop.refresh_from_db()
        self.assertFalse(self.shop.state)

        # Снова включаем магазин
        data = {
            'state': 'on'
        }

        response = self.client.post(self.partner_state_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertIn('включен', response.data['message'])

        # Проверяем, что статус магазина обновился
        self.shop.refresh_from_db()
        self.assertTrue(self.shop.state)

    def test_update_partner_state_invalid_value(self):
        """
        Тестирование обновления статуса партнера с недопустимым значением.
        """
        # Аутентификация как магазин
        self.client.force_authenticate(user=self.shop_user)

        # Данные для запроса с недопустимым значением
        data = {
            'state': 'invalid'
        }

        response = self.client.post(self.partner_state_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn("Параметр state должен быть", response.data['error'])

    def test_get_partner_orders(self):
        """
        Тестирование получения списка заказов партнера.
        """
        # Аутентификация как магазин
        self.client.force_authenticate(user=self.shop_user)

        response = self.client.get(self.partner_orders_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что магазин видит только один заказ
        self.assertEqual(len(response.data), 1)

        # Проверяем, что магазин видит только свои позиции в заказе
        order_data = response.data[0]
        self.assertEqual(order_data['id'], self.order.id)
        self.assertEqual(len(order_data['ordered_items']), 1)
        self.assertEqual(order_data['ordered_items'][0]['product_info']['id'], self.product_info1.id)

        # Проверяем, что в общей сумме учитываются только товары данного магазина
        self.assertEqual(order_data['total_sum'], self.product_info1.price * self.order_item1.quantity)

    def test_get_partner_orders_second_shop(self):
        """
        Тестирование получения списка заказов вторым магазином.
        """
        # Аутентификация как второй магазин
        self.client.force_authenticate(user=self.shop2_user)

        response = self.client.get(self.partner_orders_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что второй магазин видит оба заказа
        self.assertEqual(len(response.data), 2)

        # Проверяем, что в первом заказе магазин видит только свою позицию
        first_order = next(order for order in response.data if order['id'] == self.order.id)
        self.assertEqual(len(first_order['ordered_items']), 1)
        self.assertEqual(first_order['ordered_items'][0]['product_info']['id'], self.product_info2.id)

        # Проверяем, что во втором заказе магазин видит свою позицию
        second_order = next(order for order in response.data if order['id'] == self.order2.id)
        self.assertEqual(len(second_order['ordered_items']), 1)
        self.assertEqual(second_order['ordered_items'][0]['product_info']['id'], self.product_info2.id)

        # Проверяем суммы заказов
        self.assertEqual(first_order['total_sum'], self.product_info2.price * self.order_item2.quantity)
        self.assertEqual(second_order['total_sum'], self.product_info2.price * self.order_item3.quantity)
