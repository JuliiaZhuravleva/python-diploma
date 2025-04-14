from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from unittest.mock import patch
from backend.models import Shop

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
