from django.db.models.signals import pre_save
from django.utils.crypto import get_random_string


def set_etag(instance, **kwargs):
    instance.etag = get_random_string(
        length=instance._meta.get_field("etag").max_length
    )


pre_save.connect(set_etag, "caldav_framework.Event")
pre_save.connect(set_etag, "caldav_framework.Calendar")
