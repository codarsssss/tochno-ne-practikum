"""Модуль с моделями приложения Users."""

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Модель пользователя приложения Foodgram."""

    email = models.EmailField('емайл', max_length=254, unique=True)
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    is_subscribed = models.BooleanField(default=False)
    subscriptions = models.ManyToManyField('Author', through='Follow',
                                           related_name='subscribers',
                                           verbose_name='Подписки')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        """Мета-класс."""

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        """Возвращает строковое представление пользователя."""
        return self.email


class Author(models.Model):
    """Модель автора рецептов."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                primary_key=True,
                                related_name='author_recipes')

    def __str__(self):
        """Возвращает строковое представление автора."""
        return self.user.email

    class Meta:
        """Мета-класс."""

        verbose_name = 'Автор'
        verbose_name_plural = 'Авторы'


class Follow(models.Model):
    """Модель подписки пользователя на автора рецепта."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='follows',
                             verbose_name='Подписчик')
    author = models.ForeignKey(Author, on_delete=models.CASCADE,
                               related_name='followers',
                               verbose_name='Автор')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Мета-класс."""

        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_user_author')]

    def __str__(self):
        """Возвращает строковое представление подписки."""
        return f'{self.user} подписан на {self.author}'
