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
    def generic(
        self,
        method,
        path,
        data="",
        content_type="application/octet-stream",
        secure=False,
        **extra
    ):
        if "xml" in extra:
            data = extra.pop("xml")
            content_type = "text/xml"
        if "xml_file" in extra:
            with extra.pop("xml_file").open() as fp:
                data = fp.read()
                content_type = "text/xml"
        if "ics_file" in extra:
            with extra.pop("ics_file").open() as fp:
                data = fp.read()
                content_type = "text/calendar; charset=utf-8"

        return super().generic(method, path, data, content_type, secure, **extra)

    def propfind(self, path, **extra):
        return self.generic("PROPFIND", path, **extra)
    
    def report(self, path, **extra):
        return self.generic("REPORT", path, **extra)
