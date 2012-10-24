# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.encoding import smart_str 
from django.template import Context, Template
from django.contrib.contenttypes import generic
from django.utils.datastructures import SortedDict


def render_url(url, **kwargs):
    bits = url.split()
    if bits[0] == 'create':
        t = Template("{%% load records_tags %%}{%% create %s %%}" % " ".join(bits[1:]))
    else:
        t = Template("{%% url %s %%}" % url)
    return t.render(Context(kwargs))


def get_parent_field(options):
    no_auto_fields = filter(lambda x: not isinstance(x, models.AutoField), options.fields)
    tmp = no_auto_fields[0]
    if tmp.rel:
        return tmp
    return None

def get_parent_for_instance(instance):
    field = get_parent_field(instance._meta)
    if field:
        return getattr(instance, field.name)
    return None


class ValuesGroup(models.Model):
    name = models.CharField(max_length=255, unique=True)
    is_ordinal = models.BooleanField()

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)

class CategoricalValue(models.Model):
    group = models.ForeignKey(ValuesGroup)
    key = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    weight = models.IntegerField()

    def __unicode__(self):
        return self.value
    
    class Meta:
        unique_together = (('key', 'value', 'group'),)
        ordering = ('weight', 'value')

# class RecordTriger(models.Model):
#     setup = models.ForeignKey(RecordSetup, related_name="arguments")

#     is_create_enabled = models.BooleanField(default=True)
#     create_trigger_lookup = models.CharField(max_length=128, verbose_name="A lookup on the object that triggers the class name to be applied", blank=True)

#     is_update_enabled = models.BooleanField(default=True)
#     update_trigger_lookup = models.CharField(max_length=128, verbose_name="A lookup on the object that triggers the class name to be applied", blank=True)

#     is_delete_enabled = models.BooleanField(default=True)
#     update_trigger_lookup = models.CharField(max_length=128, verbose_name="A lookup on the object that triggers the class name to be applied", blank=True)


class RecordActionSetup(models.Model):
    ACTIONS = (('c', 'Create'), ('u', 'Update'), ('d', 'Delete'))
    setup = models.ForeignKey('RecordSetup', related_name="actions")
    action = models.CharField(max_length=1, choices=ACTIONS)
    is_enabled = models.BooleanField(verbose_name="Is this action enabled", default=False)

    title = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)
    action_label = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = (('setup', 'action'),)

class RecordSetup(models.Model):
    name = models.SlugField(max_length=255, unique=True)
    model = models.ForeignKey(ContentType, related_name="record_setups")

    # triger = models.ForeignKey('RecordTriger', related_name="record_setups") 

    only_registered_fields = models.BooleanField(default=False)
    use_model_m2m_fields = models.BooleanField(default=True)

    # where to redirect after success when create or update
    success_url = models.CharField(max_length=255)
    reverse_success_url = models.BooleanField()

    # where to redirect if creation is canceled
    cancel_url = models.CharField(max_length=255, verbose_name="Cancel creation action", help_text="Use arguments from the provided record arguments")
    reverse_cancel_url = models.BooleanField()

    # this will be used when object was deleted
    generic_url = models.CharField(max_length=255)
    reverse_generic_url = models.BooleanField()

    def get_component(self):
        try:
            return self.component_assignment.component
        except Exception, error:
            return None

    def is_delete_enabled(self):
        return not self.actions.filter(action='d', is_enabled=False).exists()

    def get_context_elements(self, context, action):

        model = self.model.model_class()
        context.update({'model': model, 'meta': model._meta})

        elements = {'title': self._default_title(action, context), 
                    'body': None,
                    'action_label': None}
        try:
            setup = self.actions.get(action=action)
            for attr in elements:
                if getattr(setup, attr):
                    elements[attr] = Template(getattr(setup, attr)).render(Context(context))
        except RecordActionSetup.DoesNotExist:
            pass
        return elements

    def _default_title(self, action, context):
        return {'c': lambda: '%s' % context['meta'].verbose_name,
                'u': lambda: '%(object)s' % context,
                'd': lambda: '%(object)s' % context,}.get(action)()


    def get_initial(self, **kwargs):
        initial = ((field.field, field.get_initial(**kwargs)) for field in self.fields.all())
        # now we remove none elements to avoid zeroing in updates
        return dict(filter(lambda x: not x[1] is None, initial))

    def get_success_url(self, **kwargs):
        print kwargs
        return self.get_url(self.success_url, self.reverse_success_url, **kwargs)

    def get_generic_url(self, **kwargs):
        return self.get_url(self.generic_url, self.reverse_generic_url, **kwargs)

    def get_cancel_url(self, **kwargs):
        return self.get_url(self.cancel_url, self.reverse_cancel_url, **kwargs)

    def get_url(self, url, reverse, **kwargs):
        if reverse:
            return render_url(url, **kwargs)
        return url

    def __unicode__(self):
        return self.name

class RecordArgument(models.Model):
    setup = models.ForeignKey(RecordSetup, related_name="arguments")
    name = models.SlugField()
    regex = models.CharField(max_length=255)
    weight = models.IntegerField()

    def __unicode__(self):
        return u"%s:%s" % (self.setup, self.name)

    class Meta:
        unique_together = (('setup', 'name'), ('setup', 'weight'))
        ordering = ('weight',)

