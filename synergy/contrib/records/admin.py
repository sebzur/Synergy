from models import *
from django.contrib import admin

class CreateAdmin(admin.ModelAdmin):
    list_display = ('name', 'model')

class O2MRelationAdmin(admin.ModelAdmin):
    list_display = ('setup', 'model')

class CategoricalValueAdmin(admin.ModelAdmin):
    list_display = ('value', 'key', 'group', 'weight')
    list_filter = ('group',)

class RecordFieldAdmin(admin.ModelAdmin):
    list_display = ('setup', 'field', 'is_hidden', 'default_value')
    list_filter = ('setup',)

    
admin.site.register(RecordSetup, CreateAdmin)
admin.site.register(RecordActionSetup)
admin.site.register(RecordField, RecordFieldAdmin)
admin.site.register(RecordArgument)
admin.site.register(ObjectLookupSetup)
admin.site.register(FieldValueSetup)
admin.site.register(RecordRelation, O2MRelationAdmin)
admin.site.register(CategoricalValue, CategoricalValueAdmin)
admin.site.register(ValuesGroup)

