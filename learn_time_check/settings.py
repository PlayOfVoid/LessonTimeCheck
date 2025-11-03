import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-key-change-me")
# Для локальной разработки: DEBUG = True (по умолчанию)
# Для продакшена: установите DEBUG = False или задайте DJANGO_DEBUG=false
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() == "true"
# Для PythonAnywhere замените на ваш домен: ["yourusername.pythonanywhere.com"]
ALLOWED_HOSTS: list[str] = ["*"]  # Для продакшена укажите конкретные домены

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "lessons.apps.LessonsConfig",
    'lessons',
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Для раздачи статики в продакшене
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "learn_time_check.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "learn_time_check.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS: list[dict] = []

LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

# WhiteNoise настройки для статики
# Используем более простой storage, который работает всегда
if not DEBUG:
    # В продакшене используем WhiteNoise с сжатием
    STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
else:
    # В режиме разработки используем стандартное хранилище
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Telegram bot config (provided by user)
TELEGRAM_BOT_TOKEN = os.environ.get(
    "TELEGRAM_BOT_TOKEN",
    "8424624364:AAH-KTrV5T4hc6XwYFMljPASfa3NRt5Zrhs",
)
TELEGRAM_CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID", "1965639178"))


