"""
Django settings for CareerCompass Kenya project.
Generated with Django 5.2.8
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from decouple import config

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-dev-key-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '.trycloudflare.com']

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://*.trycloudflare.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://*.trycloudflare.com",
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'corsheaders',
    'widget_tweaks',
    
    # Local apps
    'users',
    'analytics',
    'assessments',
    'recommendations',
    'ai_coach',
    'coaching',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'backend.context_processors.app_context',
                'backend.context_processors.static_files_local',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'careercompass'),
        'USER': os.getenv('DB_USER', 'careercompass_user'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'password'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Password validation
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

# Internationalization
LANGUAGE_CODE = 'en-ke'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.CustomUser'

# Authentication URLs
LOGIN_URL = '/users/login/'
LOGIN_REDIRECT_URL = '/users/dashboard/'
LOGOUT_REDIRECT_URL = '/users/login/'

# ── Email configuration ───────────────────────────────────────────────────────
# Django's built-in SMTP backend is used for ALL email: OTP codes, password
# resets, and welcome emails.
#
# To send REAL emails, set these variables in your .env file:
#
#   ┌── Gmail (free, recommended for dev / small-scale) ──────────────────────┐
#   │  1. Enable 2-Factor Auth on your Google account                         │
#   │  2. Go to: myaccount.google.com → Security → App Passwords              │
#   │  3. Create an App Password for "Mail" / "Other (Django)"                │
#   │  4. Set:                                                                 │
#   │     EMAIL_HOST          = smtp.gmail.com                                 │
#   │     EMAIL_PORT          = 587                                            │
#   │     EMAIL_USE_TLS       = True                                           │
#   │     EMAIL_HOST_USER     = youraddress@gmail.com                          │
#   │     EMAIL_HOST_PASSWORD = xxxx xxxx xxxx xxxx   (16-char App Password)  │
#   └─────────────────────────────────────────────────────────────────────────┘
#
#   ┌── Outlook / Office 365 ─────────────────────────────────────────────────┐
#   │     EMAIL_HOST          = smtp.office365.com                             │
#   │     EMAIL_PORT          = 587                                            │
#   │     EMAIL_USE_TLS       = True                                           │
#   │     EMAIL_HOST_USER     = youraddress@outlook.com                        │
#   │     EMAIL_HOST_PASSWORD = your_outlook_password                          │
#   └─────────────────────────────────────────────────────────────────────────┘
#
#   ┌── Brevo (SendinBlue) — free tier: 300 emails/day ──────────────────────┐
#   │     EMAIL_HOST          = smtp-relay.brevo.com                           │
#   │     EMAIL_PORT          = 587                                            │
#   │     EMAIL_USE_TLS       = True                                           │
#   │     EMAIL_HOST_USER     = your_brevo_login_email                         │
#   │     EMAIL_HOST_PASSWORD = your_brevo_smtp_key                            │
#   └─────────────────────────────────────────────────────────────────────────┘
#
# If NONE of the above are set → emails print to the terminal console
# (great for development — look for "Content-Type: text/html" in the terminal).

_email_host     = os.getenv('EMAIL_HOST', '').strip()
_email_user     = os.getenv('EMAIL_HOST_USER', '').strip()
_email_password = os.getenv('EMAIL_HOST_PASSWORD', '').strip()

if _email_host and _email_user and _email_password:
    EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST          = _email_host
    EMAIL_PORT          = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_USE_TLS       = os.getenv('EMAIL_USE_TLS', 'True')  == 'True'
    EMAIL_USE_SSL       = os.getenv('EMAIL_USE_SSL', 'False') == 'True'
    EMAIL_HOST_USER     = _email_user
    EMAIL_HOST_PASSWORD = _email_password
    EMAIL_TIMEOUT       = 10   # seconds — prevents hanging on slow SMTP servers
else:
    # Development / unconfigured: print to terminal so OTP codes are visible
    EMAIL_BACKEND       = 'django.core.mail.backends.console.EmailBackend'
    EMAIL_HOST_USER     = ''
    EMAIL_HOST_PASSWORD = ''

DEFAULT_FROM_EMAIL = os.getenv(
    'DEFAULT_FROM_EMAIL',
    f'CareerCompass Kenya <{os.getenv("EMAIL_HOST_USER", "noreply@careercompass.co.ke")}>'
)
SERVER_EMAIL = DEFAULT_FROM_EMAIL
SITE_NAME    = 'CareerCompass Kenya'
SITE_URL     = os.getenv('SITE_URL', 'http://127.0.0.1:8000')

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# Security settings for production (commented for development)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


OPENAI_API_KEY  = config('OPENAI_API_KEY',  default=None)
HF_API_TOKEN    = config('HF_API_TOKEN',    default='')   # huggingface.co/settings/tokens
AI_MODEL        = config('AI_MODEL',        default='gpt-4o-mini')
AI_TEMPERATURE  = config('AI_TEMPERATURE',  default=0.7,  cast=float)
AI_MAX_TOKENS   = config('AI_MAX_TOKENS',   default=600,  cast=int)