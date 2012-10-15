# -*- coding: utf-8 -*-
import os
import uuid

from django.conf import settings
from django.contrib.contenttypes import generic
from django.core.files.storage import FileSystemStorage
from django.db import models
from django import template
from synergy.models.current_user.models import CurrentUserField

files_location = os.path.join(settings.MEDIA_ROOT)
file_system_storage = FileSystemStorage(location=files_location, base_url=settings.MEDIA_URL) 

def get_attachment_path(instance, filename):
    context = {'attachment': instance, 'filename': filename}
    path = template.Template(instance.note.note_type.path).render(template.Context(context))
    return  os.path.join("%s" % path, '%s-%s' % (uuid.uuid4(), filename))

class PublicationInfo(models.Model):
    """ Model abstract class storing usefull authoring information """
    publication_datetime = models.DateTimeField(auto_now_add=True)
    author = CurrentUserField(related_name="%(class)s")

    class Meta:
        abstract = True

class NoteAttachment(models.Model):
    note = models.ForeignKey('Note', related_name="attachments")
    attachment = models.FileField(upload_to=get_attachment_path, storage=file_system_storage)
    description = models.CharField(max_length=255, verbose_name='Description', blank=True)

class NoteComment(PublicationInfo):
    note = models.ForeignKey('Note', verbose_name="Note", related_name="comments")
    comment = models.TextField(verbose_name="Comment content")

class Note(PublicationInfo):
    title = models.CharField(max_length=255, verbose_name=u"Note title")
    body = models.TextField(verbose_name=u"Note body")

    note_type = models.ForeignKey('NoteType', verbose_name="Note type")    
    object_id = models.PositiveIntegerField(verbose_name="Related object id")

    def get_object(self):
        return self.note_type.content_type.model_class().objects.get(id=self.object_id)

class NoteType(models.Model):
    """ Models the note type, i.e. if the content type specified in the `content_type`
    attribute is allowed to have the notes attached, the object of NoteType is registered.
    """

    name = models.SlugField(max_length=255, verbose_name="Note type machine-name")
    verbose_name = models.CharField(max_length=255, verbose_name="Note type name")
    # notes are allowed to have the files attached -- attachment_path attribute
    # defines where the file will be stored -- see attachment_save function for details
    attachment_path = models.CharField(max_length=255, verbose_name="Attachment path definition")
    content_type = models.ForeignKey('contenttypes.ContentType', verbose_name="Content Type to work with")
    
    def __unicode__(self):
        return self.name
