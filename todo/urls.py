from . import views

from django.urls import path

urlpatterns = [
    path(".well-known/caldav", views.WellKnownCaldav.as_view()),
    path("test/discovery", views.UserPrincipalDiscovery.as_view(), name="discovery"),
    path("test/directory/<user>/", views.RootCollection.as_view(), name="principal"),
    path("test/directory/<user>/<calendar>/", views.Calendar.as_view(), name="calendar"),
]
