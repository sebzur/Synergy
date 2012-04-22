# -*- coding: utf-8 -*-
import itertools

from django import forms
from django.db.models import get_model
from django.template.loader import render_to_string
from django.utils.datastructures import SortedDict
import signals

def build_aspect_hash(aspect):
    return "%d__%s" % (aspect.id, aspect.attribute)

def get_hash_property(aspect_hash, property):
    properties_position = {'id': 0, 'attribute': 1}
    return aspect_hash.split('__')[properties_position.get(property)]

def split_field_name(field_name):
    prefix, aspect_hash = field_name[:6], field_name[8:]
    return prefix, aspect_hash

def build_field_name(prefix, aspect_hash):
    return "%s__%s" % (prefix, aspect_hash)

def get_fields(prospect, variant):
    fields = SortedDict()
    source = prospect.get_source()

    excluded = get_model('prospects', 'aspectvalue').objects.filter(variant__name=variant, is_exposed=False).values_list('aspect', flat=True)
    for aspect in source.aspects.exclude(id__in=excluded):
        aspect_hash = build_aspect_hash(aspect)
        aspect_field_name = build_field_name("aspect", aspect_hash)
        lookup_field_name = build_field_name("lookup", aspect_hash)
        fields[aspect_field_name] = aspect.get_formfield()
        fields[lookup_field_name] = forms.ChoiceField(choices=aspect.get_lookups())
        try:
            stored_variant = aspect.variant_values.get(variant__name=variant)
            fields[aspect_field_name].initial = stored_variant.value
            fields[lookup_field_name].initial = stored_variant.lookup
        except:
            pass


        if isinstance(fields[aspect_field_name], forms.FloatField):
            # lokalizację ustawiami ze względu na potrzebnei
            # czasami przecinki zamiast kropek
            # wtedy w settings.py trzeba jeszcze ustawić:
            # DECIMAL_SEPARATOR = ","
            # USE_L10N = True
            # USE_L10N ważne, bo sprwadza to cleaner m.in. w FloatField
            fields[attribute_full_name].localize = True
            fields[attribute_full_name].widget.is_localized = True

        #overrides = {'label': attribute.verbose_name, 'required': attribute.required and is_key_required, 'help_text': attribute.data_type.help_text}
        overrides = {'required': False}
        for k, v in overrides.iteritems():
            setattr(fields[aspect_field_name], k, v)

    return fields


class ProspectBaseForm(forms.BaseForm):
    """ Dataset base form. """

    def __init__(self, request, instance=None, *args, **kwargs):
        super(ProspectBaseForm, self).__init__(*args, **kwargs)
        self.instance = instance
        signals.prospect_form_created.send(sender=instance, form=self, request=request)

    def _as_table(self):
        """ Overriden as_table method """
        return render_to_string('landscapes/form_as_table.html', {'form': self})

    def get_aspect_fields(self):
        for field in self:
            if field.name.startswith('aspect'):
                yield field

    def get_lookup_fields(self):
        for field in self:
            if field.name.startswith('lookup'):
                yield field

    def clean(self):
        modified = self.cleaned_data.copy()
        for key in filter(lambda x: x.startswith('aspect'), self.cleaned_data.keys()):
            if not self.cleaned_data.get(key):
                modified.pop(key)
                prefix, aspect_hash = split_field_name(key)
                modified.pop(build_field_name("lookup", aspect_hash))
        return modified

def build_query(data):
    aspects = (key for key in filter(lambda x: x.startswith('aspect'), data.keys()))
    aspect_hashes = map(lambda x: split_field_name(x)[1], aspects)
    query = dict([(get_hash_property(hash, 'id'),  {'operator': data.get(build_field_name("lookup", hash)), 'value': data.get(build_field_name("aspect", hash))}) for hash in aspect_hashes])
    return query

def prospectform_factory(prospect, variant):
    fields = get_fields(prospect, variant)
    attributes = {}
    return type('ProspectForm', (ProspectBaseForm,), {'base_fields': fields, 'attributes': attributes, 'prospect': prospect})
