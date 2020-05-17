from collections import defaultdict

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView, Response
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.shortcuts import redirect, render, reverse
from django.views.generic import RedirectView, TemplateView

from todo import caldav, models
from todo.caldav import ET


class WellKnownCaldav(APIView):
    http_method_names = ["get", "head", "options", "propfind"]
    permission_classes = [AllowAny]

    def get(self, request):
        return redirect("discovery")

    def propfind(self, request):
        return redirect("discovery")


# https://www.webdavsystem.com/server/creating_caldav_carddav/discovery/#nav_featuressupportdiscovery
class CaldavView(APIView):
    @property
    def propstat(self):
        if "{DAV:}prop" in self.request.data:
            return self.request.data["{DAV:}prop"].items()
        if "{DAV:}set" in self.request.data:
            return self.request.data["{DAV:}set"]["{DAV:}prop"].items()

    def options(self, request, *args, **kwargs):
        """Handle responding to requests for the OPTIONS HTTP verb."""
        response = HttpResponse()
        response["Allow"] = ", ".join(self._allowed_methods())
        response["Content-Length"] = "0"
        response["DAV"] = "1, 2, 3, calendar-access, addressbook, extended-mkcol"
        return response


class RootCollection(CaldavView):
    http_method_names = ["options", "propfind", "proppatch", "report", "mkcalendar"]
    # DELETE, GET, HEAD, MKCALENDAR, MKCOL, MOVE, OPTIONS, PROPFIND, PROPPATCH, PUT, REPORT

    def propfind(self, request, user):
        multi = caldav.MultistatusResponse()

        propstats = multi.propstat(request.path)
        collection = caldav.Collection(request.user)
        for prop, value in request.data.get("{DAV:}prop", {}).items():
            status, value = collection.propfind(request, prop, value)
            propstats[status].append(value)
        propstats.render(request)

        if request.headers["Depth"] == "1":
            for c in models.Calendar.objects.filter(owner=request.user):
                propstats = multi.propstat(
                    reverse("calendar", kwargs={"user": user, "calendar": c.id})
                )
                collection = caldav.Calendar(c)
                for prop, value in request.data.get("{DAV:}prop", {}).items():
                    status, value = collection.propfind(request, prop, value)
                    propstats[status].append(value)
                propstats.render(request)

        return multi

    def proppatch(self, request, user):
        propstats = caldav.Propstats()
        set_request = request.data.get("{DAV:}set", {})

        for prop, value in set_request.get("{DAV:}prop", {}).items():
            status, result = caldav.proppatch(request, prop, value, None)
            propstats[status].append(result)

        return propstats.render(request)

    def report(self, request, user):
        raise NotImplementedError()


class Calendar(CaldavView):
    http_method_names = ["options", "mkcalendar", "proppatch", "delete", "propfind"]

    def delete(self, request, user, calendar):
        calendar = get_object_or_404(models.Calendar, owner=request.user, id=calendar)
        calendar.delete()
        return HttpResponse(status=204)

    def propfind(self, request, user, calendar):
        calendar = get_object_or_404(models.Calendar, owner=request.user, id=calendar)
        collection = caldav.Calendar(calendar)

        multi = caldav.MultistatusResponse()
        propstats = multi.propstat(request.path)

        for prop, value in request.data.get("{DAV:}prop", {}).items():
            status, result = collection.propfind(request, prop, value)
            propstats[status].append(result)
        propstats.render(request)

        return multi

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

    def propfind(self, request):
        root = caldav.Collection(request.user)

        multi = caldav.MultistatusResponse()
        propstats = multi.propstat(request.path)

        for prop, value in request.data.get("{DAV:}prop", {}).items():
            status, result = root.propfind(request, prop, value)
            propstats[status].append(result)
        propstats.render(request)

        return multi
