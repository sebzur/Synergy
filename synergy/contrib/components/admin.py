from models import *
from django.contrib import admin

class ModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'verbose_name')
    search_fields = ('name', 'verbose_name')

admin.site.register(Component, ModuleAdmin)
admin.site.register(ComponentProspectVariant)
admin.site.register(ComponentRecord)
admin.site.register(ComponentMenu)

admin.site.register(Region)
admin.site.register(Block)
admin.site.register(BlockACLItem)




