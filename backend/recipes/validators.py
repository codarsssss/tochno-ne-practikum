"""Модуль содержит функции для валидации данных."""

from django.core.exceptions import ValidationError


def validate_cooking_time(value) -> None:
    """Проверяет время приготовления."""
    if value < 1:
        raise ValidationError('Минимальное значение 1.')
    if value > 360:
        raise ValidationError('Максимальное значение 360.')


def validate_positive_integer(value) -> None:
    """Проверяет целое положительное число."""
    if value < 1:
        raise ValidationError('Минимальное значение 1.')