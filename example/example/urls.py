# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
"""
example URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
import example.views
from django.conf.urls import url
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    # ASYNC VIEWS
    url(r'^$',
        example.views.ExampleView.as_view(),
        name='example_view'),
    # slow
    url(r'^slow/$',
        example.views.ExampleSlowView.as_view(),
        name='example_slow_view'),

    # ASYNC DOWNLOAD
    url(r'^example-download/$',
        example.views.ExampleDownloadView.as_view(),
        name='example_download'),
    # slow
    url(r'^example-slow-download/$',
        example.views.ExampleSlowDownloadView.as_view(),
        name='example_slow_download'),
]
