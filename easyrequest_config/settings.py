# -*- coding: utf-8 -*-

import json, os


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ['EZRQST__SECRET_KEY']

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = json.loads( os.environ['EZRQST__DEBUG'] )  # boolean

ADMINS = json.loads( os.environ['EZRQST__ADMINS_JSON'] )

ALLOWED_HOSTS = json.loads( os.environ['EZRQST__ALLOWED_HOSTS'] )  # list


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'easyrequest_app',
]

MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'easyrequest_config.urls'

template_dirs = json.loads( os.environ['EZRQST__TEMPLATE_DIRS'] )
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': template_dirs,
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

WSGI_APPLICATION = 'easyrequest_config.passenger_wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': os.environ['EZRQST__DATABASES_ENGINE'],
        'NAME': os.environ['EZRQST__DATABASES_NAME'],
        'USER': os.environ['EZRQST__DATABASES_USER'],
        'PASSWORD': os.environ['EZRQST__DATABASES_PASSWORD'],
        'HOST': os.environ['EZRQST__DATABASES_HOST'],
        'PORT': os.environ['EZRQST__DATABASES_PORT'],
    }
}


# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/
STATIC_URL = os.environ['EZRQST__STATIC_URL']
STATIC_ROOT = os.environ['EZRQST__STATIC_ROOT']  # needed for collectstatic command

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.environ['EZRQST__CACHE_DIR_PATH'],
    }
}

# Email
SERVER_EMAIL = 'easyrequest@library.brown.edu'
EMAIL_HOST = os.environ['EZRQST__EMAIL_HOST']
EMAIL_PORT = int( os.environ['EZRQST__EMAIL_PORT'] )

# sessions
# <https://docs.djangoproject.com/en/1.8/ref/settings/#std:setting-SESSION_SAVE_EVERY_REQUEST>
# Thinking: not that many concurrent users, and no pages where session info isn't required, so overhead is reasonable.
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            # 'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'format': "[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'logfile': {
            'level':'DEBUG',
            'class':'logging.FileHandler',  # note: configure server to use system's log-rotate to avoid permissions issues
            'filename': os.environ.get('EZRQST__LOG_PATH'),
            'formatter': 'standard',
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'standard'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        }
    },
    'loggers': {
        'easyrequest_app': {
            'handlers': ['logfile'],
            'level': os.environ.get('EZRQST__LOG_LEVEL'),
            'propagate': False
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
    }
}

CSRF_COOKIE_DOMAIN = os.environ['EZRQST__CSRF_COOKIE_DOMAIN']


# eof
