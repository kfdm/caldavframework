import logging

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

import requests
from todo.core.models import URL, Project, Task

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import projects from GitHub"

    def add_arguments(self, parser):
        parser.add_argument("username")
        parser.add_argument("repo")

    def fetch(self, repo):
        def state(value):
            if value == "closed":
                return Task.STATUS_CLOSED
            return Task.STATUS_OPEN

        url = "https://api.github.com/repos/" + repo + "/issues"
        result = requests.get(url)
        result.raise_for_status()
        logger.debug("X-RateLimit-Limit: %s", result.headers.get("X-RateLimit-Limit"))

        for issue in result.json():
            yield {
                "title": issue["title"],
                "status": state(issue["state"]),
                "createdAt": issue["created_at"],
                "completedAt": issue["closed_at"],
            }, {
                "project": "GitHub/" + repo,
                "external": issue["html_url"],
                "tags": [x["name"] for x in issue.get("labels", [])],
            }
        # print(issue)

    def handle(self, repo, username, **options):
        owner = User.objects.get(username=username)
        for issue, meta in self.fetch(repo):
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
