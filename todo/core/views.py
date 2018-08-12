import datetime

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.base import RedirectView, TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from todo.core import models


class About(TemplateView):

    template_name = "about.html"


class RedirectSearch(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        search = get_object_or_404(
            models.Search, owner=self.request.user, title__iexact=args[0]
        )
        return search.get_absolute_url()


class RedirectProject(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self, *args, **kwargs):
        print(args, kwargs)
        inbox, _ = models.Search.objects.get_or_create(
            owner=self.request.user, title__iexact="Inbox"
        )
        return inbox.get_absolute_url()


class Project(LoginRequiredMixin, ListView):
    model = models.Task

    def get_queryset(self):
        self.today = datetime.date.today()
        return (
            models.Project.objects.get(
                owner=self.request.user, uuid=self.kwargs["uuid"]
            )
            .task_set.filter(
                status=self.request.GET.get("status", models.Task.STATUS_OPEN)
            )
            .order_by("due", "start")
            .prefetch_related("tag_set", "project", "external")
        )


class Search(LoginRequiredMixin, ListView):
    model = models.Task

    def get_queryset(self):
        self.today = datetime.date.today()
        return (
            models.Search.objects.get(owner=self.request.user, uuid=self.kwargs["uuid"])
            .task_set.filter(
                status=self.request.GET.get("status", models.Task.STATUS_OPEN)
            )
            .order_by("due", "start")
            .prefetch_related("tag_set", "project", "external")
        )


class Task(LoginRequiredMixin, DetailView):
    model = models.Task

    def post(self, request, pk):
        task = get_object_or_404(models.Task, pk=pk)
        print(self.request.POST)
        if "start" in self.request.POST:
            task.start = (
                self.request.POST["start"] if self.request.POST["start"] else None
            )
            task.save()
        if "due" in self.request.POST:
            task.due = self.request.POST["due"] if self.request.POST["due"] else None
            task.save()

        if "next" in request.POST:
            return redirect(request.POST["next"])
        return redirect("project", task.project.uuid)


class TaskAdd(LoginRequiredMixin, View):
    def post(self, request):
        inbox, _ = models.Project.objects.get_or_create(
            owner=request.user, title="Inbox"
        )
        task = models.Task.objects.create(
            owner=request.user, title=request.POST["search"], project=inbox
        )
        return redirect("project", task.project.uuid)
