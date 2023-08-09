"""
Django settings for salmanwahed_com project.

Generated by 'django-admin startproject' using Django 3.2.8.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import os
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

if Path.exists(BASE_DIR.joinpath('.env')):
    load_dotenv(BASE_DIR.joinpath('.env'))
else:
    raise ImproperlyConfigured('.env file not found.')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
if Path.exists(BASE_DIR.joinpath('credentials.txt')):
    DEBUG = True
else:
    DEBUG = False

LOG_DIR = BASE_DIR.joinpath('log')
LOG_FILE = 'salmanwahed_com.log'

if not Path.exists(LOG_DIR):
    raise ImproperlyConfigured('log directory was not found.')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '{levelname} [{asctime}] [{module} {funcName}:{lineno}] {message}',
            'datefmt':'%d-%b-%Y %I:%M:%S %p',
            'style': '{',
        },
        'simple': {
            'format': '{pathname} {funcName}({lineno}): {message}',
            'style': '{',
        }
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': LOG_DIR.joinpath(LOG_FILE),
            'formatter': 'default',
            'level': 'INFO'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'filters': ['require_debug_true'],
            'formatter': 'simple',
            'level': 'DEBUG'
        }
    },
    'loggers': {
        'default': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}

ALLOWED_HOSTS = ['.salmanwahed.com']
if DEBUG:
    ALLOWED_HOSTS.extend(['127.0.0.1', 'localhost'])
else:
    ALLOWED_HOSTS.append('216.127.184.165')

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'debug_toolbar',
    'blog',
    'ckeditor',
    'portfolio'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware'
]

ROOT_URLCONF = 'salmanwahed_com.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'salmanwahed_com.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": "192.168.0.102:11211",
    }
}

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Dhaka'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

STATIC_ROOT = BASE_DIR.joinpath('static')

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

INTERNAL_IPS = [
    "0.0.0.0",
    "127.0.0.1",
]

MEDIA_URL = '/upload/'
MEDIA_ROOT = BASE_DIR.joinpath('upload')

PAGINATION_ITEM_COUNT = 5

CKEDITOR_CONFIGS = {
    'default': {
        'extraAllowedContent': 'script[src]',
        'height': 800,
        'width': 960
    },
}

CDN_URL = os.getenv('CDN_URL')
USE_CDN = os.getenv('USE_CDN', 'FALSE').upper() == 'TRUE'
WPM_READ = int(os.getenv('WPM_READ', 180))

# Sentry SDK
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
  dsn="https://86b26992e18b49449b144b1c7ad1d7e0@o4505572214046720.ingest.sentry.io/4505572215488512",
  integrations=[DjangoIntegration()],

  # Set traces_sample_rate to 1.0 to capture 100%
  # of transactions for performance monitoring.
  # We recommend adjusting this value in production.
  traces_sample_rate=1.0,

  # If you wish to associate users to errors (assuming you are using
  # django.contrib.auth) you may enable sending PII data.
  send_default_pii=True
)