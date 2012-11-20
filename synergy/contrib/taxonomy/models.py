# -*- coding: utf-8 -*-
from django.db import models

class Dictionary(models.Model):
    verbose_name = models.CharField(max_length=255, unique=True)
    name = models.SlugField(max_length=255, unique=True)
    is_ordinal = models.BooleanField()
    
    parent = models.ForeignKey('Dictionary', verbose_name="Parent", related_name="subdicts", null=True, blank=True, on_delete=models.SET_NULL)
    
    def __unicode__(self):
        return u"%s" % self.verbose_name

    class Meta:
        ordering = ('verbose_name',)

class Term(models.Model):
    dictionary = models.ForeignKey(Dictionary)
    key = models.SlugField(max_length=255)
    value = models.CharField(max_length=255)
    weight = models.IntegerField()

    def __unicode__(self):
        return u"%s" %(self.value)
    
    class Meta:
        unique_together = (('key', 'value', 'dictionary'),)
        ordering = ('weight', 'value')