from models import *
from django.contrib import admin

class ProspectAdmin(admin.ModelAdmin):
    list_display = ('name', 'verbose_name')
    search_fields = ('name', 'verbose_name')

class ProspectVarantAdmin(admin.ModelAdmin):
    list_display = ('verbose_name', 'name', 'prospect', 'get_model_name', 'get_app_label')
    search_fields = ('name', 'verbose_name', 'prospect__source__content_type__model', 'prospect__source__content_type__model')
    list_filter = ('prospect',)


class VariantContextAdmin(admin.ModelAdmin):
    list_display = ('object_detail', 'variant', 'weight', 'view_mode')
    list_filter = ('object_detail',)
    
class SourceAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'prospect')

class AspectAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'source')
    list_filter = ('source', )


class FieldAdmin(admin.ModelAdmin):
    list_display = ('variant', 'verbose_name', 'db_field', 'lookup', 'link_to', 'as_object_link', 'get_db_type', 'has_choices')
    list_filter = ('variant',)

class FieldURLAdmin(admin.ModelAdmin):
    list_display = ('field', 'url', 'reverse_url')
    list_filter = ('field__variant',)

class ListRepresentationAdmin(admin.ModelAdmin):
    list_display = ('variant', 'name', 'representation_type', 'representation_id', )
    search_fields = ('name',)
    list_filter = ('representation_type',)


class DetailMenuAdmin(admin.ModelAdmin):
    list_display = ('object_detail', 'menu')

class VariantMenuAdmin(admin.ModelAdmin):
    list_display = ('variant', 'menu')
    list_filter = ('menu',)


admin.site.register(Prospect, ProspectAdmin)
admin.site.register(Source, SourceAdmin)
admin.site.register(Aspect, AspectAdmin)
admin.site.register(NullState)

admin.site.register(ProspectVariant, ProspectVarantAdmin)
admin.site.register(AspectValue)
admin.site.register(AspectValueChoices)
admin.site.register(NullStateValue)
admin.site.register(UserRelation)

admin.site.register(Field, FieldAdmin)
admin.site.register(FieldURL, FieldURLAdmin)

admin.site.register(Operator)
admin.site.register(ProspectOperator)

admin.site.register(ListRepresentation, ListRepresentationAdmin)
admin.site.register(ObjectDetail)
admin.site.register(VariantContext, VariantContextAdmin)
admin.site.register(VariantContextAspectValue)
admin.site.register(VariantContextArgumentValue)

admin.site.register(CustomPostfix)
admin.site.register(Calendar)


admin.site.register(DetailMenu, DetailMenuAdmin)
admin.site.register(DetailField)
admin.site.register(DetailFieldStyle)
admin.site.register(VariantMenu, VariantMenuAdmin)

admin.site.register(Context)
admin.site.register(VariantArgument)
