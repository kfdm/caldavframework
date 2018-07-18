import logging
import os
from pprint import pprint

import requests
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from todo.core.models import URL, Project, Task

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import projects from JIRA"

    def add_arguments(self, parser):
        parser.add_argument("username")

    def fetch(self, query):

        def state(value):
            # print('state', value)
            if value["statusCategory"]["colorName"] == "green":
                return Task.STATUS_CLOSED
            return Task.STATUS_OPEN

        url = "{}/rest/api/latest/search".format(os.environ.get("JIRA_URL"))
        response = requests.post(
            url,
            auth=(os.environ.get("JIRA_USER"), os.environ.get("JIRA_PASSWORD")),
            json={
                "jql": query,
                "fields": [
                    "duedate",
                    "created",
                    "description",
                    "priority",
                    "project",
                    "resolutiondate",
                    "status",
                    "summary",
                ],
            },
        )
        response.raise_for_status()
        # print(response.headers)

        for issue in response.json().get("issues", {}):
            external = "{}/browse/{}".format(os.environ.get("JIRA_URL"), issue["key"])
            yield {
                "title": issue["fields"]["summary"],
                "status": state(issue["fields"]["status"]),
                "createdAt": issue["fields"]["created"],
                "completedAt": issue["fields"]["resolutiondate"],
                "due": issue["fields"]["duedate"],
            }, {
                "priority": priority(issue["fields"]["priority"]["name"]),
                "external": external,
                "project": "JIRA/" + issue["fields"]["project"]["key"],
            }
        pprint(issue)

    def handle(self, username, **options):
        owner = User.objects.get(username=username)
        query = "updated >= -30d AND assignee in (currentUser())"
        for issue, meta in self.fetch(query):
            # print(issue, meta)
            # continue
            try:
                task = Task.objects.get(external__url=meta["external"])
                print("Found task")
            except Task.DoesNotExist:
                print("Creating Task")
                task = Task.objects.create(owner=owner, **issue)
                task.external = URL.objects.create(url=meta["external"])

            if task.project is None:
                print("Updating Project")
                project, created = Project.objects.get_or_create(
                    title=meta["project"], owner=owner
                )
                task.project = project

            task.save()
