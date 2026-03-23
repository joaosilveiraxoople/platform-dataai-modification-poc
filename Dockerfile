FROM python:3.11-slim

WORKDIR /app

COPY requirements_batch.txt .
RUN pip install --no-cache-dir -r requirements_batch.txt

COPY app/batch_processing.py .
COPY app/seed_redis.py .

CMD ["python", "batch_processing.py"]
