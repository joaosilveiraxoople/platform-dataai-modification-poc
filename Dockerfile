FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir redis

COPY app/batch_processing.py .
COPY app/seed_redis.py .
COPY app/seed_redis_extended.py .

CMD ["python", "batch_processing.py"]
