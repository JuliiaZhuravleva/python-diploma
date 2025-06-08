from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .services.import_service import ImportService


@shared_task
def send_confirmation_email(user_id, token_key):
    """
    Асинхронная задача для отправки email с подтверждением регистрации.

    Args:
        user_id (int): ID пользователя.
        token_key (str): Ключ токена подтверждения.
    """
    from .models import User, ConfirmEmailToken

    try:
        user = User.objects.get(id=user_id)

        send_mail(
            subject='Подтверждение регистрации',
            message=f'Для подтверждения регистрации используйте токен: {token_key}\n'
                    f'Email: {user.email}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except (User.DoesNotExist, ConfirmEmailToken.DoesNotExist):
        # Логирование ошибки
        pass


@shared_task
def send_password_reset_email(user_id, token_key):
    """
    Асинхронная задача для отправки email со ссылкой для сброса пароля.

    Args:
        user_id (int): ID пользователя.
        token_key (str): Ключ токена для сброса пароля.
    """
    from .models import User

    try:
        user = User.objects.get(id=user_id)

        send_mail(
            subject='Сброс пароля',
            message=f'Для сброса пароля перейдите по ссылке: \n'
                    f'http://localhost:8000/api/v1/user/password_reset/confirm?token={token_key}&email={user.email}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except User.DoesNotExist:
        # Логирование ошибки
        pass


@shared_task
def send_order_confirmation_email(order_id):
    """
    Асинхронная задача для отправки email с подтверждением заказа.

    Args:
        order_id (int): ID заказа.
    """
    from .models import Order, OrderItem

    try:
        order = Order.objects.get(id=order_id)
        total_sum = order.get_total_cost()
        items = []

        for item in order.ordered_items.all():
            items.append(
                f"- {item.product_info.product.name}: {item.quantity} шт. x {item.product_info.price} руб. "
                f"= {item.quantity * item.product_info.price} руб."
            )

        message = f"""
        Здравствуйте, {order.user.first_name}!

        Ваш заказ №{order.id} от {order.dt.strftime('%d.%m.%Y %H:%M')} успешно оформлен.

        Состав заказа:
        {"".join(items)}

        Общая сумма заказа: {total_sum} руб.

        Адрес доставки:
        {order.contact.city}, {order.contact.street}, д. {order.contact.house},
        {'корп. ' + order.contact.structure if order.contact.structure else ''}
        {'стр. ' + order.contact.building if order.contact.building else ''}
        {'кв. ' + order.contact.apartment if order.contact.apartment else ''}

        Телефон для связи: {order.contact.phone}

        Спасибо за заказ!
        """

        send_mail(
            subject=f'Подтверждение заказа №{order.id}',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            fail_silently=False,
        )
    except Order.DoesNotExist:
        # Логирование ошибки
        pass


@shared_task
def import_shop_data_task(url, user_id):
    """
    Асинхронная задача для импорта данных магазина из внешнего источника.

    Args:
        url (str): URL источника данных.
        user_id (int): ID пользователя-магазина.

    Returns:
        dict: Результат импорта данных.
    """
    result = ImportService.import_shop_data(url, user_id)
    return result


@shared_task
def process_user_avatar(user_id):
    """
    Асинхронная задача для обработки аватара пользователя.

    Создает дополнительные размеры изображения:
    - thumbnail (50x50) - для списков
    - medium (150x150) - для профиля
    - large (300x300) - для детального просмотра

    Args:
        user_id (int): ID пользователя
    """
    from .models import User
    from PIL import Image
    import os

    try:
        user = User.objects.get(id=user_id)
        if not user.avatar:
            return {'success': False, 'error': 'У пользователя нет аватара'}

        # Проверяем существование файла
        import os
        if not os.path.exists(user.avatar.path):
            return {'success': False, 'error': f'Файл аватара не найден: {user.avatar.path}'}

        # Получаем путь к оригинальному изображению
        avatar_path = user.avatar.path

        # Создаем различные размеры
        sizes = {
            'thumbnail': (50, 50),
            'medium': (150, 150),
            'large': (300, 300)
        }

        generated_files = []

        for size_name, (width, height) in sizes.items():
            # Создаем путь для нового файла
            base_name = os.path.splitext(os.path.basename(avatar_path))[0]
            extension = '.jpg'  # Всегда сохраняем как JPEG для единообразия
            new_filename = f"{base_name}_{size_name}{extension}"
            new_path = os.path.join(os.path.dirname(avatar_path), new_filename)

            # Обрабатываем изображение
            with Image.open(avatar_path) as img:
                # Конвертируем в RGB если нужно
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')

                # Изменяем размер с сохранением пропорций и центрированием
                img.thumbnail((width, height), Image.Resampling.LANCZOS)

                # Создаем новое изображение с нужными размерами и белым фоном
                new_img = Image.new('RGB', (width, height), (255, 255, 255))

                # Вставляем обработанное изображение по центру
                paste_x = (width - img.width) // 2
                paste_y = (height - img.height) // 2
                new_img.paste(img, (paste_x, paste_y))

                # Сохраняем с оптимизацией
                new_img.save(new_path, 'JPEG', quality=85, optimize=True)
                generated_files.append(new_filename)

        return {
            'success': True,
            'user_id': user_id,
            'generated_files': generated_files,
            'message': f'Создано {len(generated_files)} дополнительных размеров аватара'
        }

    except User.DoesNotExist:
        return {'success': False, 'error': 'Пользователь не найден'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@shared_task
def process_product_image(product_id):
    """
    Асинхронная задача для обработки изображения товара.

    Создает дополнительные размеры изображения:
    - thumbnail (100x100) - для списков товаров
    - medium (400x400) - для карточки товара
    - large (800x800) - для детального просмотра

    Args:
        product_id (int): ID товара
    """
    from .models import Product
    from PIL import Image
    import os

    try:
        product = Product.objects.get(id=product_id)
        if not product.image:
            return {'success': False, 'error': 'У товара нет изображения'}

        # Проверяем существование файла
        import os
        if not os.path.exists(product.image.path):
            return {'success': False, 'error': f'Файл изображения товара не найден: {product.image.path}'}
        # Получаем путь к оригинальному изображению
        image_path = product.image.path

        # Создаем различные размеры
        sizes = {
            'thumbnail': (100, 100),
            'medium': (400, 400),
            'large': (800, 800)
        }

        generated_files = []

        for size_name, (width, height) in sizes.items():
            # Создаем путь для нового файла
            base_name = os.path.splitext(os.path.basename(image_path))[0]
            extension = '.jpg'  # Всегда сохраняем как JPEG для единообразия
            new_filename = f"{base_name}_{size_name}{extension}"
            new_path = os.path.join(os.path.dirname(image_path), new_filename)

            # Обрабатываем изображение
            with Image.open(image_path) as img:
                # Конвертируем в RGB если нужно
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')

                # Изменяем размер с сохранением пропорций и центрированием
                img.thumbnail((width, height), Image.Resampling.LANCZOS)

                # Создаем новое изображение с нужными размерами и белым фоном
                new_img = Image.new('RGB', (width, height), (255, 255, 255))

                # Вставляем обработанное изображение по центру
                paste_x = (width - img.width) // 2
                paste_y = (height - img.height) // 2
                new_img.paste(img, (paste_x, paste_y))

                # Сохраняем с оптимизацией
                new_img.save(new_path, 'JPEG', quality=85, optimize=True)
                generated_files.append(new_filename)

        return {
            'success': True,
            'product_id': product_id,
            'generated_files': generated_files,
            'message': f'Создано {len(generated_files)} дополнительных размеров изображения товара'
        }

    except Product.DoesNotExist:
        return {'success': False, 'error': 'Товар не найден'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_old_images(file_path):
    """
    Асинхронная задача для удаления старых изображений и их миниатюр.

    Args:
        file_path (str): Путь к основному файлу
    """
    import os
    import glob

    try:
        if os.path.exists(file_path):
            # Удаляем основной файл
            os.remove(file_path)

            # Удаляем все связанные миниатюры
            base_name = os.path.splitext(file_path)[0]
            pattern = f"{base_name}_*.*"

            for thumbnail_file in glob.glob(pattern):
                if os.path.exists(thumbnail_file):
                    os.remove(thumbnail_file)

            return {'success': True, 'message': 'Файлы успешно удалены'}
        else:
            return {'success': False, 'error': 'Файл не найден'}

    except Exception as e:
        return {'success': False, 'error': str(e)}