from .response import MultistatusResponse

from django.http.request import HttpRequest
from django.urls import resolve


class ReportMixin:
    def report(self, request: HttpRequest, response: MultistatusResponse):
        query = request.data.find("{DAV:}prop")
        for href in request.data.findall("{DAV:}href"):
            propstats = response.propstat(href.text)
            parts = resolve(href.text).kwargs

            for prop in query.getchildren():
                propstats << self.dispatch(
                    "report", request=request, prop=prop, **parts
                )
            propstats.render(request)


class PropfindMixin:
    def propfind(self, request: HttpRequest, response: MultistatusResponse, href: str):
        propstats = response.propstat(href)
        for prop in request.data.find("{DAV:}prop").getchildren():
            propstats << self.dispatch("propfind", request=request, prop=prop)
        propstats.render(request)
        return propstats


class ProppatchMixin:
    def proppatch(self, request: HttpRequest, response: MultistatusResponse, href: str):
        propstats = response.propstat(href)
        for prop in request.data.find("{DAV:}set").find("{DAV:}prop").getchildren():
            propstats << self.dispatch("propstat", request=request, prop=prop)
        propstats.render(request)
        return propstats
