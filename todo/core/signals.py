import datetime
import json

from django.contrib.auth.signals import user_logged_in
from django.dispatch.dispatcher import receiver

from todo.core import models


@receiver(user_logged_in)
def create_today(request, user, **kwargs):
    obj, created = models.Search.objects.get_or_create(
        owner=user,
        title="Today",
        defaults={
            "createdOn": user.date_joined,
            "data": json.dumps(
                [
                    {"start__lte": "<today>"},
                    {"start__lte": "<today>", "due__lte": "<today>"},
                    {"start": None, "due__lte": "<today>"},
                ]
            ),
        },
    )


@receiver(user_logged_in)
def create_upcoming(request, user, **kwargs):
    obj, created = models.Search.objects.get_or_create(
        owner=user,
        title="Upcoming",
        defaults={
            "createdOn": user.date_joined + datetime.timedelta(seconds=1),
            "data": json.dumps([{"due__gt": "<today>", "due__lte": "<week>"}]),
        },
    )


@receiver(user_logged_in)
def create_inbox(request, user, **kwargs):
    obj, created = models.Project.objects.get_or_create(
        owner=user, title="Inbox", defaults={"createdOn": user.date_joined}
    )
