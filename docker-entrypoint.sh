#!/bin/sh
# Apply migrations (this also provisions role permission groups) before starting the server.
set -e

python manage.py migrate --noinput

exec "$@"
