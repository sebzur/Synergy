from models import *
from django.contrib import admin

class CreateAdmin(admin.ModelAdmin):
    list_display = ('name', 'model', 'object_detail')

class O2MRelationAdmin(admin.ModelAdmin):
    list_display = ('setup', 'model')

class CategoricalValueAdmin(admin.ModelAdmin):
    list_display = ('value', 'key', 'group', 'weight')
    list_filter = ('group',)
    
admin.site.register(RecordSetup, CreateAdmin)
admin.site.register(RecordRelation, O2MRelationAdmin)
admin.site.register(CategoricalValue, CategoricalValueAdmin)
admin.site.register(ValuesGroup)

