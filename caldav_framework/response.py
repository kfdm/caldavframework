import collections
import xml.etree.ElementTree as ET

from django.http.response import HttpResponse


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

    def __lshift__(self, other):
        self.collection[other[0]].append(other[1])

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
        self["DAV"] = "1, 3, access-control, calendar-access"

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
