# -*- coding: utf-8 -*-
from django.conf import settings

class SubRegionView(type):
    def __init__(cls, name, bases, attrs):
        try:
            if RegionViewMixin not in bases:
                return
        except NameError:
                return
        RegionViewMixin._registry[name] = cls

class RegionViewMixin(object):
    __metaclass__ = SubRegionView
    _registry = {}

    def get_template_names(self):
        base_template = getattr(settings, 'THEME_INFO', {}).get('base_template', 'pageone/node.html')
        return [base_template]
   

