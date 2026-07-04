# syntax=docker/dockerfile:1
FROM python:3.11-slim

# System deps: build tools for Prophet/LightGBM, and curl for healthchecks.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential curl fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default: run the ETL pipeline then build model artifacts.
CMD ["python", "-m", "realestate.pipeline"]
