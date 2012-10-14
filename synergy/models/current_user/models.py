# This code is based on the Chapter 11, "Enhancing applications" 
# from Pro Djanog by Matin Alchin. 
# This book is worth of your spare time - read it if you can.

import registration

from django.db import models
from django.contrib.auth.models import User


class CurrentUserField(models.ForeignKey):

    def __init__(self, **kwargs):
        super(CurrentUserField, self).__init__(User, null=True, blank=True, on_delete=models.SET_NULL, **kwargs)

    def contribute_to_class(self, cls, name):
        super(CurrentUserField, self).contribute_to_class(cls, name)
        registry = registration.FieldRegistry()
        registry.add_field(cls, self)
        