class RecordField(models.Model):
    setup = models.ForeignKey('RecordSetup', related_name="fields")
    field = models.SlugField() # this shuld be renamed to `name`
    
    default_value = models.CharField(max_length=255, blank=True)
    is_hidden = models.BooleanField(default=False)

    def __unicode__(self):
        return u"%s:%s" % (self.setup, self.field)

    def get_initial(self, **kwargs):
        query = dict(((smart_str(lookup.lookup), kwargs.get(lookup.value.name)) for lookup in self.lookups.all()))
        if query:
            return self.setup.model.model_class()._meta.get_field(self.field).rel.to._default_manager.get(**query)
        try:
            return kwargs.get(self.value.value.name)
        except FieldValueSetup.DoesNotExist:
            return Template(self.default_value).render(Context(kwargs)) or None

            
class FieldValueSetup(models.Model):
    value = models.ForeignKey('RecordArgument')
    field = models.OneToOneField('RecordField', related_name="value")


class ObjectLookupSetup(models.Model):
    value = models.ForeignKey('RecordArgument')
    field = models.ForeignKey('RecordField', related_name="lookups")
    lookup = models.SlugField()


class M2MRelationSetup(models.Model):
    setup = models.ForeignKey(RecordSetup, related_name="related_m2m_models")
    through = models.ForeignKey(ContentType)
    from_field = models.SlugField(help_text="Field name pointing to the source model")
    to_field = models.SlugField(help_text="Field name pointing to the dst model")

    min_count = models.IntegerField(null=True, blank=True)
    max_count = models.IntegerField(null=True, blank=True)


    def get_model_verbose_name(self):
        return self.get_to_model()._meta.verbose_name

    def get_model_verbose_name_plural(self):
        return self.through.model_class()._meta.verbose_name_plural

    def get_to_model(self):
        return self.through.model_class()._meta.get_field(self.to_field).rel.to

    def get_from_model(self):
        return self.through.model_class()._meta.get_field(self.from_field).rel.to

    def get_choices_manager(self):
        return self.get_to_model()._default_manager

    def get_choices(self):
        return self.get_choices_manager().complex_filter(self.get_choices_field().rel.limit_choices_to)
        #return self.through.model_class()._meta.get_field(self.to_field).get_choices()

    def get_choices_field(self):
        return self.through.model_class()._meta.get_field(self.to_field)

    def get_choices_by_arguments(self, arguments):
        query = dict(((smart_str(lookup.lookup), arguments.get(lookup.field.field) ) for lookup in self.lookups.all()))
        return self.get_choices_manager().filter(**query)

class M2MChoicesSetup(models.Model):
    setup = models.ForeignKey('M2MRelationSetup', related_name="lookups")
    field = models.ForeignKey('RecordField')
    lookup = models.SlugField()

class O2MRelationSetup(models.Model):
    setup = models.ForeignKey(RecordSetup, related_name="related_o2m_models")
    model = models.ForeignKey(ContentType, related_name="o2m_setups")

    rel_field_name = models.CharField(max_length=50, verbose_name="Related content FK field", help_text="Name of the field that stores related object")
    FK_TYPES = (('f', 'Standard ForeignKey'), ('g', 'Generic relation (with CT)'), ('r', 'Raw related instance ID'))
    rel_type = models.CharField(max_length=1, choices=FK_TYPES, default='f')

    min_count = models.PositiveSmallIntegerField(null=True, blank=True)
    max_count = models.PositiveSmallIntegerField(null=True, blank=True)

    def __unicode__(self):
        return u"%s <- %s" % (self.setup, self.model)


    def get_rel_field(self):
        if self.rel_type == 'g':
            return filter(lambda x: x.name == self.rel_field_name, self.model.model_class()._meta.virtual_fields)[0]
        return self.model._meta.get_field(self.rel_field_name)


    def get_rel_field_name(self):
        if self.rel_type == 'g':
            return self.get_rel_field().fk_field
        return self.rel_field_name

    def get_rel_ct_field_name(self):
        if self.rel_type == 'g':
            return self.get_rel_field().ct_field
        return None
    
    def get_rel_id_field(self):
        if self.rel_type == 'g':
            return self.get_rel_field().fk_field
        return self.rel_field_name

    def extract_id(self, obj):
        if self.rel_type == 'f':
            return obj
        return obj.id

    def get_max_count(self):
        return self.max_count or 1

    def get_model_verbose_name(self):
        return self.model.model_class()._meta.verbose_name

    def get_model_verbose_name_plural(self):
        return self.model.model_class()._meta.verbose_name_plural

    def can_create_entry(self):
        return True


class RecordRelation(models.Model):
    setup = models.ForeignKey(RecordSetup, related_name="related_models")
    model = models.ForeignKey(ContentType)
    elements_count = models.IntegerField()

    def get_model_verbose_name(self):
        return self.model.model_class()._meta.verbose_name

    def get_model_verbose_name_plural(self):
        return self.model.model_class()._meta.verbose_name_plural

    def can_create_entry(self):
        return True





    
    
