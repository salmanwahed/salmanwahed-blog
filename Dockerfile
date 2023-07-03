FROM python:3.10-slim-bookworm

# Set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1


WORKDIR /app
RUN mkdir "log"

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ../.env .
COPY salmanwahed_com /app/salmanwahed_com

EXPOSE 8080
WORKDIR /app/salmanwahed_com

COPY start_app.sh .
RUN chmod +x start_app.sh
CMD ["./start_app.sh"]
