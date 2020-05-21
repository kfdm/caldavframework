from . import views

from django.urls import path

urlpatterns = [
    path(".well-known/caldav", views.WellKnownCaldav.as_view()),
    path("z/discovery", views.UserPrincipalDiscovery.as_view(), name="discovery"),
    path("u/<user>/", views.RootCollection.as_view(), name="principal"),
    path("u/<user>/<calendar>/", views.Calendar.as_view(), name="calendar"),
    path("u/<user>/<calendar>/<task>.ics", views.Task.as_view(), name="task"),
]
