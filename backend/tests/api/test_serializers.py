from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory
from backend.models import Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Contact, Order
from backend.api.serializers import (
    UserSerializer, ShopSerializer, CategorySerializer, ProductSerializer,
    ProductInfoSerializer, ContactSerializer, OrderSerializer
)

User = get_user_model()


class SerializersTestCase(TestCase):
    """
    Тестирование сериализаторов API.

    Проверяет, что все сериализаторы корректно преобразуют модели в JSON-представление
    и обратно, а также соблюдают требования к полям (например, read_only).
    """

    def setUp(self):
        """
        Подготовка данных для тестирования сериализаторов.
        """
        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password123',
            first_name='Test',
            last_name='User',
            company='Test Company',
            position='Manager',
            type='buyer',
            is_active=True
        )

        # Создаем тестовый магазин
        self.shop = Shop.objects.create(
            name='Test Shop',
            url='https://testshop.com',
            user=self.user,
            state=True
        )

        # Создаем тестовую категорию
        self.category = Category.objects.create(
            name='Test Category'
        )
        self.category.shops.add(self.shop)

        # Создаем тестовый продукт
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category
        )

        # Создаем тестовую информацию о продукте
        self.product_info = ProductInfo.objects.create(
            model='Test Model',
            external_id=123,
            product=self.product,
            shop=self.shop,
            quantity=10,
            price=1000,
            price_rrc=1200
        )

        # Создаем тестовый параметр
        self.parameter = Parameter.objects.create(
            name='Test Parameter'
        )

        # Создаем тестовое значение параметра
        self.product_parameter = ProductParameter.objects.create(
            product_info=self.product_info,
            parameter=self.parameter,
            value='Test Value'
        )

        # Создаем тестовый контакт
        self.contact = Contact.objects.create(
            user=self.user,
            city='Test City',
            street='Test Street',
            house='123',
            phone='+1234567890'
        )

        # Создаем тестовый заказ
        self.order = Order.objects.create(
            user=self.user,
            state='new',
            contact=self.contact
        )

    def test_user_serializer(self):
        """
        Тестирование сериализатора пользователя.
        """
        serializer = UserSerializer(self.user)
        data = serializer.data

        self.assertEqual(data['email'], self.user.email)
        self.assertEqual(data['first_name'], self.user.first_name)
        self.assertEqual(data['last_name'], self.user.last_name)
        self.assertEqual(data['company'], self.user.company)
        self.assertEqual(data['position'], self.user.position)
        self.assertEqual(data['type'], self.user.type)

    def test_shop_serializer(self):
        """
        Тестирование сериализатора магазина.
        """
        serializer = ShopSerializer(self.shop)
        data = serializer.data

        self.assertEqual(data['name'], self.shop.name)
        self.assertEqual(data['url'], self.shop.url)
        self.assertEqual(data['state'], self.shop.state)

    def test_category_serializer(self):
        """
        Тестирование сериализатора категории.
        """
        serializer = CategorySerializer(self.category)
        data = serializer.data

        self.assertEqual(data['name'], self.category.name)

    def test_product_serializer(self):
        """
        Тестирование сериализатора продукта.
        """
        serializer = ProductSerializer(self.product)
        data = serializer.data

        self.assertEqual(data['name'], self.product.name)
        self.assertEqual(data['category']['name'], self.category.name)

    def test_product_info_serializer(self):
        """
        Тестирование сериализатора информации о продукте.
        """
        serializer = ProductInfoSerializer(self.product_info)
        data = serializer.data

        self.assertEqual(data['model'], self.product_info.model)
        self.assertEqual(data['external_id'], self.product_info.external_id)
        self.assertEqual(data['price'], self.product_info.price)
        self.assertEqual(data['price_rrc'], self.product_info.price_rrc)
        self.assertEqual(data['quantity'], self.product_info.quantity)
        self.assertEqual(data['product']['name'], self.product.name)
        self.assertEqual(data['shop']['name'], self.shop.name)

        # Проверяем, что параметры продукта включены в сериализацию
        self.assertEqual(len(data['product_parameters']), 1)
        self.assertEqual(data['product_parameters'][0]['parameter']['name'], self.parameter.name)
        self.assertEqual(data['product_parameters'][0]['value'], self.product_parameter.value)

    def test_contact_serializer(self):
        """
        Тестирование сериализатора контакта.
        """
        serializer = ContactSerializer(self.contact)
        data = serializer.data

        self.assertEqual(data['city'], self.contact.city)
        self.assertEqual(data['street'], self.contact.street)
        self.assertEqual(data['house'], self.contact.house)
        self.assertEqual(data['phone'], self.contact.phone)