"""Модуль административной панели моделей приложения Users."""

from django.contrib import admin

from .models import Follow, User


class UserAdmin(admin.ModelAdmin):
    """Административная модель для пользователей."""

    list_display = ['email', 'username', 'first_name', 'last_name']
    list_filter = ['email', 'username', 'first_name', 'last_name']


class AuthorAdmin(admin.ModelAdmin):
    """Административная модель для авторов."""

    list_display = ['user']


class FollowAdmin(admin.ModelAdmin):
    """Административная модель для подписок."""

    list_display = ['user', 'author', 'created_at']
    list_filter = ['user', 'author']


admin.site.register(User, UserAdmin)
admin.site.register(Follow, FollowAdmin)
