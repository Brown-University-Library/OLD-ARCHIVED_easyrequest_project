# -*- coding: utf-8 -*-

import datetime, json, logging, os, pprint, time, urllib
import requests
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.encoding import smart_text
from django.utils.http import urlquote
from easyrequest_app.lib import common
from easyrequest_app.lib.sierra import SierraHelper
# from iii_account import IIIAccount
from requests.auth import HTTPBasicAuth


log = logging.getLogger(__name__)


## db model ##


class ItemRequest( models.Model ):
    """ Contains user & item data.
        Called by Processor(). """
    item_title = models.CharField( blank=True, max_length=200 )
    status = models.CharField( max_length=200 )
    item_bib = models.CharField( blank=True, max_length=50 )
    item_id = models.CharField( blank=True, max_length=50 )
    item_barcode = models.CharField( blank=True, max_length=50 )
    item_callnumber = models.CharField( blank=True, max_length=200 )
    patron_name = models.CharField( blank=True, max_length=100 )  # patron full name
    patron_barcode = models.CharField( blank=True, max_length=50 )
    patron_email = models.CharField( blank=True, max_length=100 )
    source_url = models.TextField( blank=True )
    create_datetime = models.DateTimeField( auto_now_add=True, blank=True )  # blank=True for backward compatibility
    admin_notes = models.TextField( blank=True )

    # def __unicode__(self):
    #     return smart_text( 'id: %s || title: %s' % (self.id, self.item_title) , 'utf-8', 'replace' )

    def __str__(self):
        return smart_text( 'id: %s || title: %s' % (self.id, self.item_title) , 'utf-8', 'replace' )

    def jsonify(self):
        """ Returns object data in json-compatible dict. """
        jsn = serializers.serialize( 'json', [self] )  # json string is single-item list
        lst = json.loads( jsn )
        object_dct = lst[0]
        return ItemRequest

    # end class ItemRequest


## non db models below  ##


