"""
Django settings for order_service project.

Generated by 'django-admin startproject' using Django 5.1.7.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from dotenv import load_dotenv
import os
from pathlib import Path

# Импорт конфигурации Baton
from .baton_config import BATON_MENU

# Импорт конфигурации Sentry
import sentry_sdk

# Детекция тестового режима
import sys
IS_TESTING = (
    'test' in sys.argv or
    any('test' in arg for arg in sys.argv) or
    'pytest' in sys.modules or
    os.environ.get('TESTING') == 'True'
)

# Load environment variables from .env file
load_dotenv()
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-ci-testing-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# Application definition

INSTALLED_APPS = [
    'baton',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'baton.autodiscover',
    'django_rest_passwordreset',

    # Сторонние библиотеки
    'rest_framework',
    'rest_framework.authtoken',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    'social_django',
    'imagekit',
    'cachalot',

    # Локальные приложения
    'backend',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'order_service.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'order_service.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
from dotenv import load_dotenv
import os

load_dotenv()

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('DB_NAME', os.path.join(BASE_DIR, 'db.sqlite3')),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', ''),
    }
}

# Django Cache settings (для django-cachalot)
if IS_TESTING:
    # В тестах используем локальный кэш в памяти, но cachalot оставляем включенным
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'test-cache',
            'TIMEOUT': 300,
        }
    }
    # В тестах тоже включаем cachalot, но с локальным кэшем
    CACHALOT_ENABLED = True
    CACHALOT_CACHE = 'default'
    CACHALOT_TIMEOUT = 300
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': os.getenv('CACHE_LOCATION', 'redis://localhost:6379/1'),
            'KEY_PREFIX': 'cachalot',
            'TIMEOUT': 300,  # 5 минут по умолчанию
        }
    }
    # Django-cachalot settings для продакшена
    CACHALOT_ENABLED = True
    CACHALOT_CACHE = 'default'
    CACHALOT_TIMEOUT = 300  # 5 минут

THROTTLE_RATES = {
    # Базовые лимиты
    'anon': '100/hour',
    'user': '1000/hour',

    # Критические операции (по IP адресу)
    'registration': '5/hour',
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'registration': '5/hour',
        'login': '10/hour',
        'password_reset': '3/hour',
    }
}

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.github.GithubOAuth2',
    'django.contrib.auth.backends.ModelBackend',
]

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Добавим директории для статических файлов в режиме разработки
STATICFILES_DIRS = [
    BASE_DIR / 'static',
] if DEBUG else []

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Настройки ImageKit
IMAGEKIT_DEFAULT_CACHEFILE_STRATEGY = 'imagekit.cachefiles.strategies.JustInTime'
IMAGEKIT_CACHEFILE_NAMER = 'imagekit.cachefiles.namers.source_name_dot_hash'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'backend.User'

# Настройки для отправки email (используем консольный бэкенд в режиме разработки)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.example.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'your_email@example.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'your_email@example.com')

# SQL logging
DEBUG_SQL = os.getenv('DEBUG_SQL', 'False').lower() == 'true'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG_SQL else 'INFO',
        },
    },
}

# Celery settings
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_STORE_EAGER_RESULT = True

# Spectacular settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'Сервис автоматизации закупок API',
    'DESCRIPTION': 'API для автоматизации закупок в розничной сети',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,  # Исключаем схему из списка эндпоинтов
    # Настройки для UI
    'SWAGGER_UI_DIST': 'SIDECAR',  # Используем локальную копию Swagger UI из sidecar
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',  # Используем локальную копию Redoc из sidecar
    # Дополнительные настройки Swagger UI
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,  # Позволяет создавать ссылки на специфичные операции
        'persistAuthorization': True,  # Сохраняет информацию об авторизации между обновлениями страницы
        'displayOperationId': False,  # Не показываем operation_id в UI
        'defaultModelsExpandDepth': 3,  # Глубина развертывания моделей по умолчанию
        'defaultModelExpandDepth': 3,  # Глубина развертывания моделей по умолчанию
        'displayRequestDuration': True,  # Показываем продолжительность запроса
        'docExpansion': 'list',  # Начальное состояние документации (list, full, none)
    },
    # Группировка по тегам
    'TAGS': [
        {'name': 'Auth', 'description': 'Операции аутентификации и управления пользователями'},
        {'name': 'Shop', 'description': 'Операции для работы с магазинами, товарами и категориями'},
        {'name': 'Orders', 'description': 'Операции для работы с заказами и корзиной'},
        {'name': 'Partner', 'description': 'Операции для партнеров (поставщиков)'},
    ],
    # Предобработка списка эндпоинтов
    'PREPROCESSING_HOOKS': [],
    # Постобработка схемы
    'POSTPROCESSING_HOOKS': [
        'drf_spectacular.hooks.postprocess_schema_enums'
    ],
    # Компонентная модель
    'COMPONENT_SPLIT_REQUEST': True,  # Разделяем компоненты на запрос и ответ
    'COMPONENT_SPLIT_PATCH': True,  # Отдельные компоненты для PATCH запросов
    # Сортировка операций
    'SORT_OPERATIONS': True,
}

# Social Auth settings
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY', '')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET', '')

SOCIAL_AUTH_GITHUB_KEY = os.getenv('SOCIAL_AUTH_GITHUB_KEY', '')
SOCIAL_AUTH_GITHUB_SECRET = os.getenv('SOCIAL_AUTH_GITHUB_SECRET', '')

# GitHub OAuth settings - запрашиваем email
SOCIAL_AUTH_GITHUB_SCOPE = ['user:email']

# Извлекаем email из GitHub API
SOCIAL_AUTH_GITHUB_EXTRA_DATA = ['login', 'email', 'name']

# Pipeline для обработки email из GitHub
def get_github_email(backend, response, user=None, *args, **kwargs):
    """Получает email из GitHub API если он не возвращается напрямую"""
    if backend.name == 'github':
        # Если email не получен, пробуем получить через API
        if not response.get('email'):
            import requests
            access_token = kwargs.get('response', {}).get('access_token')
            if access_token:
                # Запрашиваем email через GitHub API
                email_response = requests.get(
                    'https://api.github.com/user/emails',
                    headers={'Authorization': f'token {access_token}'}
                )
                if email_response.status_code == 200:
                    emails = email_response.json()
                    # Берем primary email
                    for email_data in emails:
                        if email_data.get('primary'):
                            response['email'] = email_data['email']
                            break
    return {'response': response}

# Social Auth pipeline
SOCIAL_AUTH_PIPELINE = [
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'order_service.settings.get_github_email',
    'social_core.pipeline.user.create_user',
    'backend.social_pipeline.activate_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
]

# User model compatibility
SOCIAL_AUTH_USER_MODEL = AUTH_USER_MODEL

# Social Auth redirects
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/api/v1/social/info/'
LOGOUT_REDIRECT_URL = '/api/v1/social/info/'

# Social Auth settings
SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/api/v1/social/info/'
SOCIAL_AUTH_NEW_USER_REDIRECT_URL = '/api/v1/social/info/'
SOCIAL_AUTH_LOGIN_ERROR_URL = '/api/v1/social/info/'

# Django Baton settings
BATON = {
    'SITE_HEADER': 'Система автоматизации закупок',
    'SITE_TITLE': 'Админ панель',
    'INDEX_TITLE': 'Добро пожаловать в панель управления',
    'SUPPORT_HREF': False,
    'COPYRIGHT': 'Copyright © 2024 Система автоматизации закупок',
    'POWERED_BY': '<a href="https://github.com/JuliiaZhuravleva/python-diploma">Python Diploma Project</a>',
    'MENU': BATON_MENU
}

# Sentry Configuration
SENTRY_DSN = os.getenv('SENTRY_DSN')
SENTRY_ENVIRONMENT = os.getenv('SENTRY_ENVIRONMENT', 'development')
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv('SENTRY_TRACES_SAMPLE_RATE', '1.0'))
SENTRY_PROFILES_SAMPLE_RATE = float(os.getenv('SENTRY_PROFILES_SAMPLE_RATE', '1.0'))

if SENTRY_DSN and not IS_TESTING:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        # Интеграции подключаются автоматически для Django и Celery

        # Performance Monitoring
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,

        # Profiling (новый параметр в 2.x)
        profiles_sample_rate=SENTRY_PROFILES_SAMPLE_RATE,

        # Environment
        environment=SENTRY_ENVIRONMENT,

        # Send user data with errors (email, username)
        send_default_pii=True,

        # Release tracking
        release=f"order-service@1.0.0",

        # Additional options
        attach_stacktrace=True,

        # Debug mode (only send in production if DSN is set)
        debug=DEBUG and bool(SENTRY_DSN),
    )
elif IS_TESTING:
    # В тестах полностью отключаем Sentry логирование
    import logging
    logging.getLogger('sentry_sdk').setLevel(logging.CRITICAL)
