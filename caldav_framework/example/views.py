from . import models
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.views.generic import CreateView, DetailView, TemplateView, View
from django.contrib import messages


class Home(TemplateView):
    template_name = "home.html"


class CalendarList(LoginRequiredMixin, CreateView):
    model = models.Calendar
    fields = ["name", "color", "public"]

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


class CalendarDetail(UserPassesTestMixin, DetailView):
    model = models.Calendar

    def test_func(self):
        obj = self.get_object()
        return any(
            [
                obj.owner == self.request.user,
                obj.public,
            ]
        )

    def post(self, request, **kwargs):
        if "summary" in request.POST:
            calendar = self.get_object()
            todo = models.Event.objects.create(
                calendar=calendar,
                summary=request.POST["summary"],
            )
            return redirect(todo)
        return self.get(request, **kwargs)


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


class TaskDetail(LoginRequiredMixin, DetailView):
    model = models.Event

    def get_queryset(self):
        return self.model.objects.filter(calendar__owner=self.request.user)
