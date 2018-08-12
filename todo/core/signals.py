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
            "data": json.dumps(
                [
                    {"start__lte": "<today>"},
                    {"start__lte": "<today>", "due__lte": "<today>"},
                    {"start": None, "due__lte": "<today>"},
                ]
            )
        },
    )


@receiver(user_logged_in)
def create_upcoming(request, user, **kwargs):
    obj, created = models.Search.objects.get_or_create(
        owner=user,
        title="Upcoming",
        defaults={"data": json.dumps([{"due__gt": "<today>", "due__lte": "<week>"}])},
    )
