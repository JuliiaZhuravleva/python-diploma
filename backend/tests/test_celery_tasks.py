from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch
from backend.models import ConfirmEmailToken, Order, Contact, OrderItem, ProductInfo
from backend.tasks import (
    send_confirmation_email, send_password_reset_email,
    send_order_confirmation_email, import_shop_data_task
)

User = get_user_model()


class CeleryTasksTestCase(TestCase):
    """
    Тесты для Celery-задач.
    """

    def setUp(self):
        """
        Подготовка тестовых данных.
        """
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
            is_active=False
        )

        # Создаем токен для подтверждения email
        self.token = ConfirmEmailToken.objects.create(user=self.user)

    @patch('backend.tasks.send_mail')
    def test_send_confirmation_email(self, mock_send_mail):
        """
        Тестирование отправки email с подтверждением регистрации.
        """
        # Вызов задачи
        send_confirmation_email(self.user.id, self.token.key)

        # Проверка вызова send_mail с правильными аргументами
        mock_send_mail.assert_called_once()
        args, kwargs = mock_send_mail.call_args
        self.assertEqual(kwargs['subject'], 'Подтверждение регистрации')
        self.assertIn(self.token.key, kwargs['message'])
        self.assertEqual(kwargs['recipient_list'], [self.user.email])

    @patch('backend.tasks.send_mail')
    def test_send_password_reset_email(self, mock_send_mail):
        """
        Тестирование отправки email для сброса пароля.
        """
        # Вызов задачи
        send_password_reset_email(self.user.id, self.token.key)

        # Проверка вызова send_mail с правильными аргументами
        mock_send_mail.assert_called_once()
        args, kwargs = mock_send_mail.call_args
        self.assertEqual(kwargs['subject'], 'Сброс пароля')
        self.assertIn(self.token.key, kwargs['message'])
        self.assertEqual(kwargs['recipient_list'], [self.user.email])

    @patch('backend.tasks.send_mail')
    def test_send_order_confirmation_email(self, mock_send_mail):
        """
        Тестирование отправки email с подтверждением заказа.
        """
        # Создаем тестовый заказ
        contact = Contact.objects.create(
            user=self.user,
            city='Test City',
            street='Test Street',
            house='123',
            phone='+1234567890'
        )

        order = Order.objects.create(
            user=self.user,
            state='new',
            contact=contact
        )

        # Вызов задачи
        send_order_confirmation_email(order.id)

        # Проверка вызова send_mail с правильными аргументами
        mock_send_mail.assert_called_once()
        args, kwargs = mock_send_mail.call_args
        self.assertEqual(kwargs['subject'], f'Подтверждение заказа №{order.id}')
        self.assertIn(str(order.id), kwargs['message'])
        self.assertEqual(kwargs['recipient_list'], [self.user.email])

    @patch('backend.services.import_service.ImportService.import_shop_data')
    def test_import_shop_data_task(self, mock_import_shop_data):
        """
        Тестирование асинхронного импорта данных магазина.
        """
        # Устанавливаем, что должен вернуть мок
        expected_result = {
            'status': True,
            'message': 'Импорт успешно завершен'
        }
        mock_import_shop_data.return_value = expected_result

        # Вызов задачи
        result = import_shop_data_task('https://example.com/shop1.yaml', self.user.id)

        # Проверка вызова сервиса с правильными аргументами
        mock_import_shop_data.assert_called_once_with('https://example.com/shop1.yaml', self.user.id)

        # Проверка результата
        self.assertEqual(result, expected_result)
