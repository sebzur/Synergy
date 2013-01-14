# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from synergy.contrib.prospects.printouts import views

urlpatterns = patterns('',
                       url(r'^detail-list-pdf/(?P<variant>[-\w]+)/(?P<template>[-\w]+)/$', views.PDFDetailListView.as_view(), name="detail-list-pdf"),
                       url(r'^detail-list-pdf/(?P<variant>[-\w]+)/(?P<template>[-\w]+)/(?P<arguments>.+)/$', views.PDFDetailListView.as_view(), name="detail-list-pdf"),
                       url(r'^list-pdf/(?P<variant>[-\w]+)/(?P<template>[-\w]+)/$', views.PDFListView.as_view(), name="list-pdf"),
                       url(r'^list-pdf/(?P<variant>[-\w]+)/(?P<template>[-\w]+)/(?P<arguments>.+)/$', views.PDFListView.as_view(), name="list-pdf"),
                       url(r'^detail-pdf/(?P<variant>[-\w]+)/(?P<pk>\d+)/(?P<template>[-\w]+)/$', views.PDFDetailView.as_view(), name="detail-pdf"),
                       )

