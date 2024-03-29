"""
Django settings for Word2Vec project.

Generated by 'django-admin startproject' using Django 1.10.5.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""
import os
from datetime import datetime, timedelta, date, time as dt_time
from celery.schedules import crontab
stas_api='https://api.smartanalytics.io/api/'
DB='CHdatabase'
BROKER_URL = 'redis://localhost:6379/1'
# храним результаты выполнения задач так же в redis
CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
# в течение какого срока храним результаты, после чего они удаляются
CELERY_TASK_RESULT_EXPIRES = 7*86400  # 7 days
# это нужно для мониторинга наших воркеров
# место хранения периодических задач (данные для планировщика)
#CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"

# CELERY SETTINGS
CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = 'Europe/Moscow'
#BROKER_URL = 'redis://localhost:6379/1'
CELERY_ACCEPT_CONTENT = ['json']
BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 172800}
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TRACK_STARTED = True
#CELERY_RESULT_BACKEND = 'redis://'
CELERY_SEND_EVENTS = True
#CELERY_RESULT_BACKEND = 'redis://localhost:6379/1'
CELERY_IMPORTS = ("api.tasks","api.tasks_test","api.tasks_test_v2")
CELERY_DEFAULT_QUEUE = 'log_loader_queue'
#CELERYBEAT_SCHEDULER = "djcelery.schedulers.DatabaseScheduler"
CELERYCAM_EXPIRE_SUCCESS = timedelta(days=1)
CELERYCAM_EXPIRE_ERROR = timedelta(days=3)
CELERYCAM_EXPIRE_PENDING = timedelta(days=5)
CELERY_QUEUES = {
	'default': {
		"exchange": "default",
		"binding_key": "default",
	},
	
	'log_loader_queue': {
		'exchange': 'log_loader_queue',
		'routing_key': 'log_loader_queue',
	},

}

CELERYBEAT_SCHEDULE = {
    # crontab(hour=0, minute=0, day_of_week='saturday')
		'CH_get_stat':{  # example: 'file-backup' 
			'task': 'api.tasks.task_log_loader_main',  # example: 'files.tasks.cleanup' 
			'schedule': crontab(minute='*/3'),
			#'args': (),
			'options': {'queue': 'log_loader_queue'},
	},'ad_stat_loader':{
                        'task':'api.tasks.task_adstat_loader',
                        'schedule':crontab(minute='0',hour='2'),
                        'options': {'queue': 'log_loader_queue'}},
	'CH_get_stat_test':{  # example: 'file-backup'
                        'task': 'api.tasks_test.task_log_loader_main_test',  # example: 'files.tasks.cleanup'
                        'schedule': crontab(minute='*/3'),
                        #'args': (),
                        'options': {'queue': 'log_loader_queue'},
        },'ad_stat_loader_test':{
                        'task':'api.tasks_test.task_adstat_loader_test',
                        'schedule':crontab(minute='0',hour='*/3'),
                        'options': {'queue': 'log_loader_queue'}},
	'CH_get_stat_test_v2':{  # example: 'file-backup'
                        'task': 'api.tasks_test_v2.task_log_loader_main_test_v2',  # example: 'files.tasks.cleanup'
                        'schedule': crontab(minute='*/3'),
                        #'args': (),
                        'options': {'queue': 'log_loader_queue'},
        }

}
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR= os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '@%f+@fq)*-7g6t*s0@w(mie#tr6u-7+b-rf5#5svu3^(+3nh6r'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['database.smartanalytics.io']
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/home/artur/CHapi/clickhouse/debug.log',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'loginsys',
    #'djcelery',
    #'django_celery_beat',
    'api',

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

ROOT_URLCONF = 'Word2Vec.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'),
                ]
        ,
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

WSGI_APPLICATION = 'Word2Vec.wsgi.application'
ADWORDS_DEVELOPER_TOKEN = 'yJ5krprbCJ9cUe68QmugFw'
ADWORDS_CLIENT_ID='662752301475-qecc0ib0ap0o8jeri1fkai38dmv50a14.apps.googleusercontent.com'
ADWORDS_CLIENT_SECRET='DOGpl942QcIGWMLF7qIZBPzl'
ADWORDS_USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36'

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),    }
}


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [
     os.path.join(BASE_DIR, 'api/static/'),
]
STATIC_ROOT="/home/artur/CHapi/clickhouse/static/"

MEDIA_ROOT =  '/home/artur/CHapi/clickhouse/media/'

MEDIA_URL = '/media/'
