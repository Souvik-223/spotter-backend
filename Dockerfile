# ==============================================================================
# Production Dockerfile for Spotter Fuel Route Planner Backend
# ==============================================================================

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Collect static assets & pre-seed SQLite database with fuel stations
RUN python manage.py collectstatic --noinput \
    && python manage.py migrate \
    && python manage.py load_fuel_data

EXPOSE 8000

# Start Uvicorn ASGI server
CMD ["sh", "-c", "uvicorn spotter_fuel.asgi:application --host 0.0.0.0 --port ${PORT}"]
