"""Модуль с контроллерами приложения Recipes."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError, PermissionDenied, AuthenticationFailed
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from rest_framework import (exceptions, filters, generics, mixins, status,
                            viewsets)
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import APIException
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView, Response

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Author, Follow

from django.contrib.auth import get_user_model
User = get_user_model()
from .pagination import CustomPagination
from .serializers import (CustomUserSerializer, GetRecipeSerializer,
                          IngredientSerializer, PostRecipeSerializer,
                          SubscriptionSerializer, TagSerializer)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user_profile(request):
    """Возвращает данные профиля текущего пользователя."""
    serializer = CustomUserSerializer(request.user)
    return Response(serializer.data)


class TagViewSet(viewsets.ViewSet):
    """Контроллер для получение списка тегов и отдельного тега."""

    def list(self, request):
        """Метод для получения списка тегов."""
        queryset = Tag.objects.all()
        serializer = TagSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """Получает данные определенного тега."""
        queryset = Tag.objects.all()
        tag = get_object_or_404(queryset, pk=pk)
        serializer = TagSerializer(tag)
        return Response(serializer.data)


class CustomUserViewSet(UserViewSet):
    """Контроллер для пользователей."""

    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = CustomPagination

    @action(detail=False, methods=['GET'],
            permission_classes=[IsAuthenticated],
            serializer_class=SubscriptionSerializer)
    def subscriptions(self, request):
        user = request.user
        favorites = user.followers.all()
        users_id = [favorite_instance.author.id for
                    favorite_instance in favorites]
        users = User.objects.filter(id__in=users_id)
        paginated_queryset = self.paginate_queryset(users)
        serializer = self.serializer_class(paginated_queryset, many=True)
        return self.get_paginated_response(serializer.data)


@api_view(['GET'])
def get_current_user(request):
    if not request.user.is_authenticated:
        raise exceptions.AuthenticationFailed(
            {"details": ["Неавторизованный пользователь!"]})

@action(detail=True, methods=('post', 'delete'),
        serializer_class=SubscriptionSerializer)
def subscribe(self, request, id=None):
    user = request.user
    author = get_object_or_404(User, pk=id)
    follow_search = Follow.objects.filter(user=user, author=author)

    if request.method == 'POST':
        if user == author:
            raise exceptions.ValidationError({"details": ['Подписываться на\
                                              себя запрещено.']})
        if follow_search.exists():
            raise exceptions.ValidationError({"details": ['Вы уже подписаны на\
                                              этого пользователя.']})
        Follow.objects.create(user=user, author=author)
        serializer = self.get_serializer(author)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    if request.method == 'DELETE':
        if not follow_search.exists():
            raise exceptions.ValidationError({"details": ['Вы не подписаны на\
                                              этого пользователя.']})
        Follow.objects.filter(user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Контроллер для ингридиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['name']

    def list(self, request, *args, **kwargs):
        """Метод для получения списка ингредиентов."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def get_queryset(self):
        """Возвращает отфильтрованный набор ингредиентов."""
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(Q(name__startswith=search)
                                       | Q(name__istartswith=search))
        return queryset


@api_view(['GET', 'POST', 'PATCH'])
def get_or_create_recipe(request):
    if request.method == 'GET':
        author = request.GET.get('author', None)
        tags = request.GET.getlist('tags')
        queryset = Recipe.objects.all()
        if author:
            queryset = queryset.filter(author=author)
        if tags:
            queryset = queryset.filter(tags__slug__in=tags)
        paginator = CustomPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = GetRecipeSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)
    elif request.method == 'POST':
        try:
            serializer = PostRecipeSerializer(data=request.data,
                                              context={'request': request})
            if serializer.is_valid():
                ingredients_data = request.data.get('ingredients')
                if not ingredients_data:
                    raise ValidationError('Ingredients are required.')

                author, _ = Author.objects.get_or_create(user=request.user)
                recipe = serializer.save(author=author)

                recipe_ingredients = []
                for ingredient_data in ingredients_data:
                    ingredient_id = ingredient_data['id']
                    ingredient_amount = ingredient_data['amount']
                    ingredient, _ = Ingredient.objects.get_or_create(
                        id=ingredient_id)
                    recipe_ingredient = RecipeIngredient.objects.create(
                        recipe=recipe,
                        ingredient=ingredient,
                        amount=ingredient_amount
                    )
                    recipe_ingredients.append(recipe_ingredient)

                ingredient_ids = [ingredient_data['id'] for ingredient_data
                                  in ingredients_data]
                existing_ingredients = Ingredient.objects.filter(
                    id__in=ingredient_ids)
                recipe.ingredients.set(existing_ingredients)

                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'PATCH':
        recipe = get_object_or_404(Recipe, id=request.data.get('recipe_id'))
        serializer = PostRecipeSerializer(recipe, data=request.data,
                                          partial=True)
        if serializer.is_valid():
            serializer.save()
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.data)


