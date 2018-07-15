from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from todo.core import views

urlpatterns = [
    path("", views.About.as_view(), name="about"),
    path("today", views.Today.as_view(), name="today"),
    path("upcoming", views.Upcoming.as_view(), name="upcoming"),
    path("project/", views.Inbox.as_view(), name="inbox"),
    path("project/<uuid>", views.Project.as_view(), name="project"),
    path("task/<uuid>", views.Task.as_view(), name="task"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))
