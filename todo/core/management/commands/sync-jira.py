import logging
import os
from pprint import pprint

from django.core.management.base import BaseCommand

import requests
from todo.core.models import Task

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import projects from JIRA"

    def add_arguments(self, parser):
        parser.add_argument("-s", "--site-id", default=settings.SITE_ID)
        parser.add_argument("username")

    def fetch(self, query):
        def state(value):
            # print('state', value)
            if value["statusCategory"]["colorName"] == "green":
                return Task.STATUS_CLOSED
            return Task.STATUS_OPEN

        def priority(value):
            if value == "Minor":
                return 4
            if value == "Major":
                return 6
            if value == "Critical":
                return 8
            if value == "Blocker":
                return 10
            return 0

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
        # print(response.headers)

        for issue in response.json().get("issues", {}):
            external = "{}/browse/{}".format(os.environ.get("JIRA_URL"), issue["key"])
            yield {
                "title": issue["fields"]["summary"],
                "status": state(issue["fields"]["status"]),
                "createdAt": issue["fields"]["created"],
                "completedAt": issue["fields"]["resolutiondate"],
                "due": issue["fields"]["duedate"],
                "priority": priority(issue["fields"]["priority"]["name"]),
                "meta": {
                    "external": external,
                    "project": "JIRA/" + issue["fields"]["project"]["key"],
                    "tags": [
                        "JIRA:" + x["name"] for x in issue["fields"]["components"]
                    ],
                },
            }
        pprint(issue)

    def handle(self, site_id, username, **options):
        site = Site.objects.get(pk=site_id)
        token, _ = Token.objects.get_or_create(user__username=username)
        query = "updated >= -30d AND assignee in (currentUser())"

        if site.domain.startswith("localhost"):
            url = "http://{}{}".format(site.domain, reverse("api:task-bulk-import"))
        else:
            url = "https://{}{}".format(site.domain, reverse("api:task-bulk-import"))

        batch = list(self.fetch(query))
        response = requests.post(
            url, json=batch, headers={"Authorization": "Token " + token.key}
        )
        response.raise_for_status()
        pprint(response.json())
