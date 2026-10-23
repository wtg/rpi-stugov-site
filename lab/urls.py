from django.urls import include, path

from . import views
from .prototypes import discover

app_name = "lab"

urlpatterns = [path("", views.index, name="index")]

for prototype in discover():
    urlpatterns.append(
        path(
            f"{prototype['slug']}/",
            include((f"lab.prototypes.{prototype['module']}.urls", prototype["module"])),
        )
    )
