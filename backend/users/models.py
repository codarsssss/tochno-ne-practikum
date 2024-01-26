from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import UniqueConstraint


class User(AbstractUser):
    ''' Кастомная модель пользователя.
    email используется в качестве уникального идентификатора.
    При создании пользователя все поля обязательны для заполнения
    '''

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = [
        'username',
        'first_name',
        'last_name',
    ]

    email = models.EmailField('email address', max_length=255, unique=True)

    class Meta:

        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['id']

    def __str__(self):
        return self.username


class Subscribe(models.Model):
    ''' Модель для подписок пользователей '''

    user = models.ForeignKey(to=User, verbose_name="Подписчик", on_delete=models.CASCADE, related_name='subscriber')
    author = models.ForeignKey(to=User, verbose_name="Автор", on_delete=models.CASCADE, related_name='subscribing')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['id']
        constraints = [
            UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subscription'
            )
        ]
