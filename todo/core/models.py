import datetime
import json
import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone


class Task(models.Model):
    STATUS_OPEN = 1
    STATUS_CLOSED = 2
    STATUS_CANCELED = 3

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    project = models.ForeignKey(
        "core.Project", on_delete=models.CASCADE, null=True, blank=True
    )

    status = models.IntegerField(
        default=STATUS_OPEN,
        choices=[
            (STATUS_OPEN, "Open"),
            (STATUS_CLOSED, "Closed"),
            (STATUS_CANCELED, "Canceled"),
        ],
    )
    priority = models.IntegerField(default=0)
    repeating = models.ForeignKey(
        "core.Repeating", null=True, blank=True, on_delete=models.CASCADE
    )
    external = models.ForeignKey(
        "core.URL", null=True, blank=True, on_delete=models.CASCADE
    )

    # For basic calendar date
    start = models.DateField(blank=True, null=True)
    due = models.DateField(blank=True, null=True)

    # For specific calendar times
    startAt = models.DateTimeField(blank=True, null=True)
    dueAt = models.DateTimeField(blank=True, null=True)

    createdAt = models.DateTimeField(blank=True, null=True)
    completedAt = models.DateTimeField(blank=True, null=True)

    def get_absolute_url(self):
        return reverse("task", kwargs={"pk": self.uuid})


class Project(models.Model):
    title = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public = models.BooleanField(default=False)
    createdOn = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return ":".join([self.title, self.owner.username])

    def get_absolute_url(self):
        return reverse("project", kwargs={"uuid": self.uuid})


class Search(models.Model):
    title = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    data = models.TextField()
    createdOn = models.DateTimeField(default=timezone.now)

    def get_absolute_url(self):
        return reverse("search", kwargs={"uuid": self.uuid})

    @property
    def task_set(self):
        query = json.loads(self.data)
        qs = Task.objects.filter(owner=self.owner)
        replace = {"<today>": datetime.date.today()}
        replace["<week>"] = replace["<today>"] + datetime.timedelta(days=7)

        def filter_dict(qs, query):
            print("filter_dict", query)

            for k, v in query.items():
                if v in replace:
                    query[k] = replace[v]

            return qs.filter(Q(**query))

        def filter_list(qs, query):
            print("filter_list", query)
            q_ = Q()
            for q in query:
                print("q", q)
                for k, v in q.items():
                    if v in replace:
                        q[k] = replace[v]
                q_ |= Q(**q)
            print(q_)
            return qs.filter(q_)

        if isinstance(query, list):
            return filter_list(qs, query)
        if isinstance(query, dict):
            return filter_dict(qs, query)


class Repeating(models.Model):
    data = models.TextField()


class Tag(models.Model):
    title = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public = models.BooleanField(default=False)
    task_set = models.ManyToManyField("core.Task")


class Context(models.Model):
    title = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    location = models.TextField()
    task_set = models.ManyToManyField("core.Task")


class Note(models.Model):
    task = models.ForeignKey("core.Task", on_delete=models.CASCADE)
    body = models.TextField()


class URL(models.Model):
    url = models.URLField()
