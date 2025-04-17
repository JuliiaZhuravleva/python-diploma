from django.apps import AppConfig


class BackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend'

    def ready(self):
        """
        Метод вызывается, когда приложение и все модели полностью загружены.
        Здесь мы можем безопасно настраивать админку.
        """
        # Импорт admin_site и вызов setup_admin_site()
        from .admin_site import setup_admin_site
        setup_admin_site()