@api_view(['GET', 'PATCH'])
def get_recipe_detail(request, pk):
    try:
        recipe = Recipe.objects.get(pk=pk)
    except Recipe.DoesNotExist:
        raise exceptions.NotFound({"details": ["Рецепт не найден!"]})

    if request.method == 'GET':
        serializer = PostRecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'PATCH':
        ingredients = request.data.get('ingredients')
        if not request.user.is_authenticated:
            raise AuthenticationFailed(
                {"details": ["Неавторизованный пользователь!"]})
        if f"{recipe.author}" != f"{request.user}":
            raise PermissionDenied(
                {"details": ["Недостаточно прав для редактирования рецепта!"]})
        if ingredients is None:
            raise ValidationError(
                {"ingredients": ["Поле 'ingredients' является обязательным!"]})
        if not ingredients:
            raise ValidationError(
                {"ingredients": ["Неверный ингредиент!"]})
        ingredients = request.data.get('ingredients')
        for _ in ingredients:
            requst_id = ingredients[0]["id"]
            if Ingredient.objects.get(id=requst_id) is None:
                raise ValidationError({"details": ["Ингредиент не найден!"]})
        if request.data.get('cooking_time') == 0:
            raise ValidationError(
                {"cooking_time": ["Время приготовления обязательно!"]})
        tags = request.data.get('tags', [])
        name_length = Recipe._meta.get_field('name').max_length
        if len(set(ingredient.get('id') for ingredient
                   in ingredients)) != len(ingredients):
            raise ValidationError(
                {"details": ["Ингредиенты не должны повторяться!"]})
        if not tags:
            raise ValidationError(
                {"details": ["Тег обязателен!"]})
        if any(not tag for tag in tags):
            raise ValidationError(
                {"details": ["Имя тега не может быть пустым!"]})
        existing_tags = Tag.objects.all()
        if any(tag not in existing_tags.values_list(
               'id', flat=True) for tag in tags):
            raise ValidationError(
                {"details": ["Неверный или несуществующий тег!"]})
        if len(set(tags)) != len(tags):
            raise ValidationError(
                {"details": ["Теги не должны повторяться!"]})
        if not request.data.get('image'):
            raise ValidationError(
                {"details": ["Изображение обязательно!"]})
        if len(request.data.get('name', '')) > name_length:
            raise ValidationError(
                {"details": [f"Длина имени рецепта не может быть больше {name_length} символов!"]})
        if 'text' not in request.data:
            raise ValidationError(
                {"details": ["Текст обязателен!"]})
        if ingredients:
            invalid_ingredients = [ingredient for ingredient
                                   in ingredients if ingredient.get(
                                       'amount', 0) <= 0]
            if invalid_ingredients:
                raise ValidationError(
                    {"ingredients": ["Значение 'amount' ингредиентов\
                                      должно быть больше 0."]})
        if ingredients:
            existing_ingredient_ids = list(Ingredient.objects.filter(
                id__in=[ingredient.get('id') for ingredient
                        in ingredients]).values_list('id', flat=True))
            missing_ingredient_ids = [ingredient.get('id')
                                      for ingredient in ingredients
                                      if ingredient.get('id') not in
                                      existing_ingredient_ids]
        if missing_ingredient_ids:
            raise ValidationError({"ingredients": ["Несуществующие ингредиенты"]})
        serializer = PostRecipeSerializer(recipe, data=request.data,
                                          partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            raise ValidationError(serializer.errors)
    serializer = PostRecipeSerializer(recipe, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecipeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = GetRecipeSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['id', 'name', 'cooking_time']

    def get_queryset(self):
        is_favorited = self.request.query_params.get('is_favorited')
        is_in_shopping_cart = self.request.query_params.get(
            'is_in_shopping_cart')
        author = self.request.query_params.get('author')
        tags = self.request.query_params.getlist('tags')

        queryset = super().get_queryset()

        if is_favorited:
            queryset = queryset.filter(is_favorited=is_favorited)
        if is_in_shopping_cart:
            queryset = queryset.filter(is_in_shopping_cart=is_in_shopping_cart)
        if author:
            queryset = queryset.filter(author_id=author)
        if tags:
            queryset = queryset.filter(tags__slug__in=tags)

        return queryset
