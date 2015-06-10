# -*- coding: utf-8 -*-

import datetime, logging, os, pprint
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render
from django.utils.http import urlquote
from easyrequest_app import models


log = logging.getLogger(__name__)
shib_view_helper = models.ShibViewHelper()


def info( request ):
    """ Returns info page. """
    context = {
        # u'email_general_help': os.environ[u'EZRQST__EMAIL_GENERAL_HELP'],
        # u'phone_general_help': os.environ[u'EZRQST__PHONE_GENERAL_HELP']
        }
    return render( request, u'easyrequest_app_templates/info.html', context )


# def shib_login( request ):
#     """ Examines shib headers, sets session-auth, & returns user to request page. """
#     log.debug( u'in views.shib_login(); starting' )
#     if request.method == u'POST':  # from request_login.html
#         log.debug( u'in views.shib_login(); post detected' )
#         return HttpResponseRedirect( os.environ[u'EZRQST__SHIB_LOGIN_URL'] )  # forces reauth if user clicked logout link
#     request.session[u'shib_login_error'] = u''  # initialization; updated when response is built
#     ( validity, shib_dict ) = shib_view_helper.check_shib_headers( request )
#     return_response = shib_view_helper.build_response( request, validity, shib_dict )
#     log.debug( u'in views.shib_login(); about to return response' )
#     return return_response


# def confirmation( request ):
#     """ Logs user out & displays confirmation screen after submission.
#         TODO- refactor commonalities with shib_logout() """
#     try:
#         barcode = request.session[u'item_info'][u'barcode']
#     except:
#         scheme = u'https' if request.is_secure() else u'http'
#         redirect_url = u'%s://%s%s' % ( scheme, request.get_host(), reverse(u'info_url') )
#         return HttpResponseRedirect( redirect_url )
#     if request.session[u'authz_info'][u'authorized'] == True:  # always true initially
#         return_response = confirmation_vew_helper.handle_authorized( request )
#     else:  # False is set by handle_authorized()
#         return_response = confirmation_vew_helper.handle_non_authorized( request )
#     return return_response


# def shib_logout( request ):
#     """ Clears session, hits shib logout, and redirects user to landing page. """
#     request.session[u'authz_info'][u'authorized'] = False
#     logout( request )
#     scheme = u'https' if request.is_secure() else u'http'
#     redirect_url = u'%s://%s%s' % ( scheme, request.get_host(), reverse(u'request_url') )
#     if request.get_host() == u'127.0.0.1' and project_settings.DEBUG == True:  # eases local development
#         pass
#     else:
#         encoded_redirect_url =  urlquote( redirect_url )  # django's urlquote()
#         redirect_url = u'%s?return=%s' % ( os.environ[u'EZRQST__SHIB_LOGOUT_URL_ROOT'], encoded_redirect_url )
#     log.debug( u'in views.shib_logout(); redirect_url, `%s`' % redirect_url )
#     return HttpResponseRedirect( redirect_url )