class LoginHelper( object ):
    """ Contains helpers for views.request_def() for handling GET. """

    def __init__( self ):
        """ Holds env-vars. """
        self.AVAILABILITY_API_URL_ROOT = os.environ['EZRQST__AVAILABILITY_API_URL_ROOT']
        self.PHONE_AUTH_HELP = os.environ['EZRQST__PHONE_AUTH_HELP']
        self.EMAIL_AUTH_HELP = os.environ['EZRQST__EMAIL_AUTH_HELP']
        self.LEGIT_SOURCES = json.loads( os.environ['EZRQST__LEGIT_SOURCES_JSON'] )
        self.pic_loc_helper = PickupLocation()
        self.problems = []

    def validate_source( self, request ):
        """ Ensures app is accessed from legit source.
            Called by views.login() """
        return_val = False
        if '127.0.0.1' in request.get_host() and project_settings.DEBUG == True:
            return_val = True
        referrer_host = self.get_referrer_host( request.META.get('HTTP_REFERER', 'unavailable') )
        if referrer_host in self.LEGIT_SOURCES:
            return_val = True
        else:
            log.debug( 'referrer_host, `%s`' % referrer_host )
        log.info( 'return_val, `%s`' % return_val )
        return return_val

    def get_referrer_host( self, referrer_url ):
        """ Extracts host from referrer_url.
            Called by validate_source() """
        # output = urlparse.urlparse( referrer_url )
        output = urllib.parse.urlparse( referrer_url )
        host = output.netloc
        log.info( 'referrer host, `%s`' % host )
        return host

    # def validate_params( self, request ):
    #     """ Checks params.
    #         Called by views.login()
    #         Note: `barcode` here is the item-barcode. """
    #     return_val = False
    #     if sorted( request.GET.keys() ) == ['barcode', 'bibnum']:
    #         if len(request.GET['bibnum']) == 8 and len(request.GET['barcode']) == 14:
    #             return_val = True
    #     log.info( 'return_val, `%s`' % return_val )
    #     return return_val

    def validate_params( self, querydict ):
        """ Checks params.
            Called by views.login() """
        return_val = False
        self.problems = []
        if 'itemnum' not in querydict.keys():
            self.problems.append( 'no item-number submitted' )
        # if 'barcode' not in querydict.keys():
        #     self.problems.append( 'no item-barcode submitted' )
        # else:
        #     if len( querydict['barcode'] ) != 14:
        #         self.problems.append( 'invalid item-barcode submitted' )
        if 'bibnum' not in querydict.keys():
            self.problems.append( 'no item-bib-number submitted' )
        else:
            if len( querydict['bibnum'] ) != 8:
                self.problems.append( 'invalid item-bib-number submitted' )
        if len( self.problems ) == 0:
            return_val = True
        log.info( 'return_val, `%s`' % return_val )
        log.info( 'self.problems, ``%s``' % self.problems )
        return return_val

    # def initialize_session( self, request ):
    #     """ Initializes session.
    #         Called by views.login() """
    #     self._initialize_session_item_info( request )
    #     self._initialize_session_user_info( request )
    #     source_url = request.META.get( 'HTTP_REFERER', 'unavailable' ).strip()
    #     request.session.setdefault( 'source_url', source_url )  # ensures initial valid referrer is stored, and not localhost if there's a server redirect on a login-error
    #     request.session.setdefault( 'shib_login_error', False )
    #     request.session['shib_authorized'] = False
    #     request.session.setdefault( 'barcode_login_error', False)
    #     request.session['barcode_authorized'] = False
    #     log.debug( 'request.session after initialization, `%s`' % pprint.pformat(request.session.items()) )
    #     log.info( 'bib, `%s`' % request.session.get('item_bib', None) )
    #     return

    def initialize_session( self, request ):
        """ Initializes session.
            Called by views.login() """
        self._initialize_session_item_info( request )
        self._initialize_session_user_info( request )
        source_url = request.META.get( 'HTTP_REFERER', 'unavailable' ).strip()
        request.session.setdefault( 'source_url', source_url )  # ensures initial valid referrer is stored, and not localhost if there's a server redirect on a login-error
        request.session.setdefault( 'shib_login_error', False )
        request.session['shib_authorized'] = False
        request.session.setdefault( 'barcode_login_error', False)
        request.session['barcode_authorized'] = False
        log.debug( 'request.session after initialization, `%s`' % pprint.pformat(request.session.items()) )
        log.info( 'bib, `%s`' % request.session.get('item_bib', None) )
        return

    def _initialize_session_item_info( self, request ):
        """ Initializes session item info.
            Called by initialize_session() """
        request.session.setdefault( 'item_title', '' )
        request.session['item_bib'] = request.GET['bibnum']
        # request.session.setdefault( 'item_id', '' )
        request.session['item_id'] = request.GET['itemnum']
        # request.session['item_barcode'] = request.GET['barcode']
        request.session.setdefault( 'item_callnumber', '' )
        request.session.setdefault( 'pickup_location', '' )
        return

    def _initialize_session_user_info( self, request ):
        """ Initializes session item info.
            Called by initialize_session() """
        request.session['user_full_name'] = ''  # for email
        request.session['user_last_name'] = ''  # for possible second josiah-api attempt if default shib firstname fails
        request.session['user_email'] = ''
        request.session.setdefault( 'barcode_login_name', '' )  # for barcode login form
        request.session.setdefault( 'barcode_login_barcode', '21236' )  # for barcode login form
        request.session['josiah_api_barcode'] = ''  # for josiah-patron-accounts call
        request.session['josiah_api_name'] = ''  # for josiah-patron-accounts call
        return

    # def get_item_info( self, bibnum, item_barcode ):
    #     """ Hits availability-api for bib-title, and item id and callnumber.
    #         Bib title and item callnumber are just for user display; item id needed if user proceeds.
    #         Called by views.login() """
    #     ( title, callnumber, item_id ) = ( '', '', '' )
    #     api_dct = self.hit_availability_api( bibnum )
    #     try:
    #         title = api_dct['response']['bib']['title']
    #     except:
    #         log.exception( 'unable to access title; traceback follows, but processing will continue' )
    #         title = 'title unavailable'
    #     ( callnumber, item_id ) = self.process_items( api_dct, item_barcode )
    #     log.debug( 'title, `%s`; callnumber, `%s`; item_id, `%s`' % (title, callnumber, item_id) )
    #     return ( title, callnumber, item_id )

    def get_item_info( self, bibnum, item_id ):
        """ Hits availability-api for bib-title, and item id and callnumber.
            Bib title and item callnumber are just for user display; item id needed if user proceeds.
            Called by views.login() """
        ( title, callnumber ) = ( '', '' )
        api_dct = self.hit_availability_api( bibnum )
        try:
            title = api_dct['response']['bib']['title']
        except:
            log.exception( 'unable to access title; traceback follows, but processing will continue' )
            title = 'title unavailable'
        callnumber = self.process_items( api_dct, item_id )
        log.debug( 'title, `%s`; callnumber, `%s`; item_id, `%s`' % (title, callnumber, item_id) )
        return ( title, callnumber, item_id )

    def hit_availability_api( self, bibnum ):
        """ Returns availability-api dict.
            Called by get_item_info() """
        dct = {}
        try:
            availability_api_url = '%s/v2/bib_items/%s' % ( self.AVAILABILITY_API_URL_ROOT, bibnum )
            log.info( 'availability_api_url, ```%s```' % availability_api_url )
            r = requests.get( availability_api_url, timeout=15 )
            dct = r.json()
            log.info( 'partial availability-api-response, ```%s```' % pprint.pformat(dct)[0:200] )
            # log.debug( 'full availability-api-response, ```%s```' % pprint.pformat(dct) )
        except Exception as e:
            # log.error( 'exception, %s' % unicode(repr(e)) )
            log.exception( 'unable to hit availability-api; traceback follows, but processing continues' )
        return dct

    # def process_items( self, api_dct, item_barcode ):
    #     """ Extracts the callnumber and item_id from availability-api response.
    #         Called by get_item_info() """
    #     log.debug( 'starting process_items()' )
    #     ( callnumber, item_id ) = ( '', '' )
    #     try:
    #         items = api_dct['response']['items']
    #         for item in items:
    #             if item_barcode == item['barcode']:
    #                 callnumber = item['callnumber']
    #                 item_id = item['item_id'][:-1]  # removes trailing check-digit
    #     except:
    #         log.exception( 'unable to process results; traceback follows, but processing continues' )
    #     # log.debug( 'process_items result, `%s`' % unicode(repr((callnumber, item_id))) )
    #     log.debug( 'process_items result, `%s`' % repr((callnumber, item_id)) )
    #     return ( callnumber, item_id )

    def process_items( self, api_dct, item_id ):
        """ Extracts the callnumber from availability-api response.
            Called by get_item_info() """
        log.debug( 'starting process_items()' )
        callnumber = ''
        try:
            items = api_dct['response']['items']
            for item in items:
                if item_id == item['item_id']:
                    callnumber = item['callnumber']
                    # item_id = item['item_id'][:-1]  # removes trailing check-digit
        except:
            log.exception( 'unable to process results; traceback follows, but processing continues' )
        # log.debug( 'process_items result, `%s`' % unicode(repr((callnumber, item_id))) )
        log.debug( f'extracted callnumber, ``{callnumber}``' )
        return callnumber

    def update_session( self, request, title, callnumber, item_id ):
        """ Updates session.
            Called by views.login() """
        request.session['item_title'] = title
        request.session['item_callnumber'] = callnumber
        request.session['item_id'] = item_id
        log.debug( 'request.session after update, `%s`' % pprint.pformat(request.session.items()) )
        return

    def prepare_context( self, request ):
        """ Prepares vars for template.
            Called by views.login() """
        context = {
            'title': request.session['item_title'] ,
            'callnumber': request.session['item_callnumber'],
            'ROCK_code': self.pic_loc_helper.pickup_location_dct['ROCK']['code'],
            'ROCK_display': self.pic_loc_helper.pickup_location_dct['ROCK']['display'],
            'SCI_code': self.pic_loc_helper.pickup_location_dct['SCI']['code'],
            'SCI_display': self.pic_loc_helper.pickup_location_dct['SCI']['display'],
            'HAY_code': self.pic_loc_helper.pickup_location_dct['HAY']['code'],
            'HAY_display': self.pic_loc_helper.pickup_location_dct['HAY']['display'],
            'ORWIG_code': self.pic_loc_helper.pickup_location_dct['ORWIG']['code'],
            'ORWIG_display': self.pic_loc_helper.pickup_location_dct['ORWIG']['display'],
            'barcode_form_action_url': reverse( 'barcode_handler_url' ),
            'barcode_login_name': request.session['barcode_login_name'],
            'barcode_login_barcode': request.session['barcode_login_barcode'],
            'barcode_login_error': request.session['barcode_login_error'],
            'shib_form_action_url': reverse( 'shib_handler_url' ),
            'shib_login_error': request.session['shib_login_error'],
            'PHONE_AUTH_HELP': self.PHONE_AUTH_HELP,
            'EMAIL_AUTH_HELP': self.EMAIL_AUTH_HELP,
            'pattern_header': common.grab_pattern_header(),
            'pattern_header_active': json.loads( os.environ['EZRQST__PATTERN_HEADER_ACTIVE_JSON'] ),
            }
        log.debug( 'context, ```%s```' % pprint.pformat(context) )
        return context

    # end class LoginHelper


