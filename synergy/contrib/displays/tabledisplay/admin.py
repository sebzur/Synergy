from models import *
from django.contrib import admin

class ColumnAdmin(admin.ModelAdmin):
    list_display = ('field', 'table')
    search_fields = ('field__db_field',)
    list_filter = ('table',)

class CellStyleAdmin(admin.ModelAdmin):
    list_display = ('column', 'get_table')
    search_fields = ('css',)
    list_filter = ('column__table',)

admin.site.register(Table)
admin.site.register(Column, ColumnAdmin)
admin.site.register(CellStyle, CellStyleAdmin)
