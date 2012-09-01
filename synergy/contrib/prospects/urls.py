# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from synergy.contrib.prospects import views

urlpatterns = patterns('',
                       url(r'^list/(?P<variant>[-\w]+)/$', views.ListView.as_view(), name="list"),
                       url(r'^list/(?P<variant>[-\w]+)/(?P<arguments>.+)/$', views.ListView.as_view(), name="list"),
                       url(r'^detail/(?P<variant>[-\w]+)/(?P<pk>\d+)/$', views.DetailView.as_view(), name="detail"),
                       url(r'^context/(?P<variant>[-\w]+)/(?P<pk>\d+)/(?P<context>[-\w]+)/$', views.DetailContextView.as_view(), name="context"),
                       url(r'^rest-list/(?P<variant>[-\w]+)/$', views.RESTListView.as_view(), name="rest-list"),
                       url(r'^rest-calendar/(?P<variant>[-\w]+)/$', views.RESTCalendarView.as_view(), name="rest-calendar"),
                       )

