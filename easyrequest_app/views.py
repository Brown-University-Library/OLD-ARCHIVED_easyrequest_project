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
barcode_handler_helper = models.BarcodeHandlerHelper()
pic_loc_helper = models.PickupLocation()


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


def barcode_handler( request ):
    """ Handles barcode login.
        On auth success, redirects user to non-seen views.processor()
        On auth failure, redirects back to views.login() """
    log.debug( 'starting barcode_login_handler()' )
    if barcode_handler_helper.validate_params(request) is not True:  # puts param values in session
        return barcode_handler_helper.prep_login_redirect( request )
    if barcode_handler_helper.authenticate( request.session['barcode_login_name'], request.session['barcode_login_barcode'] ) is not True:  # if login fails, redirect user back to login page with error messages that will display
        return barcode_handler_helper.prep_login_redirect( request )
    patron_info_dct = barcode_handler_helper.enhance_patron_info( request.session['barcode_login_barcode'] )
    if patron_info_dct is False:
        return HttpResponseServerError( 'Problem getting required patron info; please try again in a few minutes.' )
    barcode_handler_helper.update_session( request, patron_info_dct )
    return barcode_handler_helper.prep_processor_redirect( request )


def shib_handler( request ):
    """ Stores pickup location to session and redirects to shib_login() """
    log.debug( 'starting shib_handler()' )
    if request.method == 'POST':  # from login.html
        log.debug( 'post detected' )
        request.session['pickup_location'] = request.POST['pickup_location']
        log.debug( 'redirect url will be, `%s`' % reverse('shib_login_url') )
        return HttpResponseRedirect( reverse('shib_login_url') )
    else:
        log.info( 'non-post detected, returning 400/bad-request' )
        return HttpResponseBadRequest( "This web-application supports Josiah, the Library's search web-application. If you think you should be able to access this url, please contact '%s'." % login_helper.EMAIL_AUTH_HELP )


def shib_login( request ):
    """ Examines shib headers, sets session-auth.
        Redirects user to non-seen processor() view. """
    log.debug( 'starting shib_login()' )
    ( validity, shib_dict ) = shib_view_helper.check_shib_headers( request )
    return_response = shib_view_helper.build_response( request, validity, shib_dict )
    log.debug( 'about to return shib response' )
    return return_response


def processor( request ):
    """ Handles item request:,
        - Ensures user is authenticated.
        - Saves request.
        - Places hold.
        - Emails patron.
        - Triggers shib_logout() view.
        TODO: add to barcode_handler() required request-parameter of `selected pickup location`,
              and put that in the session,
              and grab it here from the session. """
    if processor_helper.check_request( request ) == False:
        return HttpResponseRedirect( reverse('info_url') )
    itmrqst = processor_helper.save_data( request )
    try:
        processor_helper.place_request( itmrqst, request.session['josiah_api_name'], request.session['pickup_location'] )
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
        'pickup_location_display': request.GET['pic_loc'],
        'email_general_help': EMAIL,
        'phone_general_help': PHONE
        }
    if request.GET['source_url'][0:4] == 'http':
        context['source_url'] = request.GET['source_url']
    return render( request, 'easyrequest_app_templates/summary.html', context )
