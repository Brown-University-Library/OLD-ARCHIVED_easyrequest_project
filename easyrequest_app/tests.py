# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import pprint
# from django.http import QueryDict
from django.test import TestCase
from easyrequest_app.models import LoginHelper


login_helper = LoginHelper()


class LoginHelperTest( TestCase ):
    """ Tests models.LoginHelper() """

    def test__get_referrer_host( self ):
        """ Tests extract of host from full referrer url. """
        referrer_url = 'http://josiah.brown.edu/search~S7?/tDeath+Without+Weeping%3A+The+Violence+of+Everyday+Life+in+Brazil/tdeath+without+weeping+the+violence+of+everyday+life+in+brazil/1%2C1%2C4%2CB/frameset&FF=tdeath+without+weeping+the+violence+of+everyday+life+in+brazil&2%2C%2C4   '
        self.assertEqual(
            'josiah.brown.edu',
            login_helper.get_referrer_host(referrer_url) )
        referrer_url = 'foo'
        self.assertEqual(
            '',
            login_helper.get_referrer_host(referrer_url) )

    # end class class LoginHelperTest
