import os
from celery import Celery

# Настройка переменной окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'order_service.settings')

# Создание экземпляра приложения Celery
app = Celery('order_service')

# Загрузка конфигурации из настроек Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматическое обнаружение и регистрация задач из файлов tasks.py в приложениях
app.autodiscover_tasks()