from django.db import models

class HookedForeignKey(models.ForeignKey):
    def formfield(self, **kwargs):
        field = super(HookedForeignKey, self).formfield(**kwargs)
        setattr(field, 'init_hook',  getattr(self.model, "%s_hook" % self.name))
        return field
