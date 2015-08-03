# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView


urlpatterns = patterns('',

    url( r'^info/$',  'easyrequest_app.views.info', name='info_url' ),

    url( r'^login/$',  'easyrequest_app.views.login', name='login_url' ),  # main landing page

    url( r'^shib_login/$',  'easyrequest_app.views.shib_login', name='shib_login_url' ),
    url( r'^logout/$',  'easyrequest_app.views.shib_logout', name='logout_url' ),

    url( r'^barcode_login_handler/$',  'easyrequest_app.views.barcode_login_handler', name='barcode_login_handler_url' ),

    url( r'^processor/$',  'easyrequest_app.views.processor', name='processor_url' ),
    url( r'^summary/$',  'easyrequest_app.views.summary', name='summary_url' ),

    url( r'^$',  RedirectView.as_view(pattern_name='info_url') ),

    )
