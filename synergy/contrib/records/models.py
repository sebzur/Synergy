# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.encoding import smart_str 
from django.template import Context, Template

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
    title = models.CharField(max_length=255)
    body = models.TextField(blank=True)
    action_label = models.CharField(max_length=255, blank=True)

    class Meta:
        unique_together = (('setup', 'action'),)

class RecordSetup(models.Model):
    name = models.SlugField(max_length=255, unique=True)
    model = models.ForeignKey(ContentType, related_name="record_setups")

    # triger = models.ForeignKey('RecordTriger', related_name="record_setups") 

    only_registered_fields = models.BooleanField(default=False)

    # where to redirect after success when create or update
    success_url = models.CharField(max_length=255)
    reverse_success_url = models.BooleanField()

    # where to redirect if creation is canceled
    cancel_url = models.CharField(max_length=255, verbose_name="Cancel creation action", help_text="Use arguments from the provided record arguments")
    reverse_cancel_url = models.BooleanField()

    # this will be used when object was deleted
    generic_url = models.CharField(max_length=255)
    reverse_generic_url = models.BooleanField()

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
        return dict(((field.field, field.get_initial(**kwargs)) for field in self.fields.all()))

    def get_success_url(self, **kwargs):
        return self.get_url(self.success_url, self.reverse_success_url, **kwargs)

    def get_generic_url(self, **kwargs):
        return self.get_url(self.generic_url, self.reverse_generic_url, **kwargs)

    def get_cancel_url(self, **kwargs):
        return self.get_url(self.cancel_url, self.reverse_cancel_url, **kwargs)

    def get_url(self, url, reverse, **kwargs):
        from django.template import Context, Template
        if reverse:
            t = Template("{%% url %s %%}" % url)
            return t.render(Context(kwargs))
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
    field = models.SlugField()
    default_value = models.CharField(max_length=255, blank=True)
    is_hidden = models.BooleanField(default=False)

    def __unicode__(self):
        return u"%s:%s" % (self.setup, self.field)

    def get_initial(self, **kwargs):
        query = dict( ((smart_str(lookup.lookup), kwargs.get(lookup.value.name)) for lookup in  self.lookups.all()) )
        if query:
            return self.setup.model.model_class()._meta.get_field(self.field).rel.to._default_manager.get(**query)

        try:
            return kwargs.get(self.value.value.name)
        except FieldValueSetup.DoesNotExist:
            return self.default_value or None
            
class FieldValueSetup(models.Model):
    field = models.OneToOneField('RecordField', related_name="value")
    value = models.ForeignKey('RecordArgument')

class ObjectLookupSetup(models.Model):
    field = models.ForeignKey('RecordField', related_name="lookups")
    value = models.ForeignKey('RecordArgument')
    lookup = models.SlugField()

    def clean(self):
        if 0:
            raise ValidationError('Test if field is db relation (FK, O2O, ...) field')

class M2MRelationSetup(models.Model):
    setup = models.ForeignKey(RecordSetup, related_name="related_m2m_models")
    through = models.ForeignKey(ContentType)
    from_field = models.SlugField()
    to_field = models.SlugField()


    def get_to_model(self):
        return self.through.model_class()._meta.get_field(self.to_field).rel.to

    def get_from_model(self):
        return self.through.model_class()._meta.get_field(self.from_field).rel.to

    def get_choices_manager(self):
        return self.get_to_model()._default_manager

class M2MChoicesSetup(models.Model):
    setup = models.ForeignKey('M2MRelationSetup', related_name="lookups")
    value = models.ForeignKey('RecordArgument')
    lookup = models.SlugField()

class RecordRelation(models.Model):
    setup = models.ForeignKey(RecordSetup, related_name="related_models")
    model = models.ForeignKey(ContentType)
    elements_count = models.IntegerField()

    def get_model_verbose_name(self):
        return self.model.model_class()._meta.verbose_name

    def can_create_entry(self):
        return True
