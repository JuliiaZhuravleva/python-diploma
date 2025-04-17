"""
URL configuration for order_service project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from backend.admin_site import admin_site

def index(request):
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Система автоматизации закупок</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; text-align: center; }
            .container { max-width: 800px; margin: 0 auto; }
            h1 { color: #333; }
            .links { margin-top: 40px; }
            .button { 
                display: inline-block; 
                padding: 10px 20px; 
                margin: 10px;
                background-color: #4CAF50; 
                color: white; 
                text-decoration: none; 
                border-radius: 4px;
            }
            .button.admin { background-color: #2196F3; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Система автоматизации закупок для розничной сети</h1>
            <p>Добро пожаловать в систему управления заказами и закупками.</p>

            <div class="links">
                <a href="/admin/" class="button admin">Панель администратора</a>
                <a href="/api/v1/" class="button">API документация</a>
            </div>
        </div>
    </body>
    </html>
    '''
    return HttpResponse(html)

urlpatterns = [
    path('', index, name='index'),
    path('admin/', admin_site.urls),
    path('api/v1/', include('backend.api.urls', namespace='api')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
