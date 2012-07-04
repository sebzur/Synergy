from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django import template
import os
import uuid

# Create your models here.

files_location = os.path.join(settings.MEDIA_ROOT)
file_system_storage = FileSystemStorage(location=files_location, base_url=settings.MEDIA_URL) 

def attachment_save(instance, filename):
    t = template.Template(instance.attachment_type.path)
    context = {'attachment': instance, 'filename':filename}
    path = t.render(template.Context(context))
    return  os.path.join("%s" % path, '%s-%s' % (uuid.uuid4(),filename) )
    
class Attachment(models.Model):
    attachment = models.FileField(upload_to = attachment_save, storage = file_system_storage)
    note = models.CharField(max_length=255, verbose_name='Note', blank=True)
    date = models.DateTimeField(auto_now_add=True)
    attachment_type = models.ForeignKey('AttachmentType', related_name='attachments', verbose_name="Type")
    object_id = models.PositiveIntegerField()
    
    def get_object(self):
        return self.attachment_type.content_type.model_class().objects.get(id=self.object_id)

class AttachmentType(models.Model):
    name = models.SlugField(max_length=255, verbose_name="Attachment type machine-name")
    verbose_name = models.CharField(max_length=255, verbose_name="Attachment type name")
    path = models.CharField(max_length=255, verbose_name="Path to attachment")
    content_type = models.ForeignKey(ContentType)
    
    def __unicode__(self):
        return self.name
