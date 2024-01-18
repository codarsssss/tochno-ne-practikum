from django.urls import include, path

from rest_framework.routers import DefaultRouter

from .views import (IngredientViewSet, TagViewSet, get_or_create_recipe,
                    current_user_profile, get_recipe_detail, RecipeViewSet, CustomUserViewSet)


app_name = 'api'


router = DefaultRouter()

router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('users', CustomUserViewSet, basename='users')

urlpatterns = [
    path('users/me/', current_user_profile, name='current_user_profile'),
    path('recipes/', get_or_create_recipe, name='get_or_create_recipe'),
    path('recipes/<int:pk>/', get_recipe_detail, name='get_recipe_detail'),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken'))
]