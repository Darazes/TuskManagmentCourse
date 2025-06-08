from django.contrib import admin

from web.models import *

admin.site.register(Board)
admin.site.register(List)
admin.site.register(Task)
admin.site.register(Status)