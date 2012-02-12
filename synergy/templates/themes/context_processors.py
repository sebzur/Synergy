# -*- coding: utf-8 -*-
from django.conf import settings

class ThemeInfo(object):
    def __init__(self, theme_settings):
        self.settings = theme_settings
        self.logo = self.settings.get('logo', None)

theme_info_obj = ThemeInfo(getattr(settings, 'THEME_INFO', {}))

def theme_info(request):
    return {'theme_info': theme_info_obj,}  

