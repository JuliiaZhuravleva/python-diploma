from django.urls import path
from backend.api import views
from backend.api.views import TestAuthView

app_name = 'api'

urlpatterns = [
    # Тестовый URL для проверки аутентификации
    path('test-auth/', TestAuthView.as_view(), name='test-auth'),
]