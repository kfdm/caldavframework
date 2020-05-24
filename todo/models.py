import uuid

import icalendar

from . import signals

from django.conf import settings
from django.db import models
from django.utils import timezone


class Calendar(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    color = models.CharField(max_length=7)
    order = models.IntegerField(default=0)
    etag = models.CharField(max_length=16)

    def to_ical(self):
        cal = icalendar.Calendar()

        for e in self.event_set.all():
            event = icalendar.Event.from_ical(e.raw)
            cal.add_component(event)
        return cal.to_ical().decode("utf8")


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
        cal = icalendar.Calendar()
        event = icalendar.Todo.from_ical(self.raw)
        cal.add_component(event)
        return cal.to_ical().decode("utf8")
