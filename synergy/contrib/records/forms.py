# -*- coding: utf-8 -*-
import itertools

from django import forms
from django.forms import models as model_forms
from django.db.models import get_model
from django.utils.datastructures import SortedDict
from models import get_parent_field

def create_internal_m2m_form_factory(rel, from_model):
    to_exclude = [from_model._meta.object_name.lower()]

    class M2MBaseForm(forms.ModelForm):
        def __init__(self, select, instance=None, *args, **kwargs):

            super(M2MBaseForm, self).__init__(instance=instance, *args, **kwargs)

            r_name = rel.through._meta.object_name.lower()
            self.select = select
            self.fields[r_name].initial = select.id
            self.fields[r_name].widget = forms.widgets.HiddenInput()
            self.fields.insert(0, "%s_%d" % (select._meta.object_name.lower(), select.id), forms.BooleanField(label=select, required=False, initial=bool(instance)))

        def save(self, *args, **kwargs):
            return super(M2MBaseForm, self).save(*args, **kwargs)

        class Meta:
            model =  rel.through
            exclude = to_exclude

    return M2MBaseForm


def create_m2m_form_factory(m2m_relation_setup):
    to_exclude = [m2m_relation_setup.from_field]

    class M2MBaseForm(forms.ModelForm):
        setup = m2m_relation_setup

        def __init__(self, select, instance=None, *args, **kwargs):
            super(M2MBaseForm, self).__init__(instance=instance, *args, **kwargs)
            r_name = m2m_relation_setup.to_field
            self.select = select
            self.fields[r_name].initial = select.id
            self.fields[r_name].widget = forms.widgets.HiddenInput()
            self.fields.insert(0, "%s_%d" % (select._meta.object_name.lower(), select.id), forms.BooleanField(label=select, required=False, initial=bool(instance)))

        def save(self, *args, **kwargs):
            return super(M2MBaseForm, self).save(*args, **kwargs)

        class Meta:
            model =  m2m_relation_setup.through.model_class()
            exclude = to_exclude

    return M2MBaseForm


def createform_factory(created_model, related_models, related_m2m_models, use_model_m2m_fields, excluded_fields=[], hidden_fields=[]):

    to_exclude = excluded_fields + map(lambda x: str(x.name), created_model._meta.many_to_many)

    class CreateBaseForm(forms.ModelForm):
        def __init__(self, instance=None, parent=None, *args, **kwargs):
            super(CreateBaseForm, self).__init__(instance=instance, *args, **kwargs)

            self.external = SortedDict()

            for hidden in hidden_fields:
                self.fields[hidden].widget = forms.widgets.HiddenInput()
                
            categorical_model = get_model('records', 'CategoricalValue')

            for field in self._meta.model._meta.fields:
                if field.rel and field.rel.to is categorical_model:
                    # Jeżeli pole jest relacją do CategoricalValue, to dozwolone wartości 
                    # muszą należeć do grupy o tej nazwie pola
                    self.fields[field.name].queryset = self.fields[field.name].queryset.filter(group__name=field.name)


                db_type = field.db_type()
                if db_type == 'boolean':
                    # Specjalna obsługa dla boola, ze względu na potrzebę jasności wyboru, lepiej jeżeli
                    # wyświetlimy RadioSelect, gdzie user *musi* wybrać coś, niż jeśli CheckBox będzie
                    # dawałe defaultowego False przy braku wyboru

                    self.fields[field.name] =  forms.TypedChoiceField(coerce=lambda choice: {'True': True, 'False': False}[choice],
                                                                      choices=(('False', 'Nie'), ('True', 'Tak')),
                                                                      widget=forms.RadioSelect,
                                                                      initial=self.fields[field.name].initial,
                                                                      label=self.fields[field.name].label
                                                                      )


            for related_model in related_models:
                self.external[related_model] = []
                instances = related_model.model.model_class().objects.filter(**{related_model.setup.model.model: self.instance})
                for i in range(related_model.get_max_count()):
                    ins = None
                    if not self.instance.pk is None:
                        try:
                            ins = instances[i]
                        except IndexError:
                            ins = None
                    prefix="%s_%d" % (related_model.model.model, i)
                    empty_permitted = related_model.min_count is None or i >= related_model.min_count
                    df = createform_factory(related_model.model.model_class(), [], [], excluded_fields=[self._meta.model._meta.object_name.lower()])(instance=ins, 
                                                                                                                                                     prefix=prefix,
                                                                                                                                                     empty_permitted=empty_permitted,
                                                                                                                                                     *args, **kwargs)
                    self.external[related_model].append(df)


            self.external_m2m = SortedDict()
            for related_m2m_model in related_m2m_models:
                self.external_m2m[related_m2m_model] = []
                choice_manager  = related_m2m_model.get_choices_manager()
                if choice_manager.model is categorical_model:
                    choices = choice_manager.filter(group__name=related_m2m_model.rel.through._meta.object_name.lower())
                else:
                    choices = related_m2m_model.get_choices(self.initial or self.instance.__dict__)
                for choice in choices:
                    ins = None
                    if not self.instance.pk is None:
                        try:
