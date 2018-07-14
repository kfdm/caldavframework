from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView

from todo.core import models


class About(TemplateView):

    template_name = "about.html"


class Inbox(LoginRequiredMixin, ListView):

    model = models.Task

    def get_context_data(self, **kwargs):
        context = super(Inbox, self).get_context_data(**kwargs)
        context["project_list"] = models.Project.objects.filter(owner=self.request.user)
        return context

    def get_queryset(self):
        return self.model.objects.filter(
            owner=self.request.user, project=None, status=models.Task.STATUS_OPEN
        )


class Project(LoginRequiredMixin, ListView):

    model = models.Task

    def get_context_data(self, **kwargs):
        context = super(Project, self).get_context_data(**kwargs)
        context["project_list"] = models.Project.objects.filter(owner=self.request.user)
        return context

    def get_queryset(self):
        return self.model.objects.filter(
            owner=self.request.user,
            project=self.kwargs["uuid"],
            status=models.Task.STATUS_OPEN,
        )
