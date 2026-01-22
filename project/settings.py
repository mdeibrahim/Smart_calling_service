import os
from pathlib import Path
from decouple import config
from datetime import timedelta
from .conf import database

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent



# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-24f5e@!)uckgq3vqckh&zo2$m8v$bx)4d8=_*de5xg26*hksmk'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    "daphne",  # Add at the top for Django Channels
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 3rd party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "channels",  # Django Channels
    # 'django_celery_beat',
    # 'django_celery_results',
    # lcoal
    # "apps.account",
    # "apps.sales",
    "apps.calling",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # 3rd party middleware
    # custom middleware
]

ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # custom context processors
            ],
        },
    },
]

WSGI_APPLICATION = "project.wsgi.application"

# Django Channels ASGI Application
ASGI_APPLICATION = "project.asgi.application"

# Channels Layer Configuration (In-memory for development)
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


###################################
#             DATABASE            #
###################################
from .conf import database

DATABASES = database.SQLITE


# CONSOLE EMAIL BACKEND
EMAIL_BACKEND = (
    "django.core.mail.backends.console.EmailBackend"  # use in development only
)

#################### SMTP EMAIL BACKEND ######################
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = config('EMAIL_HOST', default='localhost')
# EMAIL_PORT = config('EMAIL_PORT', default=25)
# EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
# EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
# EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)

###################################
#         STATIC FILES            #
###################################

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default file storage
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

###################################
#                DRF              #
###################################

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    # "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "project.custom_exception.custom_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=60),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

# Custom User Model
# AUTH_USER_MODEL = "account.User"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",  # keep default backend
]


# Zoho Configurations
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.zoho.com"
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_PORT = 587
EMAIL_HOST_USER = "support@pitchprox.com"
EMAIL_HOST_PASSWORD = "cB08fGPVAk3W"
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

ZOHO_CLIENT_ID = "1000.T40P931TRIA5M3KPUSA1H7LYPAIXXR"
ZOHO_CLIENT_SECRET = "8477afd1c1d72332dea71a85cdb3e272ab94d5a790"
ZOHO_REDIRECT_URI = "http://localhost:8000/oauth/zoho/callback"

IMAP_HOST = "imap.zoho.com"
IMAP_PORT = 993
IMAP_USER = EMAIL_HOST_USER
IMAP_PASSWORD = EMAIL_HOST_PASSWORD

# # Celery Configurations
# CELERY_BROKER_URL = "redis://localhost:6379/0"
# CELERY_RESULT_BACKEND = "redis://localhost:6379/0"
# CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# CELERY_BEAT_SCHEDULE = {
#     'fetch-zoho-every-1-min': {
#         'task': 'sales.tasks.fetch_all_emails',
#         'schedule': 60.0,  # every 1 minute
#     },
# }

# Twilio Configurations
TWILIO_API_KEY_SID = config(
    "TWILIO_API_KEY_SID"
)
TWILIO_API_SECRET = config(
    "TWILIO_API_SECRET"
)
TWILIO_ACCOUNT_SID = config(
    "TWILIO_ACCOUNT_SID"
)
TWILIO_PHONE_NUMBER = config("TWILIO_PHONE_NUMBER")
TWILIO_AUTH_TOKEN = config(
    "TWILIO_AUTH_TOKEN"
)

# Deepgram Configuration
DEEPGRAM_API_KEY = config(
    "DEEPGRAM_API_KEY"
)

# Groq AI Configuration
GROQ_API_KEY = config(
    "GROQ_API_KEY"
)

# WebSocket Stream URL (for Twilio to connect to)
WEBSOCKET_STREAM_URL = config(
    "WEBSOCKET_STREAM_URL", default="wss://shadeful-yun-filamentous.ngrok-free.dev"
)
###################################
#          LOGGING CONFIG         #
###################################

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{levelname}] {asctime} {name} {funcName}:{lineno} - {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "[{levelname}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "level": "DEBUG",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "debug.log",
            "formatter": "verbose",
            "level": "DEBUG",
        },
        "error_file": {
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "logs" / "errors.log",
            "formatter": "verbose",
            "level": "ERROR",
        },
    },
    "root": {
        "handlers": ["console", "file", "error_file"],
        "level": "DEBUG",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.calling": {
            "handlers": ["console", "file", "error_file"],
            "level": "DEBUG",
            "propagate": False,
        },
        "websocket": {
            "handlers": ["console", "file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Create logs directory if it doesn't exist
import os
os.makedirs(BASE_DIR / "logs", exist_ok=True)