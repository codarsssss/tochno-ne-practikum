from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from users.models import Author

User = get_user_model()


class Tag(models.Model):
    """Модель тегов для рецептов."""

    name = models.CharField('Название', max_length=200, unique=True)
    # длины полей вынести в константы
    color = models.CharField('Цветовой HEX-код', max_length=7, unique=True)
    # библиотека django-colorfield
    slug = models.SlugField('Адрес', max_length=200, unique=True)

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    measurement_unit = models.CharField(max_length=50)

    # уникальность ингридиентов

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def get_amount(self):
        recipe_ingredient = self.recipe_ingredients.first()
        if recipe_ingredient:
            return recipe_ingredient.amount
        return None

    def __str__(self):
        return self.name

    def get_id(self):
        return self.id


class Recipe(models.Model):
    author = models.ForeignKey(Author, on_delete=models.CASCADE, verbose_name='Автор рецепта', related_name='recipes')
    name = models.CharField(max_length=200, verbose_name='Картинка')
    image = models.ImageField(upload_to='recipes/', verbose_name='Картинка')
    text = models.TextField(verbose_name='Описание')
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredient', verbose_name='Ингредиент')
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    cooking_time = models.PositiveIntegerField(
        'Время приготовления в минутах',
        validators=[
            MinValueValidator(1, message='Минимальное время приготовления - 1 минута.'),
            MaxValueValidator(360, message='Максимальное время приготовления - 6 часов.')
        ]
    )
    created = models.DateTimeField('Время создания', auto_now_add=True, db_index=True)
    is_favorited = models.BooleanField(default=False)
    is_in_shopping_cart = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, related_name='recipe_ingredients', on_delete=models.CASCADE, verbose_name='Рецепт')
    ingredient = models.ForeignKey(Ingredient, related_name='recipe_ingredients', on_delete=models.CASCADE, verbose_name='Ингредиент')
    amount = models.IntegerField('Количество', validators=[MinValueValidator(1, message='Минимальное количество ингредиентов 1.')])

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'

    def __str__(self):
        return f'{self.ingredient.name} - {self.amount} {self.ingredient.measurement_unit}'


class Favorite(models.Model):
    """Модель для избранных рецептов."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='user_favorites',
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe_favorites',
        on_delete=models.CASCADE,
        verbose_name='Рецепты'
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'Favorite >>> Пользователь {self.user.username} - рецепт {self.recipe.name}'


class ShoppingCart(models.Model):
    """Модель для списка покупок пользователя."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='user_shopping_cart',
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe_shopping_cart',
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        return f'ShoppingCart >>> Пользователь {self.user.username} - рецепт {self.recipe.name}'