from models import *
from django.contrib import admin

class ProspectAdmin(admin.ModelAdmin):
    list_display = ('name', 'verbose_name')
    search_fields = ('name', 'verbose_name')

class SourceAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'prospect')

class AspectAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'source')


admin.site.register(Prospect, ProspectAdmin)
admin.site.register(Source, SourceAdmin)
admin.site.register(Aspect, AspectAdmin)

admin.site.register(ProspectVariant)
admin.site.register(AspectValue)
admin.site.register(VariantDisplay)
admin.site.register(Operator)
admin.site.register(ProspectOperator)

admin.site.register(CustomPostfixDisplay)
admin.site.register(TableDisplay)
admin.site.register(Column)
