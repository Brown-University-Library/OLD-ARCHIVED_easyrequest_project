# -*- coding: utf-8 -*-

from __future__ import unicode_literals
""" Helper for kochief/discovery/views.info() """

import datetime, json, logging, os, subprocess
from django.conf import settings


log = logging.getLogger(__name__)
# log_level = { 'DEBUG': logging.DEBUG, 'INFO': logging.INFO }
# log.setLevel( log_level[settings.LOG_LEVEL] )
# if not logging._handlers:
#     handler = logging.FileHandler( settings.LOG_PATH, mode='a', encoding='utf-8', delay=False )
#     formatter = logging.Formatter( '[%(asctime)s] %(levelname)s [%(module)s-%(funcName)s()::%(lineno)d] %(message)s' )
#     handler.setFormatter( formatter )
#     log.addHandler( handler )


def get_commit():
    """ Returns commit-string.
        Called by views.version() """
    original_directory = os.getcwd()
    log.debug( 'BASE_DIR, ```%s```' % settings.BASE_DIR )
    git_dir = settings.BASE_DIR
    os.chdir( git_dir )
    output8 = subprocess.check_output( ['git', 'log'], stderr=subprocess.STDOUT )
    output = output8.decode( 'utf-8' )
    os.chdir( original_directory )
    lines = output.split( '\n' )
    commit = lines[0]
    return commit


def get_branch():
    """ Returns branch.
        Called by views.version() """
    original_directory = os.getcwd()
    git_dir = settings.BASE_DIR
    os.chdir( git_dir )
    output8 = subprocess.check_output( ['git', 'branch'], stderr=subprocess.STDOUT )
    output = output8.decode( 'utf-8' )
    os.chdir( original_directory )
    lines = output.split( '\n' )
    branch = 'init'
    for line in lines:
        if line[0:1] == '*':
            branch = line[2:]
            break
    return branch

def make_context( request, rq_now, info_txt ):
    """ Assembles data-dct.
        Called by views.version() """
    context = {
        'request': {
        'url': '%s://%s%s' % (
            request.scheme,
            request.META.get( 'HTTP_HOST', '127.0.0.1' ),  # HTTP_HOST doesn't exist for client-tests
            request.META.get('REQUEST_URI', request.META['PATH_INFO'])
            ),
        'timestamp': str( rq_now )
        },
        'response': {
            'version': info_txt,
            'timetaken': str( datetime.datetime.now() - rq_now )
        }
    }
    return context
