from . import caldav

from django.urls import path

urlpatterns = [
    path(".well-known/caldav", caldav.WellKnownCaldav.as_view()),
    path("z/discovery", caldav.UserPrincipalDiscovery.as_view(), name="discovery"),
    path("u/<user>/", caldav.RootCollection.as_view(), name="principal"),
    path("u/<user>/<calendar>/", caldav.Calendar.as_view(), name="calendar"),
    path("u/<user>/<calendar>/<task>.ics", caldav.Task.as_view(), name="task"),
]
