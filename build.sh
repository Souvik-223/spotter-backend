#!/usr/bin/env bash
# Exit on any error
set -o errexit

echo "==> Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Collecting static assets..."
python manage.py collectstatic --no-input

echo "==> Running database migrations..."
python manage.py migrate

echo "==> Ingesting OPIS fuel prices dataset..."
python manage.py load_fuel_data

echo "==> Build completed successfully!"
