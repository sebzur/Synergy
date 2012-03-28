# -*- coding: utf-8 -*-
import itertools

from django import forms
from django.db.models import get_model
from django.template.loader import render_to_string
from django.utils.datastructures import SortedDict
import signals

def get_formfield_name(aspect):
    return "aspect_%d" % aspect.id

def get_fields(prospect):
    fields = SortedDict()
    for source in prospect.sources.all():
        for aspect in source.aspects.all():
            formfield_name = get_formfield_name(aspect)
            fields[formfield_name] = aspect.get_formfield()

            if isinstance(fields[formfield_name], forms.FloatField):
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
                setattr(fields[formfield_name], k, v)

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


def prospectform_factory(prospect):
    fields = get_fields(prospect)
    attributes = {}
    return type('ProspectForm', (ProspectBaseForm,), {'base_fields': fields, 'attributes': attributes, 'prospect': prospect})
