"""
Предопределенные примеры для OpenAPI документации.
"""

from drf_spectacular.utils import OpenApiExample


# Примеры для аутентификации
AUTH_EXAMPLES = {
    'registration_request': OpenApiExample(
        name="Регистрация пользователя",
        description="Пример данных для регистрации нового пользователя",
        value={
            "email": "user@example.com",
            "password": "securePassword123",
            "first_name": "Иван",
            "last_name": "Иванов",
            "company": "ООО Компания",
            "position": "Менеджер"
        },
        request_only=True
    ),

    'login_request': OpenApiExample(
        name="Вход в систему",
        description="Пример данных для входа в систему",
        value={
            "email": "user@example.com",
            "password": "securePassword123"
        },
        request_only=True
    ),

    'email_confirmation_request': OpenApiExample(
        name="Подтверждение email",
        description="Пример данных для подтверждения email адреса",
        value={
            "email": "user@example.com",
            "token": "a1b2c3d4e5f6"
        },
        request_only=True
    ),

    'password_reset_request': OpenApiExample(
        name="Сброс пароля",
        description="Пример запроса на сброс пароля",
        value={
            "email": "user@example.com"
        },
        request_only=True
    ),

    'password_reset_confirm_request': OpenApiExample(
        name="Подтверждение сброса пароля",
        description="Пример данных для подтверждения нового пароля",
        value={
            "email": "user@example.com",
            "token": "b50c20bd4a2282931a89adb",
            "password": "newSecurePassword123"
        },
        request_only=True
    ),

    'login_success': OpenApiExample(
        name="Успешный вход",
        description="Ответ при успешной авторизации",
        value={
            "token": "e777c8b85f4a664aab792eb2e6d794284134eaea",
            "user": {
                "id": 1,
                "email": "user@example.com",
                "first_name": "Иван",
                "last_name": "Иванов",
                "company": "ООО Компания",
                "position": "Менеджер"
            }
        },
        response_only=True,
        status_codes=["200"]
    )
}


# Примеры для заказов и корзины
ORDER_EXAMPLES = {
    'basket_add_request': OpenApiExample(
        name="Добавление товаров в корзину",
        description="Пример данных для добавления товаров в корзину",
        value={
            "items": [
                {
                    "product_info": 25,
                    "quantity": 2
                },
                {
                    "product_info": 26,
                    "quantity": 1
                }
            ]
        },
        request_only=True
    ),

    'basket_update_request': OpenApiExample(
        name="Обновление корзины",
        description="Пример данных для обновления количества товаров в корзине",
        value={
            "items": [
                {
                    "id": 95,
                    "quantity": 3
                },
                {
                    "id": 96,
                    "quantity": 1
                }
            ]
        },
        request_only=True
    ),

    'order_create_request': OpenApiExample(
        name="Создание заказа",
        description="Пример данных для оформления заказа",
        value={
            "id": 7,
            "contact": 9
        },
        request_only=True
    ),

    'contact_create_request': OpenApiExample(
        name="Добавление контакта",
        description="Пример данных для создания контактной информации",
        value={
            "city": "Москва",
            "street": "ул. Пушкина",
            "house": "д. 10",
            "structure": "стр. 1",
            "building": "корп. 2",
            "apartment": "кв. 15",
            "phone": "+7(999)123-45-67"
        },
        request_only=True
    )
}


# Примеры для партнеров
PARTNER_EXAMPLES = {
    'price_update_request': OpenApiExample(
        name="Обновление прайса",
        description="Пример запроса на обновление прайс-листа партнера",
        value={
            "url": "https://raw.githubusercontent.com/netology-code/python-final-diplom/master/data/shop1.yaml"
        },
        request_only=True
    ),

    'state_update_request': OpenApiExample(
        name="Обновление статуса партнера",
        description="Пример запроса на изменение статуса работы партнера",
        value={
            "state": "on"  # или "off"
        },
        request_only=True
    )
}


# Общие примеры ошибок
ERROR_EXAMPLES = {
    'validation_error': OpenApiExample(
        name="Ошибка валидации",
        description="Пример ответа при ошибке валидации данных",
        value={
            "status": False,
            "errors": {
                "email": ["Пользователь с таким email уже существует."],
                "password": ["Пароль должен содержать не менее 8 символов."]
            }
        },
        response_only=True,
        status_codes=["400"]
    ),

    'single_error': OpenApiExample(
        name="Одиночная ошибка",
        description="Пример ответа с одиночной ошибкой",
        value={
            "status": False,
            "error": "Произошла ошибка при выполнении операции"
        },
        response_only=True,
        status_codes=["400", "404"]
    ),

    'unauthorized': OpenApiExample(
        name="Не авторизован",
        description="Ошибка авторизации",
        value={
            "status": False,
            "error": "Учетные данные не были предоставлены."
        },
        response_only=True,
        status_codes=["401"]
    ),

    'not_found': OpenApiExample(
        name="Не найдено",
        description="Ресурс не найден",
        value={
            "status": False,
            "error": "Запрашиваемый ресурс не найден."
        },
        response_only=True,
        status_codes=["404"]
    )
}


# Примеры успешных ответов
SUCCESS_EXAMPLES = {
    'registration_success': OpenApiExample(
        name="Успешная регистрация",
        description="Ответ при успешной регистрации пользователя",
        value={
            "status": True,
            "message": "Пользователь успешно зарегистрирован. Проверьте email для подтверждения."
        },
        response_only=True,
        status_codes=["201"]
    ),

    'email_confirmed': OpenApiExample(
        name="Email подтвержден",
        description="Ответ при успешном подтверждении email",
        value={
            "message": "Email успешно подтвержден. Теперь вы можете войти в систему."
        },
        response_only=True,
        status_codes=["200"]
    ),

    'basket_updated': OpenApiExample(
        name="Корзина обновлена",
        description="Ответ при успешном обновлении корзины",
        value={
            "status": True,
            "message": "Корзина обновлена",
            "data": {}
        },
        response_only=True,
        status_codes=["200"]
    )
}


def get_examples_for_operation(operation_type, resource_type=None):
    """
    Получает примеры для конкретной операции.

    Args:
        operation_type: Тип операции ('create', 'read', 'update', 'delete', 'login', etc.)
        resource_type: Тип ресурса ('auth', 'order', 'partner', etc.)

    Returns:
        list: Список примеров для операции
    """
    examples_map = {
        'auth': {
            'register': [AUTH_EXAMPLES['registration_request']],
            'login': [AUTH_EXAMPLES['login_request']],
            'confirm_email': [AUTH_EXAMPLES['email_confirmation_request']],
            'reset_password': [AUTH_EXAMPLES['password_reset_request']],
            'confirm_reset': [AUTH_EXAMPLES['password_reset_confirm_request']]
        },
        'order': {
            'basket_add': [ORDER_EXAMPLES['basket_add_request']],
            'basket_update': [ORDER_EXAMPLES['basket_update_request']],
            'create': [ORDER_EXAMPLES['order_create_request']],
            'contact_create': [ORDER_EXAMPLES['contact_create_request']]
        },
        'partner': {
            'update_price': [PARTNER_EXAMPLES['price_update_request']],
            'update_state': [PARTNER_EXAMPLES['state_update_request']]
        }
    }

    if resource_type and operation_type:
        return examples_map.get(resource_type, {}).get(operation_type, [])

    return []