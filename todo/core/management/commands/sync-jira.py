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

        response = requests.post(
            os.environ.get("JIRA_URL"),
            auth=(os.environ.get("JIRA_USER"), os.environ.get("JIRA_PASSWORD")),
            json={
                "jql": query,
                "fields": [
                    "description",
                    "created",
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
            yield {
                "title": issue["fields"]["summary"],
                "status": state(issue["fields"]["status"]),
                "createdAt": issue["fields"]["created"],
                "completedAt": issue["fields"]["resolutiondate"],
            }, {
                "priority": issue["fields"]["priority"]["name"],
                "external": issue["self"],
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
                url = URL.objects.get(url=meta["external"])
                print("Found task")
                task = url.task
            except URL.DoesNotExist:
                print("Creating Task")
                task = Task.objects.create(owner=owner, **issue)
                URL.objects.create(url=meta["external"], task=task)

            if task.project is None:
                print("Updating Project")
                project, created = Project.objects.get_or_create(
                    title=meta["project"], owner=owner
                )
                task.project = project

            task.save()
