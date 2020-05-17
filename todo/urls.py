from . import views

from django.urls import path

urlpatterns = [
    path(".well-known/caldav", views.WellKnownCaldav.as_view()),
    path("test/discovery", views.Discovery.as_view(), name="discovery"),
    path("test/directory/<user>/", views.Principal.as_view(), name="principal"),
]
