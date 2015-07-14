# -*- coding: utf-8 -*-

import json, logging, os, pprint
import requests
# import csv, datetime, json, logging, os, pprint, StringIO
# import requests
from django.conf import settings as project_settings
from django.contrib.auth import logout
# from django.core import serializers
# from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db import models
from django.http import HttpResponse, HttpResponseRedirect
# from django.shortcuts import render
# from django.utils.encoding import smart_unicode
# from django.utils.http import urlquote
from iii_account import IIIAccount


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
    patron_name = models.CharField( blank=True, max_length=100 )
    patron_barcode = models.CharField( blank=True, max_length=50 )
    patron_email = models.CharField( blank=True, max_length=100 )
    source_url = models.TextField( blank=True )
    create_datetime = models.DateTimeField( auto_now_add=True, blank=True )  # blank=True for backward compatibility
    admin_notes = models.TextField( blank=True )

    def __unicode__(self):
        return smart_unicode( u'id: %s || title: %s' % (self.id, self.item_title) , u'utf-8', u'replace' )

    def jsonify(self):
        """ Returns object data in json-compatible dict. """
        jsn = serializers.serialize( u'json', [self] )  # json string is single-item list
        lst = json.loads( jsn )
        object_dct = lst[0]
        return ItemRequest

    # end class ItemRequest


## non db models below  ##


