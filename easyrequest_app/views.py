# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import datetime, json, logging, os, pprint
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render
from django.utils.http import urlquote
from easyrequest_app import models


log = logging.getLogger(__name__)
login_helper = models.LoginHelper()
shib_view_helper = models.ShibViewHelper()
processor_helper = models.Processor()
shib_logout_helper = models.ShibLogoutHelper()


def info( request ):
    """ Returns info page. """
    log.debug( 'starting info()' )
    context = {
        # 'email_general_help': os.environ['EZRQST__EMAIL_GENERAL_HELP'],
        # 'phone_general_help': os.environ['EZRQST__PHONE_GENERAL_HELP']
        }
    return render( request, 'easyrequest_app_templates/info.html', context )


def login( request ):
    """ Stores referring url, bib, and item-barcode in session.
        Presents shib and manual log in options. """
    log.debug( 'starting login()' )
    if not ( login_helper.validate_source(request) and login_helper.validate_params(request) ):
        return HttpResponseBadRequest( "This web-application supports Josiah, the Library's search web-application. If you think you should be able to access this url, please contact '%s'." % login_helper.EMAIL_AUTH_HELP )
    login_helper.initialize_session( request )
    ( title, callnumber, item_id ) = login_helper.get_item_info( request.GET['bibnum'], request.GET['barcode'] )
    login_helper.update_session( request, title, callnumber, item_id )
    context = login_helper.prepare_context( request )
    return render( request, 'easyrequest_app_templates/login.html', context )


def shib_login( request ):
    """ Examines shib headers, sets session-auth.
        Redirects user to non-seen processor() view. """
    log.debug( 'starting shib_login()' )
    if request.method == 'POST':  # from login.html
        log.debug( 'post detected' )
        return HttpResponseRedirect( os.environ['EZRQST__SHIB_LOGIN_URL'] )  # forces reauth if user clicked logout link
    request.session['shib_login_error'] = ''  # initialization; updated when response is built
    request.session['shib_authorized'] = False
    ( validity, shib_dict ) = shib_view_helper.check_shib_headers( request )
    return_response = shib_view_helper.build_response( request, validity, shib_dict )
    log.debug( 'about to return shib response' )
    return return_response


def processor( request ):
    """ Handles item request:,
        - Ensures user is authenticated.
        - Saves request.
        - Places hold.
        - Triggers shib_logout() view. """
    if processor_helper.check_request( request ) == False:
        return HttpResponseRedirect( reverse('info_url') )
    itmrqst = processor_helper.save_data( request )
    try:
        processor_helper.place_request( itmrqst )
    except Exception as e:
        log.error( 'Exception placing request, `%s`' % unicode(repr(e)) )
        return HttpResponseServerError( 'Problem placing request; please try again in a few minutes.' )
    processor_helper.email_patron( itmrqst.patron_email, itmrqst.patron_name, itmrqst.item_title, itmrqst.item_callnumber, itmrqst.item_bib, itmrqst.item_id, itmrqst.patron_barcode, itmrqst.item_barcode )
    return HttpResponseRedirect( reverse('logout_url') )  # shib_logout() view


def shib_logout( request ):
    """ Clears session, hits shib logout.
        Redirects user to summary() view. """
    redirect_url = shib_logout_helper.build_redirect_url( request )
    request.session['shib_authorized'] = False
    logout( request )  # from django.contrib.auth import logout
    if request.get_host() == '127.0.0.1' and project_settings.DEBUG == True:  # eases local development
        pass
    else:
        encoded_redirect_url =  urlquote( redirect_url )  # django's urlquote()
        redirect_url = '%s?return=%s' % ( os.environ['EZRQST__SHIB_LOGOUT_URL_ROOT'], encoded_redirect_url )
    log.debug( 'final redirect_url, `%s`' % redirect_url )
    return HttpResponseRedirect( redirect_url )


def summary( request ):
    """ Displays final summary screen. """
    EMAIL = os.environ['EZRQST__EMAIL_GENERAL_HELP']
    PHONE = os.environ['EZRQST__PHONE_GENERAL_HELP']
    context = {
        'bib': request.GET['bib'],
        'callnumber': request.GET['callnumber'],
        'item_id': request.GET['item_id'],
        'title': request.GET['title'],
        'user_name': request.GET['user_name'],
        'user_email': request.GET['user_email'],
        'email_general_help': EMAIL,
        'phone_general_help': PHONE
        }
    return render( request, 'easyrequest_app_templates/summary.html', context )
