# -*- coding: utf-8 -*-

# """ Prepares application environment.
#     Variables assume project setup like:
#     easyrequest_stuff
#         easyrequest_project
#             easyrequest_config
#             easyrequest_app
#         env_ezrqst
#      """


# import os, pprint, sys


# ## become self-aware
# current_directory = os.path.dirname(os.path.abspath(__file__))

# ## vars
# CONFIG_DIR = os.path.dirname( os.path.abspath(__file__) )
# PROJECT_DIR = os.path.dirname( CONFIG_DIR )  # easyrequest_project
# PROJECT_STUFF_DIR = os.path.dirname( PROJECT_DIR )
# SITE_PACKAGES_DIR = '%s/env_ezrqst/lib/python2.7/site-packages' % PROJECT_STUFF_DIR
# ACTIVATE_FILE = '%s/env_ezrqst/bin/activate_this.py' % PROJECT_STUFF_DIR
# SETTINGS_MODULE = 'easyrequest_config.settings'

# ## virtualenv
# execfile( ACTIVATE_FILE, dict(__file__=ACTIVATE_FILE) )  # _now_ django is loaded into env

# ## sys.path additions
# for entry in [PROJECT_DIR, PROJECT_STUFF_DIR, SITE_PACKAGES_DIR]:
#  if entry not in sys.path:
#    sys.path.append( entry )

# ## environment additions
# os.environ['DJANGO_SETTINGS_MODULE'] = SETTINGS_MODULE  # so django can access its settings

# ## load up env vars
# SETTINGS_FILE = os.environ['EZRQST__SETTINGS_PATH']  # set in activate_this.py, and activated above
# import shellvars
# var_dct = shellvars.get_vars( SETTINGS_FILE )
# for ( key, val ) in var_dct.items():
#     os.environ[key] = val

# ## gogogo
# from django.core.wsgi import get_wsgi_application
# try:
#     application = get_wsgi_application()
# except Exception as e:
#     print 'passenger_wsgi.py exception...'; print unicode(repr(e))


"""
WSGI config.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

"""
Note: no need to activate the virtual-environment here for passenger.
- the project's httpd/passenger.conf section allows specification of the python-path via `PassengerPython`, which auto-activates it.
- the auto-activation provides access to modules, but not, automatically, env-vars.
- passenger env-vars loading under python3.x is enabled via the `SenEnv` entry in the project's httpd/passenger.conf section.
  - usage: `SetEnv EZRQST_HAY__SETTINGS_PATH /path/to/EZRQST_HAY__env_settings.sh`
  - `SetEnv` requires apache env_module; info: <https://www.phusionpassenger.com/library/indepth/environment_variables.html>,
     enabled by default on macOS 10.12.4, and our dev and production servers.

For activating the virtual-environment manually, don't source the settings file directly. Instead, add to `project_env/bin/activate`:
  export EZRQST__SETTINGS_PATH="/path/to/EZRQST__env_settings.sh"
  source $EZRQST__SETTINGS_PATH
This allows not only the sourcing, but also creates the env-var used below by shellvars.
"""

import os, pprint, sys
import shellvars
from django.core.wsgi import get_wsgi_application


# print( 'the initial env, ```{}```'.format( pprint.pformat(dict(os.environ)) ) )

PROJECT_DIR_PATH = os.path.dirname( os.path.dirname(os.path.abspath(__file__)) )
ENV_SETTINGS_FILE = os.environ['EZRQST__SETTINGS_PATH']  # set in `httpd/passenger.conf`, and `env/bin/activate`

## update path
sys.path.append( PROJECT_DIR_PATH )

## reference django settings
os.environ[u'DJANGO_SETTINGS_MODULE'] = 'easyrequest_config.settings'  # so django can access its settings

## load up env vars
var_dct = shellvars.get_vars( ENV_SETTINGS_FILE )
for ( key, val ) in var_dct.items():
    os.environ[key.decode('utf-8')] = val.decode('utf-8')

# print( 'the final env, ```{}```'.format( pprint.pformat(dict(os.environ)) ) )

## gogogo
application = get_wsgi_application()
