import fields

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.urlresolvers import reverse
from django.template.base import VariableDoesNotExist
from django.conf import settings

def get_field(model, attribute):
    chain = attribute.split('__')
    for i, attribute in enumerate(chain):
        field = model._meta.get_field(attribute)
        if chain[i+1:]:
            if not field.rel:
                raise ValueError('Something went wrong. Field retrival for `%s` stoped at `%s` while it should represents relation' % (self.attribute, attribute))
            model = field.rel.to
    return field

def get_related_value(obj, path):
    if path == 'self':
        return obj
    chain = path.split('__')
    for i, attribute in enumerate(chain):
        value = getattr(obj, attribute)
        if chain[i+1:]:
            if not value:
                raise ValueError('Something went wrong. Field retrival for `%s` stoped at `%s` while it should represents relation' % (path, attribute))
            obj = value
    return value


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

    header = models.TextField(verbose_name="Variant header text", help_text="If present, it will be used to render the header", blank=True)
    footer = models.TextField(verbose_name="Variant footer text", help_text="If present, it will be used to render the footer", blank=True)
    empty_text = models.TextField(verbose_name="Empty text", help_text="If present, this will be used in case the variant returns no results", blank=True)
    css_classes = models.CharField(max_length=255, help_text="The CSS class names will be added to the prospect variant. This enables you to use specific CSS code for each variant. You may define multiples classes separated by spaces.", blank=True)
    submit_label = models.CharField(max_length=255, verbose_name="Sumbmit button label", default="Submit")

    def filter(self, **query):
        data = self.prospect.filter(**query)
        if self.prospect.operators.exists():
            for operator in self.prospect.operators.all():
                data = operator.callable(data)
        return data

    def get_model_name(self):
        return self.prospect.source.content_type.model

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


class Field(models.Model):
    variant = models.ForeignKey('ProspectVariant')
    verbose_name = models.CharField(max_length=255, verbose_name="Column header")
    # -----------------------------------------
    # The two fields below define the field value.
    # - db_field selects the model instance field or instance related field
    # - lookup tells what should be retrieved from the value (after the filed was selected)
    db_field = models.SlugField(max_length=255, verbose_name="Database field")
    lookup = models.CharField(max_length=255, verbose_name="Lookup", help_text="Use dotted notation here to resolve value", blank=True)
    # -----------------------------------------
    weight = models.IntegerField()
    exclude_from_output = models.BooleanField(verbose_name="Exclude from display", default=False)
    as_object_link = models.BooleanField(verbose_name="Link this field to its node", default=False)
    default_text = models.CharField(max_length=255, verbose_name="If the field is empty, display this text instead", blank=True)
    default_if_none_text = models.CharField(max_length=255, verbose_name="If the field is empty, display this text instead", blank=True)
    # The field output can be rewriten. The synatx is: %(token)s where token is a valid replacement string.
    rewrite_as = models.CharField(max_length=255, verbose_name="Rewrite the output of this field", help_text="If checked, you can alter the output of this field by specifying a string of text with replacement tokens that can use any existing field output.", blank=True)
    
    def get_object_link(self, obj):
        return reverse('detail', args=[self.variant.name, obj.pk])

    def extract(self, obj):
        # Should check if obj is instance of the variant source
        value =  get_related_value(obj, self.db_field)
        if self.lookup:
            value = self._resolve_lookup(value, self.lookup)
        if self.as_object_link:
            return {'url': self.get_object_link(obj), 'value': value}
        return value

    def _resolve_lookup(self, obj, lookup):
        """
        Performs resolution of a real variable (i.e. not a literal) against the
        given context.
        """
        current = obj
        chain = lookup.split('.')
        try: # catch-all for silent variable failures
            for bit in chain:
                try: # dictionary lookup
                    current = current[bit]
                except (TypeError, AttributeError, KeyError):
                    try: # attribute lookup
                        current = getattr(current, bit)
                    except (TypeError, AttributeError):
                        try: # list-index lookup
                            current = current[int(bit)]
                        except (IndexError, # list index out of range
                                ValueError, # invalid literal for int()
                                KeyError,   # current is a dict without `int(bit)` key
                                TypeError,  # unsubscriptable object
                                ):
                            raise VariableDoesNotExist("Failed lookup for key [%s] in %r", (bit, current)) # missing attribute
                if callable(current):
                    if getattr(current, 'alters_data', False):
                        current = settings.TEMPLATE_STRING_IF_INVALID
                    else:
                        try: # method call (assuming no args required)
                            current = current()
                        except TypeError: # arguments *were* required
                            # GOTCHA: This will also catch any TypeError
                            # raised in the function itself.
                            current = settings.TEMPLATE_STRING_IF_INVALID # invalid method call
        except Exception, e:
            if getattr(e, 'silent_variable_failure', False):
                current = settings.TEMPLATE_STRING_IF_INVALID
            else:
                raise
        return current

    def __unicode__(self):
        return self.db_field
    
