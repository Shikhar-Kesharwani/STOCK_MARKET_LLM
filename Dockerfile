FROM python:3.11-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim AS production
WORKDIR /app
RUN addgroup --system app && adduser --system --group app
COPY --from=builder /root/.local /home/app/.local
COPY . .
RUN mkdir -p data/raw data/processed data/chroma_db && chown -R app:app /app data
USER app
ENV PATH=/home/app/.local/bin:$PATH
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
CMD uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
