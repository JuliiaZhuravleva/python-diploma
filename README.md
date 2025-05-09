# Система автоматизации закупок для розничной сети

Бэкенд-приложение для автоматизации процесса закупок в розничной сети, реализованное на Django REST Framework. Система поддерживает полный цикл оформления заказов от добавления товаров в корзину до подтверждения и доставки.

## Функциональные возможности

- Регистрация и авторизация пользователей (покупателей и поставщиков)
- Просмотр каталога товаров с фильтрацией
- Управление корзиной (добавление, изменение, удаление товаров)
- Оформление заказов с указанием адреса доставки
- Отправка email-уведомлений при оформлении заказа
- Управление контактной информацией пользователя
- Просмотр истории заказов
- Для поставщиков: управление каталогом товаров, импорт прайс-листов, управление статусом магазина

## Технический стек

- Python 3.10+
- Django & Django REST Framework
- SQLite (в разработке) / PostgreSQL (опционально для продакшена)
- Redis
- Celery
- JWT аутентификация

## Установка и запуск

### Предварительные требования

- Python 3.10 или новее
- pip (менеджер пакетов Python)

### Шаги по установке

1. Клонируйте репозиторий:
    
    ```bash
    git clone <https://github.com/your-username/retail-order-service.git>
    cd retail-order-service
    
    ```
    
2. Создайте и активируйте виртуальное окружение:
    
    ```bash
    python -m venv .venv
    
    # Для Linux/macOS
    source .venv/bin/activate
    
    # Для Windows
    .venv\Scripts\activate
    
    ```
    
3. Установите зависимости:
    
    ```bash
    pip install -r requirements.txt
    
    ```

4. Создайте файл .env в корневой директории проекта и настройте следующие переменные:
    
    ```bash    
   SECRET_KEY=your_secret_key 
   DEBUG=True 
   ALLOWED_HOSTS=localhost,127.0.0.1

   # Database settings
   DB_ENGINE=django.db.backends.sqlite3 
   DB_NAME=db.sqlite3 
   DB_USER= 
   DB_PASSWORD= 
   DB_HOST= 
   DB_PORT=
   
   # Email settings
   EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
   EMAIL_HOST=smtp.gmail.com 
   EMAIL_PORT=587 
   EMAIL_USE_TLS=True 
   EMAIL_HOST_USER=your-email@gmail.com 
   EMAIL_HOST_PASSWORD=your-app-password 
   DEFAULT_FROM_EMAIL=noreply@order-service.com
   
   # Debugging settings
   DEBUG_SQL=False
    ```
5. Выполните миграции базы данных:
    
    ```bash
    python manage.py migrate
    
    ```
    
6. Создайте суперпользователя (для доступа к админ-панели):
    
    ```bash
    python manage.py createsuperuser
    
    ```
    
7. Запустите сервер разработки:
    
    ```bash
    python manage.py runserver
    
    ```
    

Приложение будет доступно по адресу: http://localhost:8000/

## Конфигурация

### Переключение базы данных

Для использования PostgreSQL вместо SQLite измените следующие переменные в .env файле:

```bash
  DB_ENGINE=django.db.backends.postgresql
  DB_NAME=your_db_name
  DB_USER=your_db_user 
  DB_PASSWORD=your_db_password 
  DB_HOST=localhost 
  DB_PORT=5432
```

### Настройка электронной почты

Для отправки реальных писем вместо вывода в консоль измените настройки в .env файле:

```bash
  EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
  EMAIL_HOST=smtp.gmail.com
  EMAIL_PORT=587
  EMAIL_USE_TLS=True
  EMAIL_HOST_USER=your-email@gmail.com
  EMAIL_HOST_PASSWORD=your-app-password
```

### Включение логирования SQL-запросов

Для включения логирования SQL-запросов установите в .env файле:

```bash
  DEBUG_SQL=True
```

## Запуск Redis для Celery

Проект использует Redis в качестве брокера сообщений для Celery. Для локальной разработки и тестирования вы можете запустить Redis с помощью Docker:

```bash
# Запуск Redis
docker compose up -d

# Остановка Redis
docker compose down
```

## Структура проекта

```
ROOT/
├── backend/              # Основное приложение Django
│   ├── api/              # API endpoints и сериализаторы
│   ├── models.py         # Модели данных
│   ├── services/         # Сервисные функции и бизнес-логика
│   └── tests/            # Тесты приложения
├── order_service/        # Настройки проекта Django
├── docs/                 # Документация
└── postman/              # Коллекция Postman для тестирования API

```

