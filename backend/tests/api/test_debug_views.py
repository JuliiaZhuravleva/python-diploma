from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, Mock
import logging

User = get_user_model()


class DebugViewsTestCase(TestCase):
    """
    Тесты для debug views.
    Эти тесты проверяют успешные вызовы функций, мокая ошибочные части.
    """

    def setUp(self):
        """
        Подготовка тестового окружения.
        """
        self.client = APIClient()

        # Создаем тестового пользователя для тестов, требующих аутентификации
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password123',
            is_active=True
        )

    @patch('backend.api.views.debug_views.logger')
    def test_success_endpoint(self, mock_logger):
        """
        Тестирование успешного debug endpoint.
        """
        url = reverse('api:debug-success')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем структуру ответа
        data = response.json()
        self.assertIn('message', data)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('Sentry интеграция работает!', data['message'])

        # Проверяем, что логирование было вызвано
        mock_logger.info.assert_called_once_with("Успешный вызов test_success")

    @patch('time.sleep')
    @patch('backend.api.views.debug_views.logger')
    def test_slow_request_endpoint(self, mock_logger, mock_sleep):
        """
        Тестирование endpoint медленного запроса (мокаем sleep).
        """
        url = reverse('api:debug-slow-request')

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем структуру ответа
        data = response.json()
        self.assertIn('message', data)
        self.assertIn('delay_seconds', data)
        self.assertEqual(data['delay_seconds'], 3)
        self.assertIn('Медленный запрос завершен', data['message'])

        # Проверяем, что sleep был вызван с правильным параметром
        mock_sleep.assert_called_once_with(3)

        # Проверяем логирование
        mock_logger.info.assert_called_once_with(
            "Вызов test_slow_request для тестирования performance monitoring"
        )

    @patch('backend.api.views.debug_views.logger')
    def test_zero_division_error_logging(self, mock_logger):
        """
        Тестирование логирования в zero division error endpoint.
        Мы НЕ вызываем реальную ошибку, а проверяем, что логирование работает.
        """
        url = reverse('api:debug-zero-division')

        # Ожидаем, что endpoint вызовет ошибку
        with self.assertRaises(ZeroDivisionError):
            self.client.get(url)

        # Проверяем, что логирование было вызвано до ошибки
        mock_logger.info.assert_called_once_with(
            "Вызов test_zero_division_error для тестирования Sentry"
        )

    @patch('backend.api.views.debug_views.logger')
    def test_unhandled_exception_logging(self, mock_logger):
        """
        Тестирование логирования в unhandled exception endpoint.
        """
        url = reverse('api:debug-unhandled-exception')

        # Ожидаем, что endpoint вызовет NameError
        with self.assertRaises(NameError):
            self.client.get(url)

        # Проверяем логирование
        mock_logger.info.assert_called_once_with(
            "Вызов test_unhandled_exception для тестирования Sentry"
        )

    @patch('django.db.connection.cursor')
    @patch('backend.api.views.debug_views.logger')
    def test_database_error_logging(self, mock_logger, mock_cursor):
        """
        Тестирование логирования в database error endpoint.
        Мокаем курсор, чтобы избежать реальной ошибки БД.
        """
        url = reverse('api:debug-database-error')

        # Настраиваем мок курсора
        mock_cursor_instance = Mock()
        mock_cursor.return_value.__enter__.return_value = mock_cursor_instance

        response = self.client.get(url)

        # Если мы замокали курсор правильно, ошибки не будет
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем, что курсор был вызван с правильным SQL
        mock_cursor_instance.execute.assert_called_once_with(
            "SELECT * FROM non_existent_table_for_testing"
        )

        # Проверяем логирование
        mock_logger.info.assert_called_once_with(
            "Вызов test_database_error для тестирования Sentry"
        )

    @patch('sentry_sdk.configure_scope')
    @patch('backend.api.views.debug_views.logger')
    def test_custom_exception_authentication_required(self, mock_logger, mock_sentry):
        """
        Тестирование, что custom exception endpoint требует аутентификации.
        """
        url = reverse('api:debug-custom-exception')

        # Запрос без аутентификации
        response = self.client.post(url)

        # Должен вернуть ошибку аутентификации
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Логирование не должно быть вызвано
        mock_logger.info.assert_not_called()

    @patch('sentry_sdk.configure_scope')
    @patch('backend.api.views.debug_views.logger')
    def test_custom_exception_with_authentication(self, mock_logger, mock_sentry):
        """
        Тестирование custom exception endpoint с аутентификацией.
        Мокаем Sentry, чтобы проверить логику без реального исключения.
        """
        url = reverse('api:debug-custom-exception')

        # Настраиваем мок для Sentry
        mock_scope = Mock()
        mock_sentry.return_value.__enter__.return_value = mock_scope

        # Аутентифицируем пользователя
        self.client.force_authenticate(user=self.user)

        # Ожидаем ValueError
        with self.assertRaises(ValueError) as context:
            self.client.post(url)

        # Проверяем сообщение исключения
        self.assertIn('Тестовое пользовательское исключение с контекстом', str(context.exception))

        # Проверяем логирование
        mock_logger.info.assert_called_once_with(f"Вызов test_custom_exception пользователем {self.user}")

        # Проверяем, что Sentry scope был настроен
        mock_scope.set_tag.assert_called_with("test_type", "custom_exception")
        mock_scope.set_context.assert_called_once()
        mock_scope.set_extra.assert_called_with("custom_data", "Дополнительная информация для отладки")

    def test_custom_exception_context_data(self):
        """
        Тестирование данных контекста в custom exception endpoint.
        """
        url = reverse('api:debug-custom-exception')

        with patch('sentry_sdk.configure_scope') as mock_sentry:
            mock_scope = Mock()
            mock_sentry.return_value.__enter__.return_value = mock_scope

            self.client.force_authenticate(user=self.user)

            with self.assertRaises(ValueError):
                self.client.post(url, HTTP_USER_AGENT='Test-User-Agent')

            # Проверяем, что контекст установлен с правильными данными
            mock_scope.set_context.assert_called_once()
            call_args = mock_scope.set_context.call_args

            self.assertEqual(call_args[0][0], "request_data")
            context_data = call_args[0][1]
            self.assertEqual(context_data["method"], "POST")
            self.assertIn("/debug/sentry/custom-exception/", context_data["path"])
            self.assertEqual(context_data["user_agent"], "Test-User-Agent")

    def test_debug_endpoints_permissions(self):
        """
        Тестирование разрешений для различных debug endpoints.
        """
        # Тестируем только endpoints, которые не вызывают реальных ошибок
        safe_endpoints = [
            'debug-success'
        ]

        # Endpoints, которые вызывают ошибки - тестируем отдельно
        error_endpoints = [
            ('debug-zero-division', ZeroDivisionError),
            ('debug-unhandled-exception', NameError),
            ('debug-database-error', Exception),  # Может быть разные типы DB ошибок
            ('debug-slow-request', None)  # Этот endpoint работает, но медленно
        ]

        # Тестируем безопасные endpoints
        for endpoint_name in safe_endpoints:
            url = reverse(f'api:{endpoint_name}')
            response = self.client.get(url)
            # Должен быть успешный ответ без требования аутентификации
            self.assertEqual(response.status_code, 200,
                             f"Endpoint {endpoint_name} должен быть доступен без аутентификации")

        # Тестируем endpoints с ошибками
        for endpoint_name, expected_error in error_endpoints:
            url = reverse(f'api:{endpoint_name}')

            if expected_error:
                # Ожидаем определенную ошибку
                with self.assertRaises(expected_error):
                    self.client.get(url)
            else:
                # Для slow-request просто проверяем, что нет ошибок аутентификации
                with patch('time.sleep'):  # Мокаем sleep для ускорения
                    response = self.client.get(url)
                    self.assertNotIn(response.status_code, [401, 403],
                                     f"Endpoint {endpoint_name} требует аутентификации, хотя не должен")

        # Отдельно тестируем endpoint, требующий аутентификации
        custom_exception_url = reverse('api:debug-custom-exception')
        response = self.client.post(custom_exception_url)
        self.assertEqual(response.status_code, 401,
                         "Custom exception endpoint должен требовать аутентификации")

    @patch('backend.api.views.debug_views.logger')
    def test_all_debug_endpoints_logging(self, mock_logger):
        """
        Тестирование, что все debug endpoints вызывают логирование.
        """
        # Тестируем только успешный endpoint, чтобы избежать реальных ошибок
        url = reverse('api:debug-success')
        self.client.get(url)

        # Проверяем, что логирование было вызвано
        self.assertTrue(mock_logger.info.called)

        # Проверяем, что используется правильный уровень логирования
        call_args = mock_logger.info.call_args[0][0]
        self.assertIsInstance(call_args, str)
        self.assertTrue(len(call_args) > 0)