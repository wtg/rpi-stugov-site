from django.urls import path

from . import views

app_name = "front_door"

urlpatterns = [
    path("", views.home, name="home"),
    path("raise-an-issue/", views.issue_index, name="issue_index"),
    path("raise-an-issue/<slug:topic>/", views.issue_topic, name="issue_topic"),
    path("your-reps/", views.reps, name="reps_index"),
    path("your-reps/<slug:key>/", views.reps, name="reps"),
    path("meetings/", views.meetings, name="meetings"),
    path("meetings/<slug:body>/<slug:term>/<int:number>/", views.meeting, name="meeting"),
    path("funding/", views.funding, name="funding"),
    path("take-part/", views.take_part, name="take_part"),
    path("about/", views.about, name="about"),
]
