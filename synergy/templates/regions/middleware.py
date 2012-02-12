# -*- coding: utf-8 -*-
import os
import itertools

from synergy.templates.regions.views import RegionViewMixin

class RegionInfoMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if RegionViewMixin._registry.has_key(view_func.__name__):
            request.region_info = RegionInfo(request, view_func, view_args, view_kwargs )
    
class RegionInfo(object):
    def __init__(self, request, view_func, view_args, view_kwargs):
        self.module_name =  view_func.__module__
        self.view_name = view_func.__name__
        
    def get_region_templates(self):
        a = __import__(self.module_name, globals(), locals(), self.module_name.split('.')[-1],-1)
        return getattr(a, self.view_name).get_region_templates()
        
    def get_path_elements(self):
        # self.module_name is app_aware
        # so we have app_name.module_name
        return self.module_name.split('.')

    def get_template_format(self):
        return "html"

    def get_region_template_names(self, region, postfix):
        """ Returns a list of templates that will be tested to render the region content.

        This list is build with the file names created from region name, optional postfix, and
        path prefixes. In most cases this will look like:
        ['{app_label}/{module_name}/{region_name}[_postfix]',  -- all views definded in the module 
         '{app_label}/{region_name}[_postfix]',                -- all views defined in app
         '{region_name}[_postfix]',]                           -- all views
         
        """

        region_template_name =  "%s" % region + '_%s' % postfix if postfix else region
        region_template_file = "%s.%s" % (region_template_name, self.get_template_format())
        path_elements = self.get_path_elements()
        elements_count = len(path_elements)
        for cut in range(elements_count):
            path_prefix = os.path.join(*path_elements[:elements_count - cut])
            yield os.path.join(path_prefix, region_template_file)
        yield region_template_file
        
    def get_view_region_template_name(self, region, postfix):
        """ Returns view specific template for region rendering.

        The template name is created using View class name and the module that
        the View is defined in. In most cases this looks like:

        '{app_label}/{module_name}/{view_name}_{region_name}[_posfix]'
        
        """
        region_template_name =  "%s_%s" % (self.view_name.lower(), region + '_%s' % postfix if postfix else region)
        region_template_file = "%s.%s" % (region_template_name, self.get_template_format())
        path_prefix = os.path.join(*self.get_path_elements())
        return os.path.join(path_prefix, region_template_file)

    def get_template_names(self, region, postfix):
        return itertools.chain([self.get_view_region_template_name(region, postfix)], self.get_region_template_names(region, postfix))
        
        
