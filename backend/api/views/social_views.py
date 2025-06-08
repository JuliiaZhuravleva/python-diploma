from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from social_django.models import UserSocialAuth


class SocialAuthInfoView(APIView):
    """
    Простой endpoint для проверки работы социальной авторизации
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Возвращает информацию о доступных провайдерах"""
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

        return Response({
            'message': 'Social Auth configured successfully',
            'providers': providers
        })
