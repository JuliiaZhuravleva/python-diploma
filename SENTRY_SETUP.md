# Настройка Sentry для мониторинга ошибок

## Описание

В проект интегрирован Sentry - сервис для мониторинга ошибок и производительности приложения.

## Установка и настройк

### 1. Установка зависимостей

```bash
pip install sentry-sdk[django]==2.29.
```

### 2. Настройка переменных окружения

Добавьте в файл `.env`:

```
SENTRY_DSN=https://your-dsn@xxxxx.ingest.sentry.io/xxxxx
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=1.0
SENTRY_PROFILES_SAMPLE_RATE=1.0
```

### 3. Получение DSN

1. Зарегистрируйтесь на [https://sentry.io](https://sentry.io/)
2. Создайте новый проект Django
3. Скопируйте предоставленный DSN
4. Добавьте его в `.env` файл

## Возможности

- **Автоматический отлов ошибок** Django и Python исключений
- **Мониторинг производительности** запросов и транзакций
- **Интеграция с Celery** для отслеживания ошибок в фоновых задачах
- **Контекст пользователя** - привязка ошибок к конкретным пользователям
- **Информация о запросах** - URL, заголовки, данные формы

## Debug endpoints (только в DEBUG=True)

Для тестирования интеграции доступны специальные endpoints:

- `GET /api/v1/debug/sentry/success/` - успешный запрос
- `GET /api/v1/debug/sentry/zero-division/` - ошибка деления на ноль
- `GET /api/v1/debug/sentry/unhandled-exception/` - необработанное исключение
- `GET /api/v1/debug/sentry/database-error/` - ошибка базы данных
- `GET /api/v1/debug/sentry/slow-request/` - медленный запрос (3 сек)
- `POST /api/v1/debug/sentry/custom-exception/` - исключение с контекстом (требует аутентификации)

## Настройка для production

Для production рекомендуется:

```
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
```

Это снизит объем данных и производительность в продакшене.