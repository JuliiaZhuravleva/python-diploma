from django.test import TestCase
from rest_framework.response import Response
from rest_framework import status
from backend.api.views import ApiResponse
from backend.api.views.test_views import TestAuthView



class ApiResponseTestCase(TestCase):
    """
    Тесты для класса ApiResponse, который используется для формирования ответов API.
    """

    def test_success_response_with_data(self):
        """
        Тестирование метода success с передачей данных и сообщения.
        """
        test_data = {'key': 'value'}
        test_message = 'Операция выполнена успешно'

        response = ApiResponse.success(
            data=test_data,
            message=test_message,
            status_code=status.HTTP_200_OK
        )

        # Проверяем, что возвращается экземпляр класса Response
        self.assertIsInstance(response, Response)

        # Проверяем статус код
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем содержимое ответа
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data'], test_data)
        self.assertEqual(response.data['message'], test_message)

    def test_success_response_without_data(self):
        """
        Тестирование метода success без передачи данных, только с сообщением.
        """
        test_message = 'Операция выполнена успешно'

        response = ApiResponse.success(
            message=test_message,
            status_code=status.HTTP_201_CREATED
        )

        # Проверяем статус код
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем содержимое ответа
        self.assertTrue(response.data['success'])
        self.assertNotIn('data', response.data)
        self.assertEqual(response.data['message'], test_message)

    def test_success_response_without_message(self):
        """
        Тестирование метода success без передачи сообщения, только с данными.
        """
        test_data = {'key': 'value'}

        response = ApiResponse.success(
            data=test_data,
            status_code=status.HTTP_200_OK
        )

        # Проверяем содержимое ответа
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data'], test_data)
        self.assertNotIn('message', response.data)

    def test_error_response_with_errors(self):
        """
        Тестирование метода error с передачей сообщения и списка ошибок.
        """
        test_message = 'Ошибка выполнения операции'
        test_errors = {'field': ['Это поле обязательно.']}

        response = ApiResponse.error(
            message=test_message,
            status_code=status.HTTP_400_BAD_REQUEST,
            errors=test_errors
        )

        # Проверяем статус код
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Проверяем содержимое ответа
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], test_message)
        self.assertEqual(response.data['errors'], test_errors)

    def test_error_response_without_errors(self):
        """
        Тестирование метода error без передачи списка ошибок.
        """
        test_message = 'Ресурс не найден'

        response = ApiResponse.error(
            message=test_message,
            status_code=status.HTTP_404_NOT_FOUND
        )

        # Проверяем статус код
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Проверяем содержимое ответа
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], test_message)
        self.assertNotIn('errors', response.data)


class TestAuthViewTestCase(TestCase):
    """
    Тесты для TestAuthView.
    """

    def test_auth_view_response(self):
        """
        Проверка, что TestAuthView возвращает правильный ответ.
        """
        view = TestAuthView()
        request = type('MockRequest', (), {})()  # Создаем простой мок-объект запроса

        response = view.get(request)

        # Проверяем статус код и содержимое ответа
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "You are authenticated")
