FROM python:3.12-slim

WORKDIR /backend

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY worker/app/ ./app/

ENV PYTHONPATH=/backend:/app

EXPOSE 8000

CMD ["celery", "-A", "app.celery_app", "worker", "--loglevel=info", "--concurrency=4"]
