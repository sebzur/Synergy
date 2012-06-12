# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from synergy.contrib.records import views

urlpatterns = patterns('',
                       url(r'^create/(?P<name>[-\w]+)/$', views.CreateRecordView.as_view(), name="create"),
                       url(r'^create/(?P<name>[-\w]+)/(?P<arguments>.+)/$', views.CreateRecordView.as_view(), name="create"),
                       url(r'^update/(?P<name>[-\w]+)/(?P<pk>\d+)/$', views.UpdateRecordView.as_view(), name="update"),
                       url(r'^delete/(?P<name>[-\w]+)/(?P<pk>\d+)/$', views.DeleteRecordView.as_view(), name="delete"),
                       )

