from models import *
from django.contrib import admin

class ProspectAdmin(admin.ModelAdmin):
    list_display = ('name', 'verbose_name')
    search_fields = ('name', 'verbose_name')

class SourceAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'prospect')

class AspectAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'source')


class ColumnAdmin(admin.ModelAdmin):
    list_display = ('field', 'table')
    search_fields = ('field__db_field',)
    list_filter = ('table',)

class FieldAdmin(admin.ModelAdmin):
    list_display = ('variant', 'verbose_name', 'db_field', 'lookup')
    list_filter = ('variant',)

class CellStyleAdmin(admin.ModelAdmin):
    list_display = ('column', 'get_table')
    search_fields = ('css',)
    list_filter = ('column__table',)


admin.site.register(Prospect, ProspectAdmin)
admin.site.register(Source, SourceAdmin)
admin.site.register(Aspect, AspectAdmin)

admin.site.register(ProspectVariant)
admin.site.register(AspectValue)
admin.site.register(UserRelation)

admin.site.register(Field, FieldAdmin)
admin.site.register(FieldURL)

admin.site.register(Operator)
admin.site.register(ProspectOperator)

admin.site.register(ListRepresentation)
admin.site.register(ObjectDetail)
admin.site.register(VariantContext)
admin.site.register(VariantContextAspectValue)

admin.site.register(CustomPostfix)
admin.site.register(Table)
admin.site.register(Column, ColumnAdmin)
admin.site.register(CellStyle, CellStyleAdmin)



admin.site.register(DetailMenu)
admin.site.register(VariantMenu)
