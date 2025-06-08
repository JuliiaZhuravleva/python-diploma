def activate_user(backend, user, response, *args, **kwargs):
    """
    Активирует пользователя после успешной социальной авторизации
    """
    if user and not user.is_active:
        user.is_active = True
        user.save()
        print(f"Пользователь {user.email} активирован через {backend.name}")
    return {'user': user}
