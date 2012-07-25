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
        elif item.item_type.model == 'm2mrelation':
            content[item] = form.external_m2m[item.item.relation]
        elif item.item_type.model == 'o2mrelation':
            content[item] = form.external[item.item.relation]
        else:
            content[item] = item.item.items.all()
    return content


@register.filter(name='layout')
def layout(form):
    items = SortedDict()
    fields = form
    try:
        ct = get_model('contenttypes', 'contenttype').objects.get_for_model(form._meta.model)
        _layout = ct.formlayout
        items = get_content(form, _layout.items.all())
        fields = [field for field in form if field.name not in _layout.fields.values_list('field', flat=True)]



        _handled = [m2m_relation.relation.through for m2m_relation in _layout.m2m_relations.all()]
        _get = get_model('contenttypes','contenttype').objects.get_for_model
        external_m2ms = dict([(relation, form.external_m2m[relation]) for relation in form.external_m2m if relation.through not in _handled])
        internal_m2ms = dict([(relation, form.internal_m2m[relation]) for relation in form.internal_m2m if _get(relation.rel.through) not in _handled])

        _handled_o2ms = _layout.o2m_relations.values_list('relation__model', flat=True)
        print _handled_o2ms
        o2ms = dict([(relation, form.external[relation]) for relation in form.external if relation.model.id not in _handled_o2ms])

    except Exception, error:
        pass
    context = {'items': items, 'form': form, 'fields': fields, 'internal_m2ms': internal_m2ms, 'external_m2ms': external_m2ms, 'o2ms': o2ms}
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



