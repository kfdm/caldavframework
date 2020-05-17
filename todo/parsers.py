from rest_framework_xml import parsers


class XMLParser(parsers.XMLParser):
    media_type = "text/xml"

