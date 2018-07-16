
import logging

from rest_framework import viewsets
from rest_framework.authentication import (
    BasicAuthentication,
    SessionAuthentication,
    TokenAuthentication,
)
from rest_framework.permissions import (
    DjangoModelPermissions,
    DjangoModelPermissionsOrAnonReadOnly,
)
from todo.core import models, serializers

logger = logging.getLogger(__name__)


class TaskViewSet(viewsets.ModelViewSet):
    # authentication_classes = (SessionAuthentication, TokenAuthentication)
    # filter_backends = (OrderingFilter,)
    # permission_classes = (DjangoModelPermissions,)
    queryset = models.Task.objects.all()
    serializer_class = serializers.TaskSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    # authentication_classes = (SessionAuthentication, TokenAuthentication)
    # filter_backends = (OrderingFilter,)
    # permission_classes = (DjangoModelPermissions,)
    queryset = models.Project.objects.all()
    serializer_class = serializers.ProjectSerializer
