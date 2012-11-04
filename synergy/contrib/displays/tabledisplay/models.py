from django.db import models
from synergy.contrib.prospects.models import RepresentationModel, resolve_lookup

class Table(RepresentationModel):
    is_filtered = models.BooleanField(verbose_name="Should the table have filtering enabled?")

    LANGS = (('pl', 'Polish'), ('en', 'English'))
    lang = models.CharField(max_length=2, default='pl', choices=LANGS, verbose_name="Language code")
    
    is_paginated = models.BooleanField(verbose_name="Should the table be paginated?")
    page_rows = models.PositiveIntegerField(verbose_name="Number of rows per page", default=100)

    def get_prospect_postfix(self):
        return 'tabledisplay'
    
    def get_posthead_postfix(self):
        return self.get_prospect_postfix()

    class Meta:
        app_label = "prospects"



class Column(models.Model):
    ACTIONS = (('a', 'Field empty label'), ('b', 'Value without link (if link is provided'))

    table = models.ForeignKey('Table', related_name="columns")
    field = models.ForeignKey('Field', related_name="columns")

    trigger_lookup = models.CharField(max_length=128, verbose_name="A lookup on the object that triggers if the column should be rendered", blank=True)
    negate_trigger = models.BooleanField()
    rewrite_disabled_as = models.CharField(max_length=1, choices=ACTIONS)

    sortable = models.BooleanField(verbose_name="Is this column sortable?")
    weight = models.IntegerField()

    def __unicode__(self):
        return u"%s %s" % (self.table, self.field)

    def is_url(self, obj):
        return self.field.as_link() and self.is_triggered(obj)

    def get_value(self, obj, **kwargs):
        triggered = self.is_triggered(obj)
        link = self.is_url(obj)
        if triggered or self.rewrite_disabled_as == 'b':
            value = self.field.get_value(obj, **kwargs)
        if not triggered and self.rewrite_disabled_as == 'b':
            value = value.get('value')
        if not triggered and self.rewrite_disabled_as == 'a':
            value = None
#        if type(value) == bool:
#            return template.Template("""{{ value|yesno:"Tak,Nie" }}""").render(template.Context({'value': value}))
        return value

    def is_triggered(self, obj):
        """ Obj is the objects that is the source of the field in column """
        if not hasattr(self, '_is_triggered'):
            self._is_triggered = {}
        
        if not self._is_triggered.has_key(obj):
            self._is_triggered[obj] = True
            if self.trigger_lookup and not (obj is None):
                self._is_triggered[obj] = self.negate_trigger ^ bool(resolve_lookup(obj, self.trigger_lookup))
            
        return self._is_triggered.get(obj, None)

    def get_styles(self, value):
        return {'class': ' '.join(self.get_triggered_styles('c', value)),
                'style': ' '.join(self.get_triggered_styles('s', value))
                }

    def get_triggered_styles(self, css_mode, value):
        return (style.css for style in self.styles.filter(css_mode=css_mode) if style.is_triggered(value))

    class Meta:
        ordering = ('weight',)
        app_label = "prospects"


class CellStyle(models.Model):
    MODES = (('c', 'class'), ('s', 'style'))
    column = models.ForeignKey('Column', related_name="styles")
    css_mode = models.CharField(max_length=1, choices=MODES)
    css = models.CharField(max_length=128, verbose_name="CSS class name")
    trigger_lookup = models.CharField(max_length=128, verbose_name="A lookup on the object that triggers the class name to be applied", blank=True)
    weight = models.IntegerField()

    def get_table(self):
        return self.column.table

    def is_triggered(self, obj):
        """ Obj is the objects that is the source of the field in column """
        if self.trigger_lookup and not (obj is None):
            return bool(resolve_lookup(obj, self.trigger_lookup))
        return True

    class Meta:
        ordering = ('weight',)
        app_label = "prospects"

