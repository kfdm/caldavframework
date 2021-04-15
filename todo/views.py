from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from django.shortcuts import get_object_or_404, redirect, resolve_url

from todo import base, caldav, models, parsers
from todo.response import HttpResponse, MultistatusResponse


class WellKnownCaldav(APIView):
    http_method_names = ["get", "head", "options", "propfind"]
    permission_classes = [AllowAny]

    def get(self, request):
        return redirect("discovery")

    def propfind(self, request):
        return redirect("discovery")


class RootCollection(base.CaldavView):
    http_method_names = ["options", "propfind", "proppatch", "report", "mkcalendar"]

    def get_driver(self, request, **kwargs):
        return caldav.RootCollection(request.user)

    def depth(self, request, response, **kwargs):
        for c in models.Calendar.objects.filter(owner=request.user):
            driver = caldav.Calendar(c)
            href = resolve_url("calendar", user=request.user.username, calendar=c.id)
            driver.propfind(request, response, href)


class Calendar(base.CaldavView):
    http_method_names = [
        "options",
        "mkcalendar",
        "proppatch",
        "delete",
        "propfind",
        "report",
    ]

    def get_driver(self, request, calendar, **kwargs):
        return caldav.Calendar(self.object)

    def get_object(self, request, calendar, **kwargs):
        return get_object_or_404(models.Calendar, owner=request.user, id=calendar)

    def depth(self, request, response, **kwargs):
        for event in self.object.event_set.all():
            driver = caldav.Task(event)
            href = resolve_url(
                "task",
                user=request.user.username,
                calendar=event.calendar_id,
                task=event.id,
            )
            driver.propfind(request, response, href)

    def delete(self, request, user, calendar):
        self.object.delete()
        return HttpResponse(status=204)

    def proppatch(self, request, **kwargs):
        response = MultistatusResponse()
        propstats = self.driver.proppatch(request, response, request.path)
        if propstats[200]:
            self.object.save()
        return response

    def mkcalendar(self, request, user, calendar):
        response = MultistatusResponse()
        self.object = models.Calendar(owner=request.user, id=calendar)
        propstats = self.driver.proppatch(request, response, request.path)

        if propstats[200]:
            self.object.save()
            return HttpResponse(status=201)

        return HttpResponse(status=400)


# https://www.webdavsystem.com/server/creating_caldav_carddav/discovery/#nav_currentuserprincipaldiscovery
class UserPrincipalDiscovery(base.CaldavView):
    http_method_names = ["options", "propfind"]

    def get_driver(self, request, **kwargs):
        return caldav.RootCollection(request.user)


class Task(base.CaldavView):
    http_method_names = ["options", "put", "delete"]
    parser_classes = [parsers.Caldav]

    def get_object(self, request, calendar, **kwargs):
        return get_object_or_404(models.Calendar, owner=request.user, id=calendar)

    def put(self, request, calendar, task, **kwargs):
        for event in request.data.walk("vtodo"):
            todo, created = models.Event.objects.update_or_create(
                id=task,
                calendar=self.object,
                defaults={
                    "raw": event.to_ical().decode("utf8"),
                    "summary": event.decoded("summary").decode("utf8"),
                    "created": event.decoded("created"),
                    "status": event.decoded("status").decode("utf8"),
                    "updated": event.decoded("LAST-MODIFIED"),
                },
            )

            response = HttpResponse(status=201)
            response["Etag"] = '"' + todo.etag + '"'
            return response
        return HttpResponse(status=500)

    def delete(self, request, task, **kwargs):
        models.Event.objects.get(pk=task).delete()
        return HttpResponse(status=204)
