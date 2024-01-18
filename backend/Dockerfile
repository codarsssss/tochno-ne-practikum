FROM python:3.9
WORKDIR /app
COPY . .

RUN pip install -r requirements.txt
RUN python manage.py collectstatic --noinput
RUN python manage.py makemigrations recipes
RUN python manage.py makemigrations users

CMD gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000