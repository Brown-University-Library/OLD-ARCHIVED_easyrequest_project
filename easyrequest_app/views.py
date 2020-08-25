# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint

# from .lib import common, version_helper

from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render
from django.utils.http import urlquote
from django.views.decorators.csrf import csrf_exempt
from easyrequest_app import models
from easyrequest_app.lib import common, version_helper
from easyrequest_app.lib.mail import Emailer

# from easyrequest_app.lib import mail

log = logging.getLogger(__name__)

emailer = Emailer()
login_helper = models.LoginHelper()
shib_view_helper = models.ShibViewHelper()
processor_helper = models.Processor()
shib_logout_helper = models.ShibLogoutHelper()
barcode_handler_helper = models.BarcodeHandlerHelper()
pic_loc_helper = models.PickupLocation()
summary_helper = models.SummaryHelper()
stats_builder = models.StatsBuilder()


def info( request ):
    """ Returns basic info about the easyrequest_hay webapp.
        Triggered by root easyrequest_hay url. """
    log.debug( '\n\nstarting info(); request.__dict__, ```%s```' % request.__dict__ )
    start = datetime.datetime.now()
    context = {
        'pattern_header': common.grab_pattern_header(),
        'pattern_header_active': json.loads( os.environ['EZRQST__PATTERN_HEADER_ACTIVE_JSON'] )
    }
    if request.GET.get('format', '') == 'json':
        context_json = json.dumps(context, sort_keys=True, indent=2)
        resp = HttpResponse( context_json, content_type='application/javascript; charset=utf-8' )
    else:
        if context['pattern_header_active'] == True:
            template = 'easyrequest_app_templates/info_02.html'
        else:
            template = 'easyrequest_app_templates/info.html'
        resp = render( request, template, context )
    return resp


def login( request ):
    """ Stores referring url, bib, and item-barcode in session.
        Presents shib and manual log in options. """
    log.info( 'starting login()' )
    log.debug( 'rquest.GET, ``%s``' % request.GET )
    context = {
        'pattern_header': common.grab_pattern_header(),
        'pattern_header_active': json.loads( os.environ['EZRQST__PATTERN_HEADER_ACTIVE_JSON'] )
    }
    if not login_helper.validate_source(request):
        if context['pattern_header_active'] == True:
            context['message'] = """You seem to have attempted to get to this login page without having started from Josiah, the Library's search web-application at <a href="https://search.library.brown.edu/">https://search.library.brown.edu/</a>. Please start there and try again. If you need help, please contact Library staff at the "Feedback" or "Help" link above, and they'll assist you. """
            template = 'easyrequest_app_templates/problem_02.html'
            resp = render( request, template, context )
        else:
            message = """You seem to have attempted to get to this login page without having started from Josiah, the Library's search web-application at ``https://search.library.brown.edu/``. Please start there and try again. If you need help, please contact Library staff at ``%s``, and they'll assist you. """ % (
            login_helper.EMAIL_AUTH_HELP,
            )
            resp = HttpResponseBadRequest( message )
        return resp
    if not login_helper.validate_params( request.GET ):
        if context['pattern_header_active'] == True:
            context['message'] = """This request could not be submitted for the following reason%s: ``%s``. Please contact Library staff at the "Feedback" or "Help" link above, and they'll assist you.""" % (
            '' if len(login_helper.problems) < 2 else 's',
            ', '.join( login_helper.problems ),
            )
            template = 'easyrequest_app_templates/problem_02.html'
            resp = render( request, template, context )
        else:
            message = """This request could not be submitted for the following reason%s: ``%s``. Please contact Library staff at ``%s``, and they'll assist you. """ % (
            '' if len(login_helper.problems) < 2 else 's',
            ', '.join( login_helper.problems ),
            login_helper.EMAIL_AUTH_HELP,
            )
            resp = HttpResponseBadRequest( message )
        return resp
    login_helper.initialize_session( request )
    ( title, callnumber, item_id ) = login_helper.get_item_info( request.GET['bibnum'], request.GET['barcode'] )
    login_helper.update_session( request, title, callnumber, item_id )
    context = login_helper.prepare_context( request )
    # return render( request, 'easyrequest_app_templates/login.html', context )
    if request.GET.get('format', '') == 'json':
        context_json = json.dumps(context, sort_keys=True, indent=2)
        resp = HttpResponse( context_json, content_type='application/javascript; charset=utf-8' )
    else:
        if context['pattern_header_active'] == True:
            template = 'easyrequest_app_templates/login_02.html'
        else:
            template = 'easyrequest_app_templates/login.html'
        resp = render( request, template, context )
    return resp


@csrf_exempt  # temp for migration
def barcode_handler( request ):
    """ Handles barcode login.
        On auth success, redirects user to non-seen views.processor()
        On auth failure, redirects back to views.login() """
    log.debug( 'starting barcode_login_handler()' )
    if barcode_handler_helper.validate_params(request) is not True:  # puts param values in session
        return barcode_handler_helper.prep_login_redirect( request )
    if barcode_handler_helper.authenticate( request.session['barcode_login_name'], request.session['barcode_login_barcode'] ) is False:  # if login fails, redirect user back to login page with error messages that will display
        return barcode_handler_helper.prep_login_redirect( request )
    patron_info_dct = barcode_handler_helper.authorize( request.session['barcode_login_barcode'] )
    if patron_info_dct is False:
        return barcode_handler_helper.prep_login_redirect( request )
    barcode_handler_helper.update_session( request, patron_info_dct )  # TODO: like easyrequest-hay, grab the user's sierra-patron-id and store it to the session
    return barcode_handler_helper.prep_processor_redirect( request )


