import os
from pathlib import Path

from django.utils.translation import gettext_lazy as _
from environ import Env

BASE_DIR = Path(__file__).resolve().parent.parent
DOTENV_FILE_NAME = os.environ.get("DOTENV_FILE_NAME", ".env")

env = Env()
env.read_env(os.path.join(BASE_DIR, DOTENV_FILE_NAME))

SECRET_KEY = 'django-insecure-*6qn_(%hgzm8rg)ro-)rs3tvnkzwvl15%9+kh+45vvn3az6uo5'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_extensions',
    'rest_framework',
    'rest_framework.authtoken',
    'django_drf_otp',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'django_drf_otp.urls'

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

WSGI_APPLICATION = 'core.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": env("DB_HOST"),
        "USER": env("DB_USER"),
        "PASSWORD": env("DB_PASSWORD"),
        "NAME": env("DB_NAME"),
        "PORT": env("DB_PORT", cast=int, default=5432),
    }
}

LANGUAGES = [
    ("tr", _("Turkish")),
    ("en", _("English")),
]

LOCALE_PATHS = [
    BASE_DIR / "django_drf_otp" / "locale",
]

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


EMAIL_HOST = env("EMAIL_HOST", cast=str, default=None)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", cast=str, default=None)
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", cast=str, default=None)
EMAIL_PORT = env("EMAIL_PORT", cast=int, default=None)
EMAIL_EMAIL = env("EMAIL_EMAIL", cast=str, default=None)
EMAIL_EMAIL_PREFIX = env("EMAIL_EMAIL_PREFIX", cast=str, default=None)
EMAIL_USE_TLS = env("EMAIL_USE_TLS", cast=bool, default=True)
DEFAULT_FROM_EMAIL = EMAIL_EMAIL
