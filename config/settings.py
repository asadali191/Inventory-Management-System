from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env from project root (dev) OR exe folder (client)
def _load_env():
    # project root
    load_dotenv(BASE_DIR / ".env")
    # exe folder (if packaged)
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        load_dotenv(exe_dir / ".env")

_load_env()


# -------------------------
# Runtime dir helper (for EXE)
# -------------------------
def _runtime_base_dir() -> Path:
    """
    If packaged with PyInstaller: use EXE folder
    Else: use project BASE_DIR
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return BASE_DIR

RUNTIME_DIR = _runtime_base_dir()


# -------------------------
# Core
# -------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
DEBUG = os.getenv("DEBUG", "1") == "1"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if h.strip()
]

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]


# -------------------------
# Apps
# -------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "inventory",
]


# -------------------------
# Middleware
# -------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # ✅ important for EXE/static
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


ROOT_URLCONF = "config.urls"


# -------------------------
# Templates
# -------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "inventory" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]


WSGI_APPLICATION = "config.wsgi.application"


# -------------------------
# Database (Render PostgreSQL)
# -------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "khussa_master"),
        "USER": os.getenv("DB_USER", "khussa_master_user"),
        "PASSWORD": os.getenv("DB_PASSWORD", "jURKda69qKhRsPpkyLrqmfQGbkx6ibMK"),  # ✅ never hardcode
        "HOST": os.getenv("DB_HOST", "dpg-d555ep95pdvs73buafig-a.virginia-postgres.render.com"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": int(os.getenv("DB_CONN_MAX_AGE", "60")),
        "OPTIONS": {
            "sslmode": os.getenv("DB_SSLMODE", "require"),
        },
    }
}


# -------------------------
# Password validation
# -------------------------
AUTH_PASSWORD_VALIDATORS: list[dict] = []


# -------------------------
# I18N / TZ
# -------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Karachi"
USE_I18N = True
USE_TZ = True


# -------------------------
# Static / Media (EXE friendly)
# -------------------------
STATIC_URL = "/static/"

# In dev: collect from this
STATICFILES_DIRS = [BASE_DIR / "inventory" / "static"]

# In EXE/production: whitenoise serves from here (after collectstatic)
STATIC_ROOT = RUNTIME_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = RUNTIME_DIR / "media"


# -------------------------
# Default PK
# -------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# -------------------------
# DRF (simple)
# -------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
}
