"""Модуль с настройками приложения Users."""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Настройки приложения Users."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    verbose_name = 'Управление пользователями'
