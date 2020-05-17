from django.db import models
from django.conf import settings


class Calendar(models.Model):
    id = models.CharField(max_length=128, primary_key=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=128)
    color = models.CharField(max_length=7)
