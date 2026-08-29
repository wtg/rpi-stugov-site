from django.urls import path

from .views import oidc_logout


urlpatterns = [
    path("admin/logout/", oidc_logout, name="sso_logout"),
]