#                            ins = related_m2m_model.rel.through._default_manager.get(**{related_m2m_model.model._meta.object_name.lower(): self.instance,
#                                                                                        related_m2m_model.rel.through._meta.object_name.lower(): choice})

                            ins = related_m2m_model.through.model_class()._default_manager.get(**{related_m2m_model.from_field: self.instance,
                                                                                                  related_m2m_model.to_field: choice})
                        except related_m2m_model.through.model_class().DoesNotExist:
                            ins = None

                    prefix="%s_%d" % (related_m2m_model.get_from_model()._meta.object_name.lower(), choice.id)

                    empty_permitted = True
                    form = create_m2m_form_factory(related_m2m_model)(prefix=prefix, instance=ins, select=choice, empty_permitted=empty_permitted, *args, **kwargs)
                    self.external_m2m[related_m2m_model].append(form)

            self.internal_m2m = SortedDict()
            if use_model_m2m_fields:
                for related_m2m_model in created_model._meta.many_to_many:
                    self.internal_m2m[related_m2m_model] = []
                    choice_manager  = related_m2m_model.rel.to._default_manager
                    if choice_manager.model is categorical_model:
                        choices = choice_manager.filter(group__name=related_m2m_model.rel.through._meta.object_name.lower())
                    else:
                        choices = choice_manager.all()
                    for choice in choices:
                        ins = None
                        if not self.instance.pk is None:
                            try:
                                ins = related_m2m_model.rel.through._default_manager.get(**{related_m2m_model.model._meta.object_name.lower(): self.instance,
                                                                                            related_m2m_model.rel.through._meta.object_name.lower(): choice})
                            except related_m2m_model.rel.through.DoesNotExist:
                                ins = None

                        prefix="%s_%d" % (related_m2m_model.model._meta.object_name.lower(), choice.id)
                        empty_permitted = True
                        self.internal_m2m[related_m2m_model].append(create_internal_m2m_form_factory(related_m2m_model.rel, related_m2m_model.model)(prefix=prefix, instance=ins, select=choice, 
                                                                                                                                                     empty_permitted=empty_permitted,
                                                                                                                                                     *args, **kwargs))
                


        def clean(self):
            super(CreateBaseForm, self).clean()
            
            self._o2m_validated = {}



            m2m_count = 0
            for m2m_model_setup, m2m_forms in self.external_m2m.iteritems():
                for f in m2m_forms:
                    if f.is_valid():
                        m2m_count += f.cleaned_data["%s_%d" % (f.select._meta.object_name.lower(), f.select.id)]
                if m2m_model_setup.min_count and m2m_count < m2m_model_setup.min_count:
                    raise forms.ValidationError(u"Wybrano zbyt mało elementów w %s. Minimalna liczba dopuszczalna %d" % (m2m_model_setup.through.model_class()._meta.verbose_name, m2m_model_setup.min_count))
                if m2m_model_setup.max_count and m2m_count > m2m_model_setup.max_count:
                    raise forms.ValidationError(u"Wybrano zbyt dużo elementów w %s. Maksymalna liczba dopuszczalna %d" % (m2m_model_setup.through.model_class()._meta.verbose_name, m2m_model_setup.max_count))

            return self.cleaned_data

        def is_valid(self):
            valid = [super(CreateBaseForm, self).is_valid()]


            for ex in itertools.chain(*self.external.values()):
                valid.append(ex.is_valid())

            for f in itertools.chain(*self.external_m2m.values()):
                valid.append(f.is_valid())

            for f in itertools.chain(*self.internal_m2m.values()):
                valid.append(f.is_valid())

            return all(valid)

        def save(self, *args, **kwargs):
            self.instance = super(CreateBaseForm, self).save(*args, **kwargs)

            for f in itertools.chain(*self.external.values()):
                if f.has_changed():
                    ins = f.save(commit=False)
                    setattr(ins, self._meta.model._meta.object_name.lower(), self.instance)
                    ins.save()

            for f in itertools.chain(*self.external_m2m.values()):
                if f.has_changed():
                    if f.cleaned_data["%s_%d" % (f.select._meta.object_name.lower(), f.select.id)]:
                        ins = f.save(commit=False)
                        setattr(ins, f.setup.from_field, self.instance)
                        ins.save()
                    else:
                        if not f.instance.pk is None:
                            f.instance.delete()

            for f in itertools.chain(*self.internal_m2m.values()):
                if f.has_changed():
                    if f.cleaned_data["%s_%d" % (f.select._meta.object_name.lower(), f.select.id)]:
                        ins = f.save(commit=False)
                        setattr(ins, self._meta.model._meta.object_name.lower(), self.instance)
                        ins.save()
                    else:
                        if not f.instance.pk is None:
                            f.instance.delete()



            return self.instance

        class Meta:
            model =  created_model
            exclude = to_exclude

    return CreateBaseForm
