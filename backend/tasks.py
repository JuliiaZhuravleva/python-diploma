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