class BarcodeHandlerHelper( object ):
    """ Contains helpers for views.barcode_handler() """

    def __init__( self ):
        self.PATRON_API_URL = os.environ['EZRQST__PAPI_URL']
        self.PATRON_API_BASIC_AUTH_USERNAME = os.environ['EZRQST__PAPI_BASIC_AUTH_USERNAME']
        self.PATRON_API_BASIC_AUTH_PASSWORD = os.environ['EZRQST__PAPI_BASIC_AUTH_PASSWORD']

    def validate_params( self, request ):
        """ Validates params.
            Returns boolean.
            Called by views.barcode_handler() """
        return_val = False
        log.debug( 'request.POST, `%s`' % pprint.pformat(request.POST) )
        log.debug( "request.POST['pickup_location'], `%s`" % pprint.pformat(request.POST['pickup_location']) )
        if sorted( request.POST.keys() ) == ['barcode_login_barcode', 'barcode_login_name', 'csrfmiddlewaretoken', 'pickup_location']:
            request.session['barcode_login_name'] = request.POST['barcode_login_name']
            request.session['barcode_login_barcode'] = request.POST['barcode_login_barcode']
            request.session['pickup_location'] = request.POST['pickup_location']
            if len(request.POST['barcode_login_name']) > 0 and len(request.POST['barcode_login_barcode']) > 13:
                return_val = True
        log.debug( 'validate_params return_val, `%s`' % return_val )
        return return_val

    def prep_login_redirect( self, request ):
        """ Prepares redirect response-object to views.login() on bad source or params or authNZ.
            Called by views.barcode_handler() """
        request.session['barcode_login_error'] = 'Problem with username and password.'
        redirect_url = '%s?bibnum=%s&barcode=%s' % ( reverse('login_url'), request.session['item_bib'], request.session['item_barcode'] )
        log.debug( 'redirect_url, `%s`' % redirect_url )
        resp = HttpResponseRedirect( redirect_url )
        return resp

    def authenticate( self, barcode_login_name, barcode_login_barcode ):
        """ Checks submitted login-name and login-barcode; returns boolean.
            Called by views.barcode_handler() """
        return_val = False
        jos_sess = IIIAccount( barcode_login_name, barcode_login_barcode )
        try:
            jos_sess.login()
            return_val = True
            jos_sess.logout()
        except Exception as e:
            log.debug( 'exception on login-try, `%s`' % repr(e) )
        log.debug( 'authenticate barcode login check, `%s`' % return_val )
        return return_val

        # papi_helper = models.PatronApiHelper()

    def authorize( self, patron_barcode ):
        """ Directs call to patron-api service; returns patron name and email address.
            Called by views.barcode_handler() """
        patron_info_dct = False
        papi_helper = PatronApiHelper( patron_barcode )
        if papi_helper.ptype_validity is not False:
            if papi_helper.patron_email is not None:
                patron_info_dct = {
                    'patron_name': papi_helper.patron_name,  # last, first middle,
                    'patron_email': papi_helper.patron_email }
        log.debug( 'authorize patron_info_dct, `%s`' % patron_info_dct )
        return patron_info_dct

    def update_session( self, request, patron_info_dct ):
        """ Updates session before redirecting to views.processor()
            Called by views.barcode_handler() """
        request.session['barcode_authorized'] = True
        request.session['josiah_api_name'] = request.session['barcode_login_name']
        request.session['josiah_api_barcode'] = request.session['barcode_login_barcode']
        request.session['user_full_name'] = patron_info_dct['patron_name']
        request.session['user_email'] = patron_info_dct['patron_email']
        return

    def prep_processor_redirect( self, request ):
        """ Prepares redirect response-object to views.process() on good login.
            Called by views.barcode_handler() """
        scheme = 'https' if request.is_secure() else 'http'
        redirect_url = '%s://%s%s' % ( scheme, request.get_host(), reverse('processor_url') )
        log.debug( 'redirect_url, `%s`' % redirect_url )
        resp = HttpResponseRedirect( redirect_url )
        log.debug( 'returning barcode_handler response' )
        return resp

    # end class BarcodeHandlerHelper


