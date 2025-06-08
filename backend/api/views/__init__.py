from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, authentication, permissions
from rest_framework.pagination import PageNumberPagination
from rest_framework.authtoken.models import Token
from django.db import transaction
from django.conf import settings
from django.http import JsonResponse
from backend.models import User, Shop, Category, Product, ProductInfo, Parameter, ProductParameter, Contact, Order, \
    OrderItem, ConfirmEmailToken
from backend.api.serializers import (
    UserSerializer, ShopSerializer, CategorySerializer, ProductSerializer,
    ProductInfoSerializer, ParameterSerializer, ProductParameterSerializer,
    ContactSerializer, OrderSerializer, OrderItemSerializer
)


class ApiResponse:
    """
    Класс для формирования унифицированного ответа API.
    """

    @staticmethod
    def success(data=None, message=None, status_code=status.HTTP_200_OK):
        """
        Формирует успешный ответ API.
        """
        response = {
            'success': True,
        }
        if data is not None:
            response['data'] = data
        if message is not None:
            response['message'] = message

        return Response(response, status=status_code)

    @staticmethod
    def error(message, status_code=status.HTTP_400_BAD_REQUEST, errors=None):
        """
        Формирует ответ с ошибкой API.
        """
        response = {
            'success': False,
            'message': message
        }
        if errors is not None:
            response['errors'] = errors

        return Response(response, status=status_code)
