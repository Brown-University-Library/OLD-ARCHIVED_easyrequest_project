# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import render
from django.utils.http import urlquote
from easyrequest_app import models


log = logging.getLogger(__name__)
confirm_request_helper = models.ConfirmRequestGetHelper()
shib_view_helper = models.ShibViewHelper()


def info( request ):
    """ Returns info page. """
    log.debug( u'starting info()' )
    context = {
        # u'email_general_help': os.environ[u'EZRQST__EMAIL_GENERAL_HELP'],
        # u'phone_general_help': os.environ[u'EZRQST__PHONE_GENERAL_HELP']
        }
    return render( request, u'easyrequest_app_templates/info.html', context )


def login( request ):
    """ Stores referring url, bib, and item-barcode in session.
        Asks user to confirm the request. """
    log.debug( u'starting login()' )
    # confirm_request_helper.validate_source( request )
    # confirm_request_helper.validate_params( request )
    ( title, callnumber, item_id ) = confirm_request_helper.get_item_info( request.GET['bibnum'], request.GET['barcode'] )
    confirm_request_helper.update_session( request, title, callnumber, item_id )
    context = {
        'title': request.session['title'] ,
        'callnumber': request.session['callnumber'],
        'PHONE_AUTH_HELP': confirm_request_helper.PHONE_AUTH_HELP,
        'EMAIL_AUTH_HELP': confirm_request_helper.EMAIL_AUTH_HELP
        }
    # return HttpResponse( u'login page coming for... `%s`' % json.dumps(context) )
    return render( request, u'easyrequest_app_templates/login.html', context )


def shib_login( request ):
    """ Examines shib headers, sets session-auth, & returns user to request page. """
    log.debug( u'starting shib_login()' )
    if request.method == u'POST':  # from login.html
        log.debug( u'post detected' )
        return HttpResponseRedirect( os.environ[u'EZRQST__SHIB_LOGIN_URL'] )  # forces reauth if user clicked logout link
    request.session[u'shib_login_error'] = u''  # initialization; updated when response is built
    request.session[u'shib_authorized'] = False
    ( validity, shib_dict ) = shib_view_helper.check_shib_headers( request )
    return_response = shib_view_helper.build_response( request, validity, shib_dict )
    log.debug( u'about to return shib response' )
    return return_response


def confirmation( request ):
    return HttpResponse( u'confirmation implemented soon' )


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
