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
from django.urls import path, include
from django.contrib.auth import views as auth_views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from backend.api.views.social_views import SocialAuthInfoView, SimpleLogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('backend.api.urls', namespace='api')),

    # drf - spectacular
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),  # схема OpenAPI
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),  # Swagger UI
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),  # Redoc UI

    # auth
    path('auth/', include('social_django.urls', namespace='social')),
    path('api/v1/social/info/', SocialAuthInfoView.as_view(), name='social-info'),
    path('auth/logout/', auth_views.LogoutView.as_view(next_page='/api/v1/social/info/'), name='logout'),
    path('logout/', SimpleLogoutView.as_view(), name='simple-logout'),
]