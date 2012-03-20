from models import *
from django.contrib import admin

class ProspectAdmin(admin.ModelAdmin):
    list_display = ('name', 'verbose_name')
    search_fields = ('name', 'verbose_name')

class SourceAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'prospect')

admin.site.register(Prospect, ProspectAdmin)
admin.site.register(Source, SourceAdmin)
admin.site.register(Aspect)
