from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from django.db import transaction
from backend.models import Shop, Category, Product, ProductInfo, Order, OrderItem, Contact

User = get_user_model()


class OrderViewAdvancedTestCase(TestCase):
    """
    Расширенные тесты для OrderView и OrderDetailView.
    Фокусируются на непокрытых сценариях и обработке ошибок.
    """

    def setUp(self):
        """
        Подготовка тестовых данных.
        """
        self.client = APIClient()

        # Создание тестовых пользователей
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
            is_active=True
        )

        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='password123',
            first_name='Other',
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
            phone='+1234567890'
        )

        # Создание тестового контакта для другого пользователя
        self.other_contact = Contact.objects.create(
            user=self.other_user,
            city='Other City',
            street='Other Street',
            house='456',
            phone='+0987654321'
        )

        # Создаем тестовую корзину
        self.basket = Order.objects.create(
            user=self.user,
            state='basket'
        )

        # Добавляем товар в корзину
        self.order_item = OrderItem.objects.create(
            order=self.basket,
            product_info=self.product_info,
            quantity=2
        )

        # Создаем оформленный заказ
        self.order = Order.objects.create(
            user=self.user,
            state='new',
            contact=self.contact
        )

        # Добавляем товар в заказ
        OrderItem.objects.create(
            order=self.order,
            product_info=self.product_info,
            quantity=1
        )

        # URLs для запросов
        self.order_url = '/api/v1/order'
        self.order_detail_url = f'/api/v1/order/{self.order.id}'
        self.basket_detail_url = f'/api/v1/order/{self.basket.id}'

    def test_get_empty_orders(self):
        """
        Тестирование получения пустого списка заказов.
        """
        # Удаляем все заказы пользователя
        Order.objects.filter(user=self.user).exclude(state='basket').delete()

        # Запрос списка заказов
        response = self.client.get(self.order_url)

        # Проверяем, что запрос успешен и список заказов пуст
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_place_order_missing_fields(self):
        """
        Тестирование оформления заказа с отсутствующими полями.
        """
        # Запрос без ID корзины
        data = {
            'contact': self.contact.id
        }

        response = self.client.post(self.order_url, data)

        # Проверяем, что запрос завершился с ошибкой
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn('Не указаны обязательные поля', response.data['error'])

        # Запрос без ID контакта
        data = {
            'id': self.basket.id
        }

        response = self.client.post(self.order_url, data)

        # Проверяем, что запрос завершился с ошибкой
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn('Не указаны обязательные поля', response.data['error'])

    def test_place_order_nonexistent_basket(self):
        """
        Тестирование оформления несуществующей корзины.
        """
        data = {
            'id': 99999,  # Несуществующий ID
            'contact': self.contact.id
        }

        response = self.client.post(self.order_url, data)

        # Проверяем, что запрос завершился с ошибкой
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['status'])
        self.assertEqual(response.data['error'], "Корзина не найдена")

    def test_place_order_other_users_basket(self):
        """
        Тестирование оформления корзины другого пользователя.
        """
        # Создаем корзину для другого пользователя
        other_basket = Order.objects.create(
            user=self.other_user,
            state='basket'
        )

        data = {
            'id': other_basket.id,
            'contact': self.contact.id
        }

        response = self.client.post(self.order_url, data)

        # Проверяем, что запрос завершился с ошибкой
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['status'])
        self.assertEqual(response.data['error'], "Корзина не найдена")

    def test_place_order_with_deleted_contact(self):
        """
        Тестирование оформления заказа с удаленным контактом.
        """
        # Помечаем контакт как удаленный
        self.contact.is_deleted = True
        self.contact.save()

        data = {
            'id': self.basket.id,
            'contact': self.contact.id
        }

        response = self.client.post(self.order_url, data)

        # Проверяем, что запрос завершился с ошибкой
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['status'])
        self.assertEqual(response.data['error'], "Контакт не найден или был удален")

        # Восстанавливаем контакт для других тестов
        self.contact.is_deleted = False
        self.contact.save()

    def test_place_order_with_other_users_contact(self):
        """
        Тестирование оформления заказа с контактом другого пользователя.
        """
        data = {
            'id': self.basket.id,
            'contact': self.other_contact.id
        }

        response = self.client.post(self.order_url, data)

        # Проверяем, что запрос завершился с ошибкой
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['status'])
        self.assertEqual(response.data['error'], "Контакт не найден или был удален")

    def test_place_order_with_inactive_shop(self):
        """
        Тестирование оформления заказа с товарами из неактивного магазина.
        """
        # Деактивируем магазин
        self.shop.state = False
        self.shop.save()

        data = {
            'id': self.basket.id,
            'contact': self.contact.id
        }

        response = self.client.post(self.order_url, data)

        # Проверяем, что запрос завершился с ошибкой
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn("не принимают заказы", response.data['error'])

        # Активируем магазин обратно для других тестов
        self.shop.state = True
        self.shop.save()

    def test_get_order_detail_nonexistent(self):
        """
        Тестирование получения деталей несуществующего заказа.
        """
        nonexistent_url = f'/api/v1/order/99999'

        response = self.client.get(nonexistent_url)

        # Проверяем, что запрос завершился с ошибкой
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['status'])
        self.assertEqual(response.data['error'], "Заказ не найден")

    def test_get_order_detail_other_user(self):
        """
        Тестирование получения деталей заказа другого пользователя.
        """
        # Создаем заказ для другого пользователя
        other_order = Order.objects.create(
            user=self.other_user,
            state='new',
            contact=self.other_contact
        )

        other_order_url = f'/api/v1/order/{other_order.id}'

        response = self.client.get(other_order_url)

        # Проверяем, что запрос завершился с ошибкой
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['status'])
        self.assertEqual(response.data['error'], "Заказ не найден")

    def test_put_with_invalid_action(self):
        """
        Тестирование PUT-запроса с неизвестным действием.
        """
        data = {
            'action': 'unknown_action'
        }

        response = self.client.put(self.order_detail_url, data)

        # Проверяем, что запрос завершился с ошибкой
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn("Неизвестное действие", response.data['error'])

    @patch('backend.api.views.order_views.transaction.atomic')
    def test_cancel_order_with_transaction_error(self, mock_atomic):
        """
        Тестирование отмены заказа с ошибкой транзакции.
        """
        # Имитируем ошибку транзакции
        mock_atomic.side_effect = Exception("Тестовая ошибка транзакции")

        data = {
            'action': 'cancel'
        }

        response = self.client.put(self.order_detail_url, data)

        # Проверяем, что запрос завершился с ошибкой
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['status'])
        self.assertEqual(response.data['error'], "Тестовая ошибка транзакции")

    @patch('backend.tasks.send_order_confirmation_email.delay')
    def test_order_confirmation_email_task(self, mock_send_email):
        """
        Тестирование вызова задачи отправки email при оформлении заказа.
        """
        data = {
            'id': self.basket.id,
            'contact': self.contact.id
        }

        response = self.client.post(self.order_url, data)

        # Проверяем, что запрос успешен и задача вызвана
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['status'])

        # Находим созданный заказ
        new_order_id = response.data['data']['id']

        # Проверяем, что задача вызвана с правильным параметром
        mock_send_email.assert_called_once_with(new_order_id)
