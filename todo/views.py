from collections import defaultdict

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView, Response

from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.views.generic import RedirectView, TemplateView

from todo import caldav
from todo.caldav import ET


class WellKnownCaldav(APIView):
    http_method_names = ["get", "head", "options", "propfind"]
    permission_classes = [AllowAny]

    def get(self, request):
        return redirect("discovery")

    def propfind(self, request):
        return redirect("discovery")


class CaldavView(APIView):
    def options(self, request, *args, **kwargs):
        """Handle responding to requests for the OPTIONS HTTP verb."""
        response = HttpResponse()
        response["Allow"] = ", ".join(self._allowed_methods())
        response["Content-Length"] = "0"
        response["DAV"] = "1, 2, 3, calendar-access, addressbook, extended-mkcol"
        return response


class Principal(CaldavView):
    http_method_names = ["options", "propfind"]

    def propfind(self, request):
        pass


class Discovery(CaldavView):
    http_method_names = ["options", "propfind"]

    def propfind(self, request):
        propstats = defaultdict(list)
        for prop in request.data["{DAV:}prop"]:
            status, value = caldav.propfind(prop, request)
            propstats[status].append(value)

        multistatus = ET.Element("{DAV:}multistatus")
        response = ET.SubElement(multistatus, "{DAV:}response")
        ET.SubElement(response, "{DAV:}href").text = request.path

        for status in propstats:
            propstat = ET.SubElement(response, "{DAV:}propstat")
            prop = ET.SubElement(propstat, "{DAV:}prop")
            for element in propstats[status]:
                prop.append(element)
            ET.SubElement(propstat, "{DAV:}status").text = caldav.status(status)

        return caldav.CaldavResponse(multistatus, status=207)
