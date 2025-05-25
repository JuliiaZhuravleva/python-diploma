"""
Модуль для централизованной OpenAPI документации.

Этот модуль предоставляет унифицированные инструменты для создания
документации API с применением принципов DRY (Don't Repeat Yourself).
"""

from .decorators import (
    api_endpoint,
    auth_endpoint,
    crud_endpoint,
    partner_endpoint
)

from .responses import (
    STANDARD_RESPONSES,
    get_success_response,
    get_error_response,
    get_validation_error_response
)

from .examples import (
    AUTH_EXAMPLES,
    ORDER_EXAMPLES,
    ERROR_EXAMPLES,
    SUCCESS_EXAMPLES
)

__all__ = [
    # Декораторы
    'api_endpoint',
    'auth_endpoint',
    'crud_endpoint',
    'partner_endpoint',

    # Responses
    'STANDARD_RESPONSES',
    'get_success_response',
    'get_error_response',
    'get_validation_error_response',

    # Examples
    'AUTH_EXAMPLES',
    'ORDER_EXAMPLES',
    'ERROR_EXAMPLES',
    'SUCCESS_EXAMPLES'
]