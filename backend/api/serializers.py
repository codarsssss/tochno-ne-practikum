from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError
from djoser.serializers import UserCreateSerializer, UserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import exceptions, serializers, status
from rest_framework.exceptions import NotAuthenticated
from .pagination import CustomPagination
from rest_framework.views import APIView, Response
from rest_framework.exceptions import ValidationError, PermissionDenied, AuthenticationFailed, NotFound

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Author, Follow

User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    """Сериализатор для автора рецепта."""

    email = serializers.EmailField(source='user.email')
    id = serializers.IntegerField(source='user.id')
    username = serializers.CharField(source='user.username')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    is_subscribed = serializers.BooleanField(source='user.is_subscribed')

    class Meta:
        """Мета-класс."""

        model = Author
        fields = ['email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed']


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя эндпоинтов users."""

    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        """Мета-класс."""

        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed')

    def get_is_subscribed(self, obj):
        """Получение подписки."""
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, author=obj.id).exists()


class CustomUserCreateSerializer(UserCreateSerializer):
    """Сериализатор для пользователя"""

    class Meta:
        """Мета-класс."""

        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'password')


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор сокращенного рецепта"""

    class Meta:
        """Мета-класс."""
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписок."""

    recipes = ShortRecipeSerializer(many=True, read_only=True)
    recipes_count = serializers.SerializerMethodField(read_only=True)
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()

    def get_is_subscribed(self, obj):
        return True

    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes',
                  'recipes', 'recipes_count')


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов"""

    class Meta:
        """Мета-класс."""

        model = Tag
        fields = ['id', 'name', 'color', 'slug']


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингридиентов"""

    class Meta:
        """Мета-класс."""

        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериалайзер для получения данных о ингриденте в рецепте"""

    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    measurement_unit = serializers.SerializerMethodField()
    amount = serializers.SerializerMethodField()

    class Meta:
        """Мета-класс."""

        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']

    def get_id(self, obj):
        """Возвращает идентификатор ингридиента."""
        return obj.id

    def get_name(self, obj):
        """Возвращает название ингридиента."""
        return obj.name

    def get_measurement_unit(self, obj):
        """Возвращает меру измерения ингридиента."""
        return obj.measurement_unit
    
    def get_amount(self, obj):
        """Возвращает количество ингридиента в рецепте."""
        return obj.get_amount()


class GetIngredientRecipeSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer()

    class Meta:
        model = RecipeIngredient
        fields = ('ingredient', 'amount')

    def get_ingredient_id(self, obj):
        """Возвращает id ингредиента"""
        return obj.ingredient.id

    def get_ingredient_name(self, obj):
        """Возвращает название ингредиента"""
        return obj.ingredient.name


class ShortIngredientSerializerForRecipe(serializers.ModelSerializer):
    """Сериализатор ингридиента для создании рецепта."""
    
    id = serializers.IntegerField()
    amount = serializers.SerializerMethodField()
    
    class Meta:
        """Мета-класс."""

        model = Ingredient
        fields = ('id', 'amount')
    
    def get_amount(self, obj):
        """Метод для получения значения атрибута 'amount'."""
        return obj.get_amount()


class GetRecipeSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = RecipeIngredientSerializer(many=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    pagination_class = CustomPagination

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time', 'measurement_unit')
    
    def get_measurement_unit(self, obj):
        return obj.measurement_unit
     
    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(user=request.user,
                                       recipe=obj.id).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request is None or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=request.user,
                                           recipe=obj.id).exists()
    
    def validate(self, attrs):
        recipe_id = self.context['request'].query_params.get('id')
        if recipe_id is None:
            raise ValidationError('Поле id обязательно')
        return attrs


class PostRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для обработки POST запроса на создание рецепта"""

    author = AuthorSerializer(read_only=True)
    ingredients = ShortIngredientSerializerForRecipe(read_only=True,
                                                     many=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True)
    cooking_time = serializers.IntegerField(required=True)
    image = Base64ImageField(required=True)

    class Meta:
        """Мета-класс."""
        model = Recipe
        fields = (
            'id', 'tags', 'author',  'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time')

    def validate_ingredients(self, ingredients):
        """Проверка наличия ингридиента в запросе"""
        if not ingredients:
            raise ValidationError('Должен быть хотя бы один ингредиент.')
        return ingredients

    def validate_tags(self, tags):
        """Проверка наличия тега в запросе"""
        if not tags:
            raise ValidationError('Должен быть хотя бы один тег.')
        return tags

    def validate_cooking_time(self, value):
        """Проверяет, что поле cooking_time больше или равно 1"""
        if value < 1:
            raise ValidationError("Поле cooking_time должно\
                                   быть больше или равно 1")
        return value

    def get_author(self, obj):
        """Получение автора"""
        return self.context['request'].user
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['tags'] = TagSerializer(instance.tags.all(),
                                               many=True).data
        representation['ingredients'] = RecipeIngredientSerializer(
            instance.ingredients.all(), many=True).data
        return representation