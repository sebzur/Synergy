from models import *
from django.contrib import admin

class CreateAdmin(admin.ModelAdmin):
    list_display = ('name', 'model', 'object_detail')

class O2MRelationAdmin(admin.ModelAdmin):
    list_display = ('setup', 'model')
    
admin.site.register(RecordSetup, CreateAdmin)
admin.site.register(RecordRelation, O2MRelationAdmin)
admin.site.register(CategoricalValue)
admin.site.register(ValuesGroup)

