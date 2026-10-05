import os
from pathlib import Path
from dotenv import load_dotenv
from django.contrib.messages import constants as messages

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# Quick-start development settings - unsuitable for production
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-smart-event-planning-platform-dev-key-2026')

DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')

allowed_hosts_env = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver')
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_env.split(',') if host.strip()]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party
    'rest_framework',
    
    # Custom apps
    'accounts.apps.AccountsConfig',
    'dashboard.apps.DashboardConfig',
    'events.apps.EventsConfig',
    'registrations.apps.RegistrationsConfig',
    'attendance.apps.AttendanceConfig',
    'vendors.apps.VendorsConfig',
    'resources.apps.ResourcesConfig',
    'budgets.apps.BudgetsConfig',
    'expenses.apps.ExpensesConfig',
    'reports.apps.ReportsConfig',
    'notifications.apps.NotificationsConfig',
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

ROOT_URLCONF = 'config.urls'

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
                'notifications.context_processors.notification_badge_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database Configuration (MySQL as primary, with environment variable control)
DB_ENGINE = os.getenv('DB_ENGINE', 'mysql').lower()
DB_NAME = os.getenv('DB_NAME', 'smartevent_db')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = os.getenv('DB_PORT', '3306')

if DB_ENGINE == 'sqlite3':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'TEST': {
                'NAME': ':memory:',
            }
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': DB_NAME,
            'USER': DB_USER,
            'PASSWORD': DB_PASSWORD,
            'HOST': DB_HOST,
            'PORT': DB_PORT,
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (User uploads, tickets, documents)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Authentication URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard:index'
LOGOUT_REDIRECT_URL = 'login'

# Bootstrap Message Tags Mapping
MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
