from django.utils import simplejson
from django.db import models
from django.utils.encoding import smart_unicode, smart_str 

class JSONDescriptor(property):

    def __init__(self, field):
        self.field = field

    def __get__(self, instance, owner):
        if instance is None:
            return self
    
        if self.field.name not in instance.__dict__:
            # The object has not been creater yet, so unpickle the data
            raw_data = getattr(instance, self.field.attname)
            # bez ztr jest type_error
            instance.__dict__[smart_str(self.field.name)] = self.field.importer(raw_data)
        return instance.__dict__[smart_str(self.field.name)]

    def __set__(self, instance, value):
        instance.__dict__[self.field.name] = value
        setattr(instance, self.field.attname, value)

class CallableField(models.CharField):

    def importer(self, post_operator):
        splitted_name = post_operator.split('.')
        callable_name = splitted_name[-1]
        import_path = '.'.join(splitted_name[:-1])
        module = __import__(import_path, globals(), locals(), [callable_name,], -1)   
        return getattr(module, callable_name)

    def get_attname(self):
        return "%s_path" % self.name
    
    def get_db_prep_lookup(self, lookup_type, value):
        raise ValueError("Can't make comparsions against serialized data.")

    def contribute_to_class(self, cls, name):
        super(CallableField, self).contribute_to_class(cls, name)
        setattr(cls, name, JSONDescriptor(self))
        
