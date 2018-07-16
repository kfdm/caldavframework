from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from rest_framework import routers
from todo.core import rest, views

router = routers.DefaultRouter(trailing_slash=False)
router.register("task", rest.TaskViewSet)
router.register("project", rest.ProjectViewSet)

urlpatterns = [
    path("", views.About.as_view(), name="about"),
    path("today", views.Today.as_view(), name="today"),
    path("upcoming", views.Upcoming.as_view(), name="upcoming"),
    path("project/", views.Inbox.as_view(), name="inbox"),
    path("project/<uuid>", views.Project.as_view(), name="project"),
    path("task/<uuid>", views.Task.as_view(), name="task"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("api/", include((router.urls, "api"))),
]

if settings.DEBUG:
    try:
        import debug_toolbar

        urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))
    except ImportError:
        pass