class FieldURL(models.Model):
    field = models.OneToOneField('Field')
    url = models.CharField(max_length=200)
    # if resolve_url is set, Django will try to
    # resolve the value to get the full URL
    reverse_url = models.BooleanField(default=True)
    css_class = models.CharField(max_length=255, blank=True)
    prefix_text = models.CharField(max_length=255, blank=True)
    suffix_text = models.CharField(max_length=255, blank=True)
    target= models.CharField(choices=(('_blank', '_blank'), ('_parent', '_parent')), max_length=32, blank=True)
    alt_text = models.CharField(max_length=200, blank=True)

class ObjectDetail(models.Model):
    variant = models.OneToOneField('ProspectVariant')
    postfix = models.BooleanField(default=False)
    use_posthead = models.BooleanField(default=False)
    context_operator = fields.CallableField(max_length=255, verbose_name="The callable to call on the context", blank=True)    

    def get_context_data(self, *args, **kwargs):
        if self.postfix:
            postfix_value = "%s_%s" % (self.variant.get_model_name(), self.variant.name)
            postfixes = {'objectdetail': postfix_value}
            if self.use_posthead:
                postfixes['posthead'] = postfix_value
            return {'region_postfixes': postfixes}
        return {}

    
class ListRepresentation(models.Model):
    variant = models.OneToOneField('ProspectVariant')
    name = models.SlugField(max_length=255, verbose_name="Display name", unique=True, db_index=True)

    representation_type = models.ForeignKey(ContentType, limit_choices_to={'model__in': ('custompostfix', 'table')})
    representation_id = models.PositiveIntegerField()
    representation = generic.GenericForeignKey('representation_type', 'representation_id')

    class Meta:
        unique_together = (('name', 'variant'), ('representation_type', 'representation_id'))

# ---------------------------------
# Representations section
# ---------------------------------


class RepresentationModel(models.Model):
    variant = generic.GenericRelation('ListRepresentation', content_type_field="representation_type", object_id_field="representation_id")

    def __unicode__(self):
        return u"%s" % self.__class__

    def get_context_data(self, *args, **kwargs):
        # Every display can add something to the context
        return {}

    def get_variant(self):
        return self.variant.get().variant

    def get_name(self):
        return self.variant.get().name

    class Meta:
        abstract = True

class CustomPostfix(RepresentationModel):
    postfix = models.SlugField(max_length=255, verbose_name="Postfix value")
    use_posthead = models.BooleanField(verbose_name="Is template using posthead entries?")

    def get_context_data(self, *args, **kwargs):
        postfixes = {'prospect': self.postfix,}
        if self.use_posthead:
            postfixes['posthead'] = self.postfix
        return {'region_postfixes': postfixes}


class Table(RepresentationModel):

    def get_context_data(self, *args, **kwargs):
        postfixes = {'prospect': 'tabledisplay'}
        postfixes['posthead'] = 'tabledisplay'
        return {'region_postfixes': postfixes}

class Column(models.Model):
    table = models.ForeignKey('Table', related_name="columns")
    field = models.ForeignKey('Field', related_name="columns")
    sortable = models.BooleanField(verbose_name="Is this column sortable?")
    weight = models.IntegerField()

    class Meta:
        ordering = ('weight',)




# --------------------------------------------
# some ideas for the future imlementation are:
# - custom template display
# - teaser display settings
# - table display
# -------------------------------------------
