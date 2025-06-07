"""
Унифицированные декораторы для OpenAPI документации.
"""

from functools import wraps
from drf_spectacular.utils import extend_schema
from .responses import get_responses_for_endpoint, STANDARD_RESPONSES
from .examples import get_examples_for_operation, AUTH_EXAMPLES, ORDER_EXAMPLES, PARTNER_EXAMPLES


def api_endpoint(tags, summary, description, **kwargs):
    """
    Базовый декоратор для API endpoints.

    Args:
        tags: Список тегов для группировки в Swagger
        summary: Краткое описание endpoint'а
        description: Подробное описание
        **kwargs: Дополнительные параметры для extend_schema

    Returns:
        function: Декоратор для применения к методам view
    """
    # Объединяем стандартные ответы с переданными
    responses = kwargs.pop('responses', {})
    default_responses = get_responses_for_endpoint(
        include_auth=kwargs.pop('include_auth', False)
    )
    final_responses = {**default_responses, **responses}

    def decorator(func):
        return extend_schema(
            tags=tags,
            summary=summary,
            description=description,
            responses=final_responses,
            **kwargs
        )(func)

    return decorator


def auth_endpoint(operation, summary, description, **kwargs):
    """
    Специализированный декоратор для endpoints аутентификации.

    Args:
        operation: Тип операции ('register', 'login', 'confirm_email', etc.)
        summary: Краткое описание
        description: Подробное описание
        **kwargs: Дополнительные параметры

    Returns:
        function: Декоратор для применения к методам view
    """
    # Получаем примеры для конкретной операции
    examples = get_examples_for_operation(operation, 'auth')

    # Стандартные ответы для auth endpoints
    custom_responses = kwargs.pop('responses', {})
    default_responses = get_responses_for_endpoint(include_auth=False)

    # Объединяем стандартные и пользовательские ответы
    responses = {**default_responses, **custom_responses}

    # Специфичные настройки для разных операций
    operation_config = {
        'register': {
            'success_status': 201,
            'success_message': "Пользователь успешно зарегистрирован"
        },
        'login': {
            'success_status': 200,
            'include_token': True
        },
        'confirm_email': {
            'success_status': 200,
            'success_message': "Email успешно подтвержден"
        },
        'reset_password': {
            'success_status': 200,
            'success_message': "Инструкции по сбросу пароля отправлены на email"
        },
        'confirm_reset': {
            'success_status': 200,
            'success_message': "Пароль успешно изменен"
        }
    }

    config = operation_config.get(operation, {})
    success_status = config.get('success_status', 200)

    if success_status == 201:
        responses[201] = responses.pop(200)  # Перемещаем успешный ответ на 201

    return api_endpoint(
        tags=['Auth'],
        summary=summary,
        description=description,
        responses=responses,
        examples=examples,
        **kwargs
    )


def crud_endpoint(operation, resource, summary=None, description=None, **kwargs):
    """
    Декоратор для CRUD операций.

    Args:
        operation: Тип операции ('create', 'read', 'update', 'delete', 'list')
        resource: Тип ресурса ('orders', 'contacts', 'products', etc.)
        summary: Краткое описание (генерируется автоматически если не указано)
        description: Подробное описание
        **kwargs: Дополнительные параметры

    Returns:
        function: Декоратор для применения к методам view
    """
    # Автоматическая генерация summary если не указан
    if not summary:
        operation_names = {
            'create': f'Создать {resource}',
            'read': f'Получить {resource}',
            'update': f'Обновить {resource}',
            'delete': f'Удалить {resource}',
            'list': f'Список {resource}'
        }
        summary = operation_names.get(operation, f'{operation.title()} {resource}')

    # Определяем тег на основе ресурса
    tag_mapping = {
        'orders': 'Orders',
        'contacts': 'Auth',
        'products': 'Shop',
        'categories': 'Shop',
        'shops': 'Shop'
    }

    tag = tag_mapping.get(resource, 'API')

    # Настройки для разных операций
    include_auth = kwargs.pop('requires_auth', True)

    # Извлекаем responses из kwargs
    custom_responses = kwargs.pop('responses', {})

    # Дополнительные ответы для разных операций
    additional_responses = {}
    if operation in ['read', 'update', 'delete']:
        additional_responses[404] = STANDARD_RESPONSES['not_found']

    # Объединяем все responses
    responses = {**additional_responses, **custom_responses}

    return api_endpoint(
        tags=[tag],
        summary=summary,
        description=description,
        include_auth=include_auth,
        responses=responses,
        **kwargs
    )


def partner_endpoint(operation, summary=None, description=None, **kwargs):
    """
    Специализированный декоратор для partner endpoints.

    Args:
        operation: Тип операции ('update_price', 'get_state', 'update_state', 'get_orders')
        summary: Краткое описание
        description: Подробное описание
        **kwargs: Дополнительные параметры

    Returns:
        function: Декоратор для применения к методам view
    """
    # Автоматическая генерация описаний
    if not summary:
        operation_summaries = {
            'update_price': 'Обновить прайс-лист партнера',
            'get_state': 'Получить статус партнера',
            'update_state': 'Обновить статус партнера',
            'get_orders': 'Получить заказы партнера'
        }
        summary = operation_summaries.get(operation, f'Partner {operation}')

    # Получаем примеры для операции
    if 'examples' not in kwargs:
        examples = get_examples_for_operation(operation, 'partner')
        kwargs['examples'] = examples

    return api_endpoint(
        tags=['Partner'],
        summary=summary,
        description=description,
        include_auth=True,  # Partner endpoints всегда требуют авторизации
        **kwargs
    )


def basket_endpoint(operation, **kwargs):
    """
    Специализированный декоратор для операций с корзиной.

    Args:
        operation: Тип операции ('get', 'add', 'update', 'delete')
        **kwargs: Дополнительные параметры

    Returns:
        function: Декоратор для применения к методам view
    """
    operation_config = {
        'get': {
            'summary': 'Получить корзину',
            'description': 'Возвращает информацию о текущей корзине пользователя и её содержимом'
        },
        'add': {
            'summary': 'Добавить товары в корзину',
            'description': 'Добавляет товары в корзину пользователя'
        },
        'update': {
            'summary': 'Обновить товары в корзине',
            'description': 'Обновляет количество товаров в корзине пользователя'
        },
        'delete': {
            'summary': 'Удалить товары из корзины',
            'description': 'Удаляет выбранные товары из корзины пользователя'
        }
    }

    config = operation_config.get(operation, {})
    examples = get_examples_for_operation(f'basket_{operation}', 'order')

    return crud_endpoint(
        operation=operation,
        resource='orders',
        summary=config.get('summary'),
        description=config.get('description'),
        examples=examples,
        **kwargs
    )