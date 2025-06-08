"""
Конфигурация меню Django Baton для админ-панели.
"""

BATON_MENU = (
    # Пользователи и аутентификация
    {
        'type': 'title',
        'label': 'Управление пользователями',
    },
    {
        'type': 'model',
        'name': 'user',
        'label': 'Пользователи',
        'app': 'backend',
    },
    {
        'type': 'model',
        'name': 'confirmemailtoken',
        'label': 'Токены подтверждения',
        'app': 'backend',
    },
    # Каталог и товары
    {
        'type': 'title',
        'label': 'Каталог товаров',
    },
    {
        'type': 'model',
        'name': 'shop',
        'label': 'Магазины',
        'app': 'backend',
    },
    {
        'type': 'model',
        'name': 'category',
        'label': 'Категории',
        'app': 'backend',
    },
    {
        'type': 'model',
        'name': 'product',
        'label': 'Товары',
        'app': 'backend',
    },
    {
        'type': 'model',
        'name': 'productinfo',
        'label': 'Информация о товарах',
        'app': 'backend',
    },
    {
        'type': 'model',
        'name': 'parameter',
        'label': 'Параметры',
        'app': 'backend',
    },
    {
        'type': 'model',
        'name': 'productparameter',
        'label': 'Параметры товаров',
        'app': 'backend',
    },
    # Заказы и доставка
    {
        'type': 'title',
        'label': 'Заказы и доставка',
    },
    {
        'type': 'model',
        'name': 'order',
        'label': 'Заказы',
        'app': 'backend',
    },
    {
        'type': 'model',
        'name': 'orderitem',
        'label': 'Позиции заказов',
        'app': 'backend',
    },
    {
        'type': 'model',
        'name': 'contact',
        'label': 'Контакты доставки',
        'app': 'backend',
    },
    # Системные настройки
    {
        'type': 'title',
        'label': 'Системные настройки',
    },
    {
        'type': 'app',
        'name': 'auth',
        'label': 'Права доступа',
    },
    {
        'type': 'app',
        'name': 'social_django',
        'label': 'Социальная аутентификация',
    },
)
