import configparser
import logging
import os
from pprint import pprint

import icalendar
import requests
from dateutil.parser import parse
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.urls import reverse
from rest_framework.authtoken.models import Token
from todo import CONFIG_DIR
from todo.core.models import Task

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import projects from JIRA"

    def handle(self, **options):
        config = configparser.ConfigParser()
        with open(os.path.join(CONFIG_DIR, "todo-sync.ini")) as fp:
            config.readfp(fp)

        caldav = ("jira", config["DEFAULTS"]["password"])

        query = "updated >= -30d AND assignee in (currentUser())"

        url = "{}/rest/api/latest/search".format(os.environ.get("JIRA_URL"))
        response = requests.post(
            url,
            auth=(os.environ.get("JIRA_USER"), os.environ.get("JIRA_PASSWORD")),
            json={
                "jql": query,
                "fields": [
                    "components",
                    "created",
                    "description",
                    "duedate",
                    "priority",
                    "project",
                    "resolutiondate",
                    "status",
                    "summary",
                ],
            },
        )
        response.raise_for_status()

        for issue in response.json().get("issues", {}):
            cal = icalendar.Calendar()
            cal["version"] = "2.0"
            cal["prodid"] = "test"

            event = icalendar.Todo()
            event["uid"] = issue["id"]
            event["summary"] = "{} {}".format(issue["key"], issue["fields"]["summary"])
            event["description"] = "{}\n{}".format(
                "{}/browse/{}".format(os.environ.get("JIRA_URL"), issue["key"]),
                issue["fields"]["description"],
            )

            event.add("dtstart", parse(issue["fields"]["created"]))

            if issue["fields"]["resolutiondate"]:
                event.add("completed", parse(issue["fields"]["resolutiondate"]))
                event.add("status", "completed")
            if issue["fields"]["duedate"]:
                event.add("due", parse(issue["fields"]["duedate"]))

                alarm = icalendar.Alarm()
                alarm["uid"] = issue["id"] + "-alarm"
                alarm["action"] = "display"
                alarm.add("trigger", parse(issue["fields"]["duedate"]))
                event.add_component(alarm)

            section = issue["fields"]["project"]["key"]
            if section not in config:
                print("skipping", issue["fields"]["project"]["key"])
                continue
            # "status": state(issue["fields"]["status"]),

            cal.add_component(event)

            # print(cal.to_ical().decode("utf8"))
            # pprint(issue)

            result = requests.put(
                "{}/jira/{}/{}.ics".format(
                    config["DEFAULTS"]["server"],
                    config[section]["calendar"].upper(),
                    event["uid"],
                ),
                auth=caldav,
                data=cal.to_ical(),
            )
            # print(result.text)
            result.raise_for_status()
            # return
