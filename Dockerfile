FROM python:3.11-slim

WORKDIR /app

# Install curl for health check
RUN apt-get update && apt-get install -y --no-install-recommends curl gcc python3-dev && rm -rf /var/lib/apt/lists/*

# Copy and install requirements with memory-efficient pip options
COPY requirements.txt .
RUN pip install --no-cache-dir --only-binary=:all: -r requirements.txt || pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN addgroup --system app && adduser --system --group app

# Copy application files
COPY . .
RUN mkdir -p data/raw data/processed data/chroma_db && chown -R app:app /app data

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
