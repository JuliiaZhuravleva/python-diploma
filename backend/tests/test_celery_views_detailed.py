from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from backend.api.views.celery_views import TaskStatusView

User = get_user_model()


class TaskStatusViewTestCase(TestCase):
    """
    Тесты для TaskStatusView, который предоставляет информацию о статусе асинхронных задач Celery.
    """

    def setUp(self):
        """
        Подготовка тестовых данных.
        """
        self.client = APIClient()

        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password123',
            is_active=True
        )

        # Аутентифицируем пользователя
        self.client.force_authenticate(user=self.user)

        # URL для тестирования
        self.task_url = '/api/v1/task/some-task-id'

    @patch('backend.api.views.celery_views.AsyncResult')
    def test_get_pending_task_status(self, mock_async_result):
        """
        Тестирование получения статуса задачи в состоянии 'PENDING'.
        """
        # Настройка мока AsyncResult
        mock_task = MagicMock()
        mock_task.state = 'PENDING'
        mock_async_result.return_value = mock_task

        # Выполнение запроса
        response = self.client.get(self.task_url)

        # Проверка результата
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'pending')
        self.assertIn('Задача находится в очереди', response.data['message'])

    @patch('backend.api.views.celery_views.AsyncResult')
    def test_get_started_task_status(self, mock_async_result):
        """
        Тестирование получения статуса задачи в состоянии 'STARTED'.
        """
        # Настройка мока AsyncResult
        mock_task = MagicMock()
        mock_task.state = 'STARTED'
        mock_async_result.return_value = mock_task

        # Выполнение запроса
        response = self.client.get(self.task_url)

        # Проверка результата
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'started')
        self.assertIn('Задача выполняется', response.data['message'])

    @patch('backend.api.views.celery_views.AsyncResult')
    def test_get_success_task_status(self, mock_async_result):
        """
        Тестирование получения статуса задачи в состоянии 'SUCCESS'.
        """
        # Настройка мока AsyncResult
        mock_task = MagicMock()
        mock_task.state = 'SUCCESS'
        mock_task.result = {'key': 'value'}
        mock_async_result.return_value = mock_task

        # Выполнение запроса
        response = self.client.get(self.task_url)

        # Проверка результата
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'success')
        self.assertIn('успешно выполнена', response.data['message'])
        self.assertEqual(response.data['result'], {'key': 'value'})

    @patch('backend.api.views.celery_views.AsyncResult')
    def test_get_failure_task_status(self, mock_async_result):
        """
        Тестирование получения статуса задачи в состоянии 'FAILURE'.
        """
        # Настройка мока AsyncResult
        mock_task = MagicMock()
        mock_task.state = 'FAILURE'
        mock_task.result = Exception('Тестовая ошибка')
        mock_async_result.return_value = mock_task

        # Выполнение запроса
        response = self.client.get(self.task_url)

        # Проверка результата
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'failure')
        self.assertIn('завершилась с ошибкой', response.data['message'])
        self.assertEqual(response.data['error'], 'Тестовая ошибка')

    @patch('backend.api.views.celery_views.AsyncResult')
    def test_get_unknown_task_status(self, mock_async_result):
        """
        Тестирование получения задачи с неизвестным статусом.
        """
        # Настройка мока AsyncResult
        mock_task = MagicMock()
        mock_task.state = 'UNKNOWN_STATE'
        mock_async_result.return_value = mock_task

        # Выполнение запроса
        response = self.client.get(self.task_url)

        # Проверка результата
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'UNKNOWN_STATE')
        self.assertIn('Неизвестный статус', response.data['message'])

    def test_unauthenticated_access(self):
        """
        Тестирование доступа без аутентификации.
        """
        # Убираем аутентификацию
        self.client.force_authenticate(user=None)

        # Выполнение запроса
        response = self.client.get(self.task_url)

        # Проверка результата - должен быть отказ в доступе
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)