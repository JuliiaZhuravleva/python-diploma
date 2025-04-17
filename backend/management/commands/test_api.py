import json
import requests
from pprint import pprint
from django.core.management.base import BaseCommand
from django.conf import settings


class OrderServiceClient:
    """Клиент для тестирования API системы автоматизации закупок"""

    def __init__(self, host='localhost', port=8000):
        """
        Инициализирует клиент API

        Args:
            host (str): Хост сервера API
            port (int): Порт сервера API
        """
        self.base_url = f'http://{host}:{port}/api/v1'
        self.token = None
        self.headers = {'Content-Type': 'application/json'}
        self.stdout = None  # Инициализируем stdout как None
        self.command = None  # Ссылка на экземпляр команды Django

    def set_command(self, command):
        """Устанавливает ссылку на команду Django и stdout"""
        self.command = command
        self.stdout = command.stdout
        self.write_success(f'🔌 Подключение к API: {self.base_url}')

    def write_message(self, message):
        """Выводит обычное сообщение"""
        if self.stdout:
            self.stdout.write(message)

    def write_success(self, message):
        """Выводит успешное сообщение"""
        if self.stdout and self.command:
            self.stdout.write(self.command.style.SUCCESS(message))
        else:
            self.write_message(f"SUCCESS: {message}")

    def write_error(self, message):
        """Выводит сообщение об ошибке"""
        if self.stdout and self.command:
            self.stdout.write(self.command.style.ERROR(message))
        else:
            self.write_message(f"ERROR: {message}")

    def write_warning(self, message):
        """Выводит предупреждение"""
        if self.stdout and self.command:
            self.stdout.write(self.command.style.WARNING(message))
        else:
            self.write_message(f"WARNING: {message}")

    def _update_headers(self):
        """Обновляет заголовки запросов с учетом токена аутентификации"""
        if self.token:
            self.headers['Authorization'] = f'Token {self.token}'

    def register_user(self, email, password, first_name='Test', last_name='User',
                      company='Test Company', position='Tester'):
        """
        Регистрация нового пользователя

        Args:
            email (str): Email пользователя
            password (str): Пароль пользователя
            first_name (str): Имя пользователя
            last_name (str): Фамилия пользователя
            company (str): Компания пользователя
            position (str): Должность пользователя

        Returns:
            dict: Результат запроса
        """
        self.write_message(f'👤 Регистрация пользователя: {email}')

        data = {
            'email': email,
            'password': password,
            'first_name': first_name,
            'last_name': last_name,
            'company': company,
            'position': position
        }

        response = requests.post(f'{self.base_url}/user/register', json=data)
        return self._process_response(response)

    def confirm_email(self, email, token):
        """
        Подтверждение email пользователя

        Args:
            email (str): Email пользователя
            token (str): Токен подтверждения

        Returns:
            dict: Результат запроса
        """
        self.write_message(f'✉️ Подтверждение email: {email}')

        data = {
            'email': email,
            'token': token
        }

        response = requests.post(f'{self.base_url}/user/register/confirm', json=data)
        return self._process_response(response)

    def login(self, email, password):
        """
        Авторизация пользователя

        Args:
            email (str): Email пользователя
            password (str): Пароль пользователя

        Returns:
            dict: Результат запроса
        """
        self.write_message(f'🔑 Авторизация пользователя: {email}')

        data = {
            'email': email,
            'password': password
        }

        response = requests.post(f'{self.base_url}/user/login', json=data)
        result = self._process_response(response)

        if response.status_code == 200 and 'token' in result:
            self.token = result['token']
            self._update_headers()
            self.write_success('✅ Успешная авторизация! Токен получен.')

        return result

    def get_user_details(self):
        """
        Получение информации о текущем пользователе

        Returns:
            dict: Результат запроса
        """
        self.write_message('👤 Получение информации о пользователе')

        response = requests.get(f'{self.base_url}/user/details', headers=self.headers)
        return self._process_response(response)

    def get_shops(self):
        """
        Получение списка магазинов

        Returns:
            dict: Результат запроса
        """
        self.write_message('🏪 Получение списка магазинов')

        response = requests.get(f'{self.base_url}/shops')
        return self._process_response(response)

    def get_categories(self):
        """
        Получение списка категорий

        Returns:
            dict: Результат запроса
        """
        self.write_message('📋 Получение списка категорий')

        response = requests.get(f'{self.base_url}/categories')
        return self._process_response(response)

    def get_products(self, shop_id=None, category_id=None, search=None):
        """
        Получение списка товаров с возможностью фильтрации

        Args:
            shop_id (int, optional): ID магазина для фильтрации
            category_id (int, optional): ID категории для фильтрации
            search (str, optional): Строка поиска

        Returns:
            dict: Результат запроса
        """
        self.write_message('🛍️ Получение списка товаров')

        params = {}
        if shop_id:
            params['shop_id'] = shop_id
        if category_id:
            params['category_id'] = category_id
        if search:
            params['search'] = search

        response = requests.get(f'{self.base_url}/products', params=params)
        return self._process_response(response)

    def get_product_details(self, product_id):
        """
        Получение информации о конкретном товаре

        Args:
            product_id (int): ID товара

        Returns:
            dict: Результат запроса
        """
        self.write_message(f'📦 Получение информации о товаре: {product_id}')

        response = requests.get(f'{self.base_url}/products/{product_id}')
        return self._process_response(response)

    def add_to_basket(self, items):
        """
        Добавление товаров в корзину

        Args:
            items (list): Список словарей с информацией о товарах
                Пример: [{"product_info": 1, "quantity": 2}]

        Returns:
            dict: Результат запроса
        """
        self.write_message('🛒 Добавление товаров в корзину')

        data = {'items': items}
        response = requests.post(f'{self.base_url}/basket',
                                 headers=self.headers, json=data)
        return self._process_response(response)

    def get_basket(self):
        """
        Получение содержимого корзины

        Returns:
            dict: Результат запроса
        """
        self.write_message('🛒 Получение содержимого корзины')

        response = requests.get(f'{self.base_url}/basket', headers=self.headers)
        return self._process_response(response)

    def add_contact(self, city, street, house, phone, structure='', building='', apartment=''):
        """
        Добавление нового контакта

        Args:
            city (str): Город
            street (str): Улица
            house (str): Дом
            phone (str): Телефон
            structure (str, optional): Корпус
            building (str, optional): Строение
            apartment (str, optional): Квартира

        Returns:
            dict: Результат запроса
        """
        self.write_message('📞 Добавление контакта')

        data = {
            'city': city,
            'street': street,
            'house': house,
            'phone': phone,
            'structure': structure,
            'building': building,
            'apartment': apartment
        }

        response = requests.post(f'{self.base_url}/user/contact',
                                 headers=self.headers, json=data)
        return self._process_response(response)

    def get_contacts(self):
        """
        Получение списка контактов

        Returns:
            dict: Результат запроса
        """
        self.write_message('📞 Получение списка контактов')

        response = requests.get(f'{self.base_url}/user/contact', headers=self.headers)
        return self._process_response(response)

    def create_order(self, basket_id, contact_id):
        """
        Оформление заказа

        Args:
            basket_id (int): ID корзины
            contact_id (int): ID контакта для доставки

        Returns:
            dict: Результат запроса
        """
        self.write_message('📝 Оформление заказа')

        data = {
            'id': basket_id,
            'contact': contact_id
        }

        response = requests.post(f'{self.base_url}/order',
                                 headers=self.headers, json=data)
        return self._process_response(response)

    def get_orders(self):
        """
        Получение списка заказов

        Returns:
            dict: Результат запроса
        """
        self.write_message('📋 Получение списка заказов')

        response = requests.get(f'{self.base_url}/order', headers=self.headers)
        return self._process_response(response)

    def get_order_details(self, order_id):
        """
        Получение информации о конкретном заказе

        Args:
            order_id (int): ID заказа

        Returns:
            dict: Результат запроса
        """
        self.write_message(f'📦 Получение информации о заказе: {order_id}')

        response = requests.get(f'{self.base_url}/order/{order_id}', headers=self.headers)
        return self._process_response(response)

    def _process_response(self, response):
        """
        Обрабатывает ответ API

        Args:
            response: Объект ответа requests

        Returns:
            dict: Результат запроса
        """
        try:
            result = response.json()
        except json.JSONDecodeError:
            result = {'error': 'Invalid JSON response', 'text': response.text}

        # Вывод статуса запроса
        if response.status_code >= 400:
            self.write_error(
                f'❌ Ошибка {response.status_code}: {result.get("error", "Unknown error")}')
        else:
            self.write_success(
                f'✅ Успешный запрос! Статус: {response.status_code}')

        return result


