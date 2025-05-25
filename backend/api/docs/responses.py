"""
Стандартизированные схемы ответов для OpenAPI документации.
"""

from drf_spectacular.utils import OpenApiResponse, OpenApiExample
from rest_framework import serializers


class StandardStatusSerializer(serializers.Serializer):
    """Базовый сериализатор для стандартных ответов API."""
    status = serializers.BooleanField(help_text="Статус выполнения операции")
    message = serializers.CharField(help_text="Сообщение о результате операции")


class ValidationErrorSerializer(serializers.Serializer):
    """Сериализатор для ошибок валидации."""
    status = serializers.BooleanField(default=False, help_text="Статус выполнения (всегда False)")
    errors = serializers.DictField(help_text="Словарь ошибок валидации по полям")


class SingleErrorSerializer(serializers.Serializer):
    """Сериализатор для одиночных ошибок."""
    status = serializers.BooleanField(default=False, help_text="Статус выполнения (всегда False)")
    error = serializers.CharField(help_text="Текст ошибки")


class SuccessWithDataSerializer(serializers.Serializer):
    """Сериализатор для успешных ответов с данными."""
    status = serializers.BooleanField(default=True, help_text="Статус выполнения (всегда True)")
    message = serializers.CharField(help_text="Сообщение об успехе")
    data = serializers.DictField(help_text="Данные ответа")


# Предопределенные схемы ответов
STANDARD_RESPONSES = {
    'success': OpenApiResponse(
        description="Операция выполнена успешно",
        response=StandardStatusSerializer,
        examples=[
            OpenApiExample(
                "Успешный ответ",
                value={
                    "status": True,
                    "message": "Операция выполнена успешно"
                },
                status_codes=["200", "201"]
            )
        ]
    ),

    'validation_error': OpenApiResponse(
        description="Ошибка валидации данных",
        response=ValidationErrorSerializer,
        examples=[
            OpenApiExample(
                "Ошибка валидации",
                value={
                    "status": False,
                    "errors": {
                        "email": ["Пользователь с таким email уже существует."],
                        "password": ["Пароль должен содержать не менее 8 символов."]
                    }
                },
                status_codes=["400"]
            )
        ]
    ),

    'single_error': OpenApiResponse(
        description="Единичная ошибка",
        response=SingleErrorSerializer,
        examples=[
            OpenApiExample(
                "Ошибка выполнения",
                value={
                    "status": False,
                    "error": "Описание ошибки"
                },
                status_codes=["400", "404"]
            )
        ]
    ),

    'unauthorized': OpenApiResponse(
        description="Ошибка авторизации",
        response=SingleErrorSerializer,
        examples=[
            OpenApiExample(
                "Не авторизован",
                value={
                    "status": False,
                    "error": "Учетные данные не были предоставлены."
                },
                status_codes=["401"]
            )
        ]
    ),

    'forbidden': OpenApiResponse(
        description="Недостаточно прав доступа",
        response=SingleErrorSerializer,
        examples=[
            OpenApiExample(
                "Доступ запрещен",
                value={
                    "status": False,
                    "error": "У вас недостаточно прав для выполнения данной операции."
                },
                status_codes=["403"]
            )
        ]
    ),

    'not_found': OpenApiResponse(
        description="Ресурс не найден",
        response=SingleErrorSerializer,
        examples=[
            OpenApiExample(
                "Не найдено",
                value={
                    "status": False,
                    "error": "Запрашиваемый ресурс не найден."
                },
                status_codes=["404"]
            )
        ]
    ),

    'server_error': OpenApiResponse(
        description="Внутренняя ошибка сервера",
        response=SingleErrorSerializer,
        examples=[
            OpenApiExample(
                "Ошибка сервера",
                value={
                    "status": False,
                    "error": "Произошла внутренняя ошибка сервера."
                },
                status_codes=["500"]
            )
        ]
    )
}


def get_success_response(message="Операция выполнена успешно", with_data=False):
    """
    Создает стандартизированный успешный ответ.

    Args:
        message: Сообщение об успехе
        with_data: Включать ли поле data в ответ

    Returns:
        OpenApiResponse: Настроенный ответ для успешной операции
    """
    serializer_class = SuccessWithDataSerializer if with_data else StandardStatusSerializer

    example_value = {
        "status": True,
        "message": message
    }

    if with_data:
        example_value["data"] = {}

    return OpenApiResponse(
        description="Операция выполнена успешно",
        response=serializer_class,
        examples=[
            OpenApiExample(
                "Успешный ответ",
                value=example_value,
                status_codes=["200", "201"]
            )
        ]
    )


def get_error_response(error_message, status_code="400"):
    """
    Создает стандартизированный ответ с ошибкой.

    Args:
        error_message: Текст ошибки
        status_code: HTTP статус код

    Returns:
        OpenApiResponse: Настроенный ответ с ошибкой
    """
    return OpenApiResponse(
        description="Ошибка выполнения операции",
        response=SingleErrorSerializer,
        examples=[
            OpenApiExample(
                "Ошибка",
                value={
                    "status": False,
                    "error": error_message
                },
                status_codes=[status_code]
            )
        ]
    )


def get_validation_error_response(field_errors=None):
    """
    Создает стандартизированный ответ с ошибками валидации.

    Args:
        field_errors: Словарь ошибок по полям

    Returns:
        OpenApiResponse: Настроенный ответ с ошибками валидации
    """
    if field_errors is None:
        field_errors = {
            "field_name": ["Пример ошибки валидации."]
        }

    return OpenApiResponse(
        description="Ошибка валидации данных",
        response=ValidationErrorSerializer,
        examples=[
            OpenApiExample(
                "Ошибки валидации",
                value={
                    "status": False,
                    "errors": field_errors
                },
                status_codes=["400"]
            )
        ]
    )


def get_responses_for_endpoint(success_message=None, with_data=False, include_auth=False, custom_errors=None):
    """
    Создает полный набор ответов для endpoint.

    Args:
        success_message: Сообщение для успешного ответа
        with_data: Включать ли данные в успешный ответ
        include_auth: Включать ли ошибки авторизации
        custom_errors: Дополнительные кастомные ошибки

    Returns:
        dict: Словарь ответов для использования в @extend_schema
    """
    responses = {
        200: get_success_response(success_message, with_data) if success_message else STANDARD_RESPONSES['success'],
        400: STANDARD_RESPONSES['validation_error'],
        500: STANDARD_RESPONSES['server_error']
    }

    if include_auth:
        responses[401] = STANDARD_RESPONSES['unauthorized']
        responses[403] = STANDARD_RESPONSES['forbidden']

    if custom_errors:
        responses.update(custom_errors)

    return responses
