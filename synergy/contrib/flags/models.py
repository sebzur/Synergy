# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import get_model

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

class Flag(models.Model):
    name = models.SlugField(max_length="100", verbose_name="Flag name", unique=True)
    
    def __unicode__(self):
        return u"%s" % self.name

class Group(models.Model):
    name = models.SlugField(max_length=100, verbose_name="Group name", unique=True)
    members = models.ManyToManyField('auth.User', verbose_name="Group")
    
    def __unicode__(self):
        return u"%s" % self.name

class ContentFlag(models.Model):
    flag = models.ForeignKey('Flag', related_name="flags", verbose_name="Flag")
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    
    def __unicode__(self):
        if self.object_id:
            return u"Object: %s - %i - %s" % (self.content_type, self.object_id, self.flag)
        return u"Model: %s - %s" % (self.content_type, self.flag)
    
    class Meta:
        unique_together = (("flag", "content_type", "object_id"),)

    
class GroupContentFlag(models.Model):
    content_flag = models.ForeignKey('ContentFlag', related_name="group_content_flags", verbose_name="Flag")
    group = models.ForeignKey('Group', related_name="group_content_flags", verbose_name="Group")

    def __unicode__(self):
        return u"%s - %s " % (self.group, self.content_flag, )
        
    class Meta:
        unique_together = (("group", "content_flag"),)

class UserContentFlag(models.Model):
    content_flag = models.ForeignKey('ContentFlag', related_name="user_content_flags", verbose_name="Flag")
    user = models.ForeignKey('auth.User', related_name="user_content_flags", verbose_name="User")
    
    def __unicode__(self):
        return u"%s - %s " % (self.user, self.content_flag, )

    class Meta:
        unique_together = (("user", "content_flag"),)

class UserContextContentFlag(models.Model):

    content_flag = models.ForeignKey('ContentFlag', related_name='user_context_content_flags', verbose_name="Content flag to assign")
    # This content flag will be assigned to user if the following conditions are fulfiled:
    # - `user_content_type` objects set related to the authenticated user (via `user_field`) exists
    # - if object is provided (in has_perm), it's posible to use it's attributes to fine-filter
    #   the query via UserContextQuery model

    user_content_type = models.ForeignKey('contenttypes.ContentType', verbose_name="User related content type")
    user_field = models.SlugField(max_length=255, verbose_name="User field", help_text="User field name used to filter out objects (of CT) related to the currently authenticated user" )

    class Meta:
        verbose_name = "User context content flag"
        verbose_name_plural = "User context content flag"

class UserContextQuery(models.Model):
    context = models.ForeignKey('UserContextContentFlag', verbose_name="Context", related_name="object_query_setups")

    # relation field has to point to content_type 
    lookup = models.SlugField(max_length=255, verbose_name="User content field to query for")
    value_field = models.SlugField(max_length=255, verbose_name="Object value field")
    mode = models.CharField(max_length=1, choices=(('f', 'Filter'), ('e', 'Exclude')), default='f')

    class Meta:
        unique_together = (('lookup', 'value_field', 'context'),)
        verbose_name = "User contex query"
        verbose_name_plural = "User context queries"

class AuthContentFlag(models.Model):
    content_flag = models.ForeignKey('ContentFlag', related_name="auth_content_flags", verbose_name="Flag")
    is_anonymous = models.BooleanField(verbose_name="Anonymous")
    is_authenticated = models.BooleanField(verbose_name="Authenticated")
    
    def __unicode__(self):
        return u"Anon - %s, Auth - %s, Perm - %s " % (self.is_anonymous,self.is_authenticated, self.content_flag )

    class Meta:
        unique_together = (("is_anonymous", "is_authenticated", "content_flag"),)

class CustomContentFlag(models.Model):
    content_flag = models.ForeignKey('ContentFlag', related_name='custom_content_flags', verbose_name="Flag")
    custom_model = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    
    content_object = generic.GenericForeignKey('custom_model', 'object_id')
    
    def __unicode__(self):
        return u"Model - %s, ID - %s, Perm - %s " % (self.custom_model,self.object_id, self.content_flag )

    class Meta:
        unique_together = (("custom_model", "object_id", "content_flag"),)

  

