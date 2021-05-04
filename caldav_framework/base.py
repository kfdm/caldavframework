from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from . import parsers, response

from django.shortcuts import redirect
from django.utils.functional import cached_property


class WellKnownCaldav(APIView):
    http_method_names = ["get", "head", "options", "propfind"]
    permission_classes = [AllowAny]
    pattern_name = None

    def get(self, request, *args, **kwargs):
        return redirect(self.pattern_name)

    def propfind(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)


# https://www.webdavsystem.com/server/creating_caldav_carddav/discovery/#nav_featuressupportdiscovery
class CaldavView(APIView):
    parser_classes = [parsers.XMLParser]

    def get_object(self, request, **kwargs):
        raise NotImplementedError()

    def get_driver(self, request, **kwargs):
        raise NotImplementedError()

    @cached_property
    def object(self):
        return self.get_object(self.request, **self.kwargs)

    @cached_property
    def driver(self):
        return self.get_driver(self.request, **self.kwargs)

    def options(self, request, *args, **kwargs):
        """Handle responding to requests for the OPTIONS HTTP verb."""
        r = response.HttpResponse()
        r["Allow"] = ", ".join(self._allowed_methods())
        r["Content-Length"] = "0"
        r["DAV"] = "1, 3, access-control, calendar-access"
        return r

    def propfind(self, request, **kwargs):
        r = response.MultistatusResponse()
        self.driver.propfind(request, r, request.path)

        if request.headers["Depth"] == "1" and hasattr(self, "depth"):
            self.depth(request, r, **kwargs)

        return r

    def report(self, request, **kwargs):
        r = response.MultistatusResponse()
        self.driver.report(request, r)
        return r

    def proppatch(self, request, **kwargs):
        r = response.MultistatusResponse()
        self.driver.proppatch(request, r, request.path)
        return r
