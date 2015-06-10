# -*- coding: utf-8 -*-

from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView


urlpatterns = patterns('',

    url( r'^info/$',  'easyscan_app.views.info', name=u'info_url' ),

    # url( r'^shib_login/$',  'easyscan_app.views.shib_login', name=u'shib_login_url' ),
    # url( r'^logout/$',  'easyscan_app.views.shib_logout', name=u'logout_url' ),

    # url( r'^confirmation/$',  'easyscan_app.views.confirmation', name=u'confirmation_url' ),

    url( r'^$',  RedirectView.as_view(pattern_name=u'info_url') ),

    )
