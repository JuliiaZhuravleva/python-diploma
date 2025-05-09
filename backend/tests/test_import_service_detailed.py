from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
import yaml
import requests
from backend.services.import_service import ImportService
from backend.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter

User = get_user_model()


class ImportServiceTestCase(TestCase):
    """
    Тесты для сервиса импорта данных ImportService.
    """

    def setUp(self):
        """
        Подготовка тестового окружения.
        """
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            email='shop@example.com',
            password='password123',
            is_active=True,
            type='shop'
        )

        # Создаем тестовый магазин
        self.shop = Shop.objects.create(
            name='Test Shop',
            user=self.user,
            state=True
        )

        # Тестовые данные YAML
        self.yaml_data = """
            shop: Test Shop
            categories:
              - id: 1
                name: Category 1
              - id: 2
                name: Category 2
            goods:
              - id: 1
                category: 1
                model: Model 1
                name: Product 1
                price: 100
                price_rrc: 120
                quantity: 10
                parameters:
                  param1: value1
                  param2: value2
              - id: 2
                category: 2
                model: Model 2
                name: Product 2
                price: 200
                price_rrc: 240
                quantity: 5
                parameters:
                  param1: value3
                  param3: value4
        """

    def test_validate_url_success(self):
        """
        Тестирование успешной валидации URL.
        """
        valid, error = ImportService.validate_url('https://example.com/data.yaml')
        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_validate_url_failure_empty(self):
        """
        Тестирование валидации пустого URL.
        """
        valid, error = ImportService.validate_url('')
        self.assertFalse(valid)
        self.assertEqual(error, "URL не указан")

    def test_validate_url_failure_invalid(self):
        """
        Тестирование валидации некорректного URL.
        """
        valid, error = ImportService.validate_url('invalid-url')
        self.assertFalse(valid)
        self.assertIn("Некорректный URL", error)

    @patch('requests.get')
    def test_fetch_data_success(self, mock_get):
        """
        Тестирование успешного получения данных по URL.
        """
        # Настройка мока для requests.get
        mock_response = MagicMock()
        mock_response.content = self.yaml_data.encode('utf-8')
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        success, content = ImportService.fetch_data('https://example.com/data.yaml')
        self.assertTrue(success)
        self.assertEqual(content, self.yaml_data.encode('utf-8'))

    @patch('requests.get')
    def test_fetch_data_failure(self, mock_get):
        """
        Тестирование неудачного получения данных по URL.
        """
        # Настройка мока для requests.get с выбросом исключения
        mock_get.side_effect = requests.RequestException("Connection error")

        success, error = ImportService.fetch_data('https://example.com/data.yaml')
        self.assertFalse(success)
        self.assertIn("Ошибка при получении данных", error)

    def test_parse_yaml_success(self):
        """
        Тестирование успешного парсинга YAML-данных.
        """
        success, data = ImportService.parse_yaml(self.yaml_data.encode('utf-8'))
        self.assertTrue(success)
        self.assertEqual(data['shop'], 'Test Shop')
        self.assertEqual(len(data['categories']), 2)
        self.assertEqual(len(data['goods']), 2)

    def test_parse_yaml_failure(self):
        """
        Тестирование неудачного парсинга YAML-данных.
        """
        invalid_yaml = "shop: Test Shop\ncategories: - invalid yaml"

        success, error = ImportService.parse_yaml(invalid_yaml.encode('utf-8'))
        self.assertFalse(success)
        self.assertIn("Ошибка при парсинге YAML", error)

    def test_validate_structure_success(self):
        """
        Тестирование успешной валидации структуры данных.
        """
        # Парсим YAML-данные для получения структуры
        _, data = ImportService.parse_yaml(self.yaml_data.encode('utf-8'))

        valid, error = ImportService.validate_structure(data)
        self.assertTrue(valid)
        self.assertIsNone(error)

    def test_validate_structure_missing_category_fields(self):
        """
        Тестирование валидации структуры с отсутствующими полями категории.
        """
        # Парсим YAML-данные и удаляем обязательное поле у категории
        _, data = ImportService.parse_yaml(self.yaml_data.encode('utf-8'))
        del data['categories'][0]['name']

        valid, error = ImportService.validate_structure(data)
        self.assertFalse(valid)
        self.assertIn("Категория должна содержать поля", error)

    def test_validate_structure_missing_product_fields(self):
        """
        Тестирование валидации структуры с отсутствующими полями товара.
        """
        # Парсим YAML-данные и удаляем обязательное поле у товара
        _, data = ImportService.parse_yaml(self.yaml_data.encode('utf-8'))
        del data['goods'][0]['price']

        valid, error = ImportService.validate_structure(data)
        self.assertFalse(valid)
        self.assertIn("Товар должен содержать поле", error)

    @patch('backend.services.import_service.Category.objects.get_or_create')
    def test_import_categories(self, mock_get_or_create):
        """
        Тестирование импорта категорий.
        """
        # Парсим YAML-данные для получения структуры
        _, data = ImportService.parse_yaml(self.yaml_data.encode('utf-8'))

        # Настройка мока для Category.objects.get_or_create
        mock_category1 = MagicMock()
        mock_category1.name = 'Category 1'
        mock_category2 = MagicMock()
        mock_category2.name = 'Category 2'

        mock_get_or_create.side_effect = [
            (mock_category1, True),  # Первый вызов - создание новой категории
            (mock_category2, False)  # Второй вызов - получение существующей категории
        ]

        success, message = ImportService.import_categories(data, self.shop)
        self.assertTrue(success)
        self.assertIn("Импортировано категорий: 2", message)

        # Проверяем, что get_or_create вызван дважды
        self.assertEqual(mock_get_or_create.call_count, 2)

        # Проверяем, что метод shops.add вызван для каждой категории
        self.assertEqual(mock_category1.shops.add.call_count, 1)
        self.assertEqual(mock_category2.shops.add.call_count, 1)

    @patch('backend.services.import_service.ProductInfo.objects.filter')
    @patch('backend.services.import_service.Product.objects.get_or_create')
    @patch('backend.services.import_service.ProductInfo.objects.create')
    @patch('backend.services.import_service.Parameter.objects.get_or_create')
    @patch('backend.services.import_service.ProductParameter.objects.create')
    def test_import_products(self, mock_param_create, mock_param_get_or_create,
                             mock_product_info_create, mock_product_get_or_create,
                             mock_product_info_filter):
        """
        Тестирование импорта товаров.
        """
        # Парсим YAML-данные для получения структуры
        _, data = ImportService.parse_yaml(self.yaml_data.encode('utf-8'))

        # Настройка моков
        mock_product1 = MagicMock()
        mock_product1.id = 1
        mock_product2 = MagicMock()
        mock_product2.id = 2

        mock_product_get_or_create.side_effect = [
            (mock_product1, True),  # Первый вызов
            (mock_product2, False)  # Второй вызов
        ]

        mock_product_info1 = MagicMock()
        mock_product_info1.id = 1
        mock_product_info2 = MagicMock()
        mock_product_info2.id = 2

        mock_product_info_create.side_effect = [
            mock_product_info1,  # Первый вызов
            mock_product_info2  # Второй вызов
        ]

        mock_parameter1 = MagicMock()
        mock_parameter1.id = 1
        mock_parameter2 = MagicMock()
        mock_parameter2.id = 2
        mock_parameter3 = MagicMock()
        mock_parameter3.id = 3

        mock_param_get_or_create.side_effect = [
            (mock_parameter1, True),  # param1 для первого товара
            (mock_parameter2, False),  # param2 для первого товара
            (mock_parameter1, False),  # param1 для второго товара
            (mock_parameter3, True)  # param3 для второго товара
        ]

        success, message = ImportService.import_products(data, self.shop)
        self.assertTrue(success)
        self.assertIn("Импортировано товаров: 2", message)
        self.assertIn("параметров: 4", message)

        # Проверяем, что методы вызваны нужное количество раз
        self.assertEqual(mock_product_get_or_create.call_count, 2)
        self.assertEqual(mock_product_info_create.call_count, 2)
        self.assertEqual(mock_param_get_or_create.call_count, 4)
        self.assertEqual(mock_param_create.call_count, 4)

    @patch('backend.services.import_service.ImportService.validate_url')
    @patch('backend.services.import_service.ImportService.fetch_data')
    @patch('backend.services.import_service.ImportService.parse_yaml')
    @patch('backend.services.import_service.ImportService.validate_structure')
    @patch('backend.services.import_service.Shop.objects.get_or_create')
    @patch('backend.services.import_service.ImportService.import_categories')
    @patch('backend.services.import_service.ImportService.import_products')
    def test_import_shop_data_success(self, mock_import_products, mock_import_categories,
                                      mock_shop_get_or_create, mock_validate_structure,
                                      mock_parse_yaml, mock_fetch_data, mock_validate_url):
        """
        Тестирование полного процесса импорта данных магазина - успешный сценарий.
        """
        # Настройка моков
        mock_validate_url.return_value = (True, None)
        mock_fetch_data.return_value = (True, self.yaml_data.encode('utf-8'))
        mock_parse_yaml.return_value = (True, {'shop': 'Test Shop', 'categories': [], 'goods': []})
        mock_validate_structure.return_value = (True, None)

        mock_shop = MagicMock()
        mock_shop.user_id = self.user.id
        mock_shop_get_or_create.return_value = (mock_shop, True)

        mock_import_categories.return_value = (True, "Импортировано категорий: 2")
        mock_import_products.return_value = (True, "Импортировано товаров: 2, параметров: 4")

        # Вызов тестируемого метода
        result = ImportService.import_shop_data('https://example.com/data.yaml', self.user.id)

        # Проверка результата
        self.assertTrue(result['status'])
        self.assertIn("Импорт успешно завершен", result['message'])

        # Проверка вызова всех методов
        mock_validate_url.assert_called_once_with('https://example.com/data.yaml')
        mock_fetch_data.assert_called_once_with('https://example.com/data.yaml')
        mock_parse_yaml.assert_called_once()
        mock_validate_structure.assert_called_once()
        mock_shop_get_or_create.assert_called_once()
        mock_import_categories.assert_called_once()
        mock_import_products.assert_called_once()

    @patch('backend.services.import_service.ImportService.validate_url')
    def test_import_shop_data_invalid_url(self, mock_validate_url):
        """
        Тестирование импорта данных магазина с некорректным URL.
        """
        # Настройка мока для validate_url - возвращает ошибку
        mock_validate_url.return_value = (False, "Некорректный URL")

        # Вызов тестируемого метода
        result = ImportService.import_shop_data('invalid-url', self.user.id)

        # Проверка результата
        self.assertFalse(result['status'])
        self.assertEqual(result['error'], "Некорректный URL")

    @patch('backend.services.import_service.ImportService.validate_url')
    @patch('backend.services.import_service.ImportService.fetch_data')
    def test_import_shop_data_fetch_failure(self, mock_fetch_data, mock_validate_url):
        """
        Тестирование импорта данных магазина с ошибкой получения данных.
        """
        # Настройка моков
        mock_validate_url.return_value = (True, None)
        mock_fetch_data.return_value = (False, "Ошибка при получении данных")

        # Вызов тестируемого метода
        result = ImportService.import_shop_data('https://example.com/data.yaml', self.user.id)

        # Проверка результата
        self.assertFalse(result['status'])
        self.assertEqual(result['error'], "Ошибка при получении данных")

    @patch('backend.services.import_service.ImportService.validate_url')
    @patch('backend.services.import_service.ImportService.fetch_data')
    @patch('backend.services.import_service.ImportService.parse_yaml')
    def test_import_shop_data_parse_failure(self, mock_parse_yaml, mock_fetch_data, mock_validate_url):
        """
        Тестирование импорта данных магазина с ошибкой парсинга YAML.
        """
        # Настройка моков
        mock_validate_url.return_value = (True, None)
        mock_fetch_data.return_value = (True, "invalid yaml")
        mock_parse_yaml.return_value = (False, "Ошибка при парсинге YAML")

        # Вызов тестируемого метода
        result = ImportService.import_shop_data('https://example.com/data.yaml', self.user.id)

        # Проверка результата
        self.assertFalse(result['status'])
        self.assertEqual(result['error'], "Ошибка при парсинге YAML")

    @patch('backend.services.import_service.ImportService.validate_url')
    @patch('backend.services.import_service.ImportService.fetch_data')
    @patch('backend.services.import_service.ImportService.parse_yaml')
    @patch('backend.services.import_service.ImportService.validate_structure')
    def test_import_shop_data_invalid_structure(self, mock_validate_structure, mock_parse_yaml,
                                                mock_fetch_data, mock_validate_url):
        """
        Тестирование импорта данных магазина с некорректной структурой данных.
        """
        # Настройка моков
        mock_validate_url.return_value = (True, None)
        mock_fetch_data.return_value = (True, self.yaml_data.encode('utf-8'))
        mock_parse_yaml.return_value = (True, {'shop': 'Test Shop'})  # Отсутствуют обязательные поля
        mock_validate_structure.return_value = (False, "Отсутствуют обязательные поля")

        # Вызов тестируемого метода
        result = ImportService.import_shop_data('https://example.com/data.yaml', self.user.id)

        # Проверка результата
        self.assertFalse(result['status'])
        self.assertEqual(result['error'], "Отсутствуют обязательные поля")

    @patch('backend.services.import_service.ImportService.validate_url')
    @patch('backend.services.import_service.ImportService.fetch_data')
    @patch('backend.services.import_service.ImportService.parse_yaml')
    @patch('backend.services.import_service.ImportService.validate_structure')
    @patch('backend.services.import_service.Shop.objects.get_or_create')
    def test_import_shop_data_unauthorized(self, mock_shop_get_or_create, mock_validate_structure,
                                           mock_parse_yaml, mock_fetch_data, mock_validate_url):
        """
        Тестирование импорта данных магазина без прав доступа.
        """
        # Настройка моков
        mock_validate_url.return_value = (True, None)
        mock_fetch_data.return_value = (True, self.yaml_data.encode('utf-8'))
        mock_parse_yaml.return_value = (True, {'shop': 'Test Shop', 'categories': [], 'goods': []})
        mock_validate_structure.return_value = (True, None)

        # Создаем магазин с другим владельцем
        mock_shop = MagicMock()
        mock_shop.user_id = self.user.id + 1  # Другой пользователь
        mock_shop_get_or_create.return_value = (mock_shop, False)

        # Вызов тестируемого метода
        result = ImportService.import_shop_data('https://example.com/data.yaml', self.user.id)

        # Проверка результата
        self.assertFalse(result['status'])
        self.assertIn("У вас нет прав на обновление данного магазина", result['error'])
