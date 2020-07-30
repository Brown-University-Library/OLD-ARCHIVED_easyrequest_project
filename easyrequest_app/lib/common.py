from __future__ import unicode_literals

import logging, os

import requests
from django.core.cache import cache
from django.core.urlresolvers import reverse


log = logging.getLogger(__name__)

PATTERN_HEADER_URL = os.environ['EZRQST__PATTERN_HEADER_URL']
PATTERN_LIB_CACHE_TIMEOUT = int( os.environ['EZRQST__PATTERN_HEADER_CACHE_TIMEOUT_IN_HOURS'] )


def grab_pattern_header():
    """ Prepares html for header. """
    cache_key = 'pattern_header'
    header_html = cache.get( cache_key, None )
    if header_html:
        log.debug( 'pattern-header in cache' )
    else:
        log.debug( 'pattern-header not in cache' )
        r = requests.get( PATTERN_HEADER_URL )
        header_html = r.content.decode( 'utf8' )
        info_url = reverse( 'info_url' )
        log.debug( 'info_url, ``%s``' % info_url )
        header_html = header_html.replace( 'DYNAMIC_SITE_URL', info_url ).replace( 'DYNAMIC_INFO_url', info_url )
        cache.set( cache_key, header_html, PATTERN_LIB_CACHE_TIMEOUT )
    return header_html