class Command(BaseCommand):
    help = 'Тестирование API системы автоматизации закупок'

    def add_arguments(self, parser):
        parser.add_argument(
            '--host',
            default='localhost',
            help='Хост API сервера (по умолчанию: localhost)'
        )
        parser.add_argument(
            '--port',
            type=int,
            default=8000,
            help='Порт API сервера (по умолчанию: 8000)'
        )
        parser.add_argument(
            '--scenario',
            choices=['full', 'auth', 'products', 'order'],
            default='full',
            help='Тестовый сценарий (по умолчанию: full)'
        )
        parser.add_argument(
            '--user',
            default='buyer1@example.com',
            help='Email пользователя для авторизации (по умолчанию: buyer1@example.com)'
        )
        parser.add_argument(
            '--password',
            default='Strong123!',
            help='Пароль пользователя для авторизации (по умолчанию: Strong123!)'
        )

    def handle(self, *args, **options):
        host = options['host']
        port = options['port']
        scenario = options['scenario']
        user_email = options['user']
        user_password = options['password']

        try:
            self.stdout.write(self.style.SUCCESS(f'Начало тестирования API ({scenario})'))
            self.stdout.write(f'Хост: {host}, Порт: {port}')

            # Инициализация клиента API
            client = OrderServiceClient(host, port)
            client.set_command(self)  # Передаем объект команды вместо только stdout

            # Выполнение выбранного сценария
            if scenario == 'full':
                self._run_full_scenario(client, user_email, user_password)
            elif scenario == 'auth':
                self._run_auth_scenario(client, user_email, user_password)
            elif scenario == 'products':
                self._run_products_scenario(client, user_email, user_password)
            elif scenario == 'order':
                self._run_order_scenario(client, user_email, user_password)

            self.stdout.write(self.style.SUCCESS('Тестирование API завершено успешно!'))

        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при выполнении запроса: {str(e)}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Неожиданная ошибка: {str(e)}'))

    def _run_full_scenario(self, client, user_email, user_password):
        """
        Выполняет полный тестовый сценарий: авторизация, получение товаров, работа с корзиной и заказами
        """
        self.stdout.write(self.style.SUCCESS('\n==== Полный тестовый сценарий ====\n'))

        # Авторизация
        self._run_auth_scenario(client, user_email, user_password)

        # Работа с товарами
        self._run_products_scenario(client, user_email, user_password)

        # Работа с заказами
        self._run_order_scenario(client, user_email, user_password)

    def _run_auth_scenario(self, client, user_email, user_password):
        """
        Тестирование аутентификации и пользовательской информации
        """
        self.stdout.write(self.style.SUCCESS('\n---- Тестирование аутентификации ----\n'))

        # Пробуем авторизоваться с указанными данными
        login_result = client.login(user_email, user_password)

        # Если не удалось, пробуем другие учетные записи из тестовых данных
        if 'token' not in login_result:
            client.write_warning(f'Не удалось войти как {user_email}, пробую другие учетные записи')

            login_users = [
                ('buyer1@example.com', 'Strong123!'),
                ('buyer2@example.com', 'Strong123!'),
                ('buyer3@example.com', 'Strong123!'),
                ('buyer4@example.com', 'Strong123!'),
                ('buyer5@example.com', 'Strong123!')
            ]

            for email, password in login_users:
                if email != user_email:  # Пропускаем, если уже пробовали
                    login_result = client.login(email, password)
                    if 'token' in login_result:
                        client.write_success(f'Успешный вход как {email}')
                        break

        # Если всё ещё не удалось авторизоваться, предлагаем регистрацию
        if 'token' not in login_result:
            client.write_warning('Не удалось войти с имеющимися учетными записями')

            # Генерируем уникальный email для регистрации
            import time
            test_email = f'test_{int(time.time())}@example.com'
            test_password = 'Strong123!'

            # Спрашиваем, хочет ли пользователь зарегистрироваться
            register = input('Зарегистрировать нового пользователя? (y/n): ').strip().lower()
            if register == 'y':
                register_result = client.register_user(test_email, test_password)

                # Для подтверждения email нужен токен
                client.write_warning('\n⚠️ Для подтверждения email требуется токен из консоли сервера')
                token = input('Введите токен подтверждения: ').strip()

                confirm_result = client.confirm_email(test_email, token)
                client.write_message(f'Результат подтверждения: {confirm_result}')

                # Авторизуемся под новым пользователем
                login_result = client.login(test_email, test_password)

        # Получаем информацию о пользователе, если авторизация успешна
        if 'token' in login_result:
            user_details = client.get_user_details()
            client.write_message('\nИнформация о пользователе:')
            pprint(user_details)

    def _run_products_scenario(self, client, user_email, user_password):
        """
        Тестирование работы с товарами и категориями
        """
        self.stdout.write(self.style.SUCCESS('\n---- Тестирование работы с товарами ----\n'))

        # Получаем список магазинов
        shops = client.get_shops()
        client.write_message('\nСписок магазинов:')
        pprint(shops)

        # Получаем список категорий
        categories = client.get_categories()
        client.write_message('\nСписок категорий:')
        pprint(categories)

        # Получаем список товаров
        products = client.get_products()
        client.write_message('\nСписок товаров:')
        if 'results' in products:
            client.write_message(f'Всего товаров: {products["count"]}')
            # Выводим первые 2 товара для примера
            for product in products['results'][:2]:
                client.write_message(f'- {product["product"]["name"]} ({product["price"]} руб.)')

        # Если есть товары, получаем детали одного из них
        if 'results' in products and products['results']:
            product_id = products['results'][0]['id']
            product_details = client.get_product_details(product_id)
            client.write_message('\nИнформация о товаре:')
            pprint(product_details)

    def _run_order_scenario(self, client, user_email, user_password):
        """
        Тестирование работы с корзиной и заказами
        """
        self.stdout.write(self.style.SUCCESS('\n---- Тестирование работы с корзиной и заказами ----\n'))

        # Проверяем авторизацию
        if not client.token:
            login_result = client.login(user_email, user_password)
            if 'token' not in login_result:
                client.write_error('Не удалось авторизоваться для тестирования корзины')
                return

        # Получаем товары для добавления в корзину
        products = client.get_products()
        if 'results' not in products or not products['results']:
            client.write_warning('Нет доступных товаров для тестирования корзины')
            return

        # Добавляем товар в корзину
        product_id = products['results'][0]['id']
        items = [{'product_info': product_id, 'quantity': 2}]
        basket_result = client.add_to_basket(items)
        client.write_message('\nРезультат добавления в корзину:')
        pprint(basket_result)

        # Получаем содержимое корзины
        basket = client.get_basket()
        client.write_message('\nСодержимое корзины:')
        pprint(basket)

        # Получаем список контактов
        contacts = client.get_contacts()
        client.write_message('\nСписок контактов:')
        pprint(contacts)

        # Если у пользователя нет контактов, создаем новый
        contact_id = None
        if isinstance(contacts, list) and contacts:
            contact_id = contacts[0]['id']
        else:
            contact_result = client.add_contact(
                city='Москва',
                street='Тестовая улица',
                house='123',
                phone='+79001234567',
                apartment='42'
            )
            client.write_message('\nРезультат добавления контакта:')
            pprint(contact_result)

            if 'id' in contact_result:
                contact_id = contact_result['id']

        # Если есть корзина и контакт, оформляем заказ
        basket_id = None
        if isinstance(basket, dict) and 'id' in basket:
            basket_id = basket['id']

        if basket_id and contact_id:
            # Спрашиваем, хочет ли пользователь оформить заказ
            create_order = input('Оформить заказ? (y/n): ').strip().lower()
            if create_order == 'y':
                order_result = client.create_order(basket_id, contact_id)
                client.write_message('\nРезультат оформления заказа:')
                pprint(order_result)

        # Получаем список заказов
        orders = client.get_orders()
        client.write_message('\nСписок заказов:')
        pprint(orders)

        # Если есть заказы, получаем детали одного из них
        if isinstance(orders, list) and orders:
            order_id = orders[0]['id']
            order_details = client.get_order_details(order_id)
            client.write_message('\nДетали заказа:')
            pprint(order_details)