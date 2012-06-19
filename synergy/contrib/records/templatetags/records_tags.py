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


    setup = ct.record_setups.get()

    context = {'object': obj, 'object_name': obj._meta.verbose_name, 'tracked_model_relations': {}, 'untracked_model_relations': {}, 
               'record_relations': {}, 'parent': parent, 'setup': setup}

    
    for related_model in setup.related_models.all():
        context['record_relations'][related_model] = related_model.model.model_class().objects.filter(**{related_model.setup.model.model: obj})
    classes_in_record = [relation.model.model_class() for relation in context['record_relations']]
    
    db_rels = [rel for rel in obj._meta.get_all_related_objects() if not rel.model in classes_in_record]
    for rel in db_rels:
        if rel.field.rel.multiple:
            related_object = getattr(obj, rel.get_accessor_name())
        else:
            try:
                related_object = getattr(obj, rel.get_accessor_name())
            except:
                related_object = None
        try:
            context['tracked_model_relations'][rel] = {'setup': get_model('records', 'RecordSetup').objects.get(model__model=rel.var_name),
                                                       'related_object': related_object}
        except get_model('records', 'RecordSetup').DoesNotExist:
            context['untracked_model_relations'][rel] = {'related_object': related_object}

    tpl = 'prospects/rendering/objectdetail/object.html'
    return render_to_string(tpl, context)


@register.filter(name='as_table')
def as_table(obj, parent):

    context = {'fields': SortedDict(), 'object': obj, 'm2m_fields': SortedDict(), 'parent': parent}

    for field in obj._meta.fields:
        context['fields'][field.verbose_name] = getattr(obj, field.name)

    if not parent is obj:
        context['fields'].pop(parent._meta.object_name.lower())
        context['fields'].pop('ID')

    for m2m_field in obj._meta.many_to_many:
        context['m2m_fields'][m2m_field] = getattr(obj, m2m_field.name).all()

    
    tpl = 'records/object_table.html'
    return render_to_string(tpl, context)


@register.filter(name='related_objects_table')
def related_objects_table(objects, parent):
    fields = [f for f in objects.model._meta.fields if not f.name in ('id', parent._meta.object_name.lower())]
    context = {'headers': [f.verbose_name for f in fields], 'data': SortedDict(),  'parent': parent}

    for obj in objects:
        context['data'][obj] = [getattr(obj, field.name) for field in fields]
    
    tpl = 'records/related_objects_table.html'
    return render_to_string(tpl, context)


@register.filter(name='rform')
def rform(form, level):
    context = {'form': form, 'level': level}
    tpl = 'records/rform.html'
    return render_to_string(tpl, context)



@register.tag
def create(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("'%s' takes at least one argument"
                                  " (menu name)" % bits[0])
    record_name = bits[1]
    args = []
    kwargs = {}
    asvar = None
    bits = bits[2:]
    if len(bits) >= 2 and bits[-2] == 'as':
        asvar = bits[-1]
        bits = bits[:-2]

    # process them as template vars
    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise TemplateSyntaxError("Malformed arguments to menu tag")
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
            else:
                args.append(parser.compile_filter(value))


    return CreateNode(record_name, args, kwargs, asvar)

class CreateNode(template.Node):
    def __init__(self, record_name, args, kwargs, asvar):
        self.record_name = template.Variable(record_name)
        self.args = args
        self.kwargs = kwargs
        self.asvar = asvar

    def render(self, context):
        args = [arg.resolve(context) for arg in self.args]
        kwargs = dict([(smart_str(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])

        record_name = self.record_name.resolve(context)
        #menu_name = self.menu_name#.resolve(context)

        arguments = [record_name]
        if args:
            arguments.append('/'.join(map(str, args)))

        url = reverse('create', args=arguments)

        if self.asvar:
            context[self.asvar] = url
            return ''
        else:
            return url


