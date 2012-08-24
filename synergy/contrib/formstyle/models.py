# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.encoding import smart_str 
from django.template import Context, Template
from django.contrib.contenttypes import generic
from django.utils.datastructures import SortedDict

class FormLayout(models.Model):
    model = models.OneToOneField(ContentType, related_name="formlayout")
    ORIENT = (('v', 'Vertical'), ('h', 'Horizontal'))
    name = models.SlugField(unique=True)
    verbose_name = models.CharField(max_length=255)
  
    def __unicode__(self):
        return self.verbose_name

class Sizer(models.Model):
    layout = models.ForeignKey(FormLayout, related_name="sizers")
    orientation = models.CharField(max_length=1, choices=FormLayout.ORIENT)
    name = models.SlugField()
    verbose_name = models.CharField(max_length=255)
    help_text = models.TextField(blank=True)
    show_description = models.BooleanField(default=True)
    css_classes = models.CharField(max_length=255, help_text="The CSS class names will be added to the sizer. This enables you to use specific CSS code for each sizer. You may define multiples classes separated by spaces.", blank=True)

    def __unicode__(self):
        return u"%s" % self.name

    class Meta:
        unique_together = (('name', 'layout'),)

class FormField(models.Model):
    layout = models.ForeignKey(FormLayout, related_name="fields")
    field = models.SlugField()

    def clean(self):
        if self.field not in self.layout.model.model_class()._meta.get_all_field_names():
            raise ValidationError("Form field incorect!")

    class Meta:
        unique_together = (('field', 'layout'),)


class O2MRelation(models.Model):
    layout = models.ForeignKey(FormLayout, related_name="o2m_relations")
    relation = models.ForeignKey('records.O2MRelationSetup')

    class Meta:
        unique_together = (('relation', 'layout'),)


class M2MRelation(models.Model):
    layout = models.ForeignKey(FormLayout, related_name="m2m_relations")
    relation = models.ForeignKey('records.M2MRelationSetup')

    class Meta:
        unique_together = (('relation', 'layout'),)
    
class LayoutItem(models.Model):
    layout = models.ForeignKey(FormLayout, related_name="items")
    item_type = models.ForeignKey(ContentType, related_name="layout_items", limit_choices_to={'model__in': ('sizer', 'formfield', 'o2mrelation', 'm2mrelation')})
    item_id = models.PositiveIntegerField()
    item = generic.GenericForeignKey('item_type', 'item_id')
    weight = models.IntegerField()
    proportion = models.PositiveIntegerField()


    def _clean(self):
        if models.get_model('formstyle', 'SizerItem').objects.filter(item_id=self.item_id, item_type=self.item_type).exists():
            raise ValidationError("Already assinged to sizer!")

    class Meta:
        ordering = ('weight',)

class SizerItem(models.Model):
    sizer = models.ForeignKey(Sizer, related_name="items", verbose_name="Master sizer")
    item_type = models.ForeignKey(ContentType, related_name="sizer_items", limit_choices_to={'model__in': ('sizer', 'formfield', 'o2mrelation', 'm2mrelation')})
    item_id = models.PositiveIntegerField()
    item = generic.GenericForeignKey('item_type', 'item_id')
    proportion = models.PositiveIntegerField()
    weight = models.IntegerField()

    def _clean(self):
        if self.item_id == self.sizer.id and self.item_type.model == 'sizer':
            raise ValidationError("Can not assign sizer to itself!")

        if LayoutItem.objects.filter(item_id=self.item_id, item_type=self.item_type).exists():
            raise ValidationError("Already assinged to layout")

    class Meta:
        ordering = ('weight',)
