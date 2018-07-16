from rest_framework import serializers
from todo.core import models


class TaskSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")
    external = serializers.ReadOnlyField(source="external.url")

    class Meta:
        model = models.Task
        fields = "__all__"
        read_only_fields = ("owner",)


class ProjectSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.username")

    class Meta:
        model = models.Project
        fields = "__all__"
        read_only_fields = ("owner",)
