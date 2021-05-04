import logging
import xml.etree.ElementTree as ET
from collections import defaultdict

from .response import MultistatusResponse

from django.http.request import HttpRequest
from django.shortcuts import resolve_url
from django.urls import resolve

ET.register_namespace("DAV:", "")


logger = logging.getLogger(__name__)


def dispatch(method, prop):
    def inner(func):
        setattr(func, "method", method)
        setattr(func, "prop", prop)
        return func

    return inner


class BaseCollection:
    def __init__(self, obj):
        self.obj = obj

        self.handlers = defaultdict(dict)
        for obj in dir(self):
            try:
                func = getattr(self, obj)
                method = getattr(func, "method")
                prop = getattr(func, "prop")
                self.handlers[method][prop] = func
            except AttributeError:
                pass

    def dispatch(self, method, prop, **kwargs):
        ele = ET.Element(prop.tag)
        try:
            func = self.handlers[method][prop.tag]
        except KeyError:
            return 404, ele
        else:
            return func(ele=ele, prop=prop, **kwargs)

    def report(self, request: HttpRequest, response: MultistatusResponse):
        query = request.data.find("{DAV:}prop")
        for href in request.data.findall("{DAV:}href"):
            propstats = response.propstat(href.text)
            parts = resolve(href.text).kwargs

            for prop in query.getchildren():
                propstats << self.dispatch(
                    "report", request=request, prop=prop, parts=parts
                )
            propstats.render(request)

    def propfind(self, request: HttpRequest, response: MultistatusResponse, href: str):
        propstats = response.propstat(href)
        for prop in request.data.find("{DAV:}prop").getchildren():
            propstats << self.dispatch("propfind", request=request, prop=prop)
        propstats.render(request)
        return propstats

    def proppatch(self, request: HttpRequest, response: MultistatusResponse, href: str):
        propstats = response.propstat(href)
        for prop in request.data.find("{DAV:}set").find("{DAV:}prop").getchildren():
            propstats << self.dispatch("proppatch", request=request, prop=prop)
        propstats.render(request)
        return propstats


class RootCollection(BaseCollection):
    @dispatch("propfind", "{DAV:}current-user-principal")
    def current_user_principal(self, ele, request, **kwargs):
        ET.SubElement(ele, "{DAV:}href").text = resolve_url(
            "principal", user=request.user.username
        )
        return 200, ele

    @dispatch("propfind", "{DAV:}current-user-privilege-set")
    def current_user_privilege_set(self, ele, **kwargs):
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}read")
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}all")
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}write")
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}write-properties")
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}write-content")
        return 200, ele

    @dispatch("propfind", "{DAV:}owner")
    def owner(self, ele, request, **kwargs):
        ET.SubElement(ele, "{DAV:}href").text = resolve_url(
            "principal", user=request.user.username
        )
        return 200, ele

    @dispatch("propfind", "{DAV:}supported-report-set")
    def supported_report_set(self, ele, **kwargs):
        return 200, ele

    @dispatch("propfind", "{urn:ietf:params:xml:ns:caldav}calendar-user-address-set")
    def calendar_user_address_set(self, ele, request, **kwargs):
        ET.SubElement(ele, "{DAV:}href").text = resolve_url(
            "principal",
            user=request.user.username,
        )
        return 200, ele

    @dispatch("propfind", "{urn:ietf:params:xml:ns:caldav}calendar-home-set")
    def calendar_home_set(self, ele, request, **kwargs):
        ET.SubElement(ele, "{DAV:}href").text = resolve_url(
            "principal", user=request.user.username
        )
        return 200, ele

    @dispatch("propfind", "{DAV:}resourcetype")
    def resource_type(self, ele, **kwargs):
        ET.SubElement(ele, "{DAV:}principal")
        ET.SubElement(ele, "{DAV:}collection")
        return 200, ele


class Calendar(BaseCollection):
    @dispatch("report", "{DAV:}getetag")
    def report_getetag(self, ele, **kwargs):
        todo = self.obj.event_set.get(id=kwargs["task"])
        ele.text = '"' + todo.etag + '"'
        return 200, ele

    @dispatch("report", "{urn:ietf:params:xml:ns:caldav}calendar-data")
    def report_calendar_data(self, ele, **kwargs):
        todo = self.obj.event_set.get(id=kwargs["task"])
        ele.text = todo.to_ical()
        return 200, ele

    @dispatch("propfind", "{DAV:}getetag")
    def getetag(self, ele, **kwargs):
        ele.text = '"' + self.obj.etag + '"'
        return 200, ele

    @dispatch("propfind", "{DAV:}displayname")
    def displayname(self, ele, **kwargs):
        ele.text = self.obj.name
        return 200, ele

    @dispatch("propfind", "{DAV:}current-user-privilege-set")
    def current_user_privilege_set(self, ele, **kwargs):
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}read")
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}all")
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}write")
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}write-properties")
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}write-content")
        return 200, ele

    @dispatch("propfind", "{DAV:}owner")
    def owner(self, ele, **kwargs):
        ET.SubElement(ele, "{DAV:}href").text = resolve_url(
            "principal", user=self.obj.owner.username
        )
        return 200, ele

    @dispatch("propfind", "{DAV:}resourcetype")
    def resourcetype(self, ele, **kwargs):
        ET.SubElement(ele, "{urn:ietf:params:xml:ns:caldav}calendar")
        ET.SubElement(ele, "collection")
        return 200, ele

    @dispatch(
        "propfind", "{urn:ietf:params:xml:ns:caldav}supported-calendar-component-set"
    )
    def supported_calendar_compontnet_set(self, ele, **kwargs):
        ET.SubElement(ele, "{urn:ietf:params:xml:ns:caldav}comp", {"name": "VTODO"})
        return 200, ele

    @dispatch("propfind", "{urn:ietf:params:xml:ns:caldav}calendar-data")
    def calendar_data(self, ele, **kwargs):
        ele.text = self.obj.to_ical()
        return 200, ele

    @dispatch("propfind", "{DAV:}getcontenttype")
    def getcontenttype(self, ele, **kwargs):
        ele.text = "text/calendar"
        return 200, ele

    @dispatch("propfind", "{DAV:}supported-report-set")
    def supported_report_set(self, ele, **kwargs):
        return 200, ele

    @dispatch("propfind", "{http://apple.com/ns/ical/}calendar-color")
    def calendar_color(self, ele, **kwargs):
        ele.text = self.obj.color
        return 200, ele

    @dispatch("propfind", "{http://apple.com/ns/ical/}calendar-order")
    def calendar_order(self, ele, **kwargs):
        ele.text = str(self.obj.order)
        return 200, ele

    @dispatch("proppatch", "{DAV:}displayname")
    def patch_displayname(self, ele, prop, **kwargs):
        self.obj.name = prop.value
        return 200, ele

    @dispatch("proppatch", "{http://apple.com/ns/ical/}calendar-color")
    def patch_calendar_color(self, ele, prop, **kwargs):
        self.obj.color = prop.text
        return 200, ele

    @dispatch("proppatch", "{http://apple.com/ns/ical/}calendar-order")
    def patch_calendar_order(self, ele, prop, **kwargs):
        self.obj.order = prop.text
        return 200, ele


class Task(BaseCollection):
    @dispatch("propfind", "{DAV:}getetag")
    def getetag(self, ele, **kwargs):
        ele.text = '"' + self.obj.etag + '"'
        return 200, ele

    @dispatch("propfind", "{DAV:}getcontenttype")
    def getcontenttype(self, ele, **kwargs):
        ele.text = "text/calendar;charset=utf-8;component=VTODO"
        return 200, ele
