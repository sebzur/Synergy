from django import template
from django.template.loader import render_to_string
from django.conf import settings
from django.db.models import get_model
import re

from synergy.contrib.records.models import get_parent_field

register = template.Library()

@register.filter(name='as_record')
def teaser(obj):
    app_label = obj._meta.app_label
    model = obj._meta.object_name.lower()
    ct = get_model('contenttypes', 'contenttype').objects.get_for_model(obj)


    # Parent
    parent_field = get_parent_field(obj._meta)
    parent = {}
    if parent_field:
        parent['object'] = getattr(obj, parent_field.name)
        parent['setup'] = get_model('records', 'RecordSetup').objects.get(model__model=parent_field.rel.to._meta.object_name.lower())


    setup = ct.record_setup

    context = {'object': obj, 'object_name': obj._meta.verbose_name, 'tracked_model_relations': {}, 'untracked_model_relations': {}, 'record_relations': {},
               'parent': parent, 'setup': setup}


    
    for related_model in setup.related_models.all():
        context['record_relations'][related_model] = related_model.model.model_class().objects.filter(**{related_model.setup.model.model: obj})
    classes_in_record = [relation.model.model_class() for relation in context['record_relations']]
    
    db_rels = [rel for rel in obj._meta.get_all_related_objects() if not rel.model in classes_in_record]
    for rel in db_rels:
        queryset = getattr(obj, rel.get_accessor_name())
        try:
            print rel.var_name, get_model('records', 'RecordSetup').objects.values_list('model__model', flat=True)
            context['tracked_model_relations'][rel] = {'setup': get_model('records', 'RecordSetup').objects.get(model__model=rel.var_name),
                                                       'queryset': queryset}
        except get_model('records', 'RecordSetup').DoesNotExist:
            context['untracked_model_relations'][rel] = {'queryset': queryset}

    tpl = 'records/object.html'
    return render_to_string(tpl, context)


@register.filter(name='as_table')
def as_table(obj):

    context = {'fields': {}, 'object': obj}
    for field in obj._meta.fields:
        context['fields'][field.verbose_name] = getattr(obj, field.name)
    
    tpl = 'records/object_table.html'
    return render_to_string(tpl, context)
