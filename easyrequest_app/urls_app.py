# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView


urlpatterns = patterns('',

    url( r'^info/$',  'easyrequest_app.views.info', name='info_url' ),

    url( r'^login/$',  'easyrequest_app.views.login', name='login_url' ),  # main landing page

    url( r'^barcode_handler/$',  'easyrequest_app.views.barcode_handler', name='barcode_handler_url' ),  # eventually (happy path) redirects to `processor/`
    url( r'^shib_handler/$',  'easyrequest_app.views.shib_handler', name='shib_handler_url' ),  # eventually (happy path) redirects to `shib_login/`

    url( r'^shib_login/$',  'easyrequest_app.views.shib_login', name='shib_login_url' ),  # eventually (happy path) redirects to `processor/`

    url( r'^processor/$',  'easyrequest_app.views.processor', name='processor_url' ),  # eventually (happy path) redirects to `logout/`

    url( r'^logout/$',  'easyrequest_app.views.shib_logout', name='logout_url' ),  # eventually (happy path) redirects to `summary/`

    url( r'^summary/$',  'easyrequest_app.views.summary', name='summary_url' ),

    url( r'^stats_api/v1/$',  'easyrequest_app.views.stats_v1', name=u'stats_v1_url' ),

    url( r'^$',  RedirectView.as_view(pattern_name='info_url') ),

    )
