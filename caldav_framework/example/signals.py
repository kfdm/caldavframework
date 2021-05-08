import icalendar

from django.db.models.signals import post_save, pre_save
from django.utils.crypto import get_random_string


def set_etag(instance, **kwargs):
    instance.etag = get_random_string(
        length=instance._meta.get_field("etag").max_length
    )


pre_save.connect(set_etag, "example.Event")
pre_save.connect(set_etag, "example.Calendar")


def populate(instance, created, **kwargs):
    if created and not instance.raw:
        calendar = icalendar.Calendar()
        calendar["version"] = "2.0"
        calendar["PRODID"] = "todo-server"
        event = icalendar.Todo()
        event.add("uid", instance.pk)
        event.add("summary", instance.summary)
        event.add("created", instance.created)
        calendar.add_component(event)
        instance.raw = calendar.to_ical().decode("utf-8")
        instance.save()


post_save.connect(populate, "example.Event")