class ConfirmRequestGetHelper( object ):
    """ Contains helpers for views.request_def() for handling GET. """

    def __init__( self ):
        self.AVAILABILITY_API_URL_ROOT = os.environ[u'EZRQST__AVAILABILITY_API_URL_ROOT']
        self.PHONE_AUTH_HELP = os.environ[u'EZRQST__PHONE_AUTH_HELP']
        self.EMAIL_AUTH_HELP = os.environ[u'EZRQST__EMAIL_AUTH_HELP']

    def initialize_session( self, request ):
        """ Initializes session.
            Called by views.login() """
        request.session['item_title'] = u''
        request.session['item_bib'] = request.GET['bibnum']
        request.session['item_id'] = u''
        request.session['item_barcode'] = request.GET['barcode']
        request.session['item_callnumber'] = u''
        request.session['user_name'] = u''
        request.session['user_barcode'] = u''
        request.session['user_email'] = u''
        request.session['source_url'] = u''
        return

    def get_item_info( self, bibnum, item_barcode ):
        """ Hits availability-api for bib-title, and item id and callnumber.
            Bib title and item callnumber are just for user display; item id needed if user proceeds.
            Called by views.login() """
        ( title, callnumber, item_id ) = ( '', '', '' )
        api_dct = self.hit_availability_api( bibnum )
        title = api_dct[u'response'][u'backend_response'][0][u'title']
        log.debug( u'title, `%s`' % title )
        ( callnumber, item_id ) = self.process_items( api_dct, item_barcode )
        return ( title, callnumber, item_id )

    def hit_availability_api( self, bibnum ):
        """ Returns availability-api dict.
            Called by get_item_info() """
        dct = {}
        try:
            availability_api_url = u'%s/bib/%s' % ( self.AVAILABILITY_API_URL_ROOT, bibnum )
            r = requests.get( availability_api_url )
            dct = r.json()
            log.debug( u'api-response, `%s`' % pprint.pformat(dct) )
        except Exception as e:
            log.error( u'exception, %s' % unicode(repr(e)) )
        return dct

    def process_items( self, api_dct, item_barcode ):
        """ Extracts the callnumber and item_id from availability-api response.
            Called by get_item_info() """
        ( callnumber, item_id ) = ( '', '' )
        results = api_dct[u'response'][u'backend_response']
        for result in results:
            items = result['items_data']
            for item in items:
                if item_barcode == item['barcode']:
                    callnumber = item['callnumber_interpreted']
                    item_id = item['item_id'][:-1]  # removes trailing check-digit
        log.debug( u'process_items result, `%s`' % unicode(repr(( callnumber, item_id ))) )
        return ( callnumber, item_id )

    def update_session( self, request, title, callnumber, item_id ):
        """ Updates session.
            Called by views.login() """
        request.session['item_title'] = title
        request.session['item_callnumber'] = callnumber
        request.session['item_id'] = item_id
        log.debug( u'session updated' )
        return


    # def handle_get( self, request ):
    #     """ Handles request-page GET; returns response.
    #         Called by views.confirm_request() """
    #     log.debug( u'in models.RequestViewGetHelper.handle_get(); referrer, `%s`' % request.META.get(u'HTTP_REFERER', u'not_in_request_meta'), )
    #     self.store_remote_source_url( request )
    #     https_check = self.check_https( request.is_secure(), request.get_host(), request.get_full_path() )
    #     if https_check[u'is_secure'] == False:
    #         return HttpResponseRedirect( https_check[u'redirect_url'] )
    #     title = self.check_title( request )
    #     self.initialize_session( request, title )
    #     return_response = self.build_response( request )
    #     log.debug( u'in models.RequestViewGetHelper.handle_get(); returning' )
    #     return return_response

    # def store_remote_source_url( self, request ):
    #     """ Stores http-refferer if from external domain.
    #         Called by handle_get() """
    #     log.debug( u'in models.RequestViewGetHelper.store_remote_source_url(); referrer, `%s`' % request.META.get(u'HTTP_REFERER', u'not_in_request_meta'), )
    #     remote_referrer = request.META.get( u'HTTP_REFERER', u'' )
    #     if not request.get_host() in remote_referrer:  # ignore same-domain and shib redirects
    #         if not u'sso.brown.edu' in remote_referrer:
    #             request.session[u'last_remote_referrer'] = remote_referrer
    #     log.debug( u'in models.RequestViewGetHelper.store_remote_source_url(); session items, `%s`' % pprint.pformat(request.session.items()) )
    #     return

    # def check_https( self, is_secure, get_host, full_path ):
    #     """ Checks for https; returns dict with result and redirect-url.
    #         Called by handle_get() """
    #     if (is_secure == False) and (get_host != u'127.0.0.1'):
    #         redirect_url = u'https://%s%s' % ( get_host, full_path )
    #         return_dict = { u'is_secure': False, u'redirect_url': redirect_url }
    #     else:
    #         return_dict = { u'is_secure': True, u'redirect_url': u'N/A' }
    #     log.debug( u'in models.RequestViewGetHelper.check_https(); return_dict, `%s`' % return_dict )
    #     return return_dict

    # def check_title( self, request ):
    #     """ Grabs and returns title from the availability-api if needed.
    #         Called by handle_get() """
    #     title = request.GET.get( u'title', u'' )
    #     if title == u'null' or title == u'':
    #         try: title = request.session[u'item_info'][u'title']
    #         except: pass
    #     if title == u'null' or title == u'':
    #         bibnum = request.GET.get( u'bibnum', u'' )
    #         if len( bibnum ) == 8:
    #             title = self.hit_availability_api( bibnum )
    #     log.debug( u'in models.RequestViewGetHelper.check_title(); title, %s' % title )
    #     return title

    # def hit_availability_api( self, bibnum ):
    #     """ Hits availability-api with bib for title.
    #         Called by check_title() """
    #     try:
    #         availability_api_url = u'%s/bib/%s' % ( self.AVAILABILITY_API_URL_ROOT, bibnum )
    #         r = requests.get( availability_api_url )
    #         d = r.json()
    #         title = d[u'response'][u'backend_response'][0][u'title']
    #     except Exception as e:
    #         log.debug( u'in models.RequestViewGetHelper.hit_availability_api(); exception, %s' % unicode(repr(e)) )
    #         title = u''
    #     return title

    # def initialize_session( self, request, title ):
    #     """ Initializes session vars if needed.
    #         Called by handle_get() """
    #     log.debug( u'in models.RequestViewGetHelper.initialize_session(); session items, `%s`' % pprint.pformat(request.session.items()) )
    #     if not u'authz_info' in request.session:
    #         request.session[u'authz_info'] = { u'authorized': False }
    #     if not u'user_info' in request.session:
    #         request.session[u'user_info'] = { u'name': u'', u'patron_barcode': u'', u'email': u'' }
    #     self.update_session_iteminfo( request, title )
    #     if not u'shib_login_error' in request.session:
    #         request.session[u'shib_login_error'] = False
    #     log.debug( u'in models.RequestViewGetHelper.initialize_session(); session initialized' )
    #     return

    # def update_session_iteminfo( self, request, title ):
    #     """ Updates 'item_info' session key data.
    #         Called by initialize_session() """
    #     if not u'item_info' in request.session:
    #         request.session[u'item_info'] = {
    #         u'callnumber': u'', u'barcode': u'', u'title': u'', u'volume_year': u'', u'article_chapter_title': u'', u'page_range': u'', u'other': u'' }
    #     for key in [ u'callnumber', u'barcode', u'volume_year' ]:  # ensures new url always updates session
    #         value = request.GET.get( key, u'' )
    #         if value:
    #             request.session[u'item_info'][key] = value
    #     request.session[u'item_info'][u'item_source_url'] = request.session.get( u'last_remote_referrer', u'not_in_request_meta' )
    #     request.session[u'item_info'][u'title'] = title
    #     log.debug( u'in models.RequestViewGetHelper.update_session_iteminfo(); request.session["item_info"], `%s`' % pprint.pformat(request.session[u'item_info']) )
    #     return

    # def build_response( self, request ):
    #     """ Builds response.
    #         Called by handle_get() """
    #     if request.session[u'item_info'][u'barcode'] == u'':
    #         return_response = HttpResponseRedirect( reverse(u'info_url') )
    #     elif request.session[u'authz_info'][u'authorized'] == False:
    #         return_response = render( request, u'easyscan_app_templates/request_login.html', self.build_data_dict(request) )
    #     else:
    #         return_response = self.handle_good_get( request )
    #     log.debug( u'in models.RequestViewGetHelper.build_response(); returning' )
    #     return return_response

    # def handle_good_get( self, request ):
    #     """ Builds response on good get.
    #         Called by build_response() """
    #     data_dict = self.build_data_dict( request )
    #     form_data = request.session.get( u'form_data', None )
    #     form = CitationForm( form_data )
    #     form.is_valid() # to get errors in form
    #     data_dict[u'form'] = form
    #     return_response = render( request, u'easyscan_app_templates/request_form.html', data_dict )
    #     return return_response

    # def build_data_dict( self, request ):
    #     """ Builds and returns data-dict for request page.
    #         Called by handle_good_get() """
    #     context = {
    #         u'title': request.session[u'item_info'][u'title'],
    #         u'callnumber': request.session[u'item_info'][u'callnumber'],
    #         u'barcode': request.session[u'item_info'][u'barcode'],
    #         u'volume_year': request.session[u'item_info'][u'volume_year'],
    #         u'login_error': request.session[u'shib_login_error'],
    #         }
    #     if request.session[u'authz_info'][u'authorized']:
    #         context[u'patron_name'] = request.session[u'user_info'][u'name']
    #         context[u'logout_url'] = reverse( u'logout_url' )
    #     log.debug( u'in models.RequestViewGetHelper.build_data_dict(); return_dict, `%s`' % pprint.pformat(context) )
    #     return context

    # end class ConfirmRequestGetHelper


