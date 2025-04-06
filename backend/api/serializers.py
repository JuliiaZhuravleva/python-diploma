from rest_framework import serializers
from backend.models import User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Contact, Order, \
    OrderItem, ConfirmEmailToken
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

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

# Сериализатор для регистрации пользователя
class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации нового пользователя.

    Включает валидацию пароля и проверку обязательных полей.
    Предназначен только для создания новых пользователей.
    """
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('email', 'password', 'password_confirm', 'first_name', 'last_name', 'company', 'position')

    def validate(self, attrs):
        # Проверяем совпадение паролей
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Пароли не совпадают"})

        # Удаляем поле password_confirm, так как оно не используется при создании пользователя
        attrs.pop('password_confirm')

        # Валидация пароля
        try:
            validate_password(attrs['password'])
        except ValidationError as e:
            raise serializers.ValidationError({"password": e.messages})

        return attrs

    def create(self, validated_data):
        # Создаем пользователя с неактивным статусом
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            company=validated_data.get('company', ''),
            position=validated_data.get('position', ''),
            is_active=False
        )
        return user


# Сериализатор для подтверждения email
class ConfirmEmailSerializer(serializers.Serializer):
    """
    Сериализатор для подтверждения email пользователя.

    Проверяет валидность токена и соответствие указанному email.
    """
    email = serializers.EmailField(required=True)
    token = serializers.CharField(required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        token = attrs.get('token')

        try:
            # Проверяем существование токена
            confirm_token = ConfirmEmailToken.objects.get(key=token)

            # Проверяем соответствие токена и email
            if confirm_token.user.email != email:
                raise serializers.ValidationError({"token": "Токен не соответствует указанному email"})

            # Сохраняем пользователя в атрибутах для удобного доступа в view
            attrs['user'] = confirm_token.user
            attrs['confirm_token'] = confirm_token

            return attrs
        except ConfirmEmailToken.DoesNotExist:
            raise serializers.ValidationError({"token": "Недействительный токен подтверждения"})


# Сериализатор для входа пользователя
class UserLoginSerializer(serializers.Serializer):
    """
    Сериализатор для аутентификации пользователя.

    Проверяет email и пароль пользователя.
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = User.objects.get(email=email)

            # Проверяем пароль и активацию аккаунта
            if not user.check_password(password):
                raise serializers.ValidationError({"password": "Неверный пароль"})

            if not user.is_active:
                raise serializers.ValidationError(
                    {"email": "Аккаунт не активирован. Проверьте email для подтверждения."})

            # Сохраняем пользователя для удобного доступа в view
            attrs['user'] = user
            return attrs
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Пользователь с таким email не существует"})


# Сериализатор для запроса сброса пароля
class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Сериализатор для запроса сброса пароля.

    Проверяет существование пользователя с указанным email.
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            if not user.is_active:
                raise serializers.ValidationError("Аккаунт не активирован. Сначала подтвердите email.")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("Пользователь с таким email не существует")


# Сериализатор для подтверждения сброса пароля
class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Сериализатор для подтверждения сброса пароля.

    Проверяет валидность токена, соответствие email и нового пароля требованиям.
    """
    email = serializers.EmailField(required=True)
    token = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate(self, attrs):
        # Проверяем совпадение паролей
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Пароли не совпадают"})

        # Проверяем токен и email
        email = attrs.get('email')
        token = attrs.get('token')

        try:
            # Проверяем существование пользователя
            user = User.objects.get(email=email)

            # Проверяем активность пользователя
            if not user.is_active:
                raise serializers.ValidationError({"email": "Аккаунт не активирован. Сначала подтвердите email."})

            # Проверяем токен
            # Здесь предполагается, что вы используете django-rest-passwordreset
            # и проверка токена происходит через встроенный функционал
            from django_rest_passwordreset.models import ResetPasswordToken
            try:
                reset_token = ResetPasswordToken.objects.get(key=token, user=user)
            except ResetPasswordToken.DoesNotExist:
                raise serializers.ValidationError({"token": "Недействительный токен сброса пароля"})

            # Валидация пароля
            try:
                validate_password(attrs['password'])
            except ValidationError as e:
                raise serializers.ValidationError({"password": e.messages})

            # Удаляем неиспользуемые поля
            attrs.pop('password_confirm')

            # Сохраняем пользователя и токен для удобного доступа в view
            attrs['user'] = user
            attrs['reset_token'] = reset_token

            return attrs
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "Пользователь с таким email не существует"})

