from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from backend.models import Shop, Category, Product, ProductInfo, Order, OrderItem, Contact

User = get_user_model()


class OrderCancelTestCase(TestCase):
    """
    Тестирование функциональности отмены заказа пользователем.
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
            quantity=10  # Изначальное количество на складе
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

        # Создание тестового заказа
        self.order = Order.objects.create(
            user=self.user,
            state='new',  # Заказ в статусе "new"
            contact=self.contact
        )

        # Добавление товара в заказ
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product_info=self.product_info,
            quantity=3  # Заказано 3 единицы товара
        )

        # Уменьшаем количество на складе (как это произошло бы при оформлении заказа)
        self.product_info.quantity -= 3
        self.product_info.save()

        # URL для доступа к деталям заказа
        self.order_detail_url = f'/api/v1/order/{self.order.id}'

    def test_cancel_order_success(self):
        """
        Тестирование успешной отмены заказа пользователем.
        """
        # Данные для запроса
        data = {
            'action': 'cancel'
        }

        response = self.client.put(self.order_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertEqual(response.data['message'], "Заказ успешно отменен")

        # Проверяем, что заказ перешел в статус 'canceled'
        self.order.refresh_from_db()
        self.assertEqual(self.order.state, 'canceled')

        # Проверяем, что количество товара вернулось на склад
        self.product_info.refresh_from_db()
        self.assertEqual(self.product_info.quantity, 10)  # 7 + 3 = 10 (исходное значение)

    def test_cancel_non_new_order(self):
        """
        Тестирование отмены заказа, который не в статусе 'new'.
        """
        # Меняем статус заказа на 'confirmed'
        self.order.state = 'confirmed'
        self.order.save()

        # Данные для запроса
        data = {
            'action': 'cancel'
        }

        response = self.client.put(self.order_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertEqual(response.data['error'], "Отменить можно только новый заказ")

        # Проверяем, что статус заказа не изменился
        self.order.refresh_from_db()
        self.assertEqual(self.order.state, 'confirmed')

        # Проверяем, что количество товара не изменилось
        self.product_info.refresh_from_db()
        self.assertEqual(self.product_info.quantity, 7)  # Остается прежним

    def test_cancel_order_invalid_action(self):
        """
        Тестирование отмены заказа с неверным действием.
        """
        # Данные для запроса с неверным действием
        data = {
            'action': 'invalid_action'
        }

        response = self.client.put(self.order_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertEqual(response.data['error'], "Неизвестное действие. Допустимое действие: 'cancel'")

        # Проверяем, что статус заказа не изменился
        self.order.refresh_from_db()
        self.assertEqual(self.order.state, 'new')

    def test_cancel_other_user_order(self):
        """
        Тестирование попытки отмены заказа другого пользователя.
        """
        # Создаем другого пользователя
        other_user = User.objects.create_user(
            email='other@example.com',
            password='password123',
            is_active=True
        )

        # Аутентифицируем другого пользователя
        self.client.force_authenticate(user=other_user)

        # Данные для запроса
        data = {
            'action': 'cancel'
        }

        response = self.client.put(self.order_detail_url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['status'])
        self.assertEqual(response.data['error'], "Заказ не найден")

        # Проверяем, что статус заказа не изменился
        self.order.refresh_from_db()
        self.assertEqual(self.order.state, 'new')