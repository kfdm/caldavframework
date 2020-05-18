from . import models

from django.contrib import admin


@admin.register(models.Calendar)
class CalendarAdmin(admin.ModelAdmin):
    list_display = ("name", "color", "owner")


@admin.register(models.Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("summary", "created", "status")
