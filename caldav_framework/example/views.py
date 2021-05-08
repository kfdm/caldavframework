from . import mixins, models

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, DetailView, TemplateView, UpdateView, View


class Home(TemplateView):
    template_name = "home.html"


class CalendarList(LoginRequiredMixin, CreateView):
    model = models.Calendar
    template_name = "example/calendar_list.html"
    fields = ["name", "color", "public"]

    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["calendar_list"] = self.get_queryset()
        return data


class CalendarDetail(mixins.LoggedinOrPublic, DetailView):
    model = models.Calendar
    template_public = "example/calendar_public.html"


class CalendarUpdate(mixins.Owner, UpdateView):
    model = models.Calendar
    fields = ["name", "color", "public"]


class CalendarToggle(LoginRequiredMixin, View):
    def post(self, request, pk):
        calendar = get_object_or_404(models.Calendar, pk=pk, owner=self.request.user)
        calendar.public = not calendar.public
        calendar.save()
        if calendar.public:
            messages.success(request, "Made '" + calendar.name + "' public")
        else:
            messages.info(request, "Made '" + calendar.name + "' Private")
        return redirect("calendar-list")


class TaskCreate(mixins.CalendarPermissionRequired, CreateView):
    model = models.Event
    fields = ["summary"]

    def form_valid(self, form):
        form.instance.calendar_id = self.kwargs["calendar"]
        return super().form_valid(form)


class TaskDetail(mixins.CalendarOrPublicRequired, DetailView):
    model = models.Event
    template_public = "example/event_public.html"
