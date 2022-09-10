import uuid

import icalendar

from . import fields

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Calendar(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    color = fields.ColorField(max_length=9)
    order = models.IntegerField(default=0)
    etag = models.CharField(max_length=16)

    public = models.BooleanField(default=False)

    def to_ical(self):
        calendar = icalendar.Calendar()
        calendar["version"] = "2.0"
        calendar["PRODID"] = "todo-server"

        for e in self.event_set.all():
            event = icalendar.Event.from_ical(e.raw)
            calendar.add_component(event)
        return calendar.to_ical().decode("utf8")

    def get_absolute_url(self):
        return reverse("calendar-detail", args=(self.pk,))


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE)
    raw = models.TextField()
    etag = models.CharField(max_length=16)

    summary = models.CharField(max_length=128)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)
    status = models.CharField(
        max_length=128,
        blank=True,
        choices=[("NEEDS-ACTION", "NEEDS-ACTION"), ("COMPLETED", "COMPLETED")],
    )

    def to_ical(self):
        return icalendar.Todo.from_ical(self.raw).to_ical().decode("utf8")

    def get_absolute_url(self):
        return reverse("todo-detail", args=(self.calendar.pk, self.pk))
