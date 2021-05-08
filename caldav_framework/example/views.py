from . import models

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import CreateView, DetailView, TemplateView


class Home(TemplateView):
    template_name = "home.html"


class CalendarList(CreateView, LoginRequiredMixin):
    model = models.Calendar
    fields = ["name", "color"]

    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["calendar_list"] = self.get_queryset()
        return data


class CalendarDetail(DetailView, LoginRequiredMixin):
    model = models.Calendar

    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user)

    def post(self, request, **kwargs):
        if "summary" in request.POST:
            calendar = self.get_object()
            todo = models.Event.objects.create(
                calendar=calendar,
                summary=request.POST["summary"],
            )
            return redirect(todo)
        return self.get(request, **kwargs)


class TaskDetail(DetailView, LoginRequiredMixin):
    model = models.Event

    def get_queryset(self):
        return self.model.objects.filter(calendar__owner=self.request.user)
