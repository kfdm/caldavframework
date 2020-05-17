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


def propfind(prop, request):
    if prop == "{DAV:}current-user-principal":
        ele = ET.Element(prop)
        ET.SubElement(ele, "{DAV:}href").text = reverse(
            "principal", kwargs={"user": request.user.username}
        )
        return 200, ele
    if prop == "{DAV:}resourcetype":
        ele = ET.Element(prop)
        ET.SubElement(ele, "{DAV:}collection")
        return 200, ele
    print("unknown prop", prop)
    return 404, ET.Element(prop)


class Propstats:
    def __init__(self):
        self.collection = collections.defaultdict(list)

    def __getitem__(self, key):
        return self.collection[key]

    def render(self, request):
        multistatus = ET.Element("{DAV:}multistatus")
        response = ET.SubElement(multistatus, "{DAV:}response")
        ET.SubElement(response, "{DAV:}href").text = request.path

        for status_code in self.collection:
            propstat = ET.SubElement(response, "{DAV:}propstat")
            prop = ET.SubElement(propstat, "{DAV:}prop")
            for element in self.collection[status_code]:
                prop.append(element)
            ET.SubElement(propstat, "{DAV:}status").text = status(status_code)
        return CaldavResponse(multistatus, status=207)


class CaldavResponse(HttpResponse):
    def __init__(self, element, *args, **kwargs):
        kwargs["content"] = "<?xml version='1.0' encoding='utf-8'?>" + ET.tostring(
            element, encoding="unicode", short_empty_elements=True
        )
        kwargs.setdefault("content_type", "text/xml; charset=utf-8")
        super().__init__(*args, **kwargs)
        self["DAV"] = "1, 2, 3, calendar-access, addressbook, extended-mkcol"
