# salmanwahed-blog

![Django CI](https://github.com/salmanwahed/salmanwahed-blog/actions/workflows/django-ci.yml/badge.svg)

Personal blog and portfolio website — [salmanwahed.com](https://salmanwahed.com)

Built with Django, PostgreSQL, and Redis.

## Running Locally with Docker

```bash
cp .env.example .env        # fill in DJANGO_SECRET_KEY and DB_* values
docker compose up --build   # starts web (port 8000), postgres, redis
```

Migrations run automatically on container start. Admin is at `http://localhost:8000/nimda/dehawnamlas/`.

## Tech Stack

- **Backend**: Django 4.2, Gunicorn
- **Database**: PostgreSQL
- **Cache**: Redis
- **Frontend**: Django templates, Django Compressor. No CSS framework and no
  jQuery — roughly 1,200 lines of hand-written CSS and one 27-line theme script.
- **Editor**: Markdown (python-markdown + Pygments), edited with EasyMDE in the admin
- **Production**: Nginx reverse proxy, Sentry for error tracking

> Django itself is not pinned in `requirements.txt` — it is installed
> transitively by `django-compressor`. Worth pinning at some point.

## Writing Posts

Posts are Markdown. Each post carries a **Body Format** field:

- **Markdown** (default for new posts) — fenced code blocks get syntax
  highlighting that follows the light/dark theme.
- **HTML (legacy)** — posts written in CKEditor before the switch. They render
  from their original HTML and were never converted. To move one over, rewrite
  the body in Markdown and flip the field.

The admin body field becomes an EasyMDE editor (fullscreen, side-by-side live
preview, code-block button) when the format is Markdown, and stays a plain
textarea for HTML posts.

## Front-end Assets

| Path | Purpose |
|---|---|
| `templates/base.html` | Single shared base for both apps |
| `templates/partials/` | Nav and footer |
| `assets/css/base.css` | Design tokens, reset, nav, footer, tags, buttons |
| `assets/css/code.css` | Pygments syntax colours, light + dark |
| `assets/fonts/` | Self-hosted WOFF2 — no third-party font request |
| `assets/js/theme.js` | Dark/light toggle, persisted to `localStorage` |
| `assets/vendor/` | EasyMDE, admin only |

`assets/` is on `STATICFILES_DIRS`; `static/` remains `STATIC_ROOT`.

To regenerate `code.css` after a Pygments upgrade:

```bash
python -c "from pygments.formatters import HtmlFormatter; print(HtmlFormatter(style='friendly').get_style_defs('.codehilite'))"
```

Dark rules are the same output from `style='github-dark'`, each line prefixed
with `[data-theme="dark"] `.
