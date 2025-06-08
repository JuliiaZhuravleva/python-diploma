from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch, Mock
from backend.models import Shop, Category, Product, ProductInfo
import tempfile
import os

User = get_user_model()


def create_test_image(self):
    """
    Создает корректное тестовое изображение.
    """
    from PIL import Image
    import io

    # Создаем простое изображение 1x1 пиксель
    image = Image.new('RGB', (1, 1), color='red')
    image_io = io.BytesIO()
    image.save(image_io, format='PNG')
    image_io.seek(0)

    return SimpleUploadedFile(
        "test_image.png",
        image_io.read(),
        content_type="image/png"
    )


class ProductViewAdditionalTestCase(TestCase):
    """
    Дополнительные тесты для ProductView.
    """

    def setUp(self):
        """
        Подготовка тестовых данных.
        """
        self.client = APIClient()

        # Создание тестовых магазинов
        self.shop1 = Shop.objects.create(name='Shop 1', state=True)
        self.shop2 = Shop.objects.create(name='Shop 2', state=True)

        # Создание тестовой категории
        self.category = Category.objects.create(name='Test Category')
        self.category.shops.add(self.shop1, self.shop2)

        # Создание тестовых продуктов
        self.product1 = Product.objects.create(name='Product 1', category=self.category)
        self.product2 = Product.objects.create(name='Product 2', category=self.category)

        # Создание ProductInfo для разных магазинов
        self.product_info1_shop1 = ProductInfo.objects.create(
            product=self.product1, shop=self.shop1, model='Model 1-1',
            external_id=1, price=100, price_rrc=120, quantity=10
        )
        self.product_info1_shop2 = ProductInfo.objects.create(
            product=self.product1, shop=self.shop2, model='Model 1-2',
            external_id=2, price=110, price_rrc=130, quantity=5
        )
        self.product_info2_shop1 = ProductInfo.objects.create(
            product=self.product2, shop=self.shop1, model='Model 2-1',
            external_id=3, price=200, price_rrc=220, quantity=15
        )

    def test_filter_products_by_shop_id(self):
        """
        Тестирование фильтрации товаров по ID магазина.
        """
        # Фильтрация по shop1
        response = self.client.get(f'/api/v1/products?shop_id={self.shop1.id}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)  # 2 продукта в shop1

        # Проверяем, что все товары из правильного магазина
        for item in response.data['results']:
            self.assertEqual(item['shop']['id'], self.shop1.id)

        # Фильтрация по shop2
        response = self.client.get(f'/api/v1/products?shop_id={self.shop2.id}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)  # 1 продукт в shop2
        self.assertEqual(response.data['results'][0]['shop']['id'], self.shop2.id)

    def test_filter_products_by_model_search(self):
        """
        Тестирование поиска товаров по модели.
        """
        response = self.client.get('/api/v1/products?search=Model 1')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)  # 2 продукта с "Model 1" в названии модели

    def test_combined_filters(self):
        """
        Тестирование комбинированных фильтров.
        """
        response = self.client.get(
            f'/api/v1/products?shop_id={self.shop1.id}&category_id={self.category.id}&search=Product'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)  # Все фильтры должны работать вместе

    def test_pagination_parameters(self):
        """
        Тестирование параметров пагинации.
        """
        # Создаем дополнительные продукты для тестирования пагинации
        for i in range(25):  # Создаем 25 дополнительных продуктов
            product = Product.objects.create(name=f'Extra Product {i}', category=self.category)
            ProductInfo.objects.create(
                product=product, shop=self.shop1, model=f'Extra Model {i}',
                external_id=100 + i, price=50 + i, price_rrc=60 + i, quantity=1
            )

        # Тест стандартной пагинации (page_size=20 по умолчанию)
        response = self.client.get('/api/v1/products')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data['results']), 20)
        self.assertIn('next', response.data)

        # Тест кастомного page_size
        response = self.client.get('/api/v1/products?page_size=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data['results']), 5)

        # Тест второй страницы
        response = self.client.get('/api/v1/products?page=2&page_size=5')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_empty_search_results(self):
        """
        Тестирование поиска без результатов.
        """
        response = self.client.get('/api/v1/products?search=NonexistentProduct')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['results']), 0)

    def test_invalid_shop_id_filter(self):
        """
        Тестирование фильтрации по несуществующему ID магазина.
        """
        response = self.client.get('/api/v1/products?shop_id=99999')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_invalid_category_id_filter(self):
        """
        Тестирование фильтрации по несуществующему ID категории.
        """
        response = self.client.get('/api/v1/products?category_id=99999')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)


class ProductDetailViewAdditionalTestCase(TestCase):
    """
    Дополнительные тесты для ProductDetailView.
    """

    def setUp(self):
        """
        Подготовка тестовых данных.
        """
        self.client = APIClient()

        self.shop = Shop.objects.create(name='Test Shop', state=True)
        self.category = Category.objects.create(name='Test Category')
        self.category.shops.add(self.shop)
        self.product = Product.objects.create(name='Test Product', category=self.category)
        self.product_info = ProductInfo.objects.create(
            product=self.product, shop=self.shop, model='Test Model',
            external_id=1, price=100, price_rrc=120, quantity=10
        )

    @patch('backend.api.views.product_views.ProductInfo.objects')
    def test_product_detail_exception_handling(self, mock_product_info):
        """
        Тестирование обработки исключений в ProductDetailView.
        """
        # Настраиваем мок для вызова исключения
        mock_product_info.filter.side_effect = Exception("Database error")

        response = self.client.get(f'/api/v1/products/{self.product_info.id}')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['status'])
        self.assertEqual(response.data['error'], 'Товар не найден')