class ShibViewHelper( object ):
    """ Contains helpers for views.shib_login() """

    def __init__( self ):
        self.sierra_patron_id = None

    def check_shib_headers( self, request ):
        """ Grabs and checks shib headers, returns boolean.
            Called by views.shib_login() """
        shib_checker = ShibChecker()
        shib_dict = shib_checker.grab_shib_info( request )
        validity = shib_checker.evaluate_shib_info( shib_dict )
        self.sierra_patron_id = shib_checker.sierra_patron_id
        log.debug( 'returning shib validity `%s`' % validity )
        return ( validity, shib_dict )

    def prep_login_redirect( self, request ):
        """ Prepares redirect response-object to views.login() on bad authZ (p-type problem).
            Called by views.shib_login() """
        request.session['shib_login_error'] = 'Problem on authorization.'
        request.session['shib_authorized'] = False
        redirect_url = '%s?bibnum=%s&barcode=%s' % ( reverse('login_url'), request.session['item_bib'], request.session['item_barcode'] )
        log.debug( 'ShibViewHelper redirect_url, `%s`' % redirect_url )
        resp = HttpResponseRedirect( redirect_url )
        return resp

    def build_response( self, request, shib_dict ):
        """ Sets session vars and redirects to the hidden processor page.
            Called by views.shib_login() """
        log.debug( 'starting ShibViewHelper.build_response()' )
        self.update_session( request, shib_dict )
        scheme = 'https' if request.is_secure() else 'http'
        redirect_url = '%s://%s%s' % ( scheme, request.get_host(), reverse('processor_url') )
        log.debug( 'leaving ShibViewHelper; redirect_url `%s`' % redirect_url )
        return_response = HttpResponseRedirect( redirect_url )
        log.debug( 'returning shib response' )
        return return_response

    def update_session( self, request, shib_dict ):
        """ Updates session with shib info.
            Called by build_response() """
        request.session['shib_login_error'] = False
        request.session['shib_authorized'] = True
        request.session['user_full_name'] = '%s %s' % ( shib_dict['firstname'], shib_dict['lastname'] )
        request.session['user_last_name'] = shib_dict['lastname']
        request.session['user_email'] = shib_dict['email']
        request.session['shib_login_error'] = False
        request.session['josiah_api_name'] = shib_dict['firstname']
        request.session['josiah_api_barcode'] = shib_dict['patron_barcode']
        log.debug( 'ShibViewHelper.update_session() completed' )
        return

    # end class ShibViewHelper


