from rest_framework.exceptions import ParseError
from rest_framework.parsers import BaseParser
from rest_framework_xml import parsers
from rest_framework_xml.compat import etree

from django.conf import settings

import icalendar


class XMLParser(parsers.XMLParser):
    media_type = "text/xml"

    def parse(self, stream, media_type=None, parser_context=None):
        assert etree, "XMLParser requires defusedxml to be installed"

        parser_context = parser_context or {}
        encoding = parser_context.get("encoding", settings.DEFAULT_CHARSET)
        parser = etree.DefusedXMLParser(encoding=encoding)
        try:
            return etree.parse(stream, parser=parser, forbid_dtd=True)
        except (etree.ParseError, ValueError) as exc:
            raise ParseError("XML parse error - %s" % str(exc))


class Caldav(parsers.BaseParser):
    media_type = "text/calendar"

    def parse(self, stream, media_type=None, parser_context=None):
        return icalendar.Calendar.from_ical(stream.read())
