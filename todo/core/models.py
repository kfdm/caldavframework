import uuid

from django.conf import settings
from django.db import models


class Task(models.Model):
    STATUS_OPEN = 1
    STATUS_CLOSED = 2
    STATUS_CANCELED = 3

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    project = models.ForeignKey("core.Project", on_delete=models.CASCADE, null=True, blank=True)

    status = models.IntegerField(default=STATUS_OPEN, choices=[
        (STATUS_OPEN, 'Open'),
        (STATUS_CLOSED, 'Closed'),
        (STATUS_CANCELED, 'Canceled'),
    ])
    priority = models.IntegerField(default=0)
 
    # For basic calendar date
    start = models.DateField(blank=True, null=True)
    end = models.DateField(blank=True, null=True)

    # For specific calendar times
    startAt = models.DateTimeField(blank=True, null=True)
    endAt = models.DateTimeField(blank=True, null=True)


class Project(models.Model):
    title = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def __str__(self):
        return ':'.join([self.title, self.owner.username])


class Repeating(models.Model):
    data = models.TextField()


class Tag(models.Model):
    title = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


class Context(models.Model):
    title = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    location = models.TextField()


class Note(models.Model):
    task = models.ForeignKey("core.Task", on_delete=models.CASCADE)
    body = models.TextField()


class URL(models.Model):
    task = models.ForeignKey("core.Task", on_delete=models.CASCADE)
    url = models.URLField()
