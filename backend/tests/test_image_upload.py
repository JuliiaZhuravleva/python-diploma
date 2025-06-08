"""
Тесты для функциональности загрузки и обработки изображений.
"""

import os
import tempfile
from PIL import Image
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from unittest.mock import patch, MagicMock

from backend.models import User, Product, Category
from backend.tasks import process_user_avatar, process_product_image, cleanup_old_images

# Временная директория для тестовых медиа файлов
TEMP_MEDIA_ROOT = tempfile.mkdtemp()


class ImageTestMixin:
    """
    Миксин с утилитами для создания тестовых изображений.
    """

    def create_test_image(self, name='test.jpg', size=(100, 100), format='JPEG'):
        """
        Создает тестовое изображение в памяти.

        Args:
            name (str): Имя файла
            size (tuple): Размер изображения (width, height)
            format (str): Формат изображения

        Returns:
            SimpleUploadedFile: Объект загружаемого файла
        """
        # Создаем тестовое изображение
        image = Image.new('RGB', size, color='red')

        # Сохраняем в временный файл
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        image.save(temp_file, format=format)
        temp_file.seek(0)

        # Читаем содержимое файла
        with open(temp_file.name, 'rb') as f:
            file_content = f.read()

        # Удаляем временный файл
        os.unlink(temp_file.name)

        return SimpleUploadedFile(
            name=name,
            content=file_content,
            content_type=f'image/{format.lower()}'
        )


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class UserAvatarUploadTestCase(APITestCase, ImageTestMixin):
    """
    Тесты для загрузки аватаров пользователей.
    """

    def setUp(self):
        """Настройка тестового окружения."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            is_active=True
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        self.upload_url = reverse('api:user-avatar')

    def tearDown(self):
        """Очистка после тестов."""
        # Удаляем все созданные файлы
        if self.user.avatar:
            try:
                os.remove(self.user.avatar.path)
            except (OSError, ValueError):
                pass

    def test_upload_avatar_success(self):
        """Тест успешной загрузки аватара."""
        test_image = self.create_test_image('avatar.jpg', (200, 200))

        response = self.client.post(self.upload_url, {
            'avatar': test_image
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertIn('успешно загружен', response.data['message'])

        # Проверяем, что аватар сохранился
        self.user.refresh_from_db()
        self.assertTrue(self.user.avatar)
        self.assertTrue(os.path.exists(self.user.avatar.path))

    def test_upload_avatar_without_file(self):
        """Тест загрузки без файла."""
        response = self.client.post(self.upload_url, {}, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertIn('avatar не найден', response.data['error'])

    def test_upload_avatar_unauthorized(self):
        """Тест загрузки без авторизации."""
        self.client.credentials()  # Убираем токен
        test_image = self.create_test_image()

        response = self.client.post(self.upload_url, {
            'avatar': test_image
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_avatar_success(self):
        """Тест успешного удаления аватара."""
        # Сначала загружаем аватар
        test_image = self.create_test_image()
        self.client.post(self.upload_url, {
            'avatar': test_image
        }, format='multipart')

        self.user.refresh_from_db()
        self.assertTrue(self.user.avatar)

        # Теперь удаляем
        response = self.client.delete(self.upload_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertIn('удален', response.data['message'])

        # Проверяем, что аватар удален
        self.user.refresh_from_db()
        self.assertFalse(self.user.avatar)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ProductImageUploadTestCase(APITestCase, ImageTestMixin):
    """
    Тесты для загрузки изображений товаров.
    """

    def setUp(self):
        """Настройка тестового окружения."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_active=True
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        # Создаем категорию и товар
        self.category = Category.objects.create(name='Тестовая категория')
        self.product = Product.objects.create(
            name='Тестовый товар',
            category=self.category
        )

        self.upload_url = reverse('api:product-image', kwargs={'product_id': self.product.id})

    def test_upload_product_image_success(self):
        """Тест успешной загрузки изображения товара."""
        test_image = self.create_test_image('product.jpg', (500, 500))

        response = self.client.post(self.upload_url, {
            'image': test_image
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertIn('успешно загружено', response.data['message'])

        # Проверяем, что изображение сохранилось
        self.product.refresh_from_db()
        self.assertTrue(self.product.image)
        self.assertTrue(os.path.exists(self.product.image.path))


class CeleryTasksTestCase(TestCase, ImageTestMixin):
    """
    Тесты для Celery задач обработки изображений.
    """

    def setUp(self):
        """Настройка тестового окружения."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_active=True
        )

        self.category = Category.objects.create(name='Тестовая категория')
        self.product = Product.objects.create(
            name='Тестовый товар',
            category=self.category
        )

    def test_process_user_avatar_task_no_avatar(self):
        """Тест задачи обработки аватара для пользователя без аватара."""
        result = process_user_avatar(self.user.id)

        self.assertFalse(result['success'])
        self.assertIn('нет аватара', result['error'])

    def test_process_user_avatar_task_user_not_found(self):
        """Тест задачи обработки аватара для несуществующего пользователя."""
        result = process_user_avatar(9999999)

        self.assertFalse(result['success'])
        self.assertIn('не найден', result['error'])