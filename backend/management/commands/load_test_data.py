import os
import csv
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from backend.models import (
    Shop, Category, Product, ProductInfo, Parameter,
    ProductParameter, Contact, Order, OrderItem
)

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Load test data from CSV files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete existing data before loading',
        )
        parser.add_argument(
            '--path',
            type=str,
            help='Path to data directory',
            default='./fixtures/test_data',
        )

    def handle(self, *args, **options):
        data_path = options['path']
        delete_existing = options['delete']

        # Проверяем наличие директории с данными
        if not os.path.exists(data_path):
            self.stdout.write(self.style.ERROR(f'Directory not found: {data_path}'))
            return

        # Если указан флаг delete, удаляем существующие данные
        if delete_existing:
            self._delete_existing_data()

        # Загружаем данные из CSV файлов
        try:
            with transaction.atomic():
                self._load_users(os.path.join(data_path, 'users.csv'))
                self._load_shops(os.path.join(data_path, 'shops.csv'))
                self._load_categories(os.path.join(data_path, 'categories.csv'))
                self._load_products(os.path.join(data_path, 'products.csv'))
                self._load_product_info(os.path.join(data_path, 'product_info.csv'))
                self._load_parameters(os.path.join(data_path, 'parameters.csv'))
                self._load_product_parameters(os.path.join(data_path, 'product_parameters.csv'))
                self._load_contacts(os.path.join(data_path, 'contacts.csv'))

                # Связываем категории с магазинами
                self._link_categories_to_shops()

                # Создаем несколько тестовых заказов
                self._create_test_orders()

            self.stdout.write(self.style.SUCCESS('Successfully loaded test data'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error loading test data: {str(e)}'))
            logger.exception('Error loading test data')

    def _delete_existing_data(self):
        """
        Удаляет существующие данные из базы
        """
        self.stdout.write('Deleting existing data...')

        # Удаляем данные в обратном порядке зависимостей
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Contact.objects.all().delete()
        ProductParameter.objects.all().delete()
        Parameter.objects.all().delete()
        ProductInfo.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Shop.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write(self.style.SUCCESS('Existing data deleted'))

    def _load_users(self, filepath):
        """
        Загружает данные пользователей из CSV
        """
        if not os.path.exists(filepath):
            self.stdout.write(f'File not found: {filepath}')
            return

        self.stdout.write(f'Loading users from {filepath}')
        count = 0

        with open(filepath, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Проверяем, существует ли пользователь
                if not User.objects.filter(email=row['email']).exists():
                    user = User.objects.create_user(
                        email=row['email'],
                        password=row['password'],
                        first_name=row['first_name'],
                        last_name=row['last_name'],
                        company=row['company'],
                        position=row['position'],
                        type=row['type'],
                        is_active=int(row['is_active']) == 1
                    )
                    count += 1

        self.stdout.write(self.style.SUCCESS(f'Loaded {count} users'))

    def _load_shops(self, filepath):
        """
        Загружает данные магазинов из CSV
        """
        if not os.path.exists(filepath):
            self.stdout.write(f'File not found: {filepath}')
            return

        self.stdout.write(f'Loading shops from {filepath}')
        count = 0

        with open(filepath, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                user = None
                if row['user_email']:
                    try:
                        user = User.objects.get(email=row['user_email'])
                    except User.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"User {row['user_email']} not found"))
                        continue

                # Проверяем, существует ли магазин
                shop, created = Shop.objects.get_or_create(
                    name=row['name'],
                    defaults={
                        'url': row['url'],
                        'user': user,
                        'state': int(row['state']) == 1
                    }
                )

                if created:
                    count += 1
                elif user:  # Если магазин существует, обновляем связь с пользователем
                    shop.user = user
                    shop.save()

        self.stdout.write(self.style.SUCCESS(f'Loaded {count} shops'))

    def _load_categories(self, filepath):
        """
        Загружает данные категорий из CSV
        """
        if not os.path.exists(filepath):
            self.stdout.write(f'File not found: {filepath}')
            return

        self.stdout.write(f'Loading categories from {filepath}')
        count = 0

        with open(filepath, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Проверяем, существует ли категория
                category, created = Category.objects.get_or_create(
                    id=int(row['id']),
                    defaults={'name': row['name']}
                )

                if not created and category.name != row['name']:
                    category.name = row['name']
                    category.save()

                if created:
                    count += 1

        self.stdout.write(self.style.SUCCESS(f'Loaded {count} categories'))

    def _load_products(self, filepath):
        """
        Загружает данные продуктов из CSV
        """
        if not os.path.exists(filepath):
            self.stdout.write(f'File not found: {filepath}')
            return

        self.stdout.write(f'Loading products from {filepath}')
        count = 0

        with open(filepath, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    category = Category.objects.get(id=int(row['category_id']))
                except Category.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"Category {row['category_id']} not found"))
                    continue

                # Проверяем, существует ли продукт
                product, created = Product.objects.get_or_create(
                    id=int(row['id']),
                    defaults={
                        'name': row['name'],
                        'category': category
                    }
                )

                if not created and (product.name != row['name'] or product.category != category):
                    product.name = row['name']
                    product.category = category
                    product.save()

                if created:
                    count += 1

        self.stdout.write(self.style.SUCCESS(f'Loaded {count} products'))

    def _load_product_info(self, filepath):
        """
        Загружает информацию о товарах (ProductInfo) из CSV
        """
        if not os.path.exists(filepath):
            self.stdout.write(f'File not found: {filepath}')
            return

        self.stdout.write(f'Loading product info from {filepath}')
        count = 0

        with open(filepath, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    product = Product.objects.get(id=int(row['product_id']))
                    shop = Shop.objects.get(name=row['shop_name'])
                except (Product.DoesNotExist, Shop.DoesNotExist):
                    self.stdout.write(self.style.WARNING(
                        f"Product {row['product_id']} or Shop {row['shop_name']} not found"))
                    continue

                # Проверяем, существует ли информация о продукте
                product_info, created = ProductInfo.objects.get_or_create(
                    external_id=int(row['external_id']),
                    shop=shop,
                    defaults={
                        'product': product,
                        'model': row['model'],
                        'quantity': int(row['quantity']),
                        'price': int(float(row['price'])),
                        'price_rrc': int(float(row['price_rrc']))
                    }
                )

                if not created:
                    product_info.product = product
                    product_info.model = row['model']
                    product_info.quantity = int(row['quantity'])
                    product_info.price = int(float(row['price']))
                    product_info.price_rrc = int(float(row['price_rrc']))
                    product_info.save()
                else:
                    count += 1

        self.stdout.write(self.style.SUCCESS(f'Loaded {count} product info records'))

    def _load_parameters(self, filepath):
        """
        Загружает параметры товаров из CSV
        """
        if not os.path.exists(filepath):
            self.stdout.write(f'File not found: {filepath}')
            return

        self.stdout.write(f'Loading parameters from {filepath}')
        count = 0

        with open(filepath, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Проверяем, существует ли параметр
                parameter, created = Parameter.objects.get_or_create(
                    id=int(row['id']),
                    defaults={'name': row['name']}
                )

                if not created and parameter.name != row['name']:
                    parameter.name = row['name']
                    parameter.save()

                if created:
                    count += 1

        self.stdout.write(self.style.SUCCESS(f'Loaded {count} parameters'))

    def _load_product_parameters(self, filepath):
        """
        Загружает значения параметров товаров из CSV
        """
        if not os.path.exists(filepath):
            self.stdout.write(f'File not found: {filepath}')
            return

        self.stdout.write(f'Loading product parameters from {filepath}')
        count = 0

        with open(filepath, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    # Находим информацию о продукте по external_id и магазину
                    shop = Shop.objects.get(name=row['shop_name'])
                    product_info = ProductInfo.objects.get(
                        external_id=int(row['product_info_external_id']),
                        shop=shop
                    )
                    parameter = Parameter.objects.get(name=row['parameter_name'])
                except (Shop.DoesNotExist, ProductInfo.DoesNotExist, Parameter.DoesNotExist):
                    self.stdout.write(self.style.WARNING(
                        f"Shop {row['shop_name']}, ProductInfo {row['product_info_external_id']} "
                        f"or Parameter {row['parameter_name']} not found"))
                    continue

                # Проверяем, существует ли значение параметра
                product_param, created = ProductParameter.objects.get_or_create(
                    product_info=product_info,
                    parameter=parameter,
                    defaults={'value': row['value']}
                )

                if not created and product_param.value != row['value']:
                    product_param.value = row['value']
                    product_param.save()

                if created:
                    count += 1

        self.stdout.write(self.style.SUCCESS(f'Loaded {count} product parameters'))

    def _load_contacts(self, filepath):
        """
        Загружает контактные данные пользователей из CSV
        """
        if not os.path.exists(filepath):
            self.stdout.write(f'File not found: {filepath}')
            return

        self.stdout.write(f'Loading contacts from {filepath}')
        count = 0

        with open(filepath, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    user = User.objects.get(email=row['user_email'])
                except User.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"User {row['user_email']} not found"))
                    continue

                # Проверяем, существует ли контакт
                contact, created = Contact.objects.get_or_create(
                    user=user,
                    city=row['city'],
                    street=row['street'],
                    house=row['house'],
                    defaults={
                        'structure': row['structure'],
                        'building': row['building'],
                        'apartment': row['apartment'],
                        'phone': row['phone'],
                        'is_deleted': int(row['is_deleted']) == 1
                    }
                )

                if not created:
                    contact.structure = row['structure']
                    contact.building = row['building']
                    contact.apartment = row['apartment']
                    contact.phone = row['phone']
                    contact.is_deleted = int(row['is_deleted']) == 1
                    contact.save()
                else:
                    count += 1

        self.stdout.write(self.style.SUCCESS(f'Loaded {count} contacts'))

    def _link_categories_to_shops(self):
        """
        Связывает категории с магазинами на основе данных ProductInfo
        """
        self.stdout.write('Linking categories to shops...')
        count = 0

        # Получаем уникальные пары магазин-категория из ProductInfo
        shop_categories = ProductInfo.objects.values_list(
            'shop', 'product__category'
        ).distinct()

        # Для каждой пары связываем категорию с магазином
        for shop_id, category_id in shop_categories:
            shop = Shop.objects.get(id=shop_id)
            category = Category.objects.get(id=category_id)

            # Проверяем, есть ли уже связь
            if category not in shop.categories.all():
                shop.categories.add(category)
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Linked {count} categories to shops'))

    def _create_test_orders(self):
        """
        Создает тестовые заказы для демонстрации
        """
        self.stdout.write('Creating test orders...')

        # Создаем заказы для двух покупателей
        buyers = User.objects.filter(type='buyer', is_active=True)[:2]

        for i, buyer in enumerate(buyers):
            # Находим контакт пользователя
            contact = Contact.objects.filter(user=buyer, is_deleted=False).first()
            if not contact:
                self.stdout.write(self.style.WARNING(f"No contact found for {buyer.email}"))
                continue

            # Создаем заказ в статусе корзины
            basket = Order.objects.create(
                user=buyer,
                state='basket'
            )

            # Добавляем несколько товаров в корзину
            product_infos = ProductInfo.objects.filter(
                shop__state=True
            ).order_by('?')[:3]  # Случайные 3 товара

            for product_info in product_infos:
                OrderItem.objects.create(
                    order=basket,
                    product_info=product_info,
                    quantity=1 + i  # Разное количество для разных покупателей
                )

            # Создаем оформленный заказ
            order = Order.objects.create(
                user=buyer,
                state='new' if i == 0 else 'confirmed',
                contact=contact
            )

            # Добавляем товары в заказ
            other_product_infos = ProductInfo.objects.filter(
                shop__state=True
            ).exclude(
                id__in=product_infos.values_list('id', flat=True)
            ).order_by('?')[:2]  # Еще 2 случайных товара

            for product_info in other_product_infos:
                OrderItem.objects.create(
                    order=order,
                    product_info=product_info,
                    quantity=2
                )

        self.stdout.write(self.style.SUCCESS(f'Created test orders for {len(buyers)} buyers'))
