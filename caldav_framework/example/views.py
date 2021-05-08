from . import models

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView


class Home(TemplateView):
    template_name = "home.html"


class CalendarList(ListView, LoginRequiredMixin):
    model = models.Calendar

    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user)
