# -*- coding: utf-8 -*-

def region_info(request):
    if hasattr(request, 'region_info'):
        return {'region_info': request.region_info,}  
    return {}
