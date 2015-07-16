# -*- coding: utf-8 -*-

from __future__ import unicode_literals
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
processor_helper = models.Processor()


def info( request ):
    """ Returns info page. """
    log.debug( 'starting info()' )
    context = {
        # 'email_general_help': os.environ[u'EZRQST__EMAIL_GENERAL_HELP'],
        # 'phone_general_help': os.environ[u'EZRQST__PHONE_GENERAL_HELP']
        }
    return render( request, 'easyrequest_app_templates/info.html', context )


def login( request ):
    """ Stores referring url, bib, and item-barcode in session.
        Asks user to confirm the request. """
    log.debug( 'starting login()' )
    # confirm_request_helper.validate_source( request )
    # confirm_request_helper.validate_params( request )
    confirm_request_helper.initialize_session( request )
    ( title, callnumber, item_id ) = confirm_request_helper.get_item_info( request.GET['bibnum'], request.GET['barcode'] )
    confirm_request_helper.update_session( request, title, callnumber, item_id )
    context = {
        'title': request.session['item_title'] ,
        'callnumber': request.session['item_callnumber'],
        'PHONE_AUTH_HELP': confirm_request_helper.PHONE_AUTH_HELP,
        'EMAIL_AUTH_HELP': confirm_request_helper.EMAIL_AUTH_HELP
        }
    return render( request, 'easyrequest_app_templates/login.html', context )


def shib_login( request ):
    """ Examines shib headers, sets session-auth, & sends user to confirmation page. """
    log.debug( 'starting shib_login()' )
    if request.method == 'POST':  # from login.html
        log.debug( 'post detected' )
        return HttpResponseRedirect( os.environ[u'EZRQST__SHIB_LOGIN_URL'] )  # forces reauth if user clicked logout link
    request.session[u'shib_login_error'] = ''  # initialization; updated when response is built
    request.session[u'shib_authorized'] = False
    ( validity, shib_dict ) = shib_view_helper.check_shib_headers( request )
    return_response = shib_view_helper.build_response( request, validity, shib_dict )
    log.debug( 'about to return shib response' )
    return return_response


def processor( request ):
    """ Handles item request:,
        - Ensures user is authenticated.
        - Saves request.
        - Places hold.
        - Triggers logout. """
    if processor_helper.check_request( request ) == False:
        return HttpResponseRedirect( reverse(u'info_url') )
    try:
        processor_helper.save_data( request )
        log.debug( 'session, `%s`' % pprint.pprint(request.session.items()) )
        processor_helper.place_request(
            request.session['user_name'], request.session['user_barcode'], request.session['item_bib'], request.session['item_id'] )
    except Exception as e:
        log.error( 'Exception, `%s`' % unicode(repr(e)) )
    processor_helper.logout( request )  # session logout
    return HttpResponse( 'processor response under construction' )
    # return HttpResponseRedirect( reverse(u'logout_url') )  # shib logout


# def confirmation( request ):
#     """ Logs user out & displays confirmation screen after submission.
#         TODO- refactor commonalities with shib_logout() """
#     try:
#         barcode = request.session[u'item_info'][u'barcode']
#     except:
#         scheme = 'https' if request.is_secure() else 'http'
#         redirect_url = '%s://%s%s' % ( scheme, request.get_host(), reverse(u'info_url') )
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
#     scheme = 'https' if request.is_secure() else 'http'
#     redirect_url = '%s://%s%s' % ( scheme, request.get_host(), reverse(u'request_url') )
#     if request.get_host() == '127.0.0.1' and project_settings.DEBUG == True:  # eases local development
#         pass
#     else:
#         encoded_redirect_url =  urlquote( redirect_url )  # django's urlquote()
#         redirect_url = '%s?return=%s' % ( os.environ[u'EZRQST__SHIB_LOGOUT_URL_ROOT'], encoded_redirect_url )
#     log.debug( 'in views.shib_logout(); redirect_url, `%s`' % redirect_url )
#     return HttpResponseRedirect( redirect_url )
