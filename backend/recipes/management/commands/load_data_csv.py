"""Модуль служебных команд."""

import os
import csv
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
        csv_filepath = os.path.join(settings.BASE_DIR,
                                    'data', 'ingredients.csv')
        try:
            csv_data = self.read_csv_file(csv_filepath)
            self.insert_csv_data(csv_data)
        except FileNotFoundError:
            handle_file_not_found_error(csv_filepath)

        self.stdout.write('Данные успешно загружены!')

    def read_csv_file(self, filepath: str) -> List[Dict[str, str]]:
        """Чтение данных из CSV файла."""
        try:
            with open(filepath, 'r') as csv_file:
                reader = csv.reader(csv_file, delimiter=',', quotechar='"')
                next(reader)
                return [{'name': row[0], 'unit': row[1]} for row in reader]
        except FileNotFoundError:
            return None

    def insert_csv_data(self, data: List[Dict[str, str]]) -> None:
        """Вставка данных из CSV файла в базу данных."""
        for row in data:
            db = Ingredient(
                name=row['name'],
                measurement_unit=row['unit']
            )
            db.save()