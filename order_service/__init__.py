from .celery import app as celery_app

# Делаем приложение Celery доступным для импорта
__all__ = ('celery_app',)