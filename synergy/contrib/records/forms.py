# -*- coding: utf-8 -*-
import itertools

from django import forms
from django.forms import models as model_forms
from django.db.models import get_model
from django.utils.datastructures import SortedDict
from models import get_parent_field

def createform_factory(created_model, related_models, excluded_fields=[]):
    class CreateBaseForm(forms.ModelForm):
        def __init__(self, instance=None, parent=None, *args, **kwargs):
            super(CreateBaseForm, self).__init__(instance=instance, *args, **kwargs)

            self.external = SortedDict()
            if parent:
                parent_field = get_parent_field(self.instance._meta)
                self.fields[parent_field.name].initial = parent.id
                self.fields[parent_field.name].widget = forms.widgets.HiddenInput()

            categorical_model = get_model('records', 'CategoricalValue')

            for field in self._meta.model._meta.fields:
                if field.rel and field.rel.to is categorical_model:
                    # Jeżeli pole jest relacją do CategoricalValue, to dozwolone wartości 
                    # muszą należeć do grupy o tej nazwie pola
                    self.fields[field.name].queryset = self.fields[field.name].queryset.filter(group__name=field.name)

            for related_model in related_models:
                self.external[related_model] = []
                for i in range(related_model.elements_count):

                    ins = None
                    if not self.instance.pk is None:
                        ins = related_model.model.model_class().objects.filter(**{related_model.setup.model.model: self.instance})[i]
                    df = createform_factory(related_model.model.model_class(), [], excluded_fields=[self._meta.model._meta.object_name.lower()])(instance=ins, *args, **kwargs)
                    self.external[related_model].append(df)

        def is_valid(self):
            valid = [super(CreateBaseForm, self).is_valid()]
            for ex in itertools.chain(*self.external.values()):
                valid.append(ex.is_valid())
            return all(valid)

        def save(self, *args, **kwargs):
            self.instance = super(CreateBaseForm, self).save(*args, **kwargs)

            for f in itertools.chain(*self.external.values()):
                ins = f.save(commit=False)
                setattr(ins, self._meta.model._meta.object_name.lower(), self.instance)
                ins.save()

            return self.instance

        class Meta:
            model =  created_model
            exclude = excluded_fields

    return CreateBaseForm
