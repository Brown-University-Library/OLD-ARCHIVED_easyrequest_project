# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import json, logging, os, pprint, time, urlparse
import requests
from django.conf import settings as project_settings
from django.contrib.auth import logout
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
from iii_account import IIIAccount
from requests.auth import HTTPBasicAuth


log = logging.getLogger(__name__)


## db models ##


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

    def __unicode__(self):
        return smart_unicode( 'id: %s || title: %s' % (self.id, self.item_title) , 'utf-8', 'replace' )

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

    def validate_source( self, request ):
        """ Ensures app is accessed from legit source.
            Called by views.login() """
        return_val = False
        if request.get_host() == '127.0.0.1' and project_settings.DEBUG == True:
            return_val = True
        referrer_host = self.get_referrer_host( request.META.get('HTTP_REFERER', 'unavailable') )
        if referrer_host in self.LEGIT_SOURCES:
            return_val = True
        else:
            log.debug( 'referrer_host, `%s`' % referrer_host )
        log.debug( 'return_val, `%s`' % return_val )
        return return_val

    def get_referrer_host( self, referrer_url ):
        """ Extracts host from referrer_url.
            Called by validate_source() """
        output = urlparse.urlparse( referrer_url )
        host = output.netloc
        log.debug( 'referrer host, `%s`' % host )
        return host

    def validate_params( self, request ):
        """ Checks params.
            Called by views.login()
            Note: `barcode` here is the item-barcode. """
        return_val = False
        if sorted( request.GET.keys() ) == ['barcode', 'bibnum']:
            if len(request.GET['bibnum']) == 8 and len(request.GET['barcode']) == 14:
                return_val = True
        log.debug( 'return_val, `%s`' % return_val )
        return return_val

    def initialize_session( self, request ):
        """ Initializes session.
            Called by views.login() """
        self._initialize_session_item_info( request )
        self._initialize_session_user_info( request )
        request.session['source_url'] = ''
        request.session.setdefault( 'shib_login_error', False )
        request.session['shib_authorized'] = False
        request.session.setdefault( 'barcode_login_error', False)
        request.session['barcode_authorized'] = False
        log.debug( 'request.session after initialization, `%s`' % pprint.pformat(request.session.items()) )
        return

    def _initialize_session_item_info( self, request ):
        """ Initializes session item info.
            Called by initialize_session() """
        request.session.setdefault( 'item_title', '' )
        request.session['item_bib'] = request.GET['bibnum']
        request.session.setdefault( 'item_id', '' )
        request.session['item_barcode'] = request.GET['barcode']
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
        request.session.setdefault( 'barcode_login_barcode', '' )  # for barcode login form
        request.session['josiah_api_barcode'] = ''  # for josiah-patron-accounts call
        request.session['josiah_api_name'] = ''  # for josiah-patron-accounts call
        return

    def get_item_info( self, bibnum, item_barcode ):
        """ Hits availability-api for bib-title, and item id and callnumber.
            Bib title and item callnumber are just for user display; item id needed if user proceeds.
            Called by views.login() """
        ( title, callnumber, item_id ) = ( '', '', '' )
        api_dct = self.hit_availability_api( bibnum )
        title = api_dct['response']['backend_response'][0]['title']
        log.debug( 'title, `%s`' % title )
        ( callnumber, item_id ) = self.process_items( api_dct, item_barcode )
        return ( title, callnumber, item_id )

    def hit_availability_api( self, bibnum ):
        """ Returns availability-api dict.
            Called by get_item_info() """
        dct = {}
        try:
            availability_api_url = '%s/bib/%s' % ( self.AVAILABILITY_API_URL_ROOT, bibnum )
            r = requests.get( availability_api_url )
            dct = r.json()
            log.debug( 'partial availability-api-response, `%s`' % pprint.pformat(dct)[0:200] )
        except Exception as e:
            log.error( 'exception, %s' % unicode(repr(e)) )
        return dct

    def process_items( self, api_dct, item_barcode ):
        """ Extracts the callnumber and item_id from availability-api response.
            Called by get_item_info() """
        ( callnumber, item_id ) = ( '', '' )
        results = api_dct['response']['backend_response']
        for result in results:
            items = result['items_data']
            for item in items:
                if item_barcode == item['barcode']:
                    callnumber = item['callnumber_interpreted']
                    item_id = item['item_id'][:-1]  # removes trailing check-digit
        log.debug( 'process_items result, `%s`' % unicode(repr((callnumber, item_id))) )
        return ( callnumber, item_id )

    def update_session( self, request, title, callnumber, item_id ):
        """ Updates session.
            Called by views.login() """
        request.session['item_title'] = title
        request.session['item_callnumber'] = callnumber
        request.session['item_id'] = item_id
        request.session['source_url'] = request.META.get( 'HTTP_REFERER', u'unavailable' ).strip()
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
            'barcode_login_name': request.session['barcode_login_name'],
            'barcode_login_barcode': request.session['barcode_login_barcode'],
            'barcode_login_error': request.session['barcode_login_error'],
            'shib_login_error': request.session['shib_login_error'],
            'PHONE_AUTH_HELP': self.PHONE_AUTH_HELP,
            'EMAIL_AUTH_HELP': self.EMAIL_AUTH_HELP,
            }
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
        if sorted( request.POST.keys() ) == ['barcode_login_barcode', 'barcode_login_name', 'csrfmiddlewaretoken', 'pickup_location']:
            request.session['barcode_login_name'] = request.POST['barcode_login_name']
            request.session['barcode_login_barcode'] = request.POST['barcode_login_barcode']
            request.session['pickup_location'] = request.POST['pickup_location'][0]
            if len(request.POST['barcode_login_name']) > 0 and len(request.POST['barcode_login_barcode']) > 13:
                return_val = True
        log.debug( 'return_val, `%s`' % return_val )
        return False
        return return_val

    def prep_login_redirect( self, request ):
        """ Prepares redirect response-object to views.login() on bad params.
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
            log.debug( 'exception on login-try, `%s`' % unicode(repr(e)) )
        log.debug( 'barcode login check, `%s`' % return_val )
        return return_val

    def enhance_patron_info( self, patron_barcode ):
        """ Hits patron-api service; returns patron name and email address.
            Called by views.barcode_handler() """
        try:
            r = requests.get( self.PATRON_API_URL, params={'patron_barcode': patron_barcode}, timeout=5, auth=(self.PATRON_API_BASIC_AUTH_USERNAME, self.PATRON_API_BASIC_AUTH_PASSWORD) )
            r.raise_for_status()  # will raise an http_error
        except Exception as e:
            log.error( 'exception, `%s`' % unicode(repr(e)) )
            return False
        patron_info_dct = {
            'patron_name': r.json()['response']['patrn_name']['value'],  # last, first middle,
            'patron_email': r.json()['response']['e-mail']['value'].lower() }
        log.debug( 'patron_info_dct, `%s`' % patron_info_dct )
        return patron_info_dct

    def update_session( self, request, patron_info_dct ):
        """ Updates session before redirecting to views.processor() """
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

    def check_shib_headers( self, request ):
        """ Grabs and checks shib headers, returns boolean.
            Called by views.shib_login() """
        shib_checker = ShibChecker()
        shib_dict = shib_checker.grab_shib_info( request )
        validity = shib_checker.evaluate_shib_info( shib_dict )
        log.debug( 'returning shib validity `%s`' % validity )
        return ( validity, shib_dict )

    def build_response( self, request, validity, shib_dict ):
        """ Sets session vars and redirects to the hidden processor page.
            Called by views.shib_login() """
        self.update_session( request, validity, shib_dict )
        scheme = 'https' if request.is_secure() else 'http'
        redirect_url = '%s://%s%s' % ( scheme, request.get_host(), reverse('processor_url') )
        return_response = HttpResponseRedirect( redirect_url )
        log.debug( 'returning shib response' )
        return return_response

    def update_session( self, request, validity, shib_dict ):
        """ Updates session with shib info.
            Called by build_response() """
        request.session['shib_login_error'] = validity  # boolean
        request.session['shib_authorized'] = validity
        if validity:
            request.session['user_full_name'] = '%s %s' % ( shib_dict['firstname'], shib_dict['lastname'] )
            request.session['user_last_name'] = shib_dict['lastname']
            request.session['user_email'] = shib_dict['email']
            request.session['shib_login_error'] = False
            request.session['josiah_api_name'] = shib_dict['firstname']
            request.session['josiah_api_barcode'] = shib_dict['patron_barcode']
        return

    # end class ShibViewHelper


class ShibChecker( object ):
    """ Contains helpers for checking Shib.
        Called by ShibViewHelper """

    def __init__( self ):
        self.TEST_SHIB_JSON = os.environ.get( 'EZRQST__TEST_SHIB_JSON', '' )
        self.SHIB_ERESOURCE_PERMISSION = os.environ['EZRQST__SHIB_ERESOURCE_PERMISSION']

    def grab_shib_info( self, request ):
        """ Grabs shib values from http-header or dev-settings.
            Called by models.ShibViewHelper.check_shib_headers() """
        shib_dict = {}
        if 'Shibboleth-eppn' in request.META:
            shib_dict = self.grab_shib_from_meta( request )
        else:
            if request.get_host() == '127.0.0.1' and project_settings.DEBUG == True:
                shib_dict = json.loads( self.TEST_SHIB_JSON )
        log.debug( 'in models.ShibChecker.grab_shib_info(); shib_dict is: %s' % pprint.pformat(shib_dict) )
        return shib_dict

    def grab_shib_from_meta( self, request ):
        """ Extracts shib values from http-header.
            Called by grab_shib_info() """
        shib_dict = {
            'eppn': request.META.get( 'Shibboleth-eppn', '' ),
            'firstname': request.META.get( 'Shibboleth-givenName', '' ),
            'lastname': request.META.get( 'Shibboleth-sn', '' ),
            'email': request.META.get( 'Shibboleth-mail', '' ).lower(),
            'patron_barcode': request.META.get( 'Shibboleth-brownBarCode', '' ),
            'member_of': request.META.get( 'Shibboleth-isMemberOf', '' ) }
        return shib_dict

    def evaluate_shib_info( self, shib_dict ):
        """ Returns boolean.
            Called by models.ShibViewHelper.check_shib_headers() """
        validity = False
        if self.all_values_present(shib_dict) and self.brown_user_confirmed(shib_dict) and self.eresources_allowed(shib_dict):
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

    def eresources_allowed( self, shib_dict ):
        """ Returns boolean.
            Called by evaluate_shib_info() """
        eresources_check = False
        if self.SHIB_ERESOURCE_PERMISSION in shib_dict['member_of']:
            eresources_check = True
        log.debug( 'in models.ShibChecker.eresources_allowed(); eresources_check, `%s`' % eresources_check )
        return eresources_check

    # end class ShibChecker


class PickupLocation( object ):
    """ Holds pickup-location info for display, and for placing hold. """

    def __init__( self ):
        """ dct structure example: { 'ROCK': {'code': 'r0001', 'display': 'Rockefeller Library'}, etc... } """
        self.pickup_location_dct = json.loads( os.environ['EZRQST__PICKUP_LOCATION_JSON'] )

    # end class PickupLocation


class Processor( object ):
    """ Handles item-hold and email functions. """

    def __init__( self ):
        self.EMAIL_FROM = os.environ['EZRQST__EMAIL_FROM']
        self.EMAIL_REPLY_TO = os.environ['EZRQST__EMAIL_REPLY_TO']
        self.EMAIL_GENERAL_HELP = os.environ['EZRQST__EMAIL_GENERAL_HELP']
        self.PHONE_GENERAL_HELP = os.environ['EZRQST__PHONE_GENERAL_HELP']

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
            itmrqst.item_barcode = request.session['item_barcode']
            itmrqst.item_callnumber = request.session['item_callnumber']
            itmrqst.save()
        except Exception as e:
            log.debug( 'Exception; session, `%s`' % pprint.pformat(request.session.items()) )
            log.error( 'Exception, `%s`' % unicode(repr(e)) )
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
            log.error( 'Exception, `%s`' % unicode(repr(e)) )
            raise Exception( 'Unable to save user-data.' )
        return itmrqst

    def place_request( self, itmrqst, josiah_api_name, pickup_location_code ):
        """ Coordinates josiah-patron-account calls.
            Called by views.processor() """
        jos_sess = IIIAccount( name=josiah_api_name, barcode=itmrqst.patron_barcode )
        jos_sess.login()
        hold = jos_sess.place_hold( bib=itmrqst.item_bib, item=itmrqst.item_id, pickup_location=pickup_location_code )
        jos_sess.logout()
        log.debug( 'hold, `%s`' % hold )
        itmrqst.status = 'request_placed'
        itmrqst.save()
        return itmrqst

    # def place_request( self, itmrqst, josiah_api_name ):
    #     """ Coordinates josiah-patron-account calls.
    #         Called by views.processor() """
    #     jos_sess = IIIAccount( josiah_api_name, itmrqst.patron_barcode )
    #     jos_sess.login()
    #     hold = jos_sess.place_hold( itmrqst.item_bib, itmrqst.item_id )
    #     jos_sess.logout()
    #     log.debug( 'hold, `%s`' % hold )
    #     itmrqst.status = 'request_placed'
    #     itmrqst.save()
    #     return itmrqst

    def email_patron( self, patron_email, patron_name, item_title, item_callnumber, item_bib, item_id, patron_barcode, item_barcode ):
        """ Emails patron confirmation.
            Called by views.processor() """
        try:
            subject = 'Brown University Library - Item Request Confirmation'
            body = self.build_email_body( patron_name, item_title, item_callnumber, item_bib, item_id, patron_barcode, item_barcode )
            ffrom = self.EMAIL_FROM  # `from` reserved
            to = [ patron_email ]
            extra_headers = { 'Reply-To': self.EMAIL_REPLY_TO }
            email = EmailMessage( subject, body, ffrom, to, headers=extra_headers )
            email.send()
            log.debug( 'mail sent' )
        except Exception as e:
            log.error( 'Exception sending email, `%s`' % unicode(repr(e)) )
        return

    def build_email_body( self,  patron_name, item_title, item_callnumber, item_bib, item_id, patron_barcode, item_barcode ):
        """ Prepares and returns email body.
            Called by email_patron().
            TODO: use render_to_string & template. """
        body = '''Greetings %s,

This is a confirmation of your request for the item...

Title: %s
Call Number: %s

Items are generally available in 1 business day. When available, you'll be notified at this email address.

If you have questions, feel free to email %s or call %s, and reference...

- Bibliographic #: "%s"
- Item #: "%s"
- User barcode: "%s"
- Item barcode: "%s"

::: easyRequest - a service of the Brown University Library :::
''' % (
            patron_name,
            item_title,
            item_callnumber,
            self.EMAIL_GENERAL_HELP,
            self.PHONE_GENERAL_HELP,
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
        redirect_url = '%s://%s%s?bib=%s&callnumber=%s&item_id=%s&title=%s&user_name=%s&user_email=%s' % (
            scheme, request.get_host(), reverse('summary_url'),
            request.session['item_bib'], request.session['item_callnumber'], request.session['item_id'], item_title,
            request.session['user_full_name'], request.session['user_email']
            )
        log.debug( 'initial redirect_url, `%s`' % redirect_url )
        return redirect_url

    # end class ShibLogoutHelper
