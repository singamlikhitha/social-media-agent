FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for psycopg2 and ffmpeg for video generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

# Create uploads directory
RUN mkdir -p uploads

# Cloud Run uses PORT env var
ENV PORT=8080

EXPOSE 8080

CMD exec uvicorn app.main:app --host 0.0.0.0 --port $PORT