class ShibViewHelper( object ):
    """ Contains helpers for views.shib_login() """

    def check_shib_headers( self, request ):
        """ Grabs and checks shib headers, returns boolean.
            Called by views.shib_login() """
        shib_checker = ShibChecker()
        shib_dict = shib_checker.grab_shib_info( request )
        validity = shib_checker.evaluate_shib_info( shib_dict )
        log.debug( u'returning shib validity `%s`' % validity )
        return ( validity, shib_dict )

    def build_response( self, request, validity, shib_dict ):
        """ Sets session vars and redirects to the request page,
              which will show the citation form on login-success, and a helpful error message on login-failure.
            Called by views.shib_login() """
        self.update_session( request, validity, shib_dict )
        scheme = u'https' if request.is_secure() else u'http'
        redirect_url = u'%s://%s%s' % ( scheme, request.get_host(), reverse(u'processor_url') )
        return_response = HttpResponseRedirect( redirect_url )
        log.debug( u'returning shib response' )
        return return_response

    def update_session( self, request, validity, shib_dict ):
        request.session[u'shib_login_error'] = validity  # boolean
        request.session[u'shib_authorized'] = validity
        if validity:
            request.session[u'user_name'] = u'%s %s' % ( shib_dict[u'firstname'], shib_dict[u'lastname'] )
            request.session[u'user_email'] = shib_dict[u'email']
            request.session[u'user_barcode'] = shib_dict[u'patron_barcode']
            request.session[u'shib_login_error'] = False
        return

    # end class ShibViewHelper


