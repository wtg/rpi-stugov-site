from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("meetings/", views.meetings, name="meetings"),
    path("meetings/<slug:body>/<slug:term>/<int:number>/", views.meeting, name="meeting"),
    path("decisions/", views.decisions, name="decisions"),
    path("decisions/<slug:id>/", views.decision, name="decision"),
    path("money/", views.money, name="money"),
    path("rules/", views.rules, name="rules"),
    path("desk/", views.desk, name="desk"),
    path("desk/health/", views.health, name="health"),
]
