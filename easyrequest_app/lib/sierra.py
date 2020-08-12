""""
Contains code to:
    - hit the Sierra request-API
"""

import datetime, json, logging, os, pprint

import requests
from requests.auth import HTTPBasicAuth


log = logging.getLogger(__name__)


class SierraHelper( object ):
    """ Gets item_id and places hold. """

    def __init__( self ):
        pass
        self.SIERRA_API_ROOT_URL = os.environ['EZRQST__SIERRA_API_ROOT_URL']
        self.SIERRA_API_KEY = os.environ['EZRQST__SIERRA_API_KEY']
        self.SIERRA_API_SECRET = os.environ['EZRQST__SIERRA_API_SECRET']

        # self.item_request = None
        # self.item_dct = {}  # populated by prep_item_data(); used by views.processor(), which passes this to aeon.build_aeon_url()
        # self.item_bib = ''
        # self.item_barcode = ''
        # self.item_id = None  # populated by get_item_id(); _no_ trailing check-digit
        # self.item_title = ''
        # self.patron_barcode = ''
        # # self.patron_login_name = ''
        # self.patron_sierra_id = ''
        # self.hold_status = 'problem'  # updated in place_hold()

    def build_data( self, item_id, pickup_location_code ):
        """ Preps item-data -- and some patron-data -- from item_request.
            Called by models.Processor.place_request() """
        payload_dct = {
            'recordType': 'i',
            'recordNumber': int( item_id[1:] ),  # removes initial 'i'
            'pickupLocation': pickup_location_code,
            'note': 'source: easyRequest'
            }
        log.debug( f'payload_dct, ``{pprint.pformat(payload_dct)}``' )
        return payload_dct

    def manage_place_hold( self, data_dct, patron_sierra_id ):
        """ Gets token and places hold.
            Called by models.Processor.place_request() """
        token = self.get_token()
        self.place_hold( token, data_dct )
        log.debug( 'manage_place_hold() done.' )
        return

    def get_token( self ):
        """ Gets token.
            Called by manage_place_hold() """
        token = 'init'
        token_url = f'{self.SIERRA_API_ROOT_URL}/token'
        log.debug( 'token_url, ```%s```' % token_url )
        try:
            r = requests.post( token_url,
                auth=HTTPBasicAuth( self.SIERRA_API_KEY, self.SIERRA_API_SECRET ),
                timeout=20 )
            log.debug( 'token r.content, ```%s```' % r.content )
            token = r.json()['access_token']
            log.debug( 'token, ```%s```' % token )
            return token
        except:
            log.exception( 'problem getting token; traceback follows' )
            raise Exception( 'exception getting token' )

    def place_hold( self, token, payload_dct, patron_sierra_id ):
        """ Attempts to place hold via sierra api.
            Called by manage_place_hold() """
        log.info( 'placing hold' )
        request_url = f'{self.SIERRA_API_ROOT_URL}/patrons/{patron_sierra_id}/holds/requests'
        custom_headers = {'Authorization': f'Bearer {token}' }
        log.debug( f'custom_headers, ```{custom_headers}```' )
        log.debug( f'payload_dct, ```{pprint.pformat(payload_dct)}```' )
        payload = json.dumps( payload_dct )
        log.debug( f'payload-json-string, ```{payload}```' )
        try:
            r = requests.post( request_url, headers=custom_headers, data=payload, timeout=30 )
            log.info( f'r.status_code, `{r.status_code}`' )
            log.info( f'r.url, `{r.url}`' )
            log.info( f'r.content, `{r.content}`' )
            if r.status_code in [ 200, 204 ]:
            # if r.status_code == 200:
                self.hold_status = 'hold_placed'
        except:
            log.exception( 'problem hitting api to request item; traceback follows; processing will continue' )
        log.debug( f'hold_status, `{self.hold_status}`' )
        return

    ## end class SierraHelper()
