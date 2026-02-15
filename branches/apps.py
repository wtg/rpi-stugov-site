from django.apps import AppConfig


class BranchesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "branches"
    # Shows as "Government Branches" in the Django admin rather than "Branches"
    verbose_name = "Government Branches"
