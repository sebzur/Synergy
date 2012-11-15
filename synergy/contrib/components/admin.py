from models import *
from django.contrib import admin

class ModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'verbose_name')
    search_fields = ('name', 'verbose_name')

class RecordAdmin(admin.ModelAdmin):
    list_display = ('records', 'component', 'flag', 'create_flag', 'update_flag', 'delete_flag')

class VariantAdmin(admin.ModelAdmin):
    list_display = ('prospect_variant', 'component', 'flag', 'list_flag', 'detail_flag')
    list_filter = ('component',)

admin.site.register(Component, ModuleAdmin)
admin.site.register(ComponentProspectVariant, VariantAdmin)
admin.site.register(ComponentRecord, RecordAdmin)
admin.site.register(ComponentMenu)

admin.site.register(Region)
admin.site.register(Block)
admin.site.register(BlockACLItem)




