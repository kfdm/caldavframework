from django.contrib import admin
from . import models

@admin.register(models.Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'owner', 'createdAt', 'completedAt')
    list_filter = ('owner', 'status',)

@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    pass