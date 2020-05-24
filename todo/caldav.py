
import logging
import xml.etree.ElementTree as ET

from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import resolve_url
from django.urls import resolve
from django.utils.crypto import get_random_string

ET.register_namespace("DAV:", "")


logger = logging.getLogger(__name__)


class BaseCollection:
    def __init__(self, obj):
        self.obj = obj

    def report(self, request: HttpRequest, response: HttpResponse, href: str):
        query = request.data.find("{DAV:}prop")
        for href in request.data.findall("{DAV:}href"):
            propstats = response.propstat(href.text)
            parts = resolve(href.text).kwargs

            for prop in query.getchildren():
                status, value = self._report(request, prop.tag, prop.text, parts)
                propstats[status].append(value)
            propstats.render(request)

    def propfind(self, request: HttpRequest, response: HttpResponse, href: str):
        propstats = response.propstat(href)
        for prop in request.data.find("{DAV:}prop").getchildren():
            status, value = self._propfind(request, prop.tag, prop.text)
            propstats[status].append(value)
        propstats.render(request)
        return propstats

    def proppatch(self, request: HttpRequest, response: HttpResponse, href: str):
        propstats = response.propstat(href)
        for prop in request.data.find("{DAV:}set").find("{DAV:}prop").getchildren():
            status, result = self._proppatch(request, prop.tag, prop.text)
            propstats[status].append(result)
        propstats.render(request)
        return propstats

    def _proppatch(self, request, prop, value):
        ele = ET.Element(prop)
        logger.warning("Not implemented %s for %s", prop, self.obj)
        return 404, ele

    def _propfind(self, request, prop, value):
        ele = ET.Element(prop)
        logger.warning("Not implemented %s for %s", prop, self.obj)
        return 404, ele

    def _report(self, request, prop, value, extras):
        ele = ET.Element(prop)
        logger.warning("Not implemented %s for %s", prop, self.obj)
        return 404, ele


class RootCollection(BaseCollection):
    def _propfind(self, request, prop, value):
        ele = ET.Element(prop)

        if prop == "{DAV:}current-user-principal":
            ET.SubElement(ele, "{DAV:}href").text = resolve_url(
                "principal", user=request.user.username
            )
            return 200, ele

        if prop == "{DAV:}resourcetype":
            ET.SubElement(ele, "{DAV:}collection")
            return 200, ele

        if prop == "{DAV:}getetag":
            ele.text = get_random_string()
            return 200, ele

        if prop == "{DAV:}current-user-privilege-set":
            ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}read")
            ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}all")
            ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}write")
            ET.SubElement(
                ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}write-properties"
            )
            ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}write-content")
            return 200, ele

        if prop == "{DAV:}owner":
            ET.SubElement(ele, "{DAV:}href").text = resolve_url(
                "principal", user=request.user.username
            )
            return 200, ele

        if prop == "{DAV:}supported-report-set":
            return 200, ele

        if prop == "{urn:ietf:params:xml:ns:caldav}calendar-user-address-set":
            ET.SubElement(ele, "{DAV:}href").text = resolve_url(
                "principal", user=request.user.username,
            )
            return 200, ele

        if prop == "{urn:ietf:params:xml:ns:caldav}calendar-home-set":
            ET.SubElement(ele, "{DAV:}href").text = resolve_url(
                "principal", user=request.user.username
            )
            return 200, ele

        if prop == "{DAV:}resourcetype":
            ET.SubElement(ele, "{DAV:}principal")
            ET.SubElement(ele, "{DAV:}collection")
            return 200, ele

        logger.debug("unknown propfind %s for collection %s ", prop, self.obj)
        return 404, ele


class Calendar(BaseCollection):
    def _report(self, request, prop, value, extra):
        ele = ET.Element(prop)

        if prop == "{DAV:}getetag":
            ele.text = get_random_string()
            return 200, ele

        if prop == "{urn:ietf:params:xml:ns:caldav}calendar-data":
            todo = self.obj.event_set.get(id=extra["task"])
            ele.text = todo.to_ical()
            return 200, ele

        return 404, ele

    def _propfind(self, request, prop, value):
        ele = ET.Element(prop)

        if prop == "{DAV:}getetag":
            ele.text = self.obj.etag
            return 200, ele

        if prop == "{DAV:}displayname":
            ele.text = self.obj.name
            return 200, ele

        if prop == "{DAV:}current-user-privilege-set":
            ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}read")
            ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}all")
            ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}write")
            ET.SubElement(
                ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}write-properties"
            )
            ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}write-content")
            return 200, ele

        if prop == "{DAV:}owner":
            ET.SubElement(ele, "{DAV:}href").text = resolve_url(
                "principal", user=self.obj.owner.username
            )
            return 200, ele

        if prop == "{DAV:}resourcetype":
            ET.SubElement(ele, "{urn:ietf:params:xml:ns:caldav}calendar")
            ET.SubElement(ele, "collection")
            return 200, ele

        if prop == "{urn:ietf:params:xml:ns:caldav}supported-calendar-component-set":
            ET.SubElement(ele, "{urn:ietf:params:xml:ns:caldav}comp", {"name": "VTODO"})
            return 200, ele

        if prop == "{urn:ietf:params:xml:ns:caldav}calendar-data":
            ele.text = self.obj.to_ical()
            return 200, ele

        if prop == "{DAV:}getcontenttype":
            ele.text = "text/calendar"
            return 200, ele

        if prop == "{DAV:}supported-report-set":
            return 200, ele

        if prop == "{http://apple.com/ns/ical/}calendar-color":
            ele.text = self.obj.color
            return 200, ele

        if prop == "{http://apple.com/ns/ical/}calendar-order":
            ele.text = str(self.obj.order)
            return 200, ele

        logger.debug("unknown propfind %s for calendar %s ", prop, self.obj)
        return 404, ele

    def _proppatch(self, request, prop, value):
        ele = ET.Element(prop)

        if prop == "{DAV:}displayname":
            self.obj.name = value
            return 200, ele

        if prop == "{http://apple.com/ns/ical/}calendar-color":
            self.obj.color = value
            return 200, ele

        if prop == "{http://apple.com/ns/ical/}calendar-order":
            self.obj.order = value
            return 200, ele

        logger.debug("unknown proppatch %s for calendar %s ", prop, self.obj)
        return 404, ele


class Task(BaseCollection):
    def _propfind(self, request, prop, value):
        ele = ET.Element(prop)

        if prop == "{DAV:}getetag":
            ele.text = self.obj.etag
            return 200, ele

        if prop == "{DAV:}getcontenttype":
            ele.text = "text/calendar;charset=utf-8;component=VTODO"
            return 200, ele

        return 404, ele
