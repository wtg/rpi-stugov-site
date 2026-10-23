from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("reps/<slug:key>/", views.reps, name="reps"),
    path("people/", views.people, name="people"),
    path("people/<slug:slug>/", views.person, name="person"),
    path("raise/", views.raise_issue, name="raise"),
    path("you-said-we-did/", views.loop, name="loop"),
    path("how-it-works/", views.how, name="how"),
]
