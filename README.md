# salmanwahed-blog

![Django CI](https://github.com/salmanwahed/salmanwahed-blog/actions/workflows/django-ci.yml/badge.svg)
[![codecov](https://codecov.io/gh/salmanwahed/salmanwahed-blog/branch/master/graph/badge.svg)](https://codecov.io/gh/salmanwahed/salmanwahed-blog)

Personal blog and portfolio website — [salmanwahed.com](https://salmanwahed.com)

Built with Django 3.2, PostgreSQL, and Redis.

## Running Locally with Docker

```bash
cp .env.example .env        # fill in DJANGO_SECRET_KEY and DB_* values
docker compose up --build   # starts web (port 8000), postgres, redis
```

Migrations run automatically on container start. Admin is at `http://localhost:8000/nimda/dehawnamlas/`.

## Tech Stack

- **Backend**: Django 3.2, Gunicorn
- **Database**: PostgreSQL
- **Cache**: Redis
- **Frontend**: Django templates, Django Compressor
- **Editor**: CKEditor (rich text for blog posts)
- **Production**: Nginx reverse proxy, Sentry for error tracking
