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


USER_AGENT = "todo-server/github-sync https://github.com/kfdm/todo-server"


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("repos", nargs="+")

    def new_issue(self, issue):
        vTodo = icalendar.Todo()
        vTodo["uid"] = issue["id"]
        vTodo.add("X-GITHUB-ISSUE", issue["id"])
        vTodo.add("url", issue["html_url"])
        vTodo.add("summary", "#{number} {title}".format(**issue))
        vTodo.add("description", issue["body"])
        if issue["closed_at"]:
            vTodo.add("completed", parse(issue["closed_at"]))
            vTodo.add("status", "completed")
        vTodo.add("dtstart", parse(issue["created_at"]))
        return vTodo

    def old_issue(self, issue, vTodo):
        newTodo = self.new_issue(issue)

        for k in ["summary", "description", "completed", "status", "dtstart", "url"]:
            if k in newTodo:
                # TODO: Push any updated values to GitHub
                vTodo[k] = newTodo[k]
        if "SEQUENCE" in vTodo:
            vTodo["SEQUENCE"] += 1

        return vTodo

    def push_github(self, vTodo, config, repo):
        gh_request = self.gh.post(
            "https://api.github.com/repos/%s/issues" % repo,
            json={
                "title": vTodo.decoded("summary"),
                "body": vTodo.decoded("description", ""),
            },
        )
        gh_request.raise_for_status()
        issue = gh_request.json()
        vTodo.add("X-GITHUB-ISSUE", issue["id"])

        return self.old_issue(issue, vTodo)

    def fetch_caldav(self, config, repo):
        cal_request = self.caldav.get(config[repo]["calendar"])
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
        gh_request = self.gh.get(
            "https://api.github.com/repos/%s/issues" % repo, params={"state": "all"}
        )
        gh_request.raise_for_status()
        return gh_request.json()

    def process(self, config, repo):
        # Fetch our old issues so that we can compare them
        new_caldav, old_caldav = self.fetch_caldav(config, repo)
        # Loop through our GitHub issues
        for issue in self.fetch_github(config, repo):
            # Update our existing issues from CalDav
            if issue["id"] in old_caldav:
                logger.info(
                    "Old GitHub->CalDav #%s %s", issue["number"], issue["title"]
                )
                yield self.old_issue(issue, old_caldav[issue["id"]])
            # Add our new issues to CalDav
            else:
                logger.info(
                    "New GitHub->CalDav #%s %s", issue["number"], issue["title"]
                )
                yield self.new_issue(issue)

        for vObject in new_caldav:
            # Push the new object to Gihub and return with the Github ID
            logger.info(
                "New CalDav->GitHub %s", vObject.decoded("summary").decode("utf8")
            )
            yield self.push_github(vObject, config, repo)

    def handle(self, repos, verbosity, **options):
        if verbosity == 2:
            logging.root.setLevel(logging.INFO)
        if verbosity == 3:
            logging.root.setLevel(logging.DEBUG)

        config = configparser.ConfigParser()
        with open(os.path.join(CONFIG_DIR, "todo-sync.ini")) as fp:
            config.readfp(fp)

        self.caldav = requests.session()
        self.caldav.auth = ("github", config["DEFAULTS"]["password"])
        self.caldav.headers = {"user-agent": USER_AGENT}

        self.gh = requests.session()
        self.gh.headers = {
            "Authorization": "token %s" % config["DEFAULTS"]["token"],
            "user-agent": USER_AGENT,
        }

        for repo in repos:
            logging.info("Processing %s", repo)
            for todo in self.process(config, repo):
                cal = icalendar.Calendar()
                cal["version"] = "2.0"
                cal["prodid"] = "test"
                cal.add_component(todo)

                # print(cal.to_ical().decode("utf8"))

                result = self.caldav.put(
                    "{}/{}.ics".format(config[repo]["calendar"], todo["uid"]),
                    data=cal.to_ical(),
                )
                # print(result.text)
                result.raise_for_status()
