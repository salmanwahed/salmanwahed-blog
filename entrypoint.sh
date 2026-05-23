#!/bin/sh
set -e

python salmanwahed_com/manage.py migrate --no-input

exec "$@"
