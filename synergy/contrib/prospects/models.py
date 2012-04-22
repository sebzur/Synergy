import fields

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic


class Prospect(models.Model):
    name = models.SlugField(verbose_name="Machine name", unique=True)
    verbose_name = models.CharField(max_length=255, verbose_name="Verbose name")
    # Operators are applied to the output of the prospect (prospect variants to be
    # specific) evalutaion. This is where one can do some custom, really cool things
    # with the data...
    operators = models.ManyToManyField('Operator', through="ProspectOperator")

    def __unicode__(self):
        return self.verbose_name

    def get_source(self):
        return self.source

    def filter(self, **query):
        return self._filter(**query)

    def _filter(self, **query):
        ids = self.get_source().aspects.values_list('id', flat=True)
        subquery = dict([(id, query.get(id)) for id in filter(lambda x: int(x) in ids, query.keys())])
        return self.get_source().filter(**subquery)
            
class Operator(models.Model):
    callable = fields.CallableField(max_length=255, verbose_name="The callable to call after the prospects returns the data", blank=True)    
    description = models.TextField()

class ProspectOperator(models.Model):
    operator = models.ForeignKey('Operator')
    prospect = models.ForeignKey('Prospect')
    weight = models.PositiveSmallIntegerField(default=0)
    
    class Meta:
        ordering = ('weight',)

# In general source does not have to be a SQL database. One can think 
# about is as a generic data source, i.e. SQL engine, file storage, web resource 
# available via REST interface, GranaryDB 
class Source(models.Model):
    content_type = models.ForeignKey('contenttypes.ContentType')
    prospect = models.OneToOneField('Prospect', related_name='source')

    def __unicode__(self):
        return u"%s, %s" % (self.content_type, self.prospect)

    def all(self):
        return self.get_model().objects.all()
        
    def get_model(self):
        return self.content_type.model_class()

    def filter(self, **query):
        # query is a python dictionary build as
        # {aspect_1: {'operator': 'exact', 'value': value},
        #  aspect_2: {'operator': 'exact', 'value': value},
        #  ....
        #  }
        return self.all().filter(**dict(self.build_query(query)))

    def build_query(self, query):
        for aspect_id in query:
            yield ("%s__%s" % (self.aspects.get(id=aspect_id).attribute, query.get(aspect_id).get('operator')), query.get(aspect_id).get('value'))

class Aspect(models.Model):
    # Attribute is stored as a string (slug) in native Django
    # format used for query building, i.e. the valid forms are
    # 'first_name', 'personal_data__first_name', 'contact_data__personal_data__last_name'
    # The field type and related aspect features are then extracted with
    # models introspecting
    attribute = models.SlugField(max_length=255, verbose_name="Machine name")
    source = models.ForeignKey('Source', related_name="aspects")
    weight = models.IntegerField(verbose_name="Aspect weight", default=0)

    def __unicode__(self):
        return self.attribute

    def get_field(self):
        chain = self.attribute.split('__')
        model = self.source.get_model()
        for i, attribute in enumerate(chain):
            field = model._meta.get_field(attribute)
            if chain[i+1:]:
                if not field.rel:
                    raise ValueError('Something went wrong. Field retrival for `%s` stoped at `%s` while it should represents relation' % (self.attribute, attribute))
                model = field.rel.to
        return field

    def get_formfield(self):
        return self.get_field().formfield()        

    def get_lookups(self):
        """ Returns lookups valid for the field type defined by the aspect """
        fields = {'AutoField':  None,
                   'BigIntegerField': None,
                   'BooleanField': None,
                   'CharField': 'textual',
                   'CommaSeparatedIntegerField': None,
                   'DateField': 'continous',
                   'DateTimeField': 'continous',
                   'DecimalField': None,
                   'EmailField': None,
                   'FileField': None,
                   'FileField': None,
                   'FieldFile': None,
                   'FilePathField': None,
                   'FloatField': None,
                   'ImageField': None,
                   'IntegerField': None,
                   'IPAddressField': None,
                   'GenericIPAddressField': None,
                   'NullBooleanField': None,
                   'PositiveIntegerField': None,
                   'PositiveSmallIntegerField': None,
                   'SlugField': None,
                   'SmallIntegerField': None,
                   'TextField': None,
                   'TimeField': None,
                   'URLField': None,
                   'ForeignKey': 'relation',
                   'ManyToManyField': None,
                   'OneToOneField': None}

        
        lookups = {'textual': (('exact', 'Exact'), ('iexact', 'Case-insensitive exact'), ('contains', 'Contains'), ('icontains', 'Case-insensitive contains'), 
                               ('startswith', 'Starts with'), ('istartswith', 'Case-insensitive starts with'), ('endswith', 'Ends with'),
                               ('iendswith', 'Case-insensitve ends with')),
                   'continous': (('exact', 'Exact'), ('gt', 'Greater then'), ('gte', 'Greater then or exact'), ('lt', 'Lower then'), ('lte', 'Lower then or exact')),
                   'relation': (('exact', 'Exact'),),
                   }

        internal_type = fields.get(self.get_field().get_internal_type())
        return lookups.get(internal_type, (('exact', 'Exact'),))
        

    def to_python(self, value):
        return self.get_field().to_python(value)

    class Meta:
        ordering = ('weight', )