class ShibChecker( object ):
    """ Contains helpers for checking Shib.
        Called by ShibViewHelper """

    def __init__( self ):
        self.TEST_SHIB_JSON = os.environ.get( 'EZRQST__TEST_SHIB_JSON', '' )
        self.SHIB_ERESOURCE_PERMISSION = os.environ['EZRQST__SHIB_ERESOURCE_PERMISSION']
        self.sierra_patron_id = None  # will be populated by self.authorized()

    def grab_shib_info( self, request ):
        """ Grabs shib values from http-header or dev-settings.
            Called by models.ShibViewHelper.check_shib_headers() """
        log.debug( 'request.__dict__, ```%s```' % pprint.pformat(request.__dict__) )
        shib_dict = {}
        # if 'Shibboleth-eppn' in request.META:
        if 'HTTP_SHIBBOLETH_EPPN' in request.META:
            shib_dict = self.grab_shib_from_meta( request )
        else:
            # log.debug( 'HERE-A' )
            # log.debug( 'request.get_host(), `%s`' % request.get_host() )
            # log.debug( 'project_settings.DEBUG, `%s`' % project_settings.DEBUG )
            if '127.0.0.1' in request.get_host() and project_settings.DEBUG == True:
                shib_dict = json.loads( self.TEST_SHIB_JSON )
        log.debug( 'in models.ShibChecker.grab_shib_info(); shib_dict is: %s' % pprint.pformat(shib_dict) )
        return shib_dict

    def grab_shib_from_meta( self, request ):
        """ Extracts shib values from http-header.
            Called by grab_shib_info() """
        shib_dict = {
            'eppn': request.META.get( 'HTTP_SHIBBOLETH_EPPN', '' ),
            'firstname': request.META.get( 'HTTP_SHIBBOLETH_GIVENNAME', '' ),
            'lastname': request.META.get( 'HTTP_SHIBBOLETH_SN', '' ),
            'email': request.META.get( 'HTTP_SHIBBOLETH_MAIL', '' ).lower(),
            'patron_barcode': request.META.get( 'HTTP_SHIBBOLETH_BROWNBARCODE', '' ),
            'member_of': request.META.get( 'HTTP_SHIBBOLETH_ISMEMBEROF', '' ) }
        return shib_dict

    def evaluate_shib_info( self, shib_dict ):
        """ Returns boolean.
            Called by models.ShibViewHelper.check_shib_headers() """
        validity = False
        if self.all_values_present(shib_dict) and self.brown_user_confirmed(shib_dict) and self.authorized(shib_dict['patron_barcode']):
            validity = True
        log.debug( 'in models.ShibChecker.evaluate_shib_info(); validity, `%s`' % validity )
        return validity

    def all_values_present( self, shib_dict ):
        """ Returns boolean.
            Called by evaluate_shib_info() """
        present_check = False
        if sorted( shib_dict.keys() ) == ['email', 'eppn', 'firstname', 'lastname', 'member_of', 'patron_barcode']:
            value_test = 'init'
            for (key, value) in shib_dict.items():
                if len( value.strip() ) == 0:
                    value_test = 'fail'
            if value_test == 'init':
                present_check = True
        log.debug( 'in models.ShibChecker.all_values_present(); present_check, `%s`' % present_check )
        return present_check

    def brown_user_confirmed( self, shib_dict ):
        """ Returns boolean.
            Called by evaluate_shib_info() """
        brown_check = False
        if '@brown.edu' in shib_dict['eppn']:
            brown_check = True
        log.debug( 'in models.ShibChecker.brown_user_confirmed(); brown_check, `%s`' % brown_check )
        return brown_check

    def authorized( self, patron_barcode ):
        """ Returns boolean.
            Called by evaluate_shib_info() """
        authZ_check = False
        papi_helper = PatronApiHelper( patron_barcode )
        self.sierra_patron_id = papi_helper.sierra_patron_id
        if papi_helper.ptype_validity is True:
            authZ_check = True
        log.debug( 'authZ_check, `%s`' % authZ_check )
        return authZ_check

    # end class ShibChecker


class PickupLocation( object ):
    """ Holds pickup-location info for display, and for placing hold.
        Called by models.LoginHelper.__init__(),
                  models.Processor.prep_pickup_location_display(), and
                  models.ShibLogoutHelper.build_redirect_url() """

    def __init__( self ):
        """ dct structure example: { 'ROCK': {'code': 'r0001', 'display': 'Rockefeller Library'}, etc... } """
        self.pickup_location_dct = json.loads( os.environ['EZRQST__PICKUP_LOCATION_JSON'] )
        self.code_to_display_dct = {}
        self.process_dct()

    def process_dct( self ):
        """ Creates another dct from the env json like: { 'sci': 'Sciences Library', 'h0001': 'John Hay Library', etc... }.
            Triggered by __init__() """
        new_dct = {}
        for ( key, val ) in self.pickup_location_dct.items():
            # log.debug( 'key, `%s`' % key ); log.debug( 'val, `%s`' % val )
            new_key = val['code']
            new_val = val['display']
            new_dct[ new_key ] = new_val
        log.debug( 'new_dct, `%s`' % new_dct )
        self.code_to_display_dct = new_dct

    # end class PickupLocation


