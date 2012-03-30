# -*- coding: utf-8 -*-
from django.conf import settings

class ThemeInfo(object):
    def __init__(self, theme_settings):
        self.settings = theme_settings
        self.logo = self.settings.get('logo', None)
        self.site_name = self.settings.get('site_name', None)
        self.site_slogan = self.settings.get('site_slogan', None)

theme_info_obj = ThemeInfo(getattr(settings, 'THEME_INFO', {}))

def theme_info(request):
    return {'theme_info': theme_info_obj,}  

