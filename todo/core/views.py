import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic.base import RedirectView, TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from todo.core import models


class About(TemplateView):

    template_name = "about.html"


class Inbox(RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        inbox, _ = models.Project.objects.get_or_create(
            owner=self.request.user,
            title='Inbox',
        )
        return inbox.get_absolute_url()


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


class ListBase(LoginRequiredMixin, ListView):

    model = models.Task

    def get_context_data(self, **kwargs):
        context = super(ListBase, self).get_context_data(**kwargs)
        context["project_list"] = models.Project.objects.filter(owner=self.request.user)
        context["today"] = self.today
        return context


class Upcoming(ListBase):
    def get_queryset(self):
        self.today = datetime.date.today()
        end = self.today + datetime.timedelta(days=7)
        return self.model.objects.filter(
            owner=self.request.user, due__gt=self.today, due__lte=end
        ).order_by("due", "start")


class Project(ListBase):
    def get_queryset(self):
        self.today = datetime.date.today()
        return self.model.objects.filter(
            owner=self.request.user,
            project=self.kwargs["uuid"],
            status=self.request.GET.get("status", models.Task.STATUS_OPEN),
        ).order_by("due", "start")


class Task(LoginRequiredMixin, DetailView):
    model = models.Task

    def ts(self, value):
        if value == "today":
            return datetime.date.today()
        if value == "yesterday":
            return datetime.date.today() - datetime.timedelta(days=1)
        if value == "tomorrow":
            return datetime.date.today() + datetime.timedelta(days=1)
        return None

    def post(self, request, pk):
        task = get_object_or_404(models.Task, uuid=uuid)
        if "start" in self.request.POST:
            task.start = self.ts(self.request.POST["start"])
            task.save()
        if "due" in self.request.POST:
            task.due = self.ts(self.request.POST["due"])
            task.save()

        print(self.request.POST)
        return redirect("project", task.project.uuid)


class TaskAdd(LoginRequiredMixin, View):
    def post(self, request):
        inbox, _ = models.Project.objects.get_or_create(
            owner=request.user,
            title='Inbox',
        )
        task = models.Task.objects.create(
            owner=request.user,
            title=request.POST['search'],
            project=inbox,
        )
        return redirect("project", task.project.uuid)
