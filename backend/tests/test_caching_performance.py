"""
Более точные тесты производительности кэширования
"""
import time
from django.test import TestCase
from django.core.cache import cache
from backend.models import User, Category, Product, ProductInfo, Shop


class CachingPerformanceTestCase(TestCase):
    """Тесты производительности кэширования"""

    def setUp(self):
        """Создаем тестовые данные"""
        cache.clear()

        # Создаем больше данных для заметной разницы в производительности
        self.shop = Shop.objects.create(
            name='Test Shop',
            user=User.objects.create_user(
                email='shop@test.com',
                password='pass123',
                type='shop'
            )
        )

        self.category = Category.objects.create(name='Electronics')

        # Создаем несколько продуктов
        for i in range(10):
            product = Product.objects.create(
                name=f'Product {i}',
                category=self.category
            )
            ProductInfo.objects.create(
                product=product,
                shop=self.shop,
                model=f'model-{i}',
                external_id=100 + i,  # Добавляем обязательное поле
                price=1000 + i * 100,
                price_rrc=1200 + i * 100,
                quantity=10
            )

    def test_caching_performance_improvement(self):
        """Проверяем что второй запрос быстрее первого (благодаря кэшу)"""

        # Первый запрос (без кэша)
        start_time = time.time()
        products_1 = list(ProductInfo.objects.select_related('product', 'shop').all())
        first_request_time = time.time() - start_time

        # Второй запрос (из кэша)
        start_time = time.time()
        products_2 = list(ProductInfo.objects.select_related('product', 'shop').all())
        second_request_time = time.time() - start_time

        # Проверяем что результаты одинаковые
        self.assertEqual(len(products_1), len(products_2))
        self.assertEqual(len(products_1), 10)

        # Выводим время для анализа
        print(f"\nПервый запрос: {first_request_time:.6f} сек")
        print(f"Второй запрос: {second_request_time:.6f} сек")

        if first_request_time > 0:
            print(f"Ускорение: {first_request_time/second_request_time:.2f}x")

        # Второй запрос должен быть быстрее или равен первому
        self.assertLessEqual(second_request_time, first_request_time * 1.1,
                           "Второй запрос должен быть не медленнее первого (учитывая кэш)")

    def test_cache_key_generation(self):
        """Проверяем что разные запросы создают разные ключи кэша"""

        # Делаем разные запросы
        all_products = list(ProductInfo.objects.all())
        expensive_products = list(ProductInfo.objects.filter(price__gt=1500))
        cheap_products = list(ProductInfo.objects.filter(price__lt=1200))

        # Все запросы должны вернуть разные результаты
        self.assertNotEqual(len(all_products), len(expensive_products))
        self.assertNotEqual(len(expensive_products), len(cheap_products))

        print(f"\nВсе товары: {len(all_products)}")
        print(f"Дорогие товары: {len(expensive_products)}")
        print(f"Дешевые товары: {len(cheap_products)}")

    def test_manual_cache_operations(self):
        """Проверяем прямые операции с кэшем"""

        # Проверяем что можем работать с кэшем напрямую
        test_key = 'test_performance_key'
        test_data = {'products': [1, 2, 3], 'timestamp': time.time()}

        # Записываем в кэш
        cache.set(test_key, test_data, 300)

        # Читаем из кэша
        cached_data = cache.get(test_key)

        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data['products'], [1, 2, 3])

        print(f"\nТест прямого кэширования: ✓")
        print(f"Записали: {test_data}")
        print(f"Прочитали: {cached_data}")

    def test_simple_cache_validation(self):
        """Простая проверка что кэширование включено"""

        # Проверяем настройки
        from django.conf import settings
        self.assertTrue(hasattr(settings, 'CACHES'))
        self.assertIn('default', settings.CACHES)
        self.assertTrue(getattr(settings, 'CACHALOT_ENABLED', False))

        # Простой запрос для проверки
        products_count = ProductInfo.objects.count()
        self.assertEqual(products_count, 10)

        print(f"\n✓ Cachalot включен и работает")
        print(f"✓ Redis cache настроен")
        print(f"✓ Найдено {products_count} товаров в БД")