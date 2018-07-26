
import json
import logging

from django.http import HttpResponse

import icalendar
from rest_framework import viewsets
from rest_framework.authentication import (
    BasicAuthentication,
    SessionAuthentication,
    TokenAuthentication,
)
from rest_framework.decorators import action
from rest_framework.permissions import (
    DjangoModelPermissions,
    DjangoModelPermissionsOrAnonReadOnly,
)
from rest_framework.response import Response
from todo.core import models, serializers

logger = logging.getLogger(__name__)


class TaskViewSet(viewsets.ModelViewSet):
    authentication_classes = (
        BasicAuthentication,
        SessionAuthentication,
        TokenAuthentication,
    )
    # filter_backends = (OrderingFilter,)
    permission_classes = (DjangoModelPermissions,)
    queryset = models.Task.objects.all()
    serializer_class = serializers.TaskSerializer

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)

    @action(detail=False)
    def calendar(self, request):
        cal = icalendar.Calendar()
        for task in (
            models.Task.objects.filter(owner=request.user)
            .exclude(start=None, due=None)
            .filter(status=models.Task.STATUS_OPEN)
        ):
            event = icalendar.Event()
            event.add("uid", task.uuid)

            if task.project:
                event.add("summary", "{} #{}".format(task.title, task.project))
            else:
                event.add("summary", task.title)
            event.add("url", request.build_absolute_uri(task.get_absolute_url()))

            if task.start and task.due:
                event.add("dtstart", task.start)
                event.add("dtend", task.due)
            elif task.start:
                event.add("dtstart", task.start)
                event.add("dtend", task.start)
            elif task.due:
                event.add("dtstart", task.due)
                event.add("dtend", task.due)

            cal.add_component(event)
        return HttpResponse(cal.to_ical(), content_type="text/plain")

    @action(methods=["post"], detail=False)
    def bulk_import(self, request):
        data = json.loads(request.body.decode("utf8"))
        updates = {}
        for issue in data:
            meta = issue.pop("meta", {})

            try:
                task = models.Task.objects.get(external__url=meta["external"])
                print("Found task")
                # TODO: Probably better way to handle this
                for key, value in issue.items():
                    setattr(task, key, value)

            except models.Task.DoesNotExist:
                print("Creating Task")
                task = models.Task.objects.create(owner=request.user, **issue)
                task.external = models.URL.objects.create(url=meta["external"])

            if task.project is None:
                print("Updating Project")
                project, created = models.Project.objects.get_or_create(
                    title=meta["project"], owner=request.user
                )
                task.project = project

            task.save()
            updates[str(task.uuid)] = {
                "title": task.title,
                "external": str(task.external),
            }

        return Response(updates)


class ProjectViewSet(viewsets.ModelViewSet):
    authentication_classes = (SessionAuthentication, TokenAuthentication)
    # filter_backends = (OrderingFilter,)
    permission_classes = (DjangoModelPermissions,)
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer

    def get_queryset(self):
        return self.queryset.filter(owner=self.request.user)
