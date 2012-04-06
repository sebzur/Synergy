from django.db import models

class Prospect(models.Model):
    name = models.SlugField(verbose_name="Machine name")
    verbose_name = models.CharField(max_length=255, verbose_name="Verbose name")

    def __unicode__(self):
        return self.verbose_name

    def get_sources(self):
        return self.sources.all()

    def filter(self, **query):
        return dict(self._filter(**query))

    def _filter(self, **query):
        for source in self.get_sources():
            ids = source.aspects.values_list('id', flat=True)
            subquery = dict([(id, query.get(id)) for id in filter(lambda x: int(x) in ids, query.keys())])
            yield source, source.filter(**subquery)
            

# In general source does not have to be a SQL database. One can think 
# about is as a generic data source, i.e. SQL engine, file storage, web resource 
# available via REST interface, GranaryDB 
class Source(models.Model):
    content_type = models.ForeignKey('contenttypes.ContentType')
    prospect = models.ForeignKey('Prospect', related_name='sources')


    def __unicode__(self):
        return "%s, %s" % (self.content_type, self.prospect)

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

    def get_field(self):
        return self.source.get_model()._meta.get_field(self.attribute)

    def get_formfield(self):
        return self.get_field().formfield()        

    def get_lookups(self):
        """ Returns lookups valid for the field type defined by the aspect """
        fields = {'AutoField':  None,
                   'BigIntegerField': None,
                   'BooleanField': None,
                   'CharField': 'textual',
                   'CommaSeparatedIntegerField': None,
                   'DateField': None,
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

class ProspectState(models.Model):
    prospect = models.ForeignKey('Prospect')

class AspectValue(models.Model):
    value = models.CharField(max_length=255)
    aspect = models.ForeignKey('Aspect')
    prospect = models.ForeignKey('Prospect')
