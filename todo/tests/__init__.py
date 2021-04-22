import pathlib

from rest_framework.test import APIClient

from django import test
from django.contrib import auth


class BaseCaldavTestCase(test.TestCase):
    test_dir = pathlib.Path(__file__).parent

    def get_user(self, **kwargs):
        return auth.get_user_model().objects.create_user(**kwargs)

    def force_user(self, **kwargs):
        self.user, _ = self.get_user(**kwargs)
        self.client.force_login(self.user)


class DAVClient(APIClient):
    def propfind(self, path, **extra):
        if "xml" in extra:
            extra["data"] = extra.pop("xml")
            extra["content_type"] = "text/xml"
        if "xml_file" in extra:
            with extra.pop("xml_file").open() as fp:
                extra["data"] = fp.read()
                extra["content_type"] = "text/xml"
        return self.generic("PROPFIND", path, **extra)
