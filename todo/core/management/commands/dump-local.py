
import logging
import os
import plistlib
import urllib

from django.core.management.base import BaseCommand

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


DEFAULT_CALENDAR = os.path.join(os.path.expanduser("~"), "Library", "Calendars")


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--folder", default=DEFAULT_CALENDAR)

    def find_plist(self, top):
        for root, dirs, files in os.walk(top, topdown=True):
            for name in files:
                if name.endswith("Info.plist"):
                    yield root, os.path.join(root, name)

    def find_calendar(self, top):
        for root, fn in self.find_plist(top):
            if not root.endswith(".caldav"):
                continue

            with open(fn, mode="rb") as fp:
                plist = plistlib.load(fp, fmt=plistlib.FMT_XML)

                if plist["Title"].startswith("github"):
                    for _, fnl in self.find_plist(root):
                        # Since we scan the same directory, we want to skip
                        # over our root Info.plist
                        if fn == fnl:
                            continue

                        yield plist, fnl

    def find_repos(self, top):
        for cal, fn in self.find_calendar(top):
            with open(fn, mode="rb") as fp:
                plist = plistlib.load(fp, fmt=plistlib.FMT_XML)

                if cal["CalendarHomePath"] == plist["OwnerPrincipalPath"]:
                    url = urllib.parse.urljoin(
                        cal["PrincipalURL"], plist["CalendarPath"]
                    )
                    yield plist["Title"], url

    def handle(self, folder, **options):
        for info in self.find_repos(folder):
            print(info)
