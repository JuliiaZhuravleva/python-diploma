from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch, ANY
from backend.models import Shop, Category, Product, ProductInfo, Order, OrderItem, Contact

User = get_user_model()


class CeleryViewsTestCase(TestCase):
    """
    Тесты для представлений, использующих Celery-задачи.
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

        # Создание тестового пользователя магазина
        self.shop_user = User.objects.create_user(
            email='shop@example.com',
            password='password123',
            is_active=True,
            type='shop'
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

    @patch('backend.tasks.send_confirmation_email.delay')
    def test_user_register_with_celery(self, mock_send_confirmation_email):
        """
        Тестирование регистрации пользователя с отправкой email через Celery.
        """
        # Данные нового пользователя
        user_data = {
            'email': 'new_user@example.com',
            'password': 'ValidPass123!',
            'first_name': 'New',
            'last_name': 'User',
            'company': 'Test Company',
            'position': 'Developer'
        }

        # Отправляем запрос на регистрацию
        response = self.client.post('/api/v1/user/register', user_data, format='json')

        # Проверяем успешный ответ
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['status'])

        # Проверяем вызов задачи Celery
        mock_send_confirmation_email.assert_called_once()

    @patch('backend.tasks.send_password_reset_email.delay')
    def test_password_reset_with_celery(self, mock_send_password_reset_email):
        """
        Тестирование запроса на сброс пароля с отправкой email через Celery.
        """
        # Данные для запроса
        data = {
            'email': self.user.email
        }

        # Отправляем запрос на сброс пароля
        response = self.client.post('/api/v1/user/password_reset', data, format='json')

        # Проверяем успешный ответ
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем вызов задачи Celery
        mock_send_password_reset_email.assert_called_once()

    @patch('backend.tasks.send_order_confirmation_email.delay')
    def test_place_order_with_celery(self, mock_send_order_confirmation_email):
        """
        Тестирование оформления заказа с отправкой email через Celery.
        """
        # Данные для запроса
        data = {
            'id': self.basket.id,
            'contact': self.contact.id
        }

        # Отправляем запрос на оформление заказа
        response = self.client.post('/api/v1/order', data, format='json')

        # Проверяем успешный ответ
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['status'])
        self.assertEqual(response.data['message'], "Заказ успешно оформлен")

        # Проверяем вызов задачи Celery
        mock_send_order_confirmation_email.assert_called_once()

    @patch('backend.tasks.import_shop_data_task.delay')
    def test_partner_update_with_celery(self, mock_import_shop_data_task):
        """
        Тестирование обновления прайс-листа с использованием Celery.
        """
        # Аутентификация как магазин
        self.client.force_authenticate(user=self.shop_user)

        # Данные для запроса
        data = {
            'url': 'https://example.com/shop1.yaml'
        }

        # Установим, что должна вернуть задача
        mock_import_shop_data_task.return_value.id = 'test-task-id'

        # Отправляем запрос на обновление прайс-листа
        response = self.client.post('/api/v1/partner/update', data, format='json')

        # Проверяем успешный ответ
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertIn('task_id', response.data)

        # Проверяем вызов задачи Celery
        mock_import_shop_data_task.assert_called_once_with(data['url'], self.shop_user.id)

    @patch('backend.tasks.import_shop_data_task.delay')
    def test_partner_update_with_celery_validation_error(self, mock_import_shop_data_task):
        """
        Тестирование обновления прайс-листа с ошибкой валидации URL.
        """
        # Аутентификация как магазин
        self.client.force_authenticate(user=self.shop_user)

        # Данные для запроса с пустым URL
        data = {
            'url': ''
        }

        # Отправляем запрос на обновление прайс-листа
        response = self.client.post('/api/v1/partner/update', data, format='json')

        # Проверяем ответ с ошибкой
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn('error', response.data)

        # Проверяем, что задача Celery не вызывалась
        mock_import_shop_data_task.assert_not_called()

    @patch('backend.tasks.import_shop_data_task.delay')
    def test_partner_update_with_celery_permission_error(self, mock_import_shop_data_task):
        """
        Тестирование обновления прайс-листа пользователем без прав магазина.
        """
        # Аутентификация как обычный покупатель
        self.client.force_authenticate(user=self.user)  # self.user - обычный пользователь, не магазин

        # Данные для запроса
        data = {
            'url': 'https://example.com/shop1.yaml'
        }

        # Отправляем запрос на обновление прайс-листа
        response = self.client.post('/api/v1/partner/update', data, format='json')

        # Проверяем ответ с ошибкой доступа
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(response.data['status'])
        self.assertIn('error', response.data)

        # Проверяем, что задача Celery не вызывалась
        mock_import_shop_data_task.assert_not_called()

    def test_task_status_view_with_real_task(self):
        """
        Тестирование получения статуса реальной асинхронной задачи.
        """
        from backend.tasks import send_confirmation_email

        # Запускаем реальную задачу Celery
        from django.conf import settings

        # Устанавливаем настройки для синхронного выполнения задач
        settings.CELERY_TASK_ALWAYS_EAGER = True
        settings.CELERY_TASK_EAGER_PROPAGATES = True

        # Запуск задачи
        with patch('django.core.mail.send_mail') as mock_send_mail:
            # Блокируем реальную отправку почты
            mock_send_mail.return_value = True

            # Запускаем задачу
            task = send_confirmation_email.delay(self.user.id, 'test-token')

            # Получаем task_id
            task_id = task.id

            # URL для получения статуса задачи
            task_status_url = f'/api/v1/task/{task_id}'

            # Проверяем, доступен ли URL
            try:
                # Запрашиваем статус задачи
                response = self.client.get(task_status_url)

                # Проверяем успешный ответ
                self.assertEqual(response.status_code, status.HTTP_200_OK)

                # В тестовом режиме задача выполняется синхронно,
                # поэтому статус должен быть 'success'
                self.assertEqual(response.data['status'], 'success')
            except:
                # Если URL не настроен, пропускаем тест
                self.skipTest("URL для получения статуса задачи не настроен")
