import collections
import xml.etree.ElementTree as ET

from django.http import HttpResponse
from django.urls import reverse

ET.register_namespace("DAV:", "")


def status(code):
    if code == 200:
        return "HTTP/1.1 200 OK"
    if code == 404:
        return "HTTP/1.1 404 Not Found"


def proppatch(request, prop, value, obj):
    ele = ET.Element(prop)

    if prop == "{DAV:}displayname":
        obj.name = value
        return 200, ele

    print("unknown proppatch", prop)
    return 404, ele


def propfind(request, prop, value, obj=None):
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
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}write-properties")
        ET.SubElement(ET.SubElement(ele, "{DAV:}privilege"), "{DAV:}write-content")
        return 200, ele

    if prop == "{DAV:}owner":
        ET.SubElement(ele, "{DAV:}href").text = reverse(
            "principal", kwargs={"user": request.user.username}
        )
        return 200, ele

    if prop == "{DAV:}supported-report-set":
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

    print("unknown propfind", prop, "for", obj)
    return 404, ele


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


class Multistatus:
    def __init__(self):
        self.multistatus = ET.Element("{DAV:}multistatus")

    def append(self, element):
        self.multistatus.append(element)

    def propstat(self, href):
        response = self.response(href)
        return Propstats(response)

    def response(self, href):
        response = ET.SubElement(self.multistatus, "{DAV:}response")
        ET.SubElement(response, "{DAV:}href").text = href
        return response

    def render(self, request):
        return CaldavResponse(self.multistatus, status=207)


class CaldavResponse(HttpResponse):
    def __init__(self, element, *args, **kwargs):
        kwargs["content"] = "<?xml version='1.0' encoding='utf-8'?>" + ET.tostring(
            element, encoding="unicode", short_empty_elements=True
        )
        kwargs.setdefault("content_type", "text/xml; charset=utf-8")
        super().__init__(*args, **kwargs)
        self["DAV"] = "1, 2, 3, calendar-access, addressbook, extended-mkcol"
