import random

from django import forms
from django.db import models


def random_color():
    return "#%06x" % random.randint(0, 0xFFFFFF)


class ColorInput(forms.TextInput):
    input_type = "color"


class ColorField(models.CharField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 7)
        kwargs.setdefault("default", random_color)
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        kwargs["widget"] = ColorInput()
        return super().formfield(**kwargs)