@csrf_exempt  # temp for migration
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


@csrf_exempt  # temp for migration
def shib_login( request ):
    """ Examines shib headers, sets session-auth.
        Redirects user to non-seen processor() view. """
    log.debug( 'starting shib_login()' )
    ( validity, shib_dict ) = shib_view_helper.check_shib_headers( request )
    if validity is False:
        return_response = shib_view_helper.prep_login_redirect( request )
    else:
        request.session['sierra_patron_id'] = shib_view_helper.sierra_patron_id
        return_response = shib_view_helper.build_response( request, shib_dict )
    log.debug( 'about to return shib response' )
    return return_response


@csrf_exempt  # temp for migration
def processor( request ):
    """ Handles item request:,
        - Ensures user is authenticated.
        - Saves request.
        - Places hold.
        - Emails patron.
        - Triggers shib_logout() view. """
    if processor_helper.check_request( request ) == False:
        return HttpResponseRedirect( reverse('info_url') )
    try:
        itmrqst = processor_helper.save_data( request )
        # processor_helper.place_request( itmrqst, request.session['josiah_api_name'], request.session['pickup_location'] )
        processor_helper.place_request( itmrqst.item_id, request.session['pickup_location'], request.session['sierra_patron_id'] )
    except:
        log.exception( 'exception placing request; traceback follows, but processing will continue with problem display to user.' )
        return HttpResponseRedirect( reverse('problem_url') )  # where retry, and contact info message will appear
    processor_helper.email_patron( itmrqst.patron_email, itmrqst.patron_name, itmrqst.item_title, itmrqst.item_callnumber, itmrqst.item_bib, itmrqst.item_id, itmrqst.patron_barcode, itmrqst.item_barcode, request.session['pickup_location'] )
    return HttpResponseRedirect( reverse('logout_url') )  # shib_logout() view


@csrf_exempt  # temp for migration
def shib_logout( request ):
    """ Clears session, hits shib logout.
        Redirects user to summary() view. """
    redirect_url = shib_logout_helper.build_redirect_url( request )
    request.session['shib_authorized'] = False
    logout( request )  # from django.contrib.auth import logout
    if request.get_host() == '127.0.0.1' and project_settings.DEBUG == True:  # eases local development
        pass
    else:
        encoded_redirect_url = urlquote( redirect_url )  # django's urlquote()
        redirect_url = '%s?return=%s' % ( os.environ['EZRQST__SHIB_LOGOUT_URL_ROOT'], encoded_redirect_url )
    log.debug( 'final redirect_url, `%s`' % redirect_url )
    return HttpResponseRedirect( redirect_url )


def summary( request ):
    """ Displays final summary screen. """
    EMAIL = os.environ['EZRQST__EMAIL_GENERAL_HELP']
    PHONE = os.environ['EZRQST__PHONE_GENERAL_HELP']
    context = summary_helper.build_main_context( request, EMAIL, PHONE )
    context['pattern_header'] = common.grab_pattern_header()
    context['pattern_header_active'] = json.loads( os.environ['EZRQST__PATTERN_HEADER_ACTIVE_JSON'] )
    if request.GET['source_url'][0:4] == 'http':
        context['source_url'] = request.GET['source_url']  # template will only show it if it exists
    if request.GET.get('format', '') == 'json':
        context_json = json.dumps(context, sort_keys=True, indent=2)
        resp = HttpResponse( context_json, content_type='application/javascript; charset=utf-8' )
    else:
        if context['pattern_header_active'] == True:
            template = 'easyrequest_app_templates/summary_02.html'
        else:
            template = 'easyrequest_app_templates/summary.html'
        resp = render( request, template, context )
    return resp


@csrf_exempt  # temp for migration
def problem( request ):
    """ Displays problem screen. """
    context = {
        'EMAIL': os.environ['EZRQST__EMAIL_GENERAL_HELP'],
        'PHONE': os.environ['EZRQST__PHONE_GENERAL_HELP']
        }
    logout(request)  # from django.contrib.auth import logout
    emailer.email_admin()
    return render( request, 'easyrequest_app_templates/problem.html', context )


@csrf_exempt  # temp for migration
def stats_v1( request ):
    """ Prepares stats for given dates; returns json. """
    log.debug( 'starting stats_v1()' )
    ## grab & validate params
    if stats_builder.check_params( request.GET, request.META[u'SERVER_NAME'] ) == False:
        return HttpResponseBadRequest( stats_builder.output, content_type=u'application/javascript; charset=utf-8' )
    ## query records for period (parse them via source)
    requests = stats_builder.run_query()
    ## process results
    data = stats_builder.process_results( requests )
    ## build response
    stats_builder.build_response( data )
    return HttpResponse( stats_builder.output, content_type=u'application/javascript; charset=utf-8' )


# ===========================
# for development convenience
# ===========================


def version( request ):
    """ Returns basic branch and commit data. """
    rq_now = datetime.datetime.now()
    commit = version_helper.get_commit()
    branch = version_helper.get_branch()
    info_txt = commit.replace( 'commit', branch )
    context = version_helper.make_context( request, rq_now, info_txt )
    output = json.dumps( context, sort_keys=True, indent=2 )
    return HttpResponse( output, content_type='application/json; charset=utf-8' )


def error_check( request ):
    """ For checking that admins receive error-emails. """
    if project_settings.DEBUG == True:
        1/0
    else:
        return HttpResponseNotFound( '<div>404 / Not Found</div>' )
