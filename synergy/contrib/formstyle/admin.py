from models import *
from django.contrib import admin
from django.contrib.contenttypes.generic import GenericStackedInline

class SizerItemInline(GenericStackedInline):
    model = SizerItem
    max_num = 1
    ct_field = 'item_type'
    ct_fk_field = 'item_id'

class LayoutItemInline(GenericStackedInline):
    model = LayoutItem
    max_num = 1
    ct_field = 'item_type'
    ct_fk_field = 'item_id'

class FormFieldAdmin(admin.ModelAdmin):
    list_display = ('layout', 'field')
    list_filter = ('layout',)
    inlines = [SizerItemInline, LayoutItemInline]

class SizerAdmin(admin.ModelAdmin):
    list_display = ('layout', 'orientation', 'name')
    inlines = [SizerItemInline, LayoutItemInline]

class SizerItemAdmin(admin.ModelAdmin):
    list_display = ('sizer', 'item_type', 'item_id')
    list_filter = ('sizer',)


admin.site.register(FormLayout)
admin.site.register(Sizer, SizerAdmin)
admin.site.register(FormField, FormFieldAdmin)
admin.site.register(LayoutItem)
admin.site.register(SizerItem, SizerItemAdmin)



