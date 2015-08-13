# -*- coding: utf-8 -*-

from __future__ import unicode_literals

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
CONFIG_DIR = os.path.dirname( os.path.abspath(__file__) )
PROJECT_DIR = os.path.dirname( CONFIG_DIR )  # easyrequest_project
PROJECT_STUFF_DIR = os.path.dirname( PROJECT_DIR )
SITE_PACKAGES_DIR = '%s/env_ezrqst/lib/python2.7/site-packages' % PROJECT_STUFF_DIR
ACTIVATE_FILE = '%s/env_ezrqst/bin/activate_this.py' % PROJECT_STUFF_DIR
SETTINGS_MODULE = 'easyrequest_config.settings'

## virtualenv
execfile( ACTIVATE_FILE, dict(__file__=ACTIVATE_FILE) )  # _now_ django is loaded into env

## sys.path additions
for entry in [PROJECT_DIR, PROJECT_STUFF_DIR, SITE_PACKAGES_DIR]:
 if entry not in sys.path:
   sys.path.append( entry )

## environment additions
os.environ['DJANGO_SETTINGS_MODULE'] = SETTINGS_MODULE  # so django can access its settings

## load up env vars
SETTINGS_FILE = os.environ['EZRQST__SETTINGS_PATH']  # set in activate_this.py, and activated above
import shellvars
var_dct = shellvars.get_vars( SETTINGS_FILE )
for ( key, val ) in var_dct.items():
    os.environ[key] = val

## gogogo
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
