# -*- coding: utf-8 -*-
import views
from django.conf.urls.defaults import *

urlpatterns = patterns('',
                       url(r'^tabledisplay/serverside/(?P<variant>[-\w]+)/$', views.Process.as_view(), name="pr"),
                       url(r'^tabledisplay/serverside/(?P<variant>[-\w]+)/(?P<arguments>.+)/$', views.Process.as_view(), name="pr"),
                       )

