# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from synergy.contrib.records import views

urlpatterns = patterns('',
                       url(r'^create/(?P<name>[-\w]+)/$', views.CreateObjectView.as_view(), name="create"),
                       url(r'^create-related/(?P<name>[-\w]+)/(?P<pk>\d+)/$', views.CreateObjectView.as_view(), name="create-related"),
                       url(r'^update/(?P<name>[-\w]+)/(?P<pk>\d+)/$', views.UpdateObjectView.as_view(), name="update"),
                       )

