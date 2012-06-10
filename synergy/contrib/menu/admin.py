from models import *
from django.contrib import admin

class MenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'verbose_name')
    search_fields = ('name', 'verbose_name')

class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('menu', 'name', 'verbose_name', 'url', 'reverse_url')
    list_filter = ('menu',)

class MenuArgumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'menu')


admin.site.register(Menu, MenuAdmin)
admin.site.register(MenuItem, MenuItemAdmin)
admin.site.register(MenuArgument, MenuArgumentAdmin)
admin.site.register(MenuItemTrigger)


