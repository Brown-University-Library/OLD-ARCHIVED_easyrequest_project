# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView


urlpatterns = patterns('',

    url( r'^info/$',  'easyrequest_app.views.info', name=u'info_url' ),

    url( r'^login/$',  'easyrequest_app.views.login', name=u'login_url' ),

    url( r'^shib_login/$',  'easyrequest_app.views.shib_login', name=u'shib_login_url' ),
    # url( r'^logout/$',  'easyrequest_app.views.shib_logout', name=u'logout_url' ),

    url( r'^processor/$',  'easyrequest_app.views.processor', name=u'processor_url' ),
    # url( r'^confirmation/$',  'easyrequest_app.views.confirmation', name=u'confirmation_url' ),

    url( r'^$',  RedirectView.as_view(pattern_name=u'info_url') ),

    )
