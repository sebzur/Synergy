# -*- coding: utf-8 -*-
import itertools

from django import forms
from django.forms import models as model_forms
from django.db.models import get_model
from django.utils.datastructures import SortedDict
from models import get_parent_field
from django.utils.encoding import smart_str 
NON_FIELD_ERRORS = '__all__'

def m2m_form_factory(to_exclude, r_name, through_model, m2m_relation_setup=None):
    class M2MBaseForm(forms.ModelForm):
        setup = m2m_relation_setup
        def __init__(self, select, instance=None, *args, **kwargs):
            super(M2MBaseForm, self).__init__(instance=instance, *args, **kwargs)
            self.select = select
            self.fields[r_name].initial = select.id
            self.fields[r_name].widget = forms.widgets.HiddenInput()

            if not self.visible_fields() and not instance:
                self.fields.insert(0, "%s_%d_take" % (select._meta.object_name.lower(), select.id), forms.BooleanField(label="Zarejestrować wpis?", required=False, initial=False))

            if instance:
                self.fields.insert(0, "%s_%d" % (select._meta.object_name.lower(), select.id), forms.BooleanField(label="Usunąć wpis?", required=False, initial=False))



        def has_data(self):
            # cleaned data == {} if form has not been changed and empty_permited is set
            return bool(self.cleaned_data) or (not self.has_changed() and not self.instance.pk is None)

        def to_update(self):
            return self.has_changed() and not self.to_delete() and self.has_data() and not self.instance.pk is None

        def to_insert(self):
            return self.has_changed() and self.has_data() and self.instance.pk is None

        def to_delete(self):
            if not self.instance.pk is None:
                return bool(self.cleaned_data.get("%s_%d" % (self.select._meta.object_name.lower(), self.select.id)))
            return False


        def save(self, *args, **kwargs):
            return super(M2MBaseForm, self).save(*args, **kwargs)

        class Meta:
            model =  through_model
            exclude = to_exclude

    return M2MBaseForm


def createform_factory(created_model, related_models, related_m2m_models, use_model_m2m_fields, excluded_fields=[], hidden_fields=[], can_delete=False):

    to_exclude = excluded_fields + map(lambda x: str(x.name), created_model._meta.many_to_many)

    class CreateBaseForm(forms.ModelForm):
        def __init__(self, instance=None, parent=None, *args, **kwargs):
            super(CreateBaseForm, self).__init__(instance=instance, *args, **kwargs)

            self.external = SortedDict()

            for hidden in hidden_fields:
                self.fields[hidden].widget = forms.widgets.HiddenInput()
                
            categorical_model = get_model('records', 'CategoricalValue')

            for field in [field for field in self._meta.model._meta.fields if field.name not in to_exclude]:
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


            if can_delete and instance:
                 self.fields.insert(0, "%s_%d_DELETE" % (instance._meta.object_name.lower(), instance.id), forms.BooleanField(label="Usunąć wpis?", required=False, initial=False))                


            for related_model in related_models:
                self.external[related_model] = []
                instances = related_model.model.model_class().objects.filter(**{smart_str(related_model.get_rel_id_field()): related_model.extract_id(self.instance)})
                for i in range(related_model.get_max_count()):
                    ins = None
                    if not self.instance.pk is None:
                        try:
                            ins = instances[i]
                        except IndexError:
                            ins = None
                    prefix="%s_%d" % (related_model.model.model, i)
                    empty_permitted = related_model.min_count is None or i >= related_model.min_count
                    df = createform_factory(related_model.model.model_class(), [], [], use_model_m2m_fields, 
                                            excluded_fields=[related_model.get_rel_field_name(), related_model.get_rel_ct_field_name()],
                                            can_delete=True,)(instance=ins, prefix=prefix, empty_permitted=empty_permitted, *args, **kwargs)
                    self.external[related_model].append(df)


            self.external_m2m = SortedDict()
            for related_m2m_model in related_m2m_models:
                self.external_m2m[related_m2m_model] = []
                choice_manager  = related_m2m_model.get_choices_manager()
                if choice_manager.model is categorical_model:
                    choices = choice_manager.filter(group__name=related_m2m_model.to_field)
                else:
                    choices = related_m2m_model.get_choices(self.initial or self.instance.__dict__)
                for choice in choices:
                    ins = None
                    if not self.instance.pk is None:
                        try:
                            ins = related_m2m_model.through.model_class()._default_manager.get(**{smart_str(related_m2m_model.from_field): self.instance,
                                                                                                  smart_str(related_m2m_model.to_field): choice})
                        except related_m2m_model.through.model_class().DoesNotExist:
                            ins = None

                    prefix="%s_%d" % (related_m2m_model.get_from_model()._meta.object_name.lower(), choice.id)

                    empty_permitted = True
                    form = m2m_form_factory([related_m2m_model.from_field], related_m2m_model.to_field, related_m2m_model.through.model_class(), related_m2m_model)(prefix=prefix, instance=ins, select=choice, empty_permitted=empty_permitted, *args, **kwargs)
                    self.external_m2m[related_m2m_model].append(form)

            self.internal_m2m = SortedDict()
            if use_model_m2m_fields:


                _handled = [m2m_relation.through for m2m_relation in related_m2m_models]
                _get = get_model('contenttypes','contenttype').objects.get_for_model
                internal_m2ms = (relation for relation in created_model._meta.many_to_many if _get(relation.rel.through) not in _handled)
                for related_m2m_model in internal_m2ms:
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
                        self.internal_m2m[related_m2m_model].append(m2m_form_factory([related_m2m_model.model._meta.object_name.lower()], related_m2m_model.rel.through._meta.object_name.lower(), related_m2m_model.rel.through)(prefix=prefix, instance=ins, select=choice, 
                                                                                                                                                     empty_permitted=empty_permitted,
                                                                                                                                                     *args, **kwargs))
                


        def has_data(self):
            return bool(self.cleaned_data) or (not self.has_changed() and not self.instance.pk is None)

        def to_update(self):
            return self.has_changed() and not self.to_delete() and self.has_data() and not self.instance.pk is None

        def to_insert(self):
            return self.has_changed() and self.has_data() and self.instance.pk is None

        def to_delete(self):
            if not self.instance.pk is None:
                return self.cleaned_data.get("%s_%d_DELETE" % (self.instance._meta.object_name.lower(), self.instance.id))
            return False


        def _post_clean(self):
            # We override _post_clean method to correctly handle the relations.
            # _post_clean is defined in ModelForm and sets self.instance attributes taken from 
            # self.initial -- we need this behaviour to get the fully polulated instances
            # in the child objects

            super(CreateBaseForm, self)._post_clean() # this gives us the self.instance update

            #for ex in itertools.chain(*self.external.values()): # loops over fk related forms
            #    setattr(ex.instance, self._meta.model._meta.object_name.lower(), self.instance)

            for related_model, related_forms in self.external.iteritems():
                for f in related_forms:                
