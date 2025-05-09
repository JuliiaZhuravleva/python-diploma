import os
from django.conf import settings
from django.core.management import call_command

# Настройка переменной окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'order_service.settings')

if __name__ == '__main__':
    # Запуск Celery воркера
    call_command('celery', 'worker', '--loglevel=info')