"""
Debug views для тестирования Sentry интеграции.
Эти endpoints предназначены только для разработки и тестирования.
"""

import logging
from django.http import JsonResponse
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.openapi import OpenApiTypes

logger = logging.getLogger(__name__)


@extend_schema(
    summary="Тестирование деления на ноль",
    description="Генерирует ошибку деления на ноль для тестирования Sentry",
    responses={
        500: OpenApiResponse(
            description="Ошибка деления на ноль",
            response=OpenApiTypes.OBJECT
        )
    },
    tags=['Debug']
)
@api_view(['GET'])
@permission_classes([])  # Разрешаем доступ всем для тестирования
def test_zero_division_error(request):
    """
    Тестовый endpoint для проверки отлова ошибок деления на ноль.

    Этот endpoint намеренно вызывает ZeroDivisionError для проверки
    интеграции с Sentry.
    """
    logger.info("Вызов test_zero_division_error для тестирования Sentry")

    # Намеренная ошибка
    result = 1 / 0  # noqa

    return JsonResponse({"result": result})


@extend_schema(
    summary="Тестирование необработанного исключения",
    description="Генерирует необработанное исключение для тестирования Sentry",
    responses={
        500: OpenApiResponse(
            description="Необработанное исключение",
            response=OpenApiTypes.OBJECT
        )
    },
    tags=['Debug']
)
@api_view(['GET'])
@permission_classes([])
def test_unhandled_exception(request):
    """
    Тестовый endpoint для проверки отлова необработанных исключений.
    """
    logger.info("Вызов test_unhandled_exception для тестирования Sentry")

    # Намеренная ошибка - обращение к несуществующей переменной
    undefined_variable = some_undefined_variable  # noqa

    return JsonResponse({"result": undefined_variable})


@extend_schema(
    summary="Тестирование ошибки базы данных",
    description="Генерирует ошибку SQL запроса для тестирования Sentry",
    responses={
        500: OpenApiResponse(
            description="Ошибка базы данных",
            response=OpenApiTypes.OBJECT
        )
    },
    tags=['Debug']
)
@api_view(['GET'])
@permission_classes([])
def test_database_error(request):
    """
    Тестовый endpoint для проверки отлова ошибок базы данных.
    """
    logger.info("Вызов test_database_error для тестирования Sentry")

    # Намеренная ошибка SQL
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM non_existent_table_for_testing")

    return JsonResponse({"result": "success"})


@extend_schema(
    summary="Тестирование медленного запроса",
    description="Симулирует медленный запрос для тестирования performance monitoring",
    responses={
        200: OpenApiResponse(
            description="Успешный ответ после задержки",
            response=OpenApiTypes.OBJECT
        )
    },
    tags=['Debug']
)
@api_view(['GET'])
@permission_classes([])
def test_slow_request(request):
    """
    Тестовый endpoint для проверки мониторинга производительности.
    Симулирует медленный запрос с задержкой.
    """
    import time

    logger.info("Вызов test_slow_request для тестирования performance monitoring")

    # Симулируем медленную операцию
    time.sleep(3)

    return JsonResponse({
        "message": "Медленный запрос завершен",
        "delay_seconds": 3
    })


@extend_schema(
    summary="Успешный тест",
    description="Успешный endpoint для проверки, что Sentry не ловит успешные запросы",
    responses={
        200: OpenApiResponse(
            description="Успешный ответ",
            response=OpenApiTypes.OBJECT
        )
    },
    tags=['Debug']
)
@api_view(['GET'])
@permission_classes([])
def test_success(request):
    """
    Успешный endpoint для контрольной проверки.
    """
    logger.info("Успешный вызов test_success")

    return JsonResponse({
        "message": "Sentry интеграция работает! Этот запрос не должен попасть в ошибки.",
        "status": "success"
    })


@extend_schema(
    summary="Тестирование пользовательского исключения",
    description="Генерирует пользовательское исключение с контекстом",
    responses={
        500: OpenApiResponse(
            description="Пользовательское исключение",
            response=OpenApiTypes.OBJECT
        )
    },
    tags=['Debug']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_custom_exception(request):
    """
    Тестовый endpoint для проверки отлова пользовательских исключений с контекстом.
    Требует аутентификации для проверки отправки данных пользователя.
    """
    import sentry_sdk

    logger.info(f"Вызов test_custom_exception пользователем {request.user}")

    # Добавляем дополнительный контекст в Sentry
    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("test_type", "custom_exception")
        scope.set_context("request_data", {
            "method": request.method,
            "path": request.path,
            "user_agent": request.META.get('HTTP_USER_AGENT', 'Unknown')
        })
        scope.set_extra("custom_data", "Дополнительная информация для отладки")

    # Намеренное исключение с дополнительной информацией
    raise ValueError("Тестовое пользовательское исключение с контекстом")
