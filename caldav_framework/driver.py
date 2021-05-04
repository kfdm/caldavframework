import logging
import xml.etree.ElementTree as ET

from . import mixins
from .dispatcher import Dispatcher, propfind, proppatch, report

from django.shortcuts import resolve_url

ET.register_namespace("DAV:", "")


logger = logging.getLogger(__name__)


class BaseCollection(
    Dispatcher,
    mixins.ReportMixin,
    mixins.PropfindMixin,
    mixins.ProppatchMixin,
):
    pass


class RootCollection(BaseCollection):
    @propfind("{DAV:}current-user-principal")
    def current_user_principal(self, ele, request, **kwargs):
        ET.SubElement(ele, "{DAV:}href").text = resolve_url(
            "principal", user=request.user.username
        )
        return 200, ele

    @propfind("{DAV:}resourcetype")
    def resource_type(self, ele, **kwargs):
        ET.SubElement(ele, "{DAV:}collection")
        return 200, ele

    @propfind("{DAV:}current-user-privilege-set")
    def current_user_privilege_set(self, ele, **kwargs):
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}read")
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}all")
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}write")
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}write-properties")
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}write-content")
        return 200, ele

    @propfind("{DAV:}owner")
    def owner(self, ele, request, **kwargs):
        ET.SubElement(ele, "{DAV:}href").text = resolve_url(
            "principal", user=request.user.username
        )
        return 200, ele

    @propfind("{DAV:}supported-report-set")
    def supported_report_set(self, ele, **kwargs):
        return 200, ele

    @propfind("{urn:ietf:params:xml:ns:caldav}calendar-user-address-set")
    def calendar_user_address_set(self, ele, request, **kwargs):
        ET.SubElement(ele, "{DAV:}href").text = resolve_url(
            "principal",
            user=request.user.username,
        )
        return 200, ele

    @propfind("{urn:ietf:params:xml:ns:caldav}calendar-home-set")
    def calendar_home_set(self, ele, request, **kwargs):
        ET.SubElement(ele, "{DAV:}href").text = resolve_url(
            "principal", user=request.user.username
        )
        return 200, ele


class Calendar(BaseCollection):
    @report("{DAV:}getetag")
    def report_getetag(self, ele, **kwargs):
        todo = self.obj.event_set.get(id=kwargs["task"])
        ele.text = '"' + todo.etag + '"'
        return 200, ele

    @report("{urn:ietf:params:xml:ns:caldav}calendar-data")
    def report_calendar_data(self, ele, **kwargs):
        todo = self.obj.event_set.get(id=kwargs["task"])
        ele.text = todo.to_ical()
        return 200, ele

    @propfind("{DAV:}getetag")
    def getetag(self, ele, **kwargs):
        ele.text = '"' + self.obj.etag + '"'
        return 200, ele

    @propfind("{DAV:}displayname")
    def displayname(self, ele, **kwargs):
        ele.text = self.obj.name
        return 200, ele

    @propfind("{DAV:}current-user-privilege-set")
    def current_user_privilege_set(self, ele, **kwargs):
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}read")
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}all")
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}write")
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}write-properties")
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}write-content")
        return 200, ele

    @propfind("{DAV:}owner")
    def owner(self, ele, **kwargs):
        ET.SubElement(ele, "{DAV:}href").text = resolve_url(
            "principal", user=self.obj.owner.username
        )
        return 200, ele

    @propfind("{DAV:}resourcetype")
    def resourcetype(self, ele, **kwargs):
        ET.SubElement(ele, "{urn:ietf:params:xml:ns:caldav}calendar")
        ET.SubElement(ele, "collection")
        return 200, ele

    @propfind("{urn:ietf:params:xml:ns:caldav}supported-calendar-component-set")
    def supported_calendar_compontnet_set(self, ele, **kwargs):
        ET.SubElement(ele, "{urn:ietf:params:xml:ns:caldav}comp", {"name": "VTODO"})
        return 200, ele

    @propfind("{urn:ietf:params:xml:ns:caldav}calendar-data")
    def calendar_data(self, ele, **kwargs):
        ele.text = self.obj.to_ical()
        return 200, ele

    @propfind("{DAV:}getcontenttype")
    def getcontenttype(self, ele, **kwargs):
        ele.text = "text/calendar"
        return 200, ele

    @propfind("{DAV:}supported-report-set")
    def supported_report_set(self, ele, **kwargs):
        return 200, ele

    @propfind("{http://apple.com/ns/ical/}calendar-color")
    def calendar_color(self, ele, **kwargs):
        ele.text = self.obj.color
        return 200, ele

    @propfind("{http://apple.com/ns/ical/}calendar-order")
    def calendar_order(self, ele, **kwargs):
        ele.text = str(self.obj.order)
        return 200, ele

    @proppatch("{DAV:}displayname")
    def patch_displayname(self, ele, prop, **kwargs):
        self.obj.name = prop.value
        return 200, ele

    @proppatch("{http://apple.com/ns/ical/}calendar-color")
    def patch_calendar_color(self, ele, prop, **kwargs):
        self.obj.color = prop.text
        return 200, ele

    @proppatch("{http://apple.com/ns/ical/}calendar-order")
    def patch_calendar_order(self, ele, prop, **kwargs):
        self.obj.order = prop.text
        return 200, ele


class Task(BaseCollection):
    @propfind("{DAV:}getetag")
    def getetag(self, ele, **kwargs):
        ele.text = '"' + self.obj.etag + '"'
        return 200, ele

    @propfind("{DAV:}getcontenttype")
    def getcontenttype(self, ele, **kwargs):
        ele.text = "text/calendar;charset=utf-8;component=VTODO"
        return 200, ele
