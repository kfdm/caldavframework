import logging
from pprint import pprint

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand
from django.urls import reverse

import requests
from rest_framework.authtoken.models import Token

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Import projects from GitHub"

    def add_arguments(self, parser):
        parser.add_argument("-s", "--site-id", default=settings.SITE_ID)
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
                "meta": {
                    "project": "GitHub/" + repo,
                    "external": issue["html_url"],
                    "tags": ["GitHub:" + x["name"] for x in issue.get("labels", [])],
                },
            }
        # print(issue)

    def handle(self, site_id, repo, username, **options):
        site = Site.objects.get(pk=site_id)
        token, _ = Token.objects.get_or_create(user__username=username)

        if site.domain.startswith("localhost"):
            url = "http://{}{}".format(site.domain, reverse("api:task-bulk-import"))
        else:
            url = "https://{}{}".format(site.domain, reverse("api:task-bulk-import"))

        batch = list(self.fetch(repo))
        response = requests.post(
            url, json=batch, headers={"Authorization": "Token " + token.key}
        )
        response.raise_for_status()
        pprint(response.json())
