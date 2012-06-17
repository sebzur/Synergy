import fields

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.urlresolvers import reverse
from django.template.base import VariableDoesNotExist
from django.conf import settings
from django.utils.encoding import smart_str 

from django.core.exceptions import ValidationError
from django import template

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


def resolve_lookup(obj, lookup):
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
        return self.get_source().filter(**self.sanitize_query(**query))
    
    def sanitize_query(self, **query):
        # the ids list of admissible aspects
        ids = self.get_source().aspects.values_list('id', flat=True)
        return dict([(smart_str(id), query.get(id)) for id in filter(lambda x: int(x) in ids, query.keys())])

            
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
            yield (smart_str("%s__%s" % (self.aspects.get(id=aspect_id).attribute, query.get(aspect_id).get('lookup'))), query.get(aspect_id).get('value'))

class Context(models.Model):
    source = models.ForeignKey('Source', related_name="contexts")
    variant = models.ForeignKey('ProspectVariant', related_name="Variant")
    value = models.SlugField(verbose_name="Value", help_text="Value to extract as flatted values_list")
    lookup = models.SlugField(verbose_name="Relation lookup", help_text="__in operator is used, provide here the model field" )

    class Meta:
        verbose_name = "Context"
        verbose_name_plural = "Contexts"

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
        return u"%s (%s)" % (self.attribute, self.source.prospect.name)

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
                   'IntegerField': 'continous',
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
    record = models.ForeignKey('records.RecordSetup', null=True, blank=True)
    # The results will be cached with the timeout specified here.
    cache_timeout = models.PositiveSmallIntegerField(verbose_name="Cache timeout", null=True, blank=True)

    header = models.TextField(verbose_name="Variant header text", help_text="If present, it will be used to render the header", blank=True)
    footer = models.TextField(verbose_name="Variant footer text", help_text="If present, it will be used to render the footer", blank=True)
    empty_text = models.TextField(verbose_name="Empty text", help_text="If present, this will be used in case the variant returns no results", blank=True)
    css_classes = models.CharField(max_length=255, help_text="The CSS class names will be added to the prospect variant. This enables you to use specific CSS code for each variant. You may define multiples classes separated by spaces.", blank=True)
    submit_label = models.CharField(max_length=255, verbose_name="Sumbmit button label", default="Submit")

    def filter(self, user, **query):
        """ Returns variant results.

        Query is a dictionary with a structure:
        {'aspect_id': {'lookup': gt|lt|exact|[...], 'value': [...]}}

        """ 
        # wartosci aspektow dla kontekstu leca po prostu w query


        # if aspect has some values stored, override the query
        c = {}
        for aspect_value in self.aspect_values.filter(is_exposed=False):
            c[str(aspect_value.aspect.id)] = {'lookup':aspect_value.lookup, 'value':  aspect_value.value}

        query.update(c)

        data = self.prospect.filter(**query)        

        for context in self.prospect.source.contexts.all():
            if context.variant.prospect.sanitize_query(**query):
                context_values = context.variant.filter(user, **query).values_list(context.value, flat=True)
                data = data.filter(**{"%s__in" % context.lookup: context_values})

        # User related lookup
        q_obj = None
        for user_relation in self.user_relations.all():
            values = user_relation.content_type.model_class().objects.filter(**{smart_str(user_relation.user_field): user}).values_list(user_relation.value_field, flat=True)
            if q_obj:
                q_obj |= models.Q(**{smart_str("%s__in" % user_relation.related_by_field): values})
            else:
                q_obj = models.Q(**{smart_str("%s__in" % user_relation.related_by_field): values})
        if q_obj:
            #data = data.filter(**{"%s__in" % user_relation.related_by_field: values})
            data = data.filter(q_obj)
        # ----------------------------------------------


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
    variant = models.ForeignKey('ProspectVariant', related_name="aspect_values")
    value = models.CharField(max_length=255, verbose_name="A value entered")
    lookup = models.CharField(max_length=255, verbose_name="Lookup")
    is_exposed = models.BooleanField(verbose_name="Should this aspect settings be exposed to the user?", default=False)

    class Meta:
        unique_together = (('variant', 'aspect'),)

class UserRelation(models.Model):
    variant = models.ForeignKey('ProspectVariant', related_name="user_relations")
    # content type with user FK
    content_type = models.ForeignKey('contenttypes.ContentType', help_text="CT with user field that will be use")
    # db field related to user which will be used to query for the 
    # content_type objects related with authenticated user
    user_field = models.SlugField(max_length=255, verbose_name="User field", help_text="User field name used to filter out objects (of CT) related to the currently authenticated user" )
    value_field = models.SlugField(max_length=255, verbose_name="Value field", help_text="The field of CT that will be used to feed the lookup")
    # relation field has to point to content_type 
    related_by_field = models.SlugField(max_length=255, verbose_name="Related by field")
    weight = models.IntegerField()
    
    class Meta:
        ordering = ('weight', )
        verbose_name = "User relation"
        verbose_name_plural = "User relations"
        unique_together = (('variant', 'content_type'),)

    