class ProspectVariant(models.Model):
    prospect = models.ForeignKey('Prospect')
    name = models.SlugField(verbose_name="Machine name", unique=True)
    verbose_name = models.CharField(max_length=255, verbose_name="Verbose name")
    is_default = models.BooleanField(verbose_name="Is this state the default one?")
    # The results will be cached with the timeout specified here.
    cache_timeout = models.PositiveSmallIntegerField(verbose_name="Cache timeout", null=True, blank=True)

    def filter(self, **query):
        data = self.prospect.filter(**query)
        if self.prospect.operators.exists():
            for operator in self.prospect.operators.all():
                data = operator.callable(data)
        return data

    def __unicode__(self):
        return self.verbose_name
    
    class Meta:
        unique_together = ('prospect', 'is_default')

class AspectValue(models.Model):
    aspect = models.ForeignKey('Aspect', related_name="variant_values")
    variant = models.ForeignKey('ProspectVariant')
    value = models.CharField(max_length=255, verbose_name="A value entered")
    lookup = models.CharField(max_length=255, verbose_name="Lookup")
    is_exposed = models.BooleanField(verbose_name="Should this aspect settings be exposed to the user?", default=False)

    class Meta:
        unique_together = (('variant', 'aspect'),)
    
class VariantDisplay(models.Model):
    variant = models.ForeignKey('ProspectVariant', related_name="displays")
    display_type = models.ForeignKey(ContentType, limit_choices_to={'model__in': ('custompostfixdisplay',)})
    display_id = models.PositiveIntegerField()
    display = generic.GenericForeignKey('display_type', 'display_id')

    class Meta:
        unique_together = (('variant', 'display_type', 'display_id'),)

class Display(models.Model):
    prospect = models.ForeignKey('Prospect')
    name = models.SlugField(max_length=255, verbose_name="Display name")
    variants = generic.GenericRelation('prospects.VariantDisplay', content_type_field='display_type', 
                                       object_id_field='display_id', related_name="%(class)s")
    class Meta:
        abstract = True
        unique_together = (('name', 'prospect'),)

class CustomPostfixDisplay(Display):
    postfix = models.SlugField(max_length=255, verbose_name="Postfix value")
    use_posthead = models.BooleanField(verbose_name="Is template using posthead entries?")

class TableDisplay(Display):
    pass

class Column(models.Model):
    table = models.ForeignKey('TableDisplay')
    verbose_name = models.CharField(max_length=255, verbose_name="Column header")
    attribue = models.CharField(max_length=255, verbose_name="Attribute")
    
# --------------------------------------------
# some ideas for the future imlementation are:
# - custom template display
# - teaser display settings
# - table display
# -------------------------------------------
