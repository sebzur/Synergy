# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from synergy.contrib.prospects import views

urlpatterns = patterns('',
                       url(r'^prospect/(?P<pk>\d+)/(?P<variant>[\w\d-]+)/$', views.ProspectView.as_view(), name="prospect"),
                       )