class Processor( object ):
    """ Handles item-hold and email functions. """

    def __init__( self ):
        self.EMAIL_FROM = os.environ['EZRQST__EMAIL_FROM']
        self.EMAIL_REPLY_TO = os.environ['EZRQST__EMAIL_REPLY_TO']
        self.EMAIL_GENERAL_HELP = os.environ['EZRQST__EMAIL_GENERAL_HELP']
        self.PHONE_GENERAL_HELP = os.environ['EZRQST__PHONE_GENERAL_HELP']
        self.email_subject = 'Brown University Library - Request Confirmation'

    def check_request( self, request ):
        """ Ensures user has logged in.
            Called by views.processor() """
        request.session['shib_login_error'] = False  # reset
        request.session['barcode_login_error'] = False  # reset
        return_val = False
        if ( request.session.get('shib_authorized', False) is True ) or ( request.session.get('barcode_authorized', False) is True ):
            return_val = True
        log.debug( 'check_request() result, `%s`' % return_val )
        return return_val

    def save_data( self, request ):
        """ Saves data for 'try-again' feature.
            Called by views.processor() """
        itmrqst = ItemRequest()
        itmrqst = self.save_item_data( itmrqst, request )
        itmrqst = self.save_user_data( itmrqst, request )
        itmrqst.source_url = request.session['source_url']
        itmrqst.status = 'in_process'
        itmrqst.save()
        log.debug( 'data saved' )
        return itmrqst

    def save_item_data( self, itmrqst, request ):
        """ Saves item data from session to db.
            Called by save_data() """
        # log.debug( 'starting save_item_data() request.session, `%s`' % pprint.pformat(request.session.items()) )
        try:
            itmrqst.item_title = request.session['item_title']
            itmrqst.item_bib = request.session['item_bib']
            itmrqst.item_id = request.session['item_id']
            # itmrqst.item_barcode = request.session['item_barcode']
            itmrqst.item_barcode = request.session.get('item_barcode', '' )
            itmrqst.item_callnumber = request.session['item_callnumber']
            itmrqst.save()
        except Exception as e:
            log.debug( 'Exception; session, `%s`' % pprint.pformat(request.session.items()) )
            log.error( 'Exception, `%s`' % repr(e) )
            raise Exception( 'Unable to save item-data.' )
        return itmrqst

    def save_user_data( self, itmrqst, request ):
        """ Saves user data from session to db.
            Called by save_data() """
        try:
            itmrqst.patron_name = request.session['user_full_name']
            itmrqst.patron_barcode = request.session['josiah_api_barcode']
            itmrqst.patron_email = request.session['user_email']
            itmrqst.save()
        except Exception as e:
            log.error( 'Exception, `%s`' % repr(e) )
            raise Exception( 'Unable to save user-data.' )
        return itmrqst

    # def place_request( self, item_id, pickup_location_code, patron_sierra_id ) -> None:
    #     """ Coordinates sierra-api call.
    #         Called by views.processor()
    #         TODO: think about good problem-handling. """
    #     log.debug( f'starting place_request() with item_id, ``{item_id}`` and pickup_location_code, ``{pickup_location_code}`` and patron_sierra_id, ``{patron_sierra_id}``' )
    #     sierra_helper = SierraHelper()
    #     data_dct = sierra_helper.build_data( item_id, pickup_location_code )
    #     sierra_helper.manage_place_hold( data_dct, patron_sierra_id )
    #     log.debug( f'hold_result, `%s`' % sierra_helper.hold_status )
    #     return

    def place_request( self, item_id, pickup_location_code, patron_sierra_id ) -> None:
        """ Coordinates sierra-api call.
            Called by views.processor()
            TODO: think about good problem-handling. """
        log.debug( f'starting place_request() with item_id, ``{item_id}`` and pickup_location_code, ``{pickup_location_code}`` and patron_sierra_id, ``{patron_sierra_id}``' )
        modified_item_id = item_id[:-1]  # removes trailing check-digit for Sierra API
        log.debug( f'modified_item_id, ``{modified_item_id}``' )
        sierra_helper = SierraHelper()
        data_dct = sierra_helper.build_data( modified_item_id, pickup_location_code )
        sierra_helper.manage_place_hold( data_dct, patron_sierra_id )
        log.debug( f'hold_result, `%s`' % sierra_helper.hold_status )
        return

    def email_patron( self, patron_email, patron_name, item_title, item_callnumber, item_bib, item_id, patron_barcode, item_barcode, pickup_location_code ):
        """ Emails patron confirmation.
            Called by views.processor() """
        try:
            pickup_location_display = self.prep_pickup_location_display( pickup_location_code )
            body = self.build_email_body( patron_name, item_title, item_callnumber, item_bib, item_id, patron_barcode, item_barcode, pickup_location_display )
            ffrom = self.EMAIL_FROM  # `from` reserved
            to = [ patron_email ]
            extra_headers = { 'Reply-To': self.EMAIL_REPLY_TO }
            email = EmailMessage( self.email_subject, body, ffrom, to, headers=extra_headers )
            email.send()
            log.debug( 'mail sent' )
        except Exception as e:
            log.exception( 'Problem sending email; exception follows; processing will continue.' )
        return

    def prep_pickup_location_display( self, pickup_location_code ):
        """ Returns pickup-location-display string.
            Called by email_patron() """
        pic_loc = PickupLocation()
        pickup_location_display = pic_loc.code_to_display_dct[ pickup_location_code ]
        return pickup_location_display

    def build_email_body( self,  patron_name, item_title, item_callnumber, item_bib, item_id, patron_barcode, item_barcode, pickup_location_display ):
        """ Prepares and returns email body.
            Called by email_patron().
            TODO: use render_to_string & template. """
        body = '''Greetings %s,

This is a confirmation of your request for the item...

Title: %s
Call Number: %s

Requested items are generally available within 96 hours. You will receive an email when the item is available for pickup at the %s.

If you have questions, feel free to email %s, and refer to...

- Bibliographic #: "%s"
- Item #: "%s"
- User barcode: "%s"
- Item barcode: "%s"

::: easyRequest -- a service of the Brown University Library :::
''' % (
            patron_name,
            item_title,
            item_callnumber,
            pickup_location_display,
            self.EMAIL_GENERAL_HELP,
            item_bib,
            item_id,
            patron_barcode,
            item_barcode
            )
        return body

    # end class Processor


