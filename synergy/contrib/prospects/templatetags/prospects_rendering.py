from django import template
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import get_model
import re

register = template.Library()

@register.filter(name='teaser')
def teaser(obj):
    app_label = obj._meta.app_label
    model = obj._meta.object_name.lower()
    tpl = '%s/teasers/%s.html' % (obj._meta.app_label, obj._meta.object_name.lower())
    try:
        if settings.DEBUG:
            print tpl
        return render_to_string(tpl, {model: obj})
    except template.TemplateDoesNotExist:
        tpl = 'synergy/contrib/prospects/teaser.html'
        return render_to_string(tpl, {'object': obj})

@register.filter(name='tr')
def table_row(obj, table):
    tpl = 'displays/tabledisplay/tr.html'
    return render_to_string(tpl, {'obj': obj, 'table': table})

@register.filter(name='td')
def table_column(obj, column):
    tpl = 'displays/tabledisplay/td.html'
    value = column.field.extract(obj)
    return render_to_string(tpl, {'value': value, 'column': column})



class VariantsNode(template.Node):
    def __init__(self, format_string, var_name):
        self.format_string = format_string
        self.var_name = var_name
    def render(self, context):
        model = {'variants': 'ProspectVariant'}[self.var_name]
        context[self.var_name] = get_model('prospects', model).objects.all()
        return ''

@register.tag
def get_prospect(parser, token):
    # This version uses a regular expression to parse tag contents.
    try:
        # Splitting by None == splitting by spaces.
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires arguments" % token.contents.split()[0])
    m = re.search(r'(.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError("%r tag had invalid arguments" % tag_name)
    format_string, var_name = m.groups()
#    if not (format_string[0] == format_string[-1] and format_string[0] in ('"', "'")):
#        raise template.TemplateSyntaxError("%r tag's argument should be in quotes" % tag_name)
    return VariantsNode(format_string[1:-1], var_name)

