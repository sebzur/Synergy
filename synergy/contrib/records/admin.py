from models import *
from django.contrib import admin

class CreateAdmin(admin.ModelAdmin):
    list_display = ('name', 'model', 'object_detail')

    
admin.site.register(RecordSetup, CreateAdmin)
admin.site.register(RecordRelation)
admin.site.register(CategoricalValue)
admin.site.register(ValuesGroup)

