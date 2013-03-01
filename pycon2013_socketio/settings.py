from __future__ import unicode_literals
import os
import os.path

# ------------------
# -- Stuff to Set --
# ------------------

# Set your database stuff with environment variables as listed here
#   (or just change these values).
DATABASES = {
    'default': {
        # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'ENGINE': 'django.db.backends.%s' % os.environ['SOCKETIO_DB_ENGINE'],
        'NAME': os.environ['SOCKETIO_DB_NAME'],
        'USER': os.environ.get('SOCKETIO_DB_USER', ''),
        'PASSWORD': os.environ.get('SOCKETIO_DB_PASSWORD', ''),
        'HOST': os.environ.get('SOCKETIO_DB_HOST', ''),
        'PORT': int(os.environ.get('SOCKETIO_DB_PORT', 0)),
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = os.environ.get('SOCKETIO_TIME_ZONE', 'America/Los_Angeles')

# Redis settings.
# If you're just running locally, you can probably skip these, but they're
#   available if you're testing this out in a non-local environment
REDIS_HOST = os.environ.get('SOCKETIO_REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('SOCKETIO_REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('SOCKETIO_REDIS_DB', 0))
REDIS_PASSWORD = os.environ.get('SOCKETIO_REDIS_PASSWORD', None)

# --------------------------
# -- Stuff to Leave Alone --
# --------------------------

# Debug mode. Self-explanatory.
# Since this is really an example project, this can just be True.
DEBUG = True
TEMPLATE_DEBUG = DEBUG

# The project root.
PROJECT_ROOT = os.path.realpath(os.path.dirname(__file__)) + '/'

# Use timezone-aware datetimes.
USE_TZ = True

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Absolute path to the directory static files should be collected to.
# This is inert since we're not actually using `./manage.py collectstatic`,
#   this example is running off the Django development server (well, a subclass)
#   which handles static collection on the fly.
STATIC_ROOT = ''

# Path to project-level static files (Bootstrap css, js, and img are in here)
STATICFILES_DIRS = (
    PROJECT_ROOT + 'static/',
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Can anyone explain to me what this does or why it's here? It seems like
#   its only purpose is to embarrass people who publish it on GitHub,
#   which is precisely what I am going to do. :)
# It's super-secret, though, so don't share it with anybody.
SECRET_KEY = 'qhxhu5o*9y=y51a4w6$9=ig2rc$gyy=jsrme+^u*3mbh0t_ve2'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

# Middleware classes. We don't need most of the defaults because this
#   example is so stripped down.
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
)

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'pycon2013_socketio.wsgi.application'

# Root URL configuration and installed apps. We aren't using the bulk
#   of the default installed apps for this example, so they're removed.
ROOT_URLCONF = 'pycon2013_socketio.urls'
INSTALLED_APPS = (
    'django.contrib.staticfiles',
    'pycon2013_socketio.chat',
)

# A sample logging configuration. The only tangible logging
#   performed by this configuration is to send an email to
#   the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
#   more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
