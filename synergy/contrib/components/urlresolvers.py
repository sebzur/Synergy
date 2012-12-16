from django.core.urlresolvers import reverse
from django.utils.datastructures import SortedDict
from django.db import models

def component_url(view_mode, view_name, *args, **kwargs):
    arg_src = {'list': models.get_model('prospects', 'prospectvariant'),
               'create': models.get_model('records', 'recordsetup')}
    
    return render_url(view_mode, view_name, arg_src.get(view_mode), *args, **kwargs)


def render_url(view_mode, view_name, arg_src, *args, **kwargs):
    admmissible_args = arg_src.objects.get(name=view_name).arguments.all().order_by('weight')
    path_content = ("%%(%s)s" % arg.name for arg in admmissible_args)
    url_template = '/'.join(path_content)
    
    url_args = SortedDict()

    i = 0 # in case args is emtpy we need it assigned 
    for i, arg in enumerate(args):
        url_args[admmissible_args[i].name] = arg

    for kwg_arg in admmissible_args[i:]:
        name = admmissible_args[i].name
        url_args[name] = kwargs.get(name)
    
    if url_args:
        url_content = url_template % url_args
        return reverse(view_mode, args=[view_name, url_content])
    return reverse(view_mode, args=[view_name])
