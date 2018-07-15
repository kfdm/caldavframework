from django import template
from django.utils.safestring import mark_safe

from todo.core import models

register = template.Library()


@register.filter
def icon(task):
    if task.repeating:
        return "R"
    if task.status == models.Task.STATUS_OPEN:
        return "[ ]"
    if task.status == models.Task.STATUS_CANCELED:
        return "[X]"
    if task.status == models.Task.STATUS_CLOSED:
        return "[/]"


@register.filter(needs_autoescape=False, is_safe=True)
def priority(task):
    if task.priority < 1:
        return mark_safe(
            '<span class="badge badge-pill badge-secondary">{}</span>'.format(
                task.priority
            )
        )
    if task.priority < 5:
        return mark_safe(
            '<span class="badge badge-pill badge-succes">{}</span>'.format(
                task.priority
            )
        )
    if task.priority < 7:
        return mark_safe(
            '<span class="badge badge-pill badge-warning">{}</span>'.format(
                task.priority
            )
        )
    return mark_safe(
        '<span class="badge badge-pill badge-danger">{}</span>'.format(task.priority)
    )
