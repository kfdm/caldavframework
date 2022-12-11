"""todo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from ..example import caldav, views

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Caldav views
    path(".well-known/caldav", caldav.WellKnownCaldav.as_view()),
    path("z/discovery", caldav.UserPrincipalDiscovery.as_view(), name="discovery"),
    path("u/<user>/", caldav.RootCollection.as_view(), name="principal"),
    path("u/<user>/<calendar>/", caldav.Calendar.as_view(), name="calendar"),
    path("u/<user>/<calendar>/<task>.ics", caldav.Task.as_view(), name="task"),
    # Others
    path("", views.Home.as_view(), name="home"),
    path("calendar", views.CalendarList.as_view(), name="calendar-list"),
    path("calendar/<uuid:calendar>/new", views.TaskCreate.as_view(), name="todo-create"),
    path("calendar/<uuid:calendar>/<uuid:pk>.ics", views.TaskDetail.as_view(), name="todo-detail"),
    path("calendar/<uuid:calendar>/<uuid:pk>/update", views.TaskUpdate.as_view(), name="todo-update"),
    path("calendar/<uuid:pk>/toggle", views.CalendarToggle.as_view(), name="calendar-toggle"),
    path("calendar/<uuid:pk>/update", views.CalendarUpdate.as_view(), name="calendar-update"),
    path("calendar/<uuid:pk>", views.CalendarDetail.as_view(), name="calendar-detail"),
    path("accounts/", include(("django.contrib.auth.urls", "auth"), "auth")),
    path("admin/", admin.site.urls),
]
