from models import *
from django.contrib import admin

class ModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'verbose_name')
    search_fields = ('name', 'verbose_name')

admin.site.register(Module, ModuleAdmin)
admin.site.register(ModuleProspectVariant)
admin.site.register(ModlueRecord)
admin.site.register(ModlueMenu)