class ShibChecker( object ):
    """ Contains helpers for checking Shib.
        Called by ShibViewHelper """

    def __init__( self ):
        self.TEST_SHIB_JSON = os.environ.get( u'EZRQST__TEST_SHIB_JSON', u'' )
        self.SHIB_ERESOURCE_PERMISSION = os.environ[u'EZRQST__SHIB_ERESOURCE_PERMISSION']

    def grab_shib_info( self, request ):
        """ Grabs shib values from http-header or dev-settings.
            Called by models.ShibViewHelper.check_shib_headers() """
        shib_dict = {}
        if u'Shibboleth-eppn' in request.META:
            shib_dict = self.grab_shib_from_meta( request )
        else:
            if request.get_host() == u'127.0.0.1' and project_settings.DEBUG == True:
                shib_dict = json.loads( self.TEST_SHIB_JSON )
        log.debug( u'in models.ShibChecker.grab_shib_info(); shib_dict is: %s' % pprint.pformat(shib_dict) )
        return shib_dict

    def grab_shib_from_meta( self, request ):
        """ Extracts shib values from http-header.
            Called by grab_shib_info() """
        shib_dict = {
            u'eppn': request.META.get( u'Shibboleth-eppn', u'' ),
            u'firstname': request.META.get( u'Shibboleth-givenName', u'' ),
            u'lastname': request.META.get( u'Shibboleth-sn', u'' ),
            u'email': request.META.get( u'Shibboleth-mail', u'' ).lower(),
            u'patron_barcode': request.META.get( u'Shibboleth-brownBarCode', u'' ),
            u'member_of': request.META.get( u'Shibboleth-isMemberOf', u'' ) }
        return shib_dict

    def evaluate_shib_info( self, shib_dict ):
        """ Returns boolean.
            Called by models.ShibViewHelper.check_shib_headers() """
        validity = False
        if self.all_values_present(shib_dict) and self.brown_user_confirmed(shib_dict) and self.eresources_allowed(shib_dict):
            validity = True
        log.debug( u'in models.ShibChecker.evaluate_shib_info(); validity, `%s`' % validity )
        return validity

    def all_values_present( self, shib_dict ):
        """ Returns boolean.
            Called by evaluate_shib_info() """
        present_check = False
        if sorted( shib_dict.keys() ) == [u'email', u'eppn', u'firstname', u'lastname', u'member_of', u'patron_barcode']:
            value_test = u'init'
            for (key, value) in shib_dict.items():
                if len( value.strip() ) == 0:
                    value_test = u'fail'
            if value_test == u'init':
                present_check = True
        log.debug( u'in models.ShibChecker.all_values_present(); present_check, `%s`' % present_check )
        return present_check

    def brown_user_confirmed( self, shib_dict ):
        """ Returns boolean.
            Called by evaluate_shib_info() """
        brown_check = False
        if u'@brown.edu' in shib_dict[u'eppn']:
            brown_check = True
        log.debug( u'in models.ShibChecker.brown_user_confirmed(); brown_check, `%s`' % brown_check )
        return brown_check

    def eresources_allowed( self, shib_dict ):
        """ Returns boolean.
            Called by evaluate_shib_info() """
        eresources_check = False
        if self.SHIB_ERESOURCE_PERMISSION in shib_dict[u'member_of']:
            eresources_check = True
        log.debug( u'in models.ShibChecker.eresources_allowed(); eresources_check, `%s`' % eresources_check )
        return eresources_check

    # end class ShibChecker


class Processor( object ):
    """ Handles item-hold functions. """

    def check_request( self, request ):
        """ Ensures user has logged in.
            Called by views.processor() """
        return_val = False
        if 'shib_authorized' in request.session:
            if request.session['shib_authorized'] == True:
                return_val = True
        log.debug( 'check_request() result, `%s`' % return_val )
        return return_val

    def save_data( self, request ):
        """ Saves data for 'try-again' feature.
            Called by views.processor() """
        itmrqst = ItemRequest()
        itmrqst = self.save_item_data( itmrqst, request )
        itmrqst = self.save_user_data( itmrqst, request )
        itmrqst.source_url = request.session[u'source_url']
        itmrqst.status = u'in_process'
        return itmrqst

    def save_item_data( self, itmrqst, request ):
        """ Saves item datetimeta from session to db.
            Called by save_data() """
        try:
            itmrqst.item_title = request.session[u'item_title']
            itmrqst.item_bib = request.session[u'item_bib']
            itmrqst.item_id = request.session[u'item_id']
            itmrqst.item_barcode = request.session[u'item_barcode']
            itmrqst.item_callnumber = request.session[u'item_callnumber']
            itmrqst.save()
        except Exception as e:
            log.debug( u'session, `%s`' % pprint.pformat(request.session.items()) )
            log.error( u'Exception, `%s`' % unicode(repr(e)) )
        return itmrqst

    def save_user_data( self, itmrqst, request ):
        """ Saves item datetimeta from session to db.
            Called by save_data() """
        try:
            itmrqst.user_name = request.session[u'user_name']
            itmrqst.user_barcode = request.session[u'user_barcode']
            itmrqst.user_email = request.session[u'user_email']
            itmrqst.save()
        except Exception as e:
            log.debug( u'Exception, `%s`' % unicode(repr(e)) )
        return itmrqst

    def place_request( self, user_name, user_barcode, item_bib, item_id ):
        """ Will coordinate josiah-patron-account calls.
            Called by views.processor() """
        log.debug( u'user_name, `%s`; user_barcode, `%s`; item_bib, `%s`; item_id, `%s`' % (user_name, user_barcode, item_bib, item_id) )
        jos_sess = IIIAccount( user_name, user_barcode )
        jos_sess.login()
        hold = jos_sess.place_hold( item_bib, item_id )
        log.debug( u'hold, `%s`' % hold )
        return


    def logout( self, request ):
        """ Will log user out of session.
            Called by views.processor() """
        request.session['shib_authorized'] = False
        logout( request )  # from django.contrib.auth import logout
        return


    # end class Processor