class VariantMenu(models.Model):
    variant = models.ForeignKey('ProspectVariant', related_name="menus")
    menu = models.ForeignKey('menu.Menu', related_name="variants")


#class VariantRelation(models.Model):
#    variant = models.ForeignKey('ProspectVariant')
#    related_variant = models.ForeignKey('ProspectVariant')
#    db_field = models.SlugField(max_length=255, verbose_name="Database field")
#    relation_field = models.CharField(max_length=255, verbose_name="Lookup")

#    class Meta:
#        unique_together = (('variant', 'related_variant'),)

class Field(models.Model):
    LINK_CHOICES = (('o', 'Object detail view'), ('u', 'Record update'), ('d', 'Record delete'))

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
    # === to do wywalenia ==
    as_object_link = models.BooleanField(verbose_name="Link this field to its node", default=False)
    # ==
    link_to = models.CharField(max_length=1, verbose_name="Link this field to...", choices=LINK_CHOICES, blank=True)

    default_text = models.CharField(max_length=255, verbose_name="If the field is empty, display this text instead", blank=True)
    default_if_none_text = models.CharField(max_length=255, verbose_name="If the field is empty, display this text instead", blank=True)
    # The field output can be rewriten. The synatx is: %(token)s where token is a valid replacement string.
    rewrite_as = models.CharField(max_length=255, verbose_name="Rewrite the output of this field", help_text="If checked, you can alter the output of this field by specifying a string of text with replacement tokens that can use any existing field output.", blank=True)
    
    def get_object_link(self, obj):
        urls = {'o': 'detail', 'u': 'update', 'd': 'delete'}
        return getattr(self, 'get_object_%s_link' % urls.get(self.link_to))(obj)

    def get_object_detail_link(self, obj):
        return reverse('detail', args=[self.variant.name, obj.pk])

    def get_object_update_link(self, obj):
        return reverse('update', args=[self.variant.record.name, obj.pk])

    def get_object_delete_link(self, obj):
        return reverse('delete', args=[self.variant.record.name, obj.pk])

    def as_link(self):
        return self.link_to or models.get_model('prospects', 'FieldURL').objects.filter(field=self).exists()

    def get_value(self, obj):
        # Should check if obj is instance of the variant source
        value =  get_related_value(obj, self.db_field)
        if self.lookup and not (value is None): # if value is None, leave the lookup
            value = self._resolve_lookup(value, self.lookup)
        value = self._rewrite(value)
        if self.link_to:
            return {'url': self.get_object_link(obj), 'value': value}

        try:
           return {'url': self._render_url(obj, value), 'value': value} 
        except models.get_model('prospects', 'FieldURL').DoesNotExist:
            return value


    def _render_url(self, obj, value):
        url_setup = self.field_url
        if url_setup.reverse_url:
            bits = url_setup.url.split()
            if bits[0] == 'create':
                t = template.Template("{%% load records_tags %%} {%% create %s %%}" % " ".join(bits[1:]))
            else:
                t = template.Template("{%% url %s %%}" % url_setup.url)
            context = {'value': value, 'object': obj}
            return t.render(template.Context(context))
        return url_setup.url


    def _rewrite(self, value):
        if self.rewrite_as:
            t = template.Template(self.rewrite_as)
            return t.render(template.Context({'value': value}))
        return value


    def _resolve_lookup(self, obj, lookup):
        return resolve_lookup(obj, lookup)

    def __unicode__(self):
        return u"%s::%s (%s)" % (self.db_field, self.lookup, self.variant.name)
    
class FieldURL(models.Model):
    field = models.OneToOneField('Field', related_name='field_url')
    url = models.CharField(max_length=200)
    # if resolve_url is set, Django will try to
    # resolve the value to get the full URL
    reverse_url = models.BooleanField(default=True)
    css_class = models.CharField(max_length=255, blank=True)
    prefix_text = models.CharField(max_length=255, blank=True)
    suffix_text = models.CharField(max_length=255, blank=True)
    target = models.CharField(choices=(('_blank', '_blank'), ('_parent', '_parent')), max_length=32, blank=True)
    alt_text = models.CharField(max_length=200, blank=True)

