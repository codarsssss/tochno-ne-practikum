"""Модуль служебных команд."""

import os
import json
from typing import List, Dict

from django.core.management.base import BaseCommand
from django.conf import settings

from recipes.models import Ingredient


def handle_file_not_found_error(filepath: str) -> None:
    """Обработка ошибки отсутствия файла с выводом сообщения."""
    message = f'Файл {filepath} не найден!'
    print(message)


class Command(BaseCommand):
    """Команда загрузки данных о ингредиентах в БД."""

    def handle(self, *args, **options) -> None:
        """Обработчик команды."""
        json_filepath = os.path.join(settings.BASE_DIR,
                                     'data', 'ingredients.json')
        try:
            json_data = self.read_json_file(json_filepath)
            self.insert_json_data(json_data)
        except FileNotFoundError:
            handle_file_not_found_error(json_filepath)

        self.stdout.write('Данные успешно загружены!')

    def read_json_file(self, filepath: str) -> List[Dict[str, str]]:
        """Чтение данных из JSON файла."""
        try:
            with open(filepath) as json_file:
                return json.load(json_file)
        except FileNotFoundError:
            return None

    def insert_json_data(self, data: List[Dict[str, str]]) -> None:
        """Вставка данных из JSON файла в базу данных."""
        ingredients = [
            Ingredient(name=ingredient['name'],
                       measurement_unit=ingredient['measurement_unit'])
            for ingredient in data
        ]
        Ingredient.objects.bulk_create(ingredients)