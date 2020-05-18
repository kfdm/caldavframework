import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Calendar(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    color = models.CharField(max_length=7)


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    calendar = models.ForeignKey(Calendar, on_delete=models.CASCADE)
    summary = models.CharField(max_length=128)
    created = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=128, blank=True)
