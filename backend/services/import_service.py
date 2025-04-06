import yaml
from yaml import Loader
import logging
import requests
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from ..models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter

logger = logging.getLogger(__name__)


class ImportService:
    """
    Сервис для импорта данных о товарах магазина из YAML-файлов.
    """

    @staticmethod
    def validate_url(url):
        """
        Проверка корректности URL для импорта данных.
        """
        if not url:
            return False, "URL не указан"

        validate_url = URLValidator()
        try:
            validate_url(url)
            return True, None
        except ValidationError as e:
            return False, f"Некорректный URL: {str(e)}"

    @staticmethod
    def fetch_data(url):
        """
        Получение данных по URL.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            return True, response.content
        except requests.RequestException as e:
            return False, f"Ошибка при получении данных: {str(e)}"

    @staticmethod
    def parse_yaml(content):
        """
        Парсинг YAML-данных.
        """
        try:
            data = yaml.load(content, Loader=Loader)

            # Проверка обязательных полей
            required_fields = ['shop', 'categories', 'goods']
            for field in required_fields:
                if field not in data:
                    return False, f"В данных отсутствует обязательное поле '{field}'"

            return True, data
        except yaml.YAMLError as e:
            return False, f"Ошибка при парсинге YAML: {str(e)}"

    @staticmethod
    def validate_structure(data):
        """
        Проверка структуры YAML-данных.
        """
        # Проверка структуры категорий
        for category in data.get('categories', []):
            if 'id' not in category or 'name' not in category:
                return False, "Категория должна содержать поля 'id' и 'name'"

        # Проверка структуры товаров
        for item in data.get('goods', []):
            required_item_fields = ['id', 'category', 'model', 'name', 'price', 'price_rrc', 'quantity', 'parameters']
            for field in required_item_fields:
                if field not in item:
                    return False, f"Товар должен содержать поле '{field}'"

        return True, None

    @classmethod
    def import_categories(cls, data, shop):
        """
        Импорт категорий из данных.
        """
        try:
            categories_count = 0
            for category in data['categories']:
                category_object, created = Category.objects.get_or_create(
                    id=category['id'],
                    defaults={'name': category['name']}
                )

                # Если категория существует, проверим, нужно ли обновить название
                if not created and category_object.name != category['name']:
                    category_object.name = category['name']
                    category_object.save()

                # Связываем категорию с магазином
                category_object.shops.add(shop.id)
                categories_count += 1

            return True, f"Импортировано категорий: {categories_count}"
        except Exception as e:
            logger.error(f"Ошибка при импорте категорий: {e}")
            return False, f"Ошибка при импорте категорий: {str(e)}"

    @classmethod
    def import_products(cls, data, shop):
        """
        Импорт товаров из данных.
        """
        try:
            # Очищаем старую информацию о товарах для данного магазина
            # перед импортом новых данных
            ProductInfo.objects.filter(shop_id=shop.id).delete()

            products_count = 0
            parameters_count = 0

            for item in data['goods']:
                # Создаем или получаем товар
                product, _ = Product.objects.get_or_create(
                    name=item['name'],
                    defaults={'category_id': item['category']}
                )

                # Создаем информацию о товаре
                product_info = ProductInfo.objects.create(
                    product_id=product.id,
                    external_id=item['id'],
                    model=item['model'],
                    price=item['price'],
                    price_rrc=item['price_rrc'],
                    quantity=item['quantity'],
                    shop_id=shop.id
                )
                products_count += 1

                # Импортируем параметры товара
                for param_name, param_value in item['parameters'].items():
                    parameter, _ = Parameter.objects.get_or_create(name=param_name)

                    ProductParameter.objects.create(
                        product_info_id=product_info.id,
                        parameter_id=parameter.id,
                        value=str(param_value)
                    )
                    parameters_count += 1

            return True, f"Импортировано товаров: {products_count}, параметров: {parameters_count}"
        except Exception as e:
            logger.error(f"Ошибка при импорте товаров: {e}")
            return False, f"Ошибка при импорте товаров: {str(e)}"

    @classmethod
    def import_shop_data(cls, url, user_id):
        """
        Основная функция импорта данных магазина.
        """
        # Проверка URL
        url_valid, url_error = cls.validate_url(url)
        if not url_valid:
            return {"status": False, "error": url_error}

        # Получение данных
        fetch_success, content = cls.fetch_data(url)
        if not fetch_success:
            return {"status": False, "error": content}

        # Парсинг YAML
        parse_success, data = cls.parse_yaml(content)
        if not parse_success:
            return {"status": False, "error": data}

        # Валидация структуры
        valid_struct, struct_error = cls.validate_structure(data)
        if not valid_struct:
            return {"status": False, "error": struct_error}

        # Создание или получение магазина
        try:
            shop, created = Shop.objects.get_or_create(
                name=data['shop'],
                defaults={"user_id": user_id}
            )

            if not created and shop.user_id != user_id:
                return {"status": False, "error": "У вас нет прав на обновление данного магазина"}
        except Exception as e:
            logger.error(f"Ошибка при получении магазина: {e}")
            return {"status": False, "error": f"Ошибка при получении магазина: {str(e)}"}

        # Импорт категорий
        cat_success, cat_message = cls.import_categories(data, shop)
        if not cat_success:
            return {"status": False, "error": cat_message}

        # Импорт товаров
        prod_success, prod_message = cls.import_products(data, shop)
        if not prod_success:
            return {"status": False, "error": prod_message}

        return {
            "status": True,
            "message": f"Импорт успешно завершен. {cat_message}. {prod_message}"
        }