#!/bin/sh

# Execute the first command
#python manage.py collectstatic

# Execute the second command
python manage.py migrate

# Run App
python manage.py runserver 0.0.0.0:8080