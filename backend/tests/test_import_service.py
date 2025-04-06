from django.test import TestCase
from django.contrib.auth import get_user_model
from backend.services.import_service import ImportService
from backend.models import Shop, Category, Product

# Получаем активную модель пользователя из настроек Django
User = get_user_model()


class ImportServiceTestCase(TestCase):
   """
   Тестирование сервиса импорта данных магазинов.

   Проверяет основные функции сервиса ImportService:
   - валидацию URL
   - парсинг YAML-файлов с данными магазинов
   """

   def setUp(self):
       """
       Подготовка тестового окружения перед каждым тестом.

       Создает тестового пользователя с типом 'shop', который будет
       использоваться для тестирования функций импорта данных магазина.
       """
       self.user = User.objects.create_user(
           email='shop@example.com',
           password='password123',
           type='shop',
           is_active=True
       )

   def test_validate_url(self):
       """
       Тестирование функции валидации URL.

       Проверяет, что функция:
       - возвращает True для корректных URL
       - возвращает False и сообщение об ошибке для некорректных URL
       """
       valid, _ = ImportService.validate_url('https://example.com/data.yaml')
       self.assertTrue(valid)

       invalid, error = ImportService.validate_url('not-a-url')
       self.assertFalse(invalid)
       self.assertIn('Некорректный URL', error)

   def test_parse_yaml(self):
       """
       Тестирование функции парсинга YAML-данных.

       Проверяет, что функция:
       - корректно парсит YAML-контент
       - правильно извлекает данные о магазине, категориях и товарах
       - возвращает структурированные данные в ожидаемом формате
       """

       # Тестовые данные YAML в бинарном формате (как они могли бы быть получены из HTTP-ответа)
       yaml_content = b"""
   shop: TestShop
   categories:
     - id: 1
       name: Category1
   goods:
     - id: 1
       category: 1
       model: test
       name: Test Product
       price: 100
       price_rrc: 120
       quantity: 10
       parameters:
         param1: value1
   """
       # Парсим YAML-контент
       success, data = ImportService.parse_yaml(yaml_content)

       # Проверяем успешность парсинга
       self.assertTrue(success)

       # Проверяем корректность извлеченных данных
       self.assertEqual(data['shop'], 'TestShop')
       self.assertEqual(len(data['categories']), 1)
       self.assertEqual(len(data['goods']), 1)