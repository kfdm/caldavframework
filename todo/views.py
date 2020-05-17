from collections import defaultdict

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

        propstats = response.propstat(request.path)
        for prop, value in request.data.get("{DAV:}prop", {}).items():
            status, value = driver.propfind(request, prop, value)
            propstats[status].append(value)
        propstats.render(request)

        if request.headers["Depth"] == "1" and hasattr(self, "depth"):
            self.depth(request, response, **kwargs)

        return response


class RootCollection(CaldavView):
    http_method_names = ["options", "propfind", "proppatch", "report", "mkcalendar"]

    def get_driver(self, request, **kwargs):
        return caldav.Collection(request.user)

    def depth(self, request, response, **kwargs):
        for c in models.Calendar.objects.filter(owner=request.user):
            propstats = response.propstat(
                resolve_url("calendar", user=request.user.username, calendar=c.id)
            )
            collection = caldav.Calendar(c)
            for prop, value in request.data.get("{DAV:}prop", {}).items():
                status, value = collection.propfind(request, prop, value)
                propstats[status].append(value)
            propstats.render(request)

    def proppatch(self, request, user):
        response = caldav.MultistatusResponse()

        propstats = response.propstat(request.path)
        set_request = request.data.get("{DAV:}set", {})

        driver = self.get_driver(request)
        for prop, value in set_request.get("{DAV:}prop", {}).items():
            status, result = driver.proppatch(request, prop, value, None)
            propstats[status].append(result)
        propstats.render(request)

        return response


class Calendar(CaldavView):
    http_method_names = ["options", "mkcalendar", "proppatch", "delete", "propfind"]

    def get_driver(self, request, calendar, **kwargs):
        calendar = get_object_or_404(models.Calendar, owner=request.user, id=calendar)
        return caldav.Calendar(calendar)

    def delete(self, request, user, calendar):
        calendar = get_object_or_404(models.Calendar, owner=request.user, id=calendar)
        calendar.delete()
        return HttpResponse(status=204)

    def proppatch(self, request, user, calendar):
        multi = caldav.MultistatusResponse()
        calendar = get_object_or_404(models.Calendar, owner=request.user, id=calendar)
        collection = caldav.Calendar(calendar)

        propstats = multi.propstat(request.path)
        set_request = request.data.get("{DAV:}set", {})

        for prop, value in set_request.get("{DAV:}prop", {}).items():
            status, result = collection.proppatch(request, prop, value)
            propstats[status].append(result)
        propstats.render(request)

        if propstats[200]:
            calendar.save()

        return multi

    def mkcalendar(self, request, user, calendar):
        calendar = models.Calendar(owner=request.user, id=calendar)
        collection = caldav.Calendar(calendar)

        propstats = caldav.Propstats(None)
        set_request = request.data.get("{DAV:}set", {})

        for prop, value in set_request.get("{DAV:}prop", {}).items():
            status, result = collection.proppatch(request, prop, value)
            propstats[status].append(result)

        if propstats[200]:
            calendar.save()
            return HttpResponse(status=201)

        return HttpResponse(status=400)


# https://www.webdavsystem.com/server/creating_caldav_carddav/discovery/#nav_currentuserprincipaldiscovery
class UserPrincipalDiscovery(CaldavView):
    http_method_names = ["options", "propfind"]

    def get_driver(self, request, **kwargs):
        return caldav.Collection(request.user)


class Task(CaldavView):
    http_method_names = ["options", "put"]

    def put(self, request, user, calendar, task):
        data = request.body.decode("utf8")
        print(data)
        return HttpResponse(status=201)
