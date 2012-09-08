from models import *
from django.contrib import admin

class ProspectAdmin(admin.ModelAdmin):
    list_display = ('name', 'verbose_name')
    search_fields = ('name', 'verbose_name')

class SourceAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'prospect')

class AspectAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'source')
    list_filter = ('source', )

class ColumnAdmin(admin.ModelAdmin):
    list_display = ('field', 'table')
    search_fields = ('field__db_field',)
    list_filter = ('table',)

class FieldAdmin(admin.ModelAdmin):
    list_display = ('variant', 'verbose_name', 'db_field', 'lookup', 'link_to', 'as_object_link', 'get_db_type', 'has_choices')
    list_filter = ('variant',)

class CellStyleAdmin(admin.ModelAdmin):
    list_display = ('column', 'get_table')
    search_fields = ('css',)
    list_filter = ('column__table',)


class ListRepresentationAdmin(admin.ModelAdmin):
    list_display = ('variant', 'name', 'representation_type', 'representation_id', )
    search_fields = ('name',)
    list_filter = ('representation_type',)


admin.site.register(Prospect, ProspectAdmin)
admin.site.register(Source, SourceAdmin)
admin.site.register(Aspect, AspectAdmin)
admin.site.register(NullState)

admin.site.register(ProspectVariant)
admin.site.register(AspectValue)
admin.site.register(AspectValueChoices)
admin.site.register(NullStateValue)
admin.site.register(UserRelation)

admin.site.register(Field, FieldAdmin)
admin.site.register(FieldURL)

admin.site.register(Operator)
admin.site.register(ProspectOperator)

admin.site.register(ListRepresentation, ListRepresentationAdmin)
admin.site.register(ObjectDetail)
admin.site.register(VariantContext)
admin.site.register(VariantContextAspectValue)
admin.site.register(VariantContextArgumentValue)

admin.site.register(CustomPostfix)
admin.site.register(Table)
admin.site.register(Column, ColumnAdmin)
admin.site.register(CellStyle, CellStyleAdmin)

admin.site.register(Calendar)


admin.site.register(DetailMenu)
admin.site.register(DetailField)
admin.site.register(DetailFieldStyle)
admin.site.register(VariantMenu)

admin.site.register(Context)
admin.site.register(VariantArgument)
