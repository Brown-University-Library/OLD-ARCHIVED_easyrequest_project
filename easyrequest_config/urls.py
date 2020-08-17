# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from django.contrib import admin


urlpatterns = [

    url( r'^', include('easyrequest_app.urls_app') ),

    url( r'^admin/', include(admin.site.urls) ),
]