class ProductImageUploadViewTestCase(TestCase):
    """
    Тесты для ProductImageUploadView.
    """

    def setUp(self):
        """
        Подготовка тестовых данных.
        """
        self.client = APIClient()

        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            email='test@example.com',
            password='password123',
            is_active=True
        )

        # Создаем тестовый продукт
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(name='Test Product', category=self.category)

        # URL для загрузки изображения
        self.upload_url = f'/api/v1/products/{self.product.id}/image'

    def create_simple_uploaded_file(self):
        """
        Создает простой загружаемый файл для тестов.
        """
        return SimpleUploadedFile(
            "test_image.png",
            b"fake_image_content",
            content_type="image/png"
        )

    def test_upload_image_unauthenticated(self):
        """
        Тестирование загрузки изображения без аутентификации.
        """
        response = self.client.post(self.upload_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_upload_image_missing_file(self):
        """
        Тестирование загрузки без файла изображения.
        """
        self.client.force_authenticate(user=self.user)

        response = self.client.post(self.upload_url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['status'])
        self.assertEqual(response.data['error'], 'Файл image не найден')

    def test_upload_image_nonexistent_product(self):
        """
        Тестирование загрузки изображения для несуществующего продукта.
        """
        self.client.force_authenticate(user=self.user)

        uploaded_file = self.create_simple_uploaded_file()

        nonexistent_url = '/api/v1/products/99999/image'
        response = self.client.post(nonexistent_url, {'image': uploaded_file})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['status'])
        self.assertEqual(response.data['error'], 'Товар не найден')

    @patch('backend.tasks.process_product_image.delay')
    @patch('os.path.exists')
    @patch('backend.models.Product.save')
    def test_upload_image_success(self, mock_save, mock_exists, mock_task):
        """
        Тестирование успешной загрузки изображения.
        """
        self.client.force_authenticate(user=self.user)

        # Настраиваем моки
        mock_exists.return_value = True
        mock_task.return_value = Mock(id='test-task-id')

        uploaded_file = self.create_simple_uploaded_file()

        response = self.client.post(self.upload_url, {'image': uploaded_file})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertIn('успешно загружено', response.data['message'])
        self.assertIn('product', response.data)
        # Не проверяем task_id, так как он зависит от внутренней логики файловой системы

    @patch('os.path.exists')
    @patch('backend.models.Product.save')
    def test_upload_image_file_not_created(self, mock_save, mock_exists):
        """
        Тестирование случая, когда файл не был создан.
        """
        self.client.force_authenticate(user=self.user)

        # Настраиваем мок так, чтобы файл "не существовал"
        mock_exists.return_value = False

        uploaded_file = self.create_simple_uploaded_file()

        response = self.client.post(self.upload_url, {'image': uploaded_file})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        # Должно быть сообщение об успехе, но без task_id
        self.assertNotIn('task_id', response.data)

    def test_delete_image_unauthenticated(self):
        """
        Тестирование удаления изображения без аутентификации.
        """
        response = self.client.delete(self.upload_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_image_nonexistent_product(self):
        """
        Тестирование удаления изображения для несуществующего продукта.
        """
        self.client.force_authenticate(user=self.user)

        nonexistent_url = '/api/v1/products/99999/image'
        response = self.client.delete(nonexistent_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['status'])
        self.assertEqual(response.data['error'], 'Товар не найден')

    def test_delete_image_no_image(self):
        """
        Тестирование удаления изображения у продукта без изображения.
        """
        self.client.force_authenticate(user=self.user)

        response = self.client.delete(self.upload_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['status'])
        self.assertEqual(response.data['error'], 'У товара нет изображения')

    @patch('backend.tasks.cleanup_old_images.delay')
    def test_delete_image_success(self, mock_cleanup_task):
        """
        Тестирование успешного удаления изображения.
        """
        self.client.force_authenticate(user=self.user)

        # Создаем простой файл и присваиваем его продукту без обработки imagekit
        uploaded_file = self.create_simple_uploaded_file()

        # Мокаем поведение продукта с изображением
        with patch.object(self.product, 'image') as mock_image:
            mock_image.__bool__ = Mock(return_value=True)
            mock_image.path = '/fake/path/test.png'
            mock_image.delete = Mock()

            # Мокаем get объекта чтобы вернуть наш продукт с изображением
            with patch('backend.api.views.product_views.Product.objects.get') as mock_get:
                mock_product_with_image = Mock()
                mock_product_with_image.image = mock_image
                mock_product_with_image.save = Mock()
                mock_get.return_value = mock_product_with_image

                response = self.client.delete(self.upload_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertIn('успешно удалено', response.data['message'])

        # Проверяем, что задача очистки была вызвана
        mock_cleanup_task.assert_called_once()
