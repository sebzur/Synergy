# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.contenttypes.models import ContentType

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

class RecordSetup(models.Model):
    name = models.SlugField(max_length=255)
    model = models.OneToOneField(ContentType, related_name="record_setup")
    object_detail = models.ForeignKey('prospects.ObjectDetail')

    def __unicode__(self):
        return self.name

class RecordRelation(models.Model):
    setup = models.ForeignKey(RecordSetup, related_name="related_models")
    model = models.ForeignKey(ContentType)
    elements_count = models.IntegerField()

    def get_model_verbose_name(self):
        return self.model.model_class()._meta.verbose_name

    def can_create_entry(self):
        return True

