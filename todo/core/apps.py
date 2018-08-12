from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "todo.core"

    def ready(self):
        from todo.core import signals
