import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
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
        context["today"] = self.today
        return context

    def get_queryset(self):
        self.today = datetime.date.today()
        return self.model.objects.filter(
            owner=self.request.user, project=None, status=models.Task.STATUS_OPEN
        ).order_by("due")


class Today(Inbox):
    def get_queryset(self):
        self.today = datetime.date.today()
        return (
            self.model.objects.filter(
                owner=self.request.user, status=models.Task.STATUS_OPEN
            )
            .filter(
                Q(start__lte=self.today)
                | Q(start__lte=self.today) & Q(due__lte=self.today)
                | Q(start=None) & Q(due__lte=self.today)
            )
            .order_by("due", "start")
        )


class Upcoming(Inbox):
    def get_queryset(self):
        self.today = datetime.date.today()
        end = self.today + datetime.timedelta(days=7)
        return self.model.objects.filter(
            owner=self.request.user, due__gt=self.today, due__lte=end
        ).order_by("due", "start")


class Project(Inbox):
    def get_queryset(self):
        self.today = datetime.date.today()
        return self.model.objects.filter(
            owner=self.request.user,
            project=self.kwargs["uuid"],
            status=self.request.GET.get("status", models.Task.STATUS_OPEN),
        ).order_by("due", "start")


class Task(LoginRequiredMixin, View):
    def ts(self, value):
        if value == "today":
            return datetime.date.today()
        if value == "yesterday":
            return datetime.date.today() - datetime.timedelta(days=1)
        if value == "tomorrow":
            return datetime.date.today() + datetime.timedelta(days=1)
        return None

    def get(self, request, uuid):
        task = get_object_or_404(models.Task, uuid=uuid)
        return render(request, "core/task_detail.html", {"task": task})

    def post(self, request, uuid):
        task = get_object_or_404(models.Task, uuid=uuid)
        if "start" in self.request.POST:
            task.start = self.ts(self.request.POST["start"])
            task.save()
        if "due" in self.request.POST:
            task.due = self.ts(self.request.POST["due"])
            task.save()

        print(self.request.POST)
        return redirect("project", task.project.uuid)