#                    if related_model.rel_type == 'g':
#                        filter(lambda x: x.name == related_model.rel_field_name, f.instance._meta.virtual_fields)[0]
                    setattr(f.instance, related_model.rel_field_name, self.instance)


            try:
                # Check if the proper number of forms is filled 
                for m2m_model_setup, m2m_forms in itertools.chain(self.external_m2m.iteritems(), self.external.iteritems()):
                    m2m_count = 0
                    for f in m2m_forms:
                        if f.is_valid():
                            m2m_count += f.to_insert() or f.to_update() or (f.has_data() and not f.to_delete())

                    if m2m_model_setup.min_count and m2m_count < m2m_model_setup.min_count:
                        raise forms.ValidationError(u"Wybrano zbyt mało elementów w %s. Minimalna liczba dopuszczalna %d" % (m2m_model_setup.get_model_verbose_name(), m2m_model_setup.min_count))
                    if m2m_model_setup.max_count and m2m_count > m2m_model_setup.max_count:
                        raise forms.ValidationError(u"Wybrano zbyt dużo elementów w %s. Maksymalna liczba dopuszczalna %d" % (m2m_model_setup.get_model_verbose_name(), m2m_model_setup.max_count))
            except forms.ValidationError, e:
                self._errors[NON_FIELD_ERRORS] = self.error_class(e.messages)


        def is_valid(self):
            valid = [super(CreateBaseForm, self).is_valid()]

            for ex in itertools.chain(*self.external.values()):
                setattr(ex.instance, self._meta.model._meta.object_name.lower(), self.instance)
                valid.append(ex.is_valid())

            for f in itertools.chain(*self.external_m2m.values()):
                valid.append(f.is_valid())

            for f in itertools.chain(*self.internal_m2m.values()):
                valid.append(f.is_valid())

            return all(valid)

            
        def save(self, *args, **kwargs):
            self.instance = super(CreateBaseForm, self).save(*args, **kwargs)

#            for f in itertools.chain(*self.external.values()):

            for related_model, related_forms in self.external.iteritems():
                for f in related_forms:                
                    if f.to_update() or f.to_insert():
                        # probably we shuld assign self.instance here and then simply
                        # save with commit = True, or an option is to 
                        # use _post_clean internal ModelForm method hook
                        ins = f.save(commit=False)
                        setattr(ins, related_model.get_rel_id_field(), related_model.extract_id(self.instance))
                        if related_model.get_rel_ct_field_name():
                            setattr(ins, related_model.get_rel_ct_field_name(), get_model('contenttypes','contenttype').objects.get_for_model(self.instance))
                        ins.save()
                    elif f.to_delete():
                        f.instance.delete()

            for f in itertools.chain(*self.external_m2m.values()):
                if f.to_update() or f.to_insert():
                    ins = f.save(commit=False)
                    setattr(ins, f.setup.from_field, self.instance)
                    ins.save()
                elif f.to_delete():
                    f.instance.delete()

            for f in itertools.chain(*self.internal_m2m.values()):
                if f.to_update() or f.to_insert():
                    ins = f.save(commit=False)
                    setattr(ins, self._meta.model._meta.object_name.lower(), self.instance)
                    ins.save()
                if f.to_delete():
                    f.instance.delete()


            return self.instance

        class Meta:
            model =  created_model
            exclude = to_exclude

    return CreateBaseForm

        
    
    
