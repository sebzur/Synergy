# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from synergy.contrib.pdfgen import views

urlpatterns = patterns('',
                       #url(r'^list/(?P<variant>[-\w]+)/$', views.ListView.as_view(), name="list"),
                       #url(r'^list/(?P<variant>[-\w]+)/(?P<arguments>.+)/$', views.ListView.as_view(), name="list"),
                       url(r'^detail-pdf/(?P<variant>[-\w]+)/(?P<pk>\d+)/$', views.PDFDetailView.as_view(), name="detail-pdf"),
                       url(r'^detail-pdf/(?P<variant>[-\w]+)/(?P<pk>\d+)/(?P<parent>\d+)/$', views.PDFDetailView.as_view(), name="detail-pdf"),
                       )

