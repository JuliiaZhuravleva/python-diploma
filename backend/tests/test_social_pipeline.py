from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import Mock, patch
from backend.social_pipeline import activate_user

User = get_user_model()


class SocialPipelineTestCase(TestCase):
    """
    Тесты для функций pipeline социальной авторизации.
    """

    def setUp(self):
        """
        Подготовка тестовых данных.
        """
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
            is_active=False  # Неактивный пользователь
        )

    def test_activate_user_activates_inactive_user(self):
        """
        Тестирование активации неактивного пользователя.
        """
        # Создаем мок backend
        backend = Mock()
        backend.name = 'google-oauth2'

        response = {}

        # Убеждаемся, что пользователь неактивен
        self.assertFalse(self.user.is_active)

        # Вызываем функцию
        with patch('builtins.print') as mock_print:
            result = activate_user(backend, self.user, response)

        # Проверяем, что пользователь активирован
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

        # Проверяем возвращаемое значение
        self.assertEqual(result, {'user': self.user})

        # Проверяем, что вызван print с правильным сообщением
        mock_print.assert_called_once_with(f"Пользователь {self.user.email} активирован через {backend.name}")

    def test_activate_user_does_not_change_active_user(self):
        """
        Тестирование, что уже активный пользователь остается активным.
        """
        # Активируем пользователя
        self.user.is_active = True
        self.user.save()

        # Создаем мок backend
        backend = Mock()
        backend.name = 'github'

        response = {}

        # Убеждаемся, что пользователь активен
        self.assertTrue(self.user.is_active)

        # Вызываем функцию
        with patch('builtins.print') as mock_print:
            result = activate_user(backend, self.user, response)

        # Проверяем, что пользователь остался активным
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

        # Проверяем возвращаемое значение
        self.assertEqual(result, {'user': self.user})

        # Проверяем, что print НЕ был вызван (пользователь уже активен)
        mock_print.assert_not_called()

    def test_activate_user_with_none_user(self):
        """
        Тестирование поведения функции с None user.
        """
        backend = Mock()
        backend.name = 'google-oauth2'
        response = {}

        # Вызываем функцию с None пользователем
        with patch('builtins.print') as mock_print:
            result = activate_user(backend, None, response)

        # Проверяем возвращаемое значение
        self.assertEqual(result, {'user': None})

        # Проверяем, что print НЕ был вызван
        mock_print.assert_not_called()

    def test_activate_user_with_extra_args_kwargs(self):
        """
        Тестирование функции с дополнительными аргументами.
        """
        backend = Mock()
        backend.name = 'google-oauth2'
        response = {}
        extra_args = ('arg1', 'arg2')
        extra_kwargs = {'key1': 'value1', 'key2': 'value2'}

        # Убеждаемся, что пользователь неактивен
        self.assertFalse(self.user.is_active)

        # Вызываем функцию с дополнительными аргументами
        with patch('builtins.print') as mock_print:
            result = activate_user(backend, self.user, response, *extra_args, **extra_kwargs)

        # Проверяем, что пользователь активирован
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

        # Проверяем возвращаемое значение
        self.assertEqual(result, {'user': self.user})

        # Проверяем, что вызван print с правильным сообщением
        mock_print.assert_called_once_with(f"Пользователь {self.user.email} активирован через {backend.name}")