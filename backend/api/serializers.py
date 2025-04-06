from rest_framework import serializers
from backend.models import User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Contact, Order, \
    OrderItem


# Сериализаторы для пользователей
class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели пользователя.
    Используется для отображения и редактирования данных пользователя.
    """

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'company', 'position', 'type')
        read_only_fields = ('id',)


# Сериализаторы для магазинов
class ShopSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели магазина.
    Используется для отображения списка магазинов.
    """

    class Meta:
        model = Shop
        fields = ('id', 'name', 'url', 'state')
        read_only_fields = ('id',)


# Сериализаторы для категорий
class CategorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели категории.
    Используется для отображения списка категорий товаров.
    """

    class Meta:
        model = Category
        fields = ('id', 'name')
        read_only_fields = ('id',)


# Сериализаторы для продуктов
class ProductSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели продукта.
    Используется для отображения базовой информации о продукте.
    """
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'category')
        read_only_fields = ('id',)


# Сериализатор для параметров
class ParameterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели параметра.
    Используется для отображения названий параметров товаров.
    """

    class Meta:
        model = Parameter
        fields = ('id', 'name')
        read_only_fields = ('id',)


# Сериализатор для параметров продукта
class ProductParameterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для связи параметров и продуктов.
    Используется для отображения значений параметров конкретного товара.
    """
    parameter = ParameterSerializer(read_only=True)

    class Meta:
        model = ProductParameter
        fields = ('parameter', 'value')


# Сериализатор для информации о продукте
class ProductInfoSerializer(serializers.ModelSerializer):
    """
    Сериализатор для информации о продукте.
    Используется для отображения детальной информации о товаре, включая его параметры.
    """
    product = ProductSerializer(read_only=True)
    shop = ShopSerializer(read_only=True)
    product_parameters = ProductParameterSerializer(read_only=True, many=True)

    class Meta:
        model = ProductInfo
        fields = ('id', 'model', 'external_id', 'product', 'shop',
                  'quantity', 'price', 'price_rrc', 'product_parameters')
        read_only_fields = ('id',)


# Сериализаторы для контактов
class ContactSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели контакта.
    Используется для отображения и редактирования контактных данных пользователя.
    """

    class Meta:
        model = Contact
        fields = ('id', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'phone')
        read_only_fields = ('id',)


# Сериализаторы для заказов
class OrderItemSerializer(serializers.ModelSerializer):
    """
    Сериализатор для позиции заказа.
    Используется для отображения информации о товаре в заказе.
    """
    product_info = ProductInfoSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'product_info', 'quantity')
        read_only_fields = ('id',)


class OrderSerializer(serializers.ModelSerializer):
    """
    Сериализатор для заказа.
    Используется для отображения полной информации о заказе.
    """
    ordered_items = OrderItemSerializer(read_only=True, many=True)
    contact = ContactSerializer(read_only=True)
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True, source='get_total_cost')

    class Meta:
        model = Order
        fields = ('id', 'dt', 'state', 'contact', 'ordered_items', 'total_cost')
        read_only_fields = ('id', 'dt')