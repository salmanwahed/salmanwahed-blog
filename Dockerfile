FROM python:3.10-alpine
WORKDIR /app

COPY ../requirements.txt .
COPY ../.env .
RUN pip install --no-cache-dir -r requirements.txt

COPY ../salmanwahed_com /app/salmanwahed_com

WORKDIR /app/salmanwahed_com

RUN python manage.py collectstatic
RUN python manage.py migrate

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "salmanwahed_com.wsgi"]
