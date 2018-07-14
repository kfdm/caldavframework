from django.contrib import admin
from django.urls import path, include

from todo.core import views

urlpatterns = [
    path("", views.About.as_view(), name="about"),
    path("project/", views.Inbox.as_view(), name="inbox"),
    path("project/<uuid>", views.Project.as_view(), name="project"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
]
