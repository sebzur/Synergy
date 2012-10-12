from models import *
from django.contrib import admin

class MenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'verbose_name')
    search_fields = ('name', 'verbose_name')

class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('menu', 'name', 'verbose_name', 'url', 'reverse_url')
    list_filter = ('menu',)

class MenuItemTriggerAdmin(admin.ModelAdmin):
    list_display = ('item', 'argument', 'trigger_lookup', 'negate_trigger', 'weight')
    list_filter = ('item__menu',)


class MenuArgumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'menu')


admin.site.register(Menu, MenuAdmin)
admin.site.register(AccessPermission)
admin.site.register(MenuItem, MenuItemAdmin)
admin.site.register(MenuArgument, MenuArgumentAdmin)
admin.site.register(MenuItemTrigger, MenuItemTriggerAdmin)


