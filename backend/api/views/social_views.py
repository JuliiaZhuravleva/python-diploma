from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from social_django.models import UserSocialAuth
from backend.api.serializers import UserSerializer
from django.http import HttpResponse
from django.contrib.auth import logout
from django.shortcuts import redirect


class SocialAuthInfoView(APIView):
    """
    Endpoint для проверки работы социальной авторизации и отображения результата
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Возвращает информацию о провайдерах и текущем пользователе"""
        providers = [
            {
                'name': 'Google',
                'provider': 'google-oauth2',
                'auth_url': '/auth/login/google-oauth2/'
            },
            {
                'name': 'GitHub',
                'provider': 'github',
                'auth_url': '/auth/login/github/'
            }
        ]

        # Если пользователь авторизован, показываем его данные
        user_info = None
        if request.user.is_authenticated:
            social_accounts = UserSocialAuth.objects.filter(user=request.user)
            user_info = {
                'id': request.user.id,
                'email': request.user.email,
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'is_active': request.user.is_active,
                'social_accounts': [
                    {
                        'provider': social.provider,
                        'uid': social.uid
                    }
                    for social in social_accounts
                ]
            }

        # Если это браузерный запрос, возвращаем HTML
        if 'text/html' in request.META.get('HTTP_ACCEPT', ''):
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Social Auth Test</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; }}
                    .success {{ color: green; }}
                    .info {{ background: #f0f0f0; padding: 10px; margin: 10px 0; }}
                    .provider {{ margin: 10px 0; }}
                    a {{ color: #007cba; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                </style>
            </head>
            <body>
                <h1>Social Auth Test Page</h1>

                {'<div class="success"><h2>✅ Авторизация успешна!</h2></div>' if user_info else '<div><h2>Не авторизован</h2></div>'}

                {f'<div class="info"><h3>Данные пользователя:</h3><pre>{user_info}</pre></div>' if user_info else ''}

                <h3>Доступные провайдеры:</h3>
                <div class="provider">
                    <a href="/auth/login/google-oauth2/">🔐 Войти через Google</a>
                </div>
                <div class="provider">
                    <a href="/auth/login/github/">🔐 Войти через GitHub</a>
                </div>

                <div class="provider">
                    <a href="/admin/">👤 Админка Django</a>
                </div>

                {f'<div class="provider"><a href="/logout/">🚪 Выйти</a></div>' if user_info else ''}
            </body>
            </html>
            """
            return HttpResponse(html_content)

        # Для API запросов возвращаем JSON
        return Response({
            'message': 'Social Auth configured successfully',
            'providers': providers,
            'current_user': user_info
        })


class SimpleLogoutView(APIView):
    """Простой logout через GET запрос"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        logout(request)
        return redirect('/api/v1/social/info/')