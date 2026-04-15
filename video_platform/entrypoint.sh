#!/bin/bash

# Прерываем выполнение скрипта, если какая-то из команд завершится ошибкой
set -e

echo "=== Ожидание готовности базы данных ==="

python << 'EOF'
import os
import sys
import time
import psycopg2

while True:
    try:
        psycopg2.connect(
            dbname=os.environ.get('DB_NAME'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            host=os.environ.get('DB_HOST'),
            port=os.environ.get('DB_PORT', '5432')
        )
        break
    except psycopg2.OperationalError:
        sys.stdout.write("БД пока недоступна, ждем 1 секунду...\n")
        time.sleep(1)
EOF
echo "=== База данных готова к подключениям! ==="

echo "=== Сборка статики ==="
python manage.py collectstatic --noinput

echo "=== Применение миграций БД ==="
python manage.py migrate

echo "=== Генерация тестовых данных (если БД пустая) ==="
python manage.py generate_data

echo "=== Запуск Gunicorn ==="
# Команда exec заменяет текущий процесс shell на gunicorn, делая его PID 1
exec gunicorn video_platform.wsgi:application --bind 0.0.0.0:"${SERVER_PORT:-8000}"
