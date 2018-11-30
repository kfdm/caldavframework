import collections
import configparser
import logging
import os

import icalendar
import requests
from dateutil.parser import parse
from django.core.management.base import BaseCommand
from todo import CONFIG_DIR

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import projects from JIRA"
    headers = {"user-agent": "todo-server/ https://github.com/kfdm/todo-server"}

    def add_arguments(self, parser):
        parser.add_argument(
            "--maxResults", type=int, default=50, help="Number of JIRA issues to query"
        )

    def handle(self, verbosity, **options):
        if verbosity > 1:
            logging.root.setLevel(logging.INFO)
        if verbosity > 2:
            logging.root.setLevel(logging.DEBUG)

        config = configparser.ConfigParser()
        with open(os.path.join(CONFIG_DIR, "todo-sync.ini")) as fp:
            config.readfp(fp)

        caldav = (config["DEFAULTS"]["user"], config["DEFAULTS"]["password"])

        for project, todo in self.process(config, **options):
            cal = icalendar.Calendar()
            cal["version"] = "2.0"
            cal["prodid"] = "test"
            cal.add_component(todo)

            if verbosity > 3:
                print(cal.to_ical().decode("utf8"))

            result = requests.put(
                "{}/{}.ics".format(config[project]["calendar"], todo["uid"]),
                auth=caldav,
                data=cal.to_ical(),
                headers=self.headers,
            )
            # print(result.text)
            result.raise_for_status()
            # return

    def fetch_caldav(self, config, projects):
        new_issue = collections.defaultdict(list)
        old_issue = collections.defaultdict(dict)

        for section in projects:
            caldav = (config["DEFAULTS"]["user"], config["DEFAULTS"]["password"])
            cal_request = requests.get(
                config[section]["calendar"], auth=caldav, headers=self.headers
            )
            cal_request.raise_for_status()
            calendar = icalendar.Calendar.from_ical(cal_request.text)

            for i in calendar.walk("vtodo"):
                if "X-JIRA-ISSUE" in i:
                    old_issue[section][
                        int(i.decoded("X-JIRA-ISSUE").decode("utf8"))
                    ] = i
                else:
                    new_issue[section].append(i)
        return new_issue, old_issue

    def fetch_jira(self, config, maxResults, **kwargs):
        query = "updated >= -30d AND assignee in (currentUser()) ORDER BY updated DESC"

        url = "{}/rest/api/latest/search".format(os.environ.get("JIRA_URL"))
        response = requests.post(
            url,
            auth=(os.environ.get("JIRA_USER"), os.environ.get("JIRA_PASSWORD")),
            json={
                "jql": query,
                "maxResults": maxResults,
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
            headers=self.headers,
        )
        response.raise_for_status()

        for issue in response.json().get("issues", {}):
            yield issue

    def process(self, config, **kwargs):
        projects = [s for s in config._sections if s != "DEFAULTS"]
        # Fetch our old issues so that we can compare them
        new_caldav, old_caldav = self.fetch_caldav(config, projects)

        # Loop through our JIRA issues
        for issue in self.fetch_jira(config, **kwargs):
            project = issue["fields"]["project"]["key"]
            issue_id = int(issue["id"])

            if issue_id in old_caldav[project]:
                logger.info(
                    "Old JIRA->CalDav #%s %s", issue["key"], issue["fields"]["summary"]
                )
                yield project, self.old_issue(issue, old_caldav[project][issue_id])
            else:
                logger.info(
                    "New JIRA->CalDav #%s %s", issue["key"], issue["fields"]["summary"]
                )
                yield project, self.new_issue(issue)

        for project in new_caldav:
            for vObject in new_caldav[project]:
                yield project, self.push_jira(vObject)

    def new_issue(self, issue):
        event = icalendar.Todo()
        event["uid"] = issue["id"]
        event["summary"] = "{} {}".format(issue["key"], issue["fields"]["summary"])
        event["description"] = "{}\n{}".format(
            "{}/browse/{}".format(os.environ.get("JIRA_URL"), issue["key"]),
            issue["fields"]["description"],
        )
        event["url"] = "{}/browse/{}".format(os.environ.get("JIRA_URL"), issue["key"])

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

        event.add("X-JIRA-ISSUE", issue["id"])
        event.add("X-JIRA-KEY", issue["key"])
        event.add("X-JIRA-PROJECT", issue["fields"]["project"]["key"])
        return event

    def old_issue(self, issue, vTodo):
        newTodo = self.new_issue(issue)

        for k in ["summary", "description", "completed", "status", "dtstart", "url"]:
            if k in newTodo:
                # TODO: Push any updated values to GitHub
                vTodo[k] = newTodo[k]
        # Update our alarms
        vTodo.subcomponents = newTodo.subcomponents

        return vTodo

    def push_jira(self, vTodo):
        logger.warn("New CalDav->JIRA %s", vTodo.decoded("summary").decode("utf8"))
        return vTodo
