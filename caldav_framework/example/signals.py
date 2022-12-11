import logging

from . import convert

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.crypto import get_random_string

logger = logging.getLogger(__name__)


def set_etag(instance, **kwargs):
    instance.etag = get_random_string(
        length=instance._meta.get_field("etag").max_length
    )


pre_save.connect(set_etag, "example.Event")
pre_save.connect(set_etag, "example.APIEvent")
pre_save.connect(set_etag, "example.Calendar")


@receiver(pre_save, sender="example.Event")
def update_calendar_data(instance, raw, **kwargs):
    if raw:
        return
    # When an Event object is updated, we want to ensure
    # that our 'updated' field is updated, along with ensuring
    # our calendar raw data is also updated
    logger.debug("Updating raw calendar data for %s", instance)
    instance.updated = timezone.now()
    instance.raw = convert.to_ical(instance)


# Not currently in use but showing in the comments for future use
# @receiver(pre_save, sender="example.APIEvent")
# def pre_save_api(**kwargs):
#     print("pre_save_api", kwargs)
