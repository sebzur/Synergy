# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from synergy.contrib.prospects import views

urlpatterns = patterns('',
                       url(r'^list/(?P<variant>[-\w]+)/$', views.ListView.as_view(), name="list"),
                       url(r'^list/(?P<variant>[-\w]+)/(?P<arguments>.+)/$', views.ListView.as_view(), name="list"),
                       url(r'^detail/(?P<variant>[-\w]+)/(?P<pk>\d+)/$', views.DetailView.as_view(), name="detail"),
                       )

