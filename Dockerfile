# The front end (frontend/) is built ahead of time with `npm run build` and copied in as
# static files, so the runtime image has no Node: one small Python process.
FROM python:3.12-slim AS build
WORKDIR /w
COPY backend/requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DSA_DB_PATH=/data/dsa-prep.db \
    DSA_SEED_DIR=/app/seed \
    DSA_WEB_DIST=/app/web/dist

COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels fastapi uvicorn \
 && rm -rf /wheels \
 && useradd --system --uid 10001 --no-create-home app

COPY backend/app ./app
COPY backend/seed ./seed
COPY frontend/dist ./web/dist

# Create /data owned by the app user BEFORE declaring the volume. Docker seeds an
# empty named volume from the image path, ownership included; without this the
# volume lands root-owned and an unprivileged container cannot open the database.
RUN mkdir -p /data && chown 10001:10001 /data
VOLUME ["/data"]

USER app
EXPOSE 8080

HEALTHCHECK --interval=60s --timeout=5s --start-period=15s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8080/healthz')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", \
     "--workers", "1", "--no-access-log"]
