from django import template
from django.template.defaultfilters import stringfilter
from todo.core import models
register = template.Library()

@register.filter
def icon(task):
    if task.repeating:
        return 'R'
    if task.status == models.Task.STATUS_OPEN:
        return '[ ]'
    if task.status == models.Task.STATUS_CANCELED:
        return '[X]'
    if task.status == models.Task.STATUS_CLOSED:
        return '[/]'
