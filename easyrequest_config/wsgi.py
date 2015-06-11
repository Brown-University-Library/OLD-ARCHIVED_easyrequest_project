""" Prepares application environment.
    Variables assume project setup like:
    easyrequest_stuff
        easyrequest_project
            easyrequest_config
            easyrequest_app
        env_ezrqst
     """


import os, pprint, sys


## become self-aware
current_directory = os.path.dirname(os.path.abspath(__file__))

## vars
ACTIVATE_FILE = os.path.abspath( u'%s/../../env_ezrqst/bin/activate_this.py' % current_directory )
PROJECT_DIR = os.path.abspath( u'%s/../../easyrequest_project' % current_directory )
PROJECT_ENCLOSING_DIR = os.path.abspath( u'%s/../..' % current_directory )
SETTINGS_MODULE = u'easyrequest_config.settings'
SITE_PACKAGES_DIR = os.path.abspath( u'%s/../../env_ezrqst/lib/python*/site-packages' % current_directory )

## virtualenv
execfile( ACTIVATE_FILE, dict(__file__=ACTIVATE_FILE) )  # _now_ django is loaded into env, so following command will work
from django.core.wsgi import get_wsgi_application

## sys.path additions
for entry in [PROJECT_DIR, PROJECT_ENCLOSING_DIR, SITE_PACKAGES_DIR]:
 if entry not in sys.path:
   sys.path.append( entry )

## environment additions
os.environ[u'DJANGO_SETTINGS_MODULE'] = SETTINGS_MODULE  # so django can access its settings

## gogogo
application = get_wsgi_application()
