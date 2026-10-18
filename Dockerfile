# syntax=docker/dockerfile:1
FROM node:22-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY web/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 DATA_DIR=/data WEB_DIR=/app/web/dist \
    DATABASE_URL=sqlite:////data/holdover.db TZ=America/Los_Angeles
WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
COPY alembic.ini ./
RUN pip install ".[postgres]" && useradd --system --uid 10001 holdover && mkdir -p /data && chown holdover /data
COPY --from=web /web/dist ./web/dist
USER holdover
VOLUME /data
EXPOSE 8000
# Single worker on purpose: the scheduler runs in-process.
CMD ["sh", "-c", "python -m app.cli migrate && python -m app.cli seed && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
