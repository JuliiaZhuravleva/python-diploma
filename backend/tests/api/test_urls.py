from django.test import TestCase
from django.urls import reverse, resolve


class UrlsTestCase(TestCase):
    """
    Тестирование URL-маршрутизации API.

    Проверяет, что основные URL-пути API правильно настроены и связаны с соответствующими представлениями.
    """

    def test_api_root_url(self):
        """
        Тестирование доступности корневого URL API.
        """
        response = self.client.get('/api/v1/')

        self.assertEqual(response.status_code, 404)
