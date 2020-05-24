import defusedxml.ElementTree as etree
import icalendar
from rest_framework.exceptions import ParseError
from rest_framework.parsers import BaseParser

from django.conf import settings


class XMLParser(BaseParser):
    media_type = "text/xml"

    def parse(self, stream, media_type=None, parser_context=None):
        parser_context = parser_context or {}
        encoding = parser_context.get("encoding", settings.DEFAULT_CHARSET)
        parser = etree.DefusedXMLParser(encoding=encoding)
        try:
            return etree.parse(stream, parser=parser, forbid_dtd=True)
        except (etree.ParseError, ValueError) as exc:
            raise ParseError("XML parse error - %s" % str(exc))


class Caldav(BaseParser):
    media_type = "text/calendar"

    def parse(self, stream, media_type=None, parser_context=None):
        return icalendar.Calendar.from_ical(stream.read())