class ShibLogoutHelper( object ):
    """ Assists shib_logout() view. """

    def build_redirect_url( self, request ):
        """ Returns initial redirect-url.
            Called by views.shib_logout() """
        scheme = 'https' if request.is_secure() else 'http'
        item_title = request.session['item_title']
        if len( item_title ) > 50:
            item_title = '%s...' % item_title[0:45]
        pic_loc = PickupLocation()
        pickup_location_code = request.session['pickup_location']
        pickup_location_display = pic_loc.code_to_display_dct[ pickup_location_code ]
        source_url = urlquote( request.session['source_url'] )  # django's urlquote, imported above
        redirect_url = self.assemble_url( scheme, request, item_title, pickup_location_display, source_url )
        log.debug( 'initial redirect_url, `%s`' % redirect_url )
        return redirect_url

    def assemble_url( self, scheme, request, item_title, pickup_location_display, source_url ):
        """ Format's url.
            Called by build_redirect_url() """
        redirect_url = '%s://%s%s?bib=%s&callnumber=%s&item_id=%s&title=%s&user_name=%s&user_email=%s&pic_loc=%s&source_url=%s' % (
            scheme, request.get_host(), reverse('summary_url'),  # beginning stuff
            request.session['item_bib'], request.session['item_callnumber'], request.session['item_id'], item_title,  # item stuff
            request.session['user_full_name'], request.session['user_email'],  # user stuff
            pickup_location_display, source_url  # other stuff
            )
        return redirect_url

    # end class ShibLogoutHelper


class SummaryHelper( object ):
    """ Assists summary() view. """

    def build_main_context( self, request, EMAIL, PHONE ):
        """ Builds and returns initial context.
            Called by views.summary() """
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
        return context

    # end class SummaryHelper


class PatronApiHelper( object ):
    """ Assists getting and evaluating patron-api data.
        Used by BarcodeHandlerHelper() and ShibChecker(). """

    def __init__( self, patron_barcode ):
        self.PATRON_API_URL = os.environ['EZRQST__PAPI_URL']
        self.PATRON_API_BASIC_AUTH_USERNAME = os.environ['EZRQST__PAPI_BASIC_AUTH_USERNAME']
        self.PATRON_API_BASIC_AUTH_PASSWORD = os.environ['EZRQST__PAPI_BASIC_AUTH_PASSWORD']
        self.PATRON_API_LEGIT_PTYPES = json.loads( os.environ['EZRQST__PAPI_LEGIT_PTYPES_JSON'] )
        self.ptype_validity = False
        self.patron_name = None  # will be last, first middle (used only by BarcodeHandler)
        self.patron_email = None  # will be lower-case (used only by BarcodeHandler)
        self.sierra_patron_id = None # will be extracted by self.extract_sierra_patron_id()
        self.process_barcode( patron_barcode )

    def process_barcode( self, patron_barcode ):
        """ Hits patron-api and populates attributes.
            Called by __init__(); triggered by BarcodeHandlerHelper.authorize() and ShibChecker.authorized()
            Note: If patron-api email does not exist, will not block shib-login flow, but will block barcode-login flow.
            """
        api_dct = self.hit_api( patron_barcode )
        if api_dct is False:
            return
        self.ptype_validity = self.check_ptype( api_dct )
        self.sierra_patron_id = self.extract_sierra_patron_id( api_dct )
        if self.ptype_validity is False:
            return
        self.patron_name = api_dct['response']['patrn_name']['value']  # last, first middle
        if 'e-mail' in api_dct['response'].keys():
            self.patron_email = api_dct['response']['e-mail']['value'].lower()
        else:
            log.warning( 'no email found in patron-api response; a shib-login will proceed, but a barcode-login will fail' )
        return

    def hit_api( self, patron_barcode ):
        """ Runs web-query.
            Called by process_barcode() """
        try:
            r = requests.get( self.PATRON_API_URL, params={'patron_barcode': patron_barcode}, timeout=10, auth=(self.PATRON_API_BASIC_AUTH_USERNAME, self.PATRON_API_BASIC_AUTH_PASSWORD) )
            log.debug( 'full patron-api url, ```%s```' % r.url )
            r.raise_for_status()  # will raise an http_error if not 200
            # log.debug( 'r.content, `%s`' % unicode(r.content) )
            log.debug( f'r.content, ``{r.content}``' )
        except Exception as e:
            # log.error( 'exception, `%s`' % unicode(repr(e)) )
            log.exception( 'problem hitting patron-api; traceback follows, but processing will continue' )
            return False
        return r.json()

    def check_ptype( self, api_dct ):
        """ Sees if ptype is valid.
            Called by process_barcode() """
        return_val = False
        patron_ptype = api_dct['response']['p_type']['value']
        if patron_ptype in self.PATRON_API_LEGIT_PTYPES:
            return_val = True
        log.debug( 'ptype check, `%s`' % return_val )
        return return_val

    def extract_sierra_patron_id( self, api_dct ):
        """ Extracts and saves sierra-patron-id if possible.
            Called by process_barcode() """
        log.debug( f'patron-api-dct, ``{pprint.pformat(api_dct)}``' )
        try:
            self.sierra_patron_id = api_dct['response']['record_']['value'][1:]  # strips initial character from, eg, '=1234567'
            log.debug( f'sierra_patron_id, `{self.sierra_patron_id}`' )
        except:
            log.exception( 'problem extracting sierra-patron-id; traceback follows; returning `False`' )
            self.sierra_patron_id = False
        log.debug( f'self.sierra_patron_id, `{self.sierra_patron_id}`' )
        return self.sierra_patron_id

    # end class PatronApiHelper


