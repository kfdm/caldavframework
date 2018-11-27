import configparser
import logging
import os

from django.core.management.base import BaseCommand

import icalendar
import requests
from dateutil.parser import parse
from todo import CONFIG_DIR

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import projects from GitHub"

    def add_arguments(self, parser):
        parser.add_argument("repos", nargs="+")

    def new_issue(self, issue):
        logger.info("New GitHub->CalDav #%s %s", issue["number"], issue["title"])
        vTodo = icalendar.Todo()
        vTodo["uid"] = issue["id"]
        vTodo.add("X-GITHUB-ISSUE", issue["id"])
        vTodo.add("summary", "#{number} {title}".format(**issue))
        vTodo.add("description", "{html_url}\n{body}".format(**issue))
        if issue["closed_at"]:
            vTodo.add("completed", parse(issue["closed_at"]))
            vTodo.add("status", "completed")
        vTodo.add("dtstart", parse(issue["created_at"]))
        return vTodo

    def old_issue(self, issue, vTodo):
        logger.info("Update GitHub->CalDav #%s %s", issue["number"], issue["title"])
        for k in ["summary", "description", "completed", "status", "dtstart"]:
            vTodo.pop(k)

        vTodo.add("summary", "#{number} {title}".format(**issue))
        vTodo.add("description", "{html_url}\n{body}".format(**issue))
        if issue["closed_at"]:
            vTodo.add("completed", parse(issue["closed_at"]))
            vTodo.add("status", "completed")
        vTodo.add("dtstart", parse(issue["created_at"]))
        return vTodo

    def fetch_caldav(self, config, repo):
        caldav = ("github", config["DEFAULTS"]["password"])
        cal_request = requests.get(config[repo]["calendar"], auth=caldav)
        cal_request.raise_for_status()
        calendar = icalendar.Calendar.from_ical(cal_request.text)

        new_issue = []
        old_issue = {}
        for i in calendar.walk("vtodo"):
            if "X-GITHUB-ISSUE" in i:
                old_issue[int(i.decoded("X-GITHUB-ISSUE").decode("utf8"))] = i
            else:
                new_issue.append(i)
        return new_issue, old_issue

    def fetch_github(self, config, repo):
        gh = {"Authorization": "token %s" % config["DEFAULTS"]["token"]}
        gh_request = requests.get(
            "https://api.github.com/repos/%s/issues" % repo,
            headers=gh,
            params={"state": "all"},
        )
        gh_request.raise_for_status()
        return gh_request.json()

    def push_github(self, vTodo):
        logger.warn("New CalDav->GitHub %s", vTodo.decoded("summary").decode("utf8"))
        # TODO: Finish push_to_github
        return vTodo

    def process(self, config, repo):
        # Fetch our old issues so that we can compare them
        new_caldav, old_caldav = self.fetch_caldav(config, repo)
        # Loop through our GitHub issues
        for issue in self.fetch_github(config, repo):
            # Update our existing issues from CalDav
            if issue["id"] in old_caldav:
                yield self.old_issue(issue, old_caldav[issue["id"]])
            # Add our new issues to CalDav
            else:
                yield self.new_issue(issue)

        for vObject in new_caldav:
            # Push the new object to Gihub and return with the Github ID
            yield self.push_github(vObject)

    def handle(self, repos, verbosity, **options):
        if verbosity == 2:
            logging.root.setLevel(logging.INFO)
        if verbosity == 3:
            logging.root.setLevel(logging.DEBUG)

        config = configparser.ConfigParser()
        with open(os.path.join(CONFIG_DIR, "todo-sync.ini")) as fp:
            config.readfp(fp)

        caldav = ("github", config["DEFAULTS"]["password"])

        for repo in repos:
            logging.info("Processing %s", repo)
            for todo in self.process(config, repo):
                cal = icalendar.Calendar()
                cal["version"] = "2.0"
                cal["prodid"] = "test"
                cal.add_component(todo)

                # print(cal.to_ical().decode("utf8"))

                result = requests.put(
                    "{}/{}.ics".format(config[repo]["calendar"], todo["uid"]),
                    auth=caldav,
                    data=cal.to_ical(),
                )
                # print(result.text)
                result.raise_for_status()
