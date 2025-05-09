from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from backend.models import Shop, Category, Product, ProductInfo, Order, OrderItem, Contact

User = get_user_model()


class PartnerViewsAdvancedTestCase(TestCase):
    """
    Расширенные тесты для представлений партнеров.
    Фокусируются на граничных случаях и обработке ошибок.
    """

    def setUp(self):
        """
        Подготовка тестовых данных.
        """
        self.client = APIClient()

        # Создание тестовых пользователей
        self.shop_user = User.objects.create_user(
            email='shop@example.com',
            password='password123',
            is_active=True,
            type='shop'
        )

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
            user=self.buyer_user,
            city='Test City',
            street='Test Street',
            house='123',
            phone='+1234567890'
        )

        # Создание тестового заказа
        self.order = Order.objects.create(
            user=self.buyer_user,
            state='new',
            contact=self.contact
        )

        # Добавление товара в заказ
        OrderItem.objects.create(
            order=self.order,
            product_info=self.product_info,
            quantity=2
        )

        # URLs для запросов
        self.partner_update_url = '/api/v1/partner/update'
        self.partner_state_url = '/api/v1/partner/state'
        self.partner_orders_url = '/api/v1/partner/orders'

    def test_partner_update_without_url(self):
        """
        Тестирование обновления прайс-листа без указания URL.
        """
        # Аутентификация как магазин
        self.client.force_authenticate(user=self.shop_user)

        # Запрос без URL
        response = self.client.post(self.partner_update_url)

        # Проверяем ответ
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn("Необходимо указать URL", response.data['error'])

    @patch('backend.tasks.import_shop_data_task.delay')
    def test_partner_update_empty_url(self, mock_import_task):
        """
        Тестирование обновления прайс-листа с пустым URL.
        """
        # Аутентификация как магазин
        self.client.force_authenticate(user=self.shop_user)

        # Запрос с пустым URL
        data = {"url": ""}
        response = self.client.post(self.partner_update_url, data)

        # Проверяем ответ
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn("Необходимо указать URL", response.data['error'])

        # Проверяем, что задача не вызвана
        mock_import_task.assert_not_called()

    def test_partner_state_without_authorization(self):
        """
        Тестирование доступа к состоянию партнера без аутентификации.
        """
        # Запрос без аутентификации
        self.client.force_authenticate(user=None)

        response = self.client.get(self.partner_state_url)

        # Проверяем, что запрос завершился с ошибкой аутентификации
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_partner_state_invalid_value(self):
        """
        Тестирование обновления состояния партнера с некорректным значением.
        """
        # Аутентификация как магазин
        self.client.force_authenticate(user=self.shop_user)

        # Запрос с некорректным значением state
        data = {"state": "invalid"}
        response = self.client.post(self.partner_state_url, data)

        # Проверяем ответ
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn("Параметр state должен быть", response.data['error'])

    def test_update_partner_state_without_state(self):
        """
        Тестирование обновления состояния партнера без указания state.
        """
        # Аутентификация как магазин
        self.client.force_authenticate(user=self.shop_user)

        # Запрос без указания state
        response = self.client.post(self.partner_state_url, {})

        # Проверяем ответ
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn("Параметр state должен быть", response.data['error'])

    def test_get_partner_state_for_nonexistent_shop(self):
        """
        Тестирование получения состояния для пользователя без магазина.
        """
        # Создаем пользователя без магазина
        user_without_shop = User.objects.create_user(
            email='noshop@example.com',
            password='password123',
            is_active=True,
            type='shop'
        )

        # Аутентификация
        self.client.force_authenticate(user=user_without_shop)

        response = self.client.get(self.partner_state_url)

        # Проверяем ответ
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['status'])
        self.assertEqual(response.data['error'], "Магазин не найден")

    def test_partner_orders_empty_list(self):
        """
        Тестирование получения пустого списка заказов для партнера.
        """
        # Создаем магазин без заказов
        shop_user2 = User.objects.create_user(
            email='shop2@example.com',
            password='password123',
            is_active=True,
            type='shop'
        )

        shop2 = Shop.objects.create(
            name='Test Shop 2',
            user=shop_user2,
            state=True
        )

        # Аутентификация
        self.client.force_authenticate(user=shop_user2)

        response = self.client.get(self.partner_orders_url)

        # Проверяем ответ
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # Пустой список

    def test_partner_orders_basket_excluded(self):
        """
        Тестирование, что заказы в статусе 'basket' не включаются в список.
        """
        # Аутентификация как магазин
        self.client.force_authenticate(user=self.shop_user)

        # Создаем заказ в статусе 'basket'
        basket_order = Order.objects.create(
            user=self.buyer_user,
            state='basket'
        )

        # Добавляем товар в корзину
        OrderItem.objects.create(
            order=basket_order,
            product_info=self.product_info,
            quantity=1
        )

        response = self.client.get(self.partner_orders_url)

        # Проверяем ответ
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что в ответе нет заказов в статусе 'basket'
        order_states = [order['state'] for order in response.data]
        self.assertNotIn('basket', order_states)

    def test_partner_orders_multiple_items(self):
        """
        Тестирование заказа с несколькими позициями от одного магазина.
        """
        # Аутентификация как магазин
        self.client.force_authenticate(user=self.shop_user)

        # Создаем второй товар
        product2 = Product.objects.create(
            name='Test Product 2',
            category=self.category
        )

        product_info2 = ProductInfo.objects.create(
            product=product2,
            shop=self.shop,
            external_id=2,
            model='Test Model 2',
            price=200,
            price_rrc=240,
            quantity=5
        )

        # Добавляем второй товар в существующий заказ
        OrderItem.objects.create(
            order=self.order,
            product_info=product_info2,
            quantity=3
        )

        response = self.client.get(self.partner_orders_url)

        # Проверяем ответ
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Один заказ

        # Проверяем количество позиций в заказе
        self.assertEqual(len(response.data[0]['ordered_items']), 2)  # Две позиции

        # Проверяем общую сумму заказа (2*100 + 3*200 = 800)
        self.assertEqual(response.data[0]['total_sum'], 800)
