# -*- coding: utf-8 -*-

from __future__ import unicode_literals

"""
Manages email to admin on error.
Triggered by views.problem()

TODO: move email to patron handling here, too.
"""

import datetime, json, logging, os

from django.core.mail import EmailMessage


log = logging.getLogger(__name__)


class Emailer(object):

    def __init__( self ):
        self.EMAIL_FROM = os.environ['EZRQST__EMAIL_FROM']
        self.EMAIL_REPLY_TO = os.environ['EZRQST__EMAIL_REPLY_TO']
        self.ADMIN_EMAIL = json.loads( os.environ['EZRQST__ADMINS_JSON'] )[0][1]  # single entry in list of tuples; address is second part of the tuple
        self.email_subject = 'easyRequest admin-alert; problem'

    def email_admin(self):
        """ Emails admin notification of problem.
            Called by views.problem() """
        try:
            body = self.build_email_body()
            ffrom = self.EMAIL_FROM  # `from` reserved
            to = [ self.ADMIN_EMAIL ]
            extra_headers = { 'Reply-To': self.EMAIL_REPLY_TO }
            email = EmailMessage( self.email_subject, body, ffrom, to, headers=extra_headers )
            email.send()
            log.debug( 'mail sent' )
        except Exception as e:
            log.exception( 'exception sending email; traceback follows, but processing will continue' )
        return

    def build_email_body( self ):
        """ Prepares and returns email body.
            Called by email_patron().
            TODO: Send identifiers for the patron and the item. """
        body = '''Problem -- user was just shown the problem message.

::: Item-Requesting -- a service of the Brown University Library :::
'''
        return body

    ## end class Emailer
