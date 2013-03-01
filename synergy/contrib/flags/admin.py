# -*- coding: utf-8 -*-
from models import *
from django.contrib import admin


admin.site.register(Flag)
admin.site.register(Group)
admin.site.register(ContentFlag)
admin.site.register(GroupContentFlag)
admin.site.register(UserContentFlag)
admin.site.register(UserContextContentFlag)
admin.site.register(UserContextQuery)
admin.site.register(AuthContentFlag)
admin.site.register(CustomContentFlag)



