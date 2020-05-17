from . import models

from django.contrib import admin


@admin.register(models.Calendar)
class CalendarAdmin(admin.ModelAdmin):
    pass
