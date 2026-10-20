# CareCore production image: Django + gunicorn, static files via WhiteNoise, SQLite on a volume.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CARECORE_DEBUG=false \
    CARECORE_DB_PATH=/data/db.sqlite3 \
    CARECORE_MEDIA_ROOT=/data/media

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# collectstatic needs a key at build time only; the real one comes from the environment at runtime.
RUN CARECORE_SECRET_KEY=build-only python manage.py collectstatic --noinput

RUN useradd --create-home carecore \
    && mkdir -p /data \
    && chown -R carecore /data
USER carecore

VOLUME ["/data"]
EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["gunicorn", "carecore.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-"]
