from django.db import models
from django.contrib.contenttypes.models import ContentType

class Comment(models.Model):
    title = models.CharField(max_length=255, verbose_name="Comment title")
    comment = models.TextField(verbose_name="Comment")
    pubdate = models.DateTimeField(auto_now_add=True)
    comment_type = models.ForeignKey('CommentType', verbose_name="Comment type")
    object_id = models.PositiveIntegerField()

    def get_object(self):
        return comment_type.content_type.model_class().objects.get(id=self.object_id)

class CommentType(models.Model):
    name = models.SlugField(max_length=255, verbose_name="Comment type machine-name")
    verbose_name = models.CharField(max_length=255, verbose_name="Comment type name")
    content_type = models.ForeignKey(ContentType)

    def __unicode__(self):
        return self.name
    
    
