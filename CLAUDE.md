# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal blog and portfolio website built with Django 4.2 (unpinned in
`requirements.txt` -- it arrives transitively via django-compressor). The Django project root is `salmanwahed_com/` (one level below the repo root).

## Running Locally with Docker

```bash
cp .env.example .env        # fill in DJANGO_SECRET_KEY and DB_* values
docker compose up --build   # starts web (port 8000), postgres, redis
```

Migrations run automatically on container start via `entrypoint.sh`. Admin is at `http://localhost:8000/nimda/dehawnamlas/`.

## Common Commands

All `manage.py` commands run from `salmanwahed_com/`:

```bash
cd salmanwahed_com
python manage.py runserver          # Start dev server
python manage.py migrate            # Apply migrations
python manage.py makemigrations     # Create migrations after model changes
python manage.py collectstatic      # Collect static files for production
python manage.py shell_plus         # Interactive shell (ipython)
```

Run tests with Docker:

```bash
docker compose run --rm web python salmanwahed_com/manage.py test blog portfolio
```

## Test Coverage

**coverage.py** is configured in `pyproject.toml` (`[tool.coverage.*]`), measuring
`blog` and `portfolio` with branch coverage on. Migrations, `apps.py` and the test
modules themselves are excluded; `fail_under = 80` makes the report exit non-zero
below that.

Run from the **repo root** — coverage only reads `pyproject.toml` from the current
directory, and `PYTHONPATH` is what lets `manage.py` resolve its imports from there:

```bash
PYTHONPATH=salmanwahed_com coverage run salmanwahed_com/manage.py test blog portfolio && coverage report
```

`pip install -r requirements-dev.txt` installs it. The `[toml]` extra matters: on
Python 3.8 there is no stdlib `tomllib`, and without `tomli` coverage silently
ignores its configuration instead of erroring.

## Linting and Formatting

**ruff** is configured in `pyproject.toml` (Python 3.8 target, line length 119).

```bash
pip install -r requirements-dev.txt   # install ruff locally (one-time)
ruff format salmanwahed_com/          # auto-format
ruff check salmanwahed_com/ --fix     # lint + auto-fix
ruff check salmanwahed_com/           # lint only
```

A **git pre-commit hook** (`.git/hooks/pre-commit`) runs `ruff format` then `ruff check` on staged Python files automatically. It soft-skips if ruff is not installed. Install ruff with `pip install -r requirements-dev.txt` to activate it.

The `/lint` Claude Code skill runs the full format + check cycle interactively.

## Architecture

### Django Apps

**`blog/`** — Main app mounted at `/`:
- `BlogPost`: Posts with slug, Markdown body (`body_format` is `MD` or `HTML`; legacy CKEditor posts stay HTML), hero/thumbnail images, tags, `DRAFT`/`PUBLISHED` status, visit/clap counters
- `BlogImages`: Stores images with CDN URL support and compression metadata; type is `HERO`, `THUMBNAIL`, or `BASIC`
- `Tag`: Tags with name, Bengali name, and color code
- `templatetags/blog_extras.py`: `render_body` (branches on `body_format`; Markdown via python-markdown + Pygments) and `minutes_to_read` (BeautifulSoup over the rendered HTML, 180 WPM default, overridable via `WPM_READ`)

**`portfolio/`** — Mounted at `/portfolio/`:
- `Project`: With type (`MOBILE_APP`/`WEB_APP`), status (`LIVE`/`ONGOING`/`CLOSED`), `category` (`PROFESSIONAL`/`PERSONAL`, which splits the projects page), `role`/`period`/`is_featured` for the featured card, and `weight` for ordering
- `ProjectStat`: Headline numbers on a featured card, edited as an admin inline
- `AppPrivacyPolicy`: Privacy policy docs for mobile apps, served at `/portfolio/app/privacy-policy/<slug>/`
- `Tag`: Tech/skill tags with external URLs (separate from blog tags)

### URL Structure

| URL | View | Notes |
|-----|------|-------|
| `/` | `blog_home` | Paginated post list, cached 15 min |
| `/post/<id>/<slug>/` | `post_detail` | Cached |
| `/posts/tagged/<tag>/` | `tagged_posts` | Cached |
| `/post/preview/<id>` | `post_preview` | Login required, draft preview |
| `/about/` | `AboutView` | Cached 1 hr |
| `/clear-cache/` | `clear_cache` | Login required, flushes Redis |
| `/portfolio/` | `ProjectListView` | Cached 45 min, split professional/personal |
| `/resume/` | `ResumeView` | Cached 1 hr, content hardcoded in template |
| `/contact/` | `ContactView` | **Never cached** (CSRF), honeypot + per-IP throttle |
| `/nimda/dehawnamlas/` | Django admin | Obfuscated admin URL |

### Configuration

**Debug mode** is controlled by the presence of `credentials.txt` in `BASE_DIR` (not by an environment variable directly). Settings read `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` from environment for PostgreSQL, and `CDN_URL` / `USE_CDN` for optional CDN image serving.

**Caching**: Redis at `redis://127.0.0.1:6379`. Views use per-view cache decorators with varying TTLs. Clear via `/clear-cache/` (login required) or `python manage.py shell` + `cache.clear()`.

**Static/Media**: Shared front-end assets live in `BASE_DIR/assets` (on `STATICFILES_DIRS`); `BASE_DIR/static` is `STATIC_ROOT` (collectstatic output); media uploads at `BASE_DIR/upload`. Django Compressor concatenates base.css + code.css + both app stylesheets into a single bundle.

**Templates**: One shared `templates/base.html` with `templates/partials/_nav.html` and `_footer.html`. Views pass an `active` context var so the nav can mark the current page. There is no Bootstrap, jQuery or Font Awesome -- do not reintroduce their classes.

**Logging**: File-based to `log/salmanwahed_com.log`; console output added in DEBUG mode. Sentry SDK active in production.

### Production Stack

- **Gunicorn**: Two worker processes (`web1` on port 9001, `web2` on port 9002), each with 3 workers
- **Nginx**: Reverse proxy with load balancing between the two Gunicorn instances; serves static and media files directly
- **Systemd**: Services defined in `deployment/gunicorn/web1.service` and `web2.service`

Deployment steps are documented in `deployment/instructions.txt`.
