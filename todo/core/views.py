import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.base import TemplateView, View
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
        ).order_by('due')


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
            status=self.request.GET.get('status', models.Task.STATUS_OPEN),
        ).order_by('due')


class Task(LoginRequiredMixin, View):
    def ts(self, value):
        if value == 'today':
            return datetime.date.today()
        if value == 'yesterday':
            return datetime.date.today() - datetime.timedelta(days=1)
        if value == 'tomorrow':
            return datetime.date.today() + datetime.timedelta(days=1)
        return None

    def post(self, request, uuid):
        task = get_object_or_404(models.Task, uuid=uuid)
        if 'start' in self.request.POST:
            task.start = self.ts(self.request.POST['start'])
            task.save()
        if 'due' in self.request.POST:
            task.due = self.ts(self.request.POST['due'])
            task.save()

        print(self.request.POST)
        return redirect('project', task.project.uuid)
