import configparser
import logging
import os

from django.core.management.base import BaseCommand

import icalendar
import requests
from dateutil.parser import parse
from todo import CONFIG_DIR

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import projects from GitHub"

    def handle(self, **options):
        config = configparser.ConfigParser()
        with open(os.path.join(CONFIG_DIR, "todo-sync.ini")) as fp:
            config.readfp(fp)

        gh = {"Authorization": "token %s" % config["DEFAULTS"]["token"]}
        caldav = ("github", config["DEFAULTS"]["password"])

        for section in config._sections:
            if section == "DEFAULTS":
                continue

            gh_request = requests.get(
                "https://api.github.com/repos/%s/issues" % section,
                headers=gh,
                params={"state": "all"},
            )
            gh_request.raise_for_status()

            for issue in gh_request.json():
                cal = icalendar.Calendar()
                cal["version"] = "2.0"
                cal["prodid"] = "test"

                event = icalendar.Todo()
                event["uid"] = issue["id"]
                event["summary"] = "#{number} {title}".format(**issue)
                event["description"] = "{html_url}\n{body}".format(**issue)
                if issue["closed_at"]:
                    event.add("completed", parse(issue["closed_at"]))
                    event.add("status", "completed")
                event.add("dtstart", parse(issue["created_at"]))
                cal.add_component(event)

                # pprint(issue)
                # print(cal.to_ical().decode("utf8"))

                result = requests.put(
                    "{}/github/{}/{}.ics".format(
                        config["DEFAULTS"]["server"],
                        config[section]["calendar"].upper(),
                        event["uid"],
                    ),
                    auth=caldav,
                    data=cal.to_ical(),
                )
                # print(result.text)
                result.raise_for_status()

                # break
