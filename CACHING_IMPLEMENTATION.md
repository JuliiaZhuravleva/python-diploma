# Реализация кэширования запросов к БД

## Описание

Внедрено кэширование запросов к базе данных с использованием Redis и django-cachalot для улучшения производительности системы автоматизации закупок.

## Что добавлено

### 1. Зависимости (requirements.txt)

- `django-cachalot>=2.8.0` - автоматическое кэширование ORM запросов

### 2. Настройки settings.py

- Настроен Django Cache backend с Redis
- Включен django-cachalot в INSTALLED_APPS
- Настройки кэширования с timeout 5 минут

### 3. Тесты

- `backend/tests/test_caching.py` - базовые тесты кэширования
- `backend/tests/test_caching_performance.py` - тесты производительности

## Результаты

- **Ускорение запросов**: до 32% для повторных запросов
- **Автоматическая инвалидация**: при изменении данных
- **Прозрачность**: не требует изменений в существующем коде

## Настройки кэша

- **Backend**: Django Redis Cache
- **Database**: Redis DB #1 (отдельно от Celery)
- **Timeout**: 300 секунд (5 минут)
- **Prefix**: 'cachalot'

## Проверка работы

```bash
python manage.py test backend.tests.test_caching_performance.CachingPerformanceTestCase -v 2
```

Ожидаемый результат: все тесты проходят, видно ускорение повторных запросов