class ObjectDetail(models.Model):
    variant = models.OneToOneField('ProspectVariant')
    postfix = models.BooleanField(default=False)
    use_posthead = models.BooleanField(default=False)
    context_operator = fields.CallableField(max_length=255, verbose_name="The callable to call on the context", blank=True)    

    title = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)

    def get_title(self, obj):
        if self.title:
            t = template.Template(self.title)
            return t.render(template.Context({'object': obj}))
        return u"%s" % obj

    def get_body(self, obj):
        if self.body:
            t = template.Template(self.body)
            return t.render(template.Context({'object': obj}))
        return ''

    def get_record(self):
        return self.variant.record

    def __unicode__(self):
        return self.variant.name

    def get_context_data(self, obj, *args, **kwargs):
        
        ctx = {'variant_contexts': dict((v_c, v_c.get_query(obj)) for v_c in self.variant_contexts.all())}

        if self.postfix:
            postfix_value = "%s" % self.variant.name
            postfixes = {'objectdetail': postfix_value}
            if self.use_posthead:
                postfixes['posthead'] = postfix_value
            ctx.update({'region_postfixes': postfixes})
        return ctx


class DetailField(models.Model):
    object_detail = models.ForeignKey('ObjectDetail', related_name="fields")
    field = models.ForeignKey('Field', related_name="detail_fields")
    weight = models.IntegerField()

    def __unicode__(self):
        return u"%s : %s" % (self.object_detail, self.field)

    class Meta:
        verbose_name = "Detail Field"
        verbose_name_plural = "Detail Fields"
        ordering = ('weight',)


class DetailFieldStyle(models.Model):
    MODES = (('c', 'class'), ('s', 'style'))
    field = models.ForeignKey('DetailField', related_name="styles")
    css_mode = models.CharField(max_length=1, choices=MODES)
    css = models.CharField(max_length=128, verbose_name="CSS class name")
    trigger_lookup = models.CharField(max_length=128, verbose_name="A lookup on the object that triggers the class name to be applied", blank=True)
    weight = models.IntegerField()

    class Meta:
        verbose_name = "Detail field style"
        verbose_name_plural = "Detail field styles"
        ordering = ('weight',)

class DetailMenu(models.Model):
    object_detail = models.ForeignKey('ObjectDetail', related_name="menus")
    menu = models.ForeignKey('menu.Menu', related_name="object_details")

#class DetailMenuArgument(models.Model):
#    detail_menu = models.ForeignKey('DetailMenu', related_name="arguments")
#    argument = models.ForeignKey('Aspect')
#    value_field = models.ForeignKey('Field')
    

class VariantContext(models.Model):
    object_detail = models.ForeignKey('prospects.ObjectDetail', related_name="variant_contexts")
    variant = models.ForeignKey('ProspectVariant')

    def __unicode__(self):
        return u"%s <- %s" % (self.object_detail, self.variant)

    def get_query(self, obj):
        return dict([(str(aspect_value.aspect.id), {'lookup': aspect_value.lookup, 'value': aspect_value.value_field.get_value(obj)}) for aspect_value in self.aspect_values.all()])

class VariantContextAspectValue(models.Model):
    variant_context = models.ForeignKey('VariantContext', related_name="aspect_values")
    aspect = models.ForeignKey('Aspect')
    value_field = models.ForeignKey('Field')
    lookup = models.CharField(max_length=255, verbose_name="Lookup")

    def __unicode__(self):
        return u"%s %s %s" % (self.variant_context, self.aspect, self.value_field)

    def clean(self):
        if self.variant_context.variant.prospect != self.aspect.source.prospect:
            raise ValidationError('Variant context and aspect prospects mismatch!')
        

#class ObjectDetailContext(models.Model):
#    verbose_name = models.CharField(max_length=255, verbose_name="Verbose name")
#    object_detail = models.ForeignKey('prospects.ObjectDetail')
#    context_operator = fields.CallableField(max_length=255, verbose_name="The callable to call on the context", blank=True)
    
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
        try:
            return u"%s" % self.variant.get().name
        except ListRepresentation.DoesNotExist, error:
            return "%s" % error

    def get_context_data(self, *args, **kwargs):
        # Every display can add something to the context
        return {}

    def get_variant(self):
        return self.variant.get().variant

    def get_name(self):
        return self.variant.get().name

    def get_verbose_name(self):
        return self.variant.get().variant.verbose_name

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

    def is_triggered(self, obj):
        """ Obj is the objects that is the source of the field in column """
        if self.trigger_lookup and not (obj is None):
            return self.negate_trigger ^ bool(resolve_lookup(obj, self.trigger_lookup))
        return True

    def get_styles(self, value):
        return {'class': ' '.join(self.get_triggered_styles('c', value)),
                'style': ' '.join(self.get_triggered_styles('s', value))
                }

    def get_triggered_styles(self, css_mode, value):
        return (style.css for style in self.styles.filter(css_mode=css_mode) if style.is_triggered(value))

    class Meta:
        ordering = ('weight',)

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


# --------------------------------------------
# some ideas for the future imlementation are:
# - custom template display
# - teaser display settings
# - table display
# -------------------------------------------
