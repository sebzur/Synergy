from django import template
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import get_model
from django.core.urlresolvers import reverse

import re

from synergy.contrib.records.models import get_parent_field
from django.utils.datastructures import SortedDict

kwarg_re = re.compile(r"(?:(\w+)=)?(.+)")

register = template.Library()


def get_content(form, items):
    content = SortedDict()
    for item in items:
        if item.item_type.model == 'formfield':
            content[item] = form[item.item.field]
        else:
            content[item] = item.item.items.all()
    return content


@register.filter(name='layout')
def layout(form):
    items = SortedDict()
    fields = form
    try:
        ct = get_model('contenttypes','contenttype').objects.get_for_model(form._meta.model)
        _layout = ct.formlayout
        items = get_content(form, _layout.items.all())
        fields = [field for field in form if field.name not in _layout.fields.values_list('field', flat=True)]
    except Exception, error:
        pass
    context = {'items': items, 'form': form, 'fields': fields}
    tpl = 'formstyle/layout.html' 
    return render_to_string(tpl, context)

@register.filter(name='v_layout')
def v_layout(form, items):
    context = {'items': get_content(form, items), 'form': form, 'norm_factor': sum([item.proportion for item in items])}
    tpl = 'formstyle/v_layout.html' 
    return render_to_string(tpl, context)

@register.filter(name='h_layout')
def h_layout(form, items):
    context = {'items': get_content(form, items), 'form': form, 'norm_factor': sum([item.proportion for item in items])}
    tpl = 'formstyle/h_layout.html' 
    return render_to_string(tpl, context)



