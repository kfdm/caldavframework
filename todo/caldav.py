import collections
import logging
import xml.etree.ElementTree as ET

import icalendar

from django.http.response import HttpResponse, HttpResponseBase
from django.urls import reverse

ET.register_namespace("DAV:", "")


logger = logging.getLogger(__name__)


class Collection:
    def __init__(self, user):
        self.user = user

    def propfind(self, request, prop, value):
        ele = ET.Element(prop)

        if prop == "{DAV:}current-user-principal":
            ET.SubElement(ele, "{DAV:}href").text = reverse(
                "principal", kwargs={"user": request.user.username}
            )
            return 200, ele

        if prop == "{DAV:}resourcetype":
            ET.SubElement(ele, "{DAV:}collection")
            return 200, ele

        if prop == "{DAV:}supported-calendar-component-set":
            # Return list of calendars
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
            ET.SubElement(ele, "{DAV:}href").text = reverse(
                "principal", kwargs={"user": request.user.username}
            )
            return 200, ele

        if prop == "{DAV:}supported-report-set":
            return 200, ele

        if prop == "{urn:ietf:params:xml:ns:caldav}calendar-user-address-set":
            ET.SubElement(ele, "{DAV:}href").text = reverse(
                "principal", kwargs={"user": request.user.username}
            )
            return 200, ele

        if prop == "{urn:ietf:params:xml:ns:caldav}calendar-home-set":
            ET.SubElement(ele, "{DAV:}href").text = reverse(
                "principal", kwargs={"user": request.user.username}
            )
            return 200, ele

        if prop == "{DAV:}resourcetype":
            ET.SubElement(ele, "{DAV:}principal")
            ET.SubElement(ele, "{DAV:}collection")
            return 200, ele

        logger.debug("unknown propfind %s for collection %s ", prop, self.user)
        return 404, ele


class Calendar:
    def __init__(self, calendar):
        self.calendar = calendar

    def propfind(self, request, prop, value):
        ele = ET.Element(prop)

        if prop == "{DAV:}displayname":
            ele.text = self.calendar.name
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
            ET.SubElement(ele, "{DAV:}href").text = reverse(
                "principal", kwargs={"user": self.calendar.owner.username}
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
            ele.text = self.to_ical(request, self.calendar)
            return 200, ele

        if prop == "{DAV:}getcontenttype":
            ele.text = "text/calendar"
            return 200, ele

        if prop == "{DAV:}supported-report-set":
            return 200, ele

        logger.debug("unknown propfind %s for calendar %s ", prop, self.calendar)
        return 404, ele

    def proppatch(self, request, prop, value):
        ele = ET.Element(prop)

        if prop == "{DAV:}displayname":
            self.calendar.name = value
            return 200, ele

        if prop == "{http://apple.com/ns/ical/}calendar-color":
            self.calendar.color = value
            return 200, ele

        logger.debug("unknown proppatch %s for calendar %s ", prop, self.calendar)
        return 404, ele

    def to_ical(self, request, calendar):
        cal = icalendar.Calendar()

        for e in calendar.event_set.all():
            event = icalendar.Event()
            event.add("uid", e.id)
            event.add("summary", e.summary)
            event.add("created", e.created)
            cal.add_component(event)
        return cal.to_ical()


class Task:
    def __init__(self, task):
        self.task = task

    def propfind(self, request, prop, value):
        ele = ET.Element(prop)
        
        if prop == "{DAV:}getcontenttype":
            ele.text = "text/calendar"
            return 200, ele

        return 404, ele


def status(code):
    if code == 200:
        return "HTTP/1.1 200 OK"
    if code == 404:
        return "HTTP/1.1 404 Not Found"


class Propstats:
    def __init__(self, parent):
        self.collection = collections.defaultdict(list)
        self.parent = parent

    def __getitem__(self, key):
        return self.collection[key]

    def render(self, request):
        for status_code in self.collection:
            propstat = ET.SubElement(self.parent, "{DAV:}propstat")
            prop = ET.SubElement(propstat, "{DAV:}prop")
            for element in self.collection[status_code]:
                prop.append(element)
            ET.SubElement(propstat, "{DAV:}status").text = status(status_code)


class MultistatusResponse(HttpResponse):
    streaming = False

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("content_type", "text/xml; charset=utf-8")
        kwargs.setdefault("status", 207)

        super().__init__(*args, **kwargs)
        self.__element = ET.Element("{DAV:}multistatus")
        self._is_rendered = False
        self["DAV"] = "1, 2, 3, calendar-access, addressbook, extended-mkcol"

    def sub_response(self, href):
        response = ET.SubElement(self.__element, "{DAV:}response")
        ET.SubElement(response, "{DAV:}href").text = href
        return response

    def propstat(self, href):
        response = self.sub_response(href)
        return Propstats(response)

    def render(self):
        if not self._is_rendered:
            self.content = "<?xml version='1.0' encoding='utf-8'?>" + ET.tostring(
                self.__element, encoding="unicode", short_empty_elements=True
            )
        return self
