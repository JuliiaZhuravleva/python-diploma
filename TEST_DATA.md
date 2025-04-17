# Работа с тестовыми данными

В проекте предусмотрена возможность быстрого наполнения базы данных тестовыми сущностями для разработки и тестирования. 

## Структура тестовых данных

Тестовые данные представлены в виде CSV-файлов в директории `fixtures/test_data/`:

- **users.csv** - пользователи (покупатели и магазины)
- **shops.csv** - магазины 
- **categories.csv** - категории товаров
- **products.csv** - товары
- **product_info.csv** - информация о товарах в конкретных магазинах
- **parameters.csv** - параметры (характеристики) товаров
- **product_parameters.csv** - значения параметров для конкретных товаров
- **contacts.csv** - контактные данные пользователей

## Загрузка тестовых данных

Для загрузки всех тестовых данных используйте команду:

```bash
python manage.py load_test_data
```

### Дополнительные опции

- `--delete` - удалить существующие данные перед загрузкой новых
- `--path` - указать альтернативный путь к директории с данными

Пример:
```bash
python manage.py load_test_data --delete --path=my_data
```

## Тестовые учетные записи

После загрузки тестовых данных вы можете использовать следующие учетные записи:

### Покупатели:
- Email: buyer1@example.com, Пароль: Strong123!
- Email: buyer2@example.com, Пароль: Strong123!
- Email: buyer3@example.com, Пароль: Strong123!
- Email: buyer4@example.com, Пароль: Strong123!
- Email: buyer5@example.com, Пароль: Strong123!

### Магазины:
- Email: shop1@example.com, Пароль: Strong123!
- Email: shop2@example.com, Пароль: Strong123!
- Email: shop3@example.com, Пароль: Strong123!
- Email: shop4@example.com, Пароль: Strong123!

## Создание собственных тестовых данных

Вы можете создать собственные тестовые данные, добавив или изменив CSV-файлы в директории `data/`. 

### Формат CSV-файлов

#### users.csv
```
email,password,first_name,last_name,company,position,type,is_active
user@example.com,password,Имя,Фамилия,Компания,Должность,buyer,1
```

#### shops.csv
```
name,url,user_email,state
Магазин,https://example.com,shop@example.com,1
```

#### categories.csv
```
id,name
1,Категория
```

#### products.csv
```
id,category_id,name
1,1,Название товара
```

#### product_info.csv
```
product_id,shop_name,model,external_id,quantity,price,price_rrc
1,Магазин,model,1001,10,1000,1200
```

#### parameters.csv
```
id,name
1,Параметр
```

#### product_parameters.csv
```
product_info_external_id,shop_name,parameter_name,value
1001,Магазин,Параметр,Значение
```

#### contacts.csv
```
user_email,city,street,house,structure,building,apartment,phone,is_deleted
user@example.com,Город,Улица,1,A,1,1,+79001234567,0
```

## Автоматическое создание заказов

Скрипт `load_test_data.py` также создает несколько тестовых заказов для двух первых покупателей в списке:
- Один заказ в статусе "Корзина" (незавершенный)
- Один завершенный заказ в статусе "Новый" или "Подтвержден"

Это позволяет сразу тестировать API для работы с заказами.

## Модификация скрипта загрузки

Если вам нужно изменить логику загрузки тестовых данных, отредактируйте файл `backend/management/commands/load_test_data.py`.

## Тестирование API с использованием тестовых данных

После загрузки тестовых данных вы можете легко протестировать функциональность API с помощью встроенной команды Django:

```bash
# Загрузка тестовых данных (если ещё не загружены)
python manage.py load_test_data

# Запуск тестирования API
python manage.py test_api
```

### Основные сценарии тестирования

Вы можете выбрать конкретный сценарий тестирования:

```bash
# Тестирование авторизации
python manage.py test_api --scenario auth

# Тестирование работы с товарами и категориями
python manage.py test_api --scenario products

# Тестирование работы с корзиной и заказами
python manage.py test_api --scenario order
```

### Выбор тестового пользователя

Для тестирования доступны следующие предустановленные пользователи:

```bash
# Тестирование с покупателем 1
python manage.py test_api --user buyer1@example.com --password Strong123!

# Тестирование с покупателем 2
python manage.py test_api --user buyer2@example.com --password Strong123!

# Тестирование с магазином
python manage.py test_api --user shop1@example.com --password Strong123!
```

### Преимущества использования команды test_api

1. Автоматическое тестирование всех основных функций API
2. Интеграция с тестовыми данными
3. Быстрая проверка работоспособности системы
4. Демонстрация возможностей API для презентаций и обучения
5. Возможность выбора конкретных сценариев тестирования

Подробнее о команде test_api и всех её возможностях можно узнать, выполнив:

```bash
python manage.py test_api --help
```
