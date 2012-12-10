from django.db import models
from django import template
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import uuid


class PDFTemplate(models.Model):
    header = models.TextField(blank=True)
    body = models.TextField(blank=True)
    footer = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True)

    def get_template(self):
        return template.Template(self.header + self.body + self.footer)

    def get_context(self):
        return dict((image.name, image.image) for image in self.images.all())

class PDFTemplateImage(models.Model):
    template = models.ForeignKey('PDFTemplate', related_name='images')
    image = models.ForeignKey('Image', related_name='templates')


class VariantPDF(models.Model):
    variant = models.OneToOneField('prospects.ProspectVariant', related_name="pdf",null=True,blank=True)
    detail_tpl = models.ForeignKey('PDFTemplate', related_name='detail_pdfs',null=True,blank=True)
    list_tpl = models.ForeignKey('PDFTemplate', related_name='list_pdfs',null=True,blank=True)

    class Meta:
        verbose_name = "PDF"


files_location = os.path.join(settings.MEDIA_ROOT,'imagelibrary')
file_system_storage = FileSystemStorage(location=files_location, base_url=settings.MEDIA_URL)

def image_save(instance, filename):
    return  os.path.join("%s" % instance.library.name, '%s-%s' % (uuid.uuid4(),filename) )

class Image(models.Model):
    name = models.SlugField(max_length=255, verbose_name="Image library machine-name",unique=True)
    attachment = models.ImageField(upload_to = image_save, storage = file_system_storage)
    note = models.CharField(max_length=255, verbose_name='Note', blank=True)
    date = models.DateTimeField(auto_now_add=True)
    library = models.ForeignKey('ImageLibrary', related_name='images', verbose_name="Library")

class ImageLibrary(models.Model):
    name = models.SlugField(max_length=255, verbose_name="Image library machine-name", unique=True)
    verbose_name = models.CharField(max_length=255, verbose_name="Image library name")

    def __unicode__(self):
        return self.name

