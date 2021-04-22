from . import DAVClient, TestCase

from django.urls import reverse


class CaldavTest(TestCase):
    client_class = DAVClient
    fixtures = ["testcase"]

    def setUp(self):
        self.client.credentials(HTTP_AUTHORIZATION="Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==")

    def test_discovery(self):
        result = self.client.propfind(
            reverse("discovery"),
            xml_file=self.test_dir / "discovery.xml",
            HTTP_DEPTH=0,
        )
        self.assertEqual(result.status_code, 207, result.content)

    def test_principal(self):
        result = self.client.propfind(
            reverse("principal", kwargs={"user": "Aladdin"}),
            xml_file=self.test_dir / "principal.xml",
            HTTP_DEPTH="1",
        )
        self.assertEqual(result.status_code, 207, result.content)