class StatsBuilder( object ):
    """ Handles stats-api calls. """

    def __init__( self ):
        self.date_start = None  # set by check_params()
        self.date_end = None  # set by check_params()
        self.output = None  # set by build_response()
        self.count_buckets = None  # set by process_results() & _update_count_buckets()
        self.static_info = {
            'service': 'easyRequest',
            'stats_documentation': 'https://github.com/birkin/easyrequest_project/blob/master/README.md#stats' }

    def check_params( self, get_params, server_name ):
        """ Checks parameters; returns boolean.
            Called by views.stats_v1() """
        return_val = False
        if 'start_date' in get_params and 'end_date' in get_params:
            if self._validate_date( get_params['start_date'] ) is True and self._validate_date( get_params['end_date'] ) is True:
                self.date_start = '%s 00:00:00' % get_params['start_date']
                self.date_end = '%s 23:59:59' % get_params['end_date']
                return_val = True
        if return_val == False:
            self._handle_bad_params( get_params, server_name )
        log.debug( 'get_params, `%s`' % get_params )
        log.debug( 'check_params() return_val, `%s`' % return_val )
        return return_val

    def _validate_date( self, date_string ):
        """ Checks date-validity; returns boolean.
            Called by check_params() """
        return_val = False
        try:
            datetime.datetime.strptime( date_string, '%Y-%m-%d' )
            return_val = True
        except Exception as e:
            pass
        log.debug( '_validate_date() return_val, `%s`' % return_val )
        return return_val

    def run_query( self ):
        """ Queries db.
            Called by views.stats_v1() """
        requests = ItemRequest.objects.filter(
            create_datetime__gte=self.date_start).filter(create_datetime__lte=self.date_end)
        return requests

    def process_results( self, requests ):
        """ Extracts desired data from resultset.
            Called by views.stats_v1() """
        log.debug( 'starting process_results()' )
        self.count_buckets = {}
        data = { 'count_request_for_period': len(requests) }
        for item_request in requests:
            log.debug( 'item_request.source_url, `%s`' % item_request.source_url )
            # url_obj = urlparse.urlparse( item_request.source_url )
            url_obj = urllib.parse.urlparse( item_request.source_url )
            partial_path = self._make_partial_path( url_obj )
            self._update_count_buckets( url_obj, partial_path )
        data['count_breakdown'] = self.count_buckets
        return data

    def _make_partial_path( self, url_obj ):
        """ Returns partial url path.
            Called by process_results() """
        split_path = url_obj.path.split( '/' )  # from 'http://host:port/aa/bb/cc/?a=1&b=2' yields ['', 'aa', 'bb', 'cc', '']
        cleaned_split_path = [ element for element in split_path if ( len(element) > 0 ) ]
        if cleaned_split_path == ['unavailable']:
            return 'unavailable'
        partial_path = ''
        for segment in cleaned_split_path[0:2]:
            partial_path = partial_path + '/' + segment
        partial_path = partial_path + '...'
        log.debug( 'partial_path, `%s`' % partial_path )
        return partial_path

    def _update_count_buckets( self, url_obj, partial_path ):
        """ Populates counts of main url-paths.
            Called by process_results() """
        if url_obj.scheme == '':
            partial_url = partial_path
        else:
            partial_url = '%s://%s%s' % ( url_obj.scheme, url_obj.netloc, partial_path )
        if partial_url in self.count_buckets.keys():
            self.count_buckets[partial_url] += 1
        else:
            self.count_buckets[partial_url] = 1
        log.debug( 'count buckets updated' )
        return

    def build_response( self, data ):
        """ Builds json response.
            Called by views.stats_v1() """
        jdict = {
            'info': self.static_info,
            'request': {
                'date_begin': self.date_start, 'date_end': self.date_end,
                'date_of_request': str( datetime.datetime.now() ) },
            'response': {
                'count_all': data['count_request_for_period'],
                'count_breakdown': data['count_breakdown'], }
            }
        self.output = json.dumps( jdict, sort_keys=True, indent=2 )
        return

    def _handle_bad_params( self, get_params, server_name ):
        """ Prepares bad-parameters data.
            Called by check_params() """
        self.output = None
        data = {
          'request': {
            'url': reverse( 'stats_v1_url' ),
            'params': get_params },
          'response': {
            'status': '400 / Bad Request',
            'message': 'example url: https://%s/easyrequest/stats_api/v1/?start_date=2015-09-01&end_date=2015-09-30' % server_name, }
          }
        self.output = json.dumps( data, sort_keys=True, indent=2 )
        return

    # end class StatsBuilder
