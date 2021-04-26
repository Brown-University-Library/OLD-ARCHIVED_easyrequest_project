# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from django.views.generic import RedirectView
from easyrequest_app import views


urlpatterns = [

    ## viewable by end-user

    url( r'^info/$', views.info, name='info_url' ),

    url( r'^login/$', views.login, name='login_url' ),  # main landing page

    url( r'^summary/$', views.summary, name='summary_url' ),

    url( r'^problem/$', views.problem, name='problem_url' ),

    ## other

    url( r'^barcode_handler/$', views.barcode_handler, name='barcode_handler_url' ),  # eventually (happy path) redirects to `processor/`
    url( r'^shib_handler/$', views.shib_handler, name='shib_handler_url' ),  # eventually (happy path) redirects to `shib_login/`

    url( r'^shib_login/$', views.shib_login, name='shib_login_url' ),  # eventually (happy path) redirects to `processor/`

    url( r'^processor/$', views.processor, name='processor_url' ),  # eventually (happy path) redirects to `logout/`

    url( r'^logout/$', views.shib_logout, name='logout_url' ),  # eventually (happy path) redirects to `summary/`

    url( r'^stats_api/v1/$', views.stats_v1, name=u'stats_v1_url' ),

    # ====================
    # development support
    # ====================

    url( r'^version/$', views.version, name='version_url' ),
    url( r'^error_check/$', views.error_check, name='error_check_url' ),

    url( r'^$',  RedirectView.as_view(pattern_name='info_url') ),

    ]
