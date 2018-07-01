import uuid

from django.conf import settings
from django.db import models


class Task(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    project = models.ForeignKey("core.Project", on_delete=models.CASCADE, null=True, blank=True)

    priority = models.IntegerField(max_value=9, min_value=0, default=0)
 
    start = models.DateField(blank=True)
    end = models.DateField(blank=True)


class Project(models.Model):
    title = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)


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
