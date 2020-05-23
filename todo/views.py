from collections import defaultdict

import icalendar
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView, Response

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render, resolve_url
from django.views.generic import RedirectView, TemplateView

from todo import caldav, models


class WellKnownCaldav(APIView):
    http_method_names = ["get", "head", "options", "propfind"]
    permission_classes = [AllowAny]

    def get(self, request):
        return redirect("discovery")

    def propfind(self, request):
        return redirect("discovery")


# https://www.webdavsystem.com/server/creating_caldav_carddav/discovery/#nav_featuressupportdiscovery
class CaldavView(APIView):
    def options(self, request, *args, **kwargs):
        """Handle responding to requests for the OPTIONS HTTP verb."""
        response = HttpResponse()
        response["Allow"] = ", ".join(self._allowed_methods())
        response["Content-Length"] = "0"
        response["DAV"] = "1, 2, 3, calendar-access, addressbook, extended-mkcol"
        return response

    def propfind(self, request, **kwargs):
        response = caldav.MultistatusResponse()
        driver = self.get_driver(request, **kwargs)
        driver.propfind(request, response, request.path)

        if request.headers["Depth"] == "1" and hasattr(self, "depth"):
            self.depth(request, response, **kwargs)

        return response

    def report(self, request, **kwargs):
        response = caldav.MultistatusResponse()
        driver = self.get_driver(request, **kwargs)
        driver.report(request, response, request.path)
        return response

    def proppatch(self, request, user):
        response = caldav.MultistatusResponse()
        driver = self.get_driver(request)
        propstats = driver.proppatch(request, response, request.path)
        return response


class RootCollection(CaldavView):
    http_method_names = ["options", "propfind", "proppatch", "report", "mkcalendar"]

    def get_driver(self, request, **kwargs):
        return caldav.RootCollection(request.user)

    def depth(self, request, response, **kwargs):
        for c in models.Calendar.objects.filter(owner=request.user):
            driver = caldav.Calendar(c)
            href = resolve_url("calendar", user=request.user.username, calendar=c.id)
            driver.propfind(request, response, href)


class Calendar(CaldavView):
    http_method_names = ["options", "mkcalendar", "proppatch", "delete", "propfind", "report"]

    def get_driver(self, request, calendar, **kwargs):
        self.calendar = get_object_or_404(
            models.Calendar, owner=request.user, id=calendar
        )
        return caldav.Calendar(self.calendar)

    def depth(self, request, response, **kwargs):
        for event in self.calendar.event_set.all():
            driver = caldav.Task(event)
            href = resolve_url(
                "task",
                user=request.user.username,
                calendar=event.calendar_id,
                task=event.id,
            )
            driver.propfind(request, response, href)

    def delete(self, request, user, calendar):
        calendar = get_object_or_404(models.Calendar, owner=request.user, id=calendar)
        calendar.delete()
        return HttpResponse(status=204)

    def proppatch(self, request, **kwargs):
        response = caldav.MultistatusResponse()
        driver = self.get_driver(request, **kwargs)
        propstats = driver.proppatch(request, response, request.path)
        if propstats[200]:
            self.calendar.save()
        return response

    def mkcalendar(self, request, user, calendar):
        calendar = models.Calendar(owner=request.user, id=calendar)
        driver = caldav.Calendar(calendar)

        response = caldav.MultistatusResponse()
        propstats = driver.proppatch(request, response, request.path)

        if propstats[200]:
            calendar.save()
            return HttpResponse(status=201)

        return HttpResponse(status=400)


# https://www.webdavsystem.com/server/creating_caldav_carddav/discovery/#nav_currentuserprincipaldiscovery
class UserPrincipalDiscovery(CaldavView):
    http_method_names = ["options", "propfind"]

    def get_driver(self, request, **kwargs):
        return caldav.RootCollection(request.user)


class Task(CaldavView):
    http_method_names = ["options", "put", "delete"]

    def put(self, request, calendar, task, **kwargs):
        calendar = get_object_or_404(models.Calendar, owner=request.user, id=calendar)
        data = request.body.decode("utf8")
        for event in icalendar.Calendar.from_ical(data).walk("vtodo"):
            todo = models.Event()
            todo.calendar = calendar
            todo.summary = event.decoded("summary").decode("utf8")
            todo.created = event.decoded("created")
            todo.status = event.decoded("status").decode("utf8")
            todo.save()
        return HttpResponse(status=201)

    def delete(self, request, task, **kwargs):
        return HttpResponse(status=405)