## API Endpoints

### Пользователи

- `POST /api/v1/user/register` - Регистрация нового пользователя
- `POST /api/v1/user/register/confirm` - Подтверждение email
- `POST /api/v1/user/login` - Авторизация пользователя
- `GET/POST /api/v1/user/details` - Получение/обновление деталей пользователя
- `GET/POST/PUT/DELETE /api/v1/user/contact` - Управление контактами пользователя
- `POST /api/v1/user/password_reset` - Запрос на сброс пароля
- `POST /api/v1/user/password_reset/confirm` - Подтверждение сброса пароля

### Магазин

- `GET /api/v1/shops` - Список магазинов
- `GET /api/v1/categories` - Список категорий
- `GET /api/v1/products` - Список товаров с возможностью фильтрации
- `GET /api/v1/products/{id}` - Детальная информация о товаре
- `GET/POST/PUT/DELETE /api/v1/basket` - Управление корзиной
- `GET/POST /api/v1/order` - Просмотр заказов/создание заказа
- `GET/PUT /api/v1/order/{id}` - Просмотр/отмена конкретного заказа

### Партнеры (поставщики)

- `POST /api/v1/partner/update` - Обновление прайс-листа
- `GET/POST /api/v1/partner/state` - Получение/изменение статуса магазина
- `GET /api/v1/partner/orders` - Получение заказов, содержащих товары магазина

## Разработка и тестирование

При разработке и тестировании вы можете легко изменять конфигурацию проекта, редактируя файл .env. Это позволяет быстро переключаться между различными настройками базы данных, почтовыми серверами и режимами отладки без изменения кода.

### Запуск тестов с измерением покрытия
[![codecov](https://codecov.io/gh/JuliiaZhuravleva/python-diploma/branch/main/graph/badge.svg)](https://codecov.io/gh/JuliiaZhuravleva/python-diploma)

Проект имеет обширный набор тестов для проверки функциональности API и внутренних сервисов. Для измерения покрытия кода тестами используется инструмент Coverage.py.

```bash
# Установка зависимостей для тестирования
pip install coverage

# Запуск тестов с измерением покрытия
coverage run --source=backend manage.py test

# Генерация отчета о покрытии
coverage report

# Создание HTML-отчета для более детального анализа
coverage html
```

### Тестирование API

Для тестирования API можно использовать Postman-коллекцию, включенную в проект.

#### Порядок тестирования с Postman:

1. Импортируйте коллекцию `netology-pd-diplom.postman_collection.json` в Postman.
2. Установите переменную коллекции `server_address` со значением `localhost:8000` (или вашим собственным адресом сервера).
3. Выполните запросы в следующем порядке:
    - Регистрация пользователя (`register user`)
    - Подтверждение email (требуется токен из консоли сервера)
    - Вход пользователя (`login user`) - автоматически сохранит токен авторизации
    - Остальные запросы будут автоматически выполняться с использованием сохраненного токена


### Тестовые данные для разработки

Для ускорения разработки и тестирования в проекте предусмотрены инструменты для быстрой загрузки тестовых данных:

Примечание: Убедитесь, что в вашем .env файле установлено `DEBUG=True` для использования тестовых данных.

```bash
# Загрузка тестовых данных
python manage.py load_test_data

# Удаление старых данных и загрузка новых
python manage.py load_test_data --delete
```

После загрузки тестовых данных станут доступны:
- 10 пользователей (5 покупателей, 4 магазина, 1 неактивный)
- 10 категорий товаров
- 20 товаров с разными характеристиками
- 5 магазинов с набором товаров
- Контактные данные покупателей
- Тестовые заказы

#### Тестовые учетные записи

**Покупатели:**
- Email: buyer1@example.com, Пароль: Strong123!
- Email: buyer2@example.com, Пароль: Strong123!
- *и другие (см. [TEST_DATA.md](TEST_DATA.md))*

**Магазины:**
- Email: shop1@example.com, Пароль: Strong123!
- Email: shop2@example.com, Пароль: Strong123!
- *и другие (см. [TEST_DATA.md](TEST_DATA.md))*

#### Автоматическое тестирование API

Для быстрой проверки API можно использовать команду:

```bash
python manage.py test_api
```

Команда выполнит основной сценарий работы с API (авторизация, просмотр товаров, добавление в корзину, оформление заказа).

Подробнее о тестовых данных и инструментах тестирования читайте в [TEST_DATA.md](TEST_DATA.md).