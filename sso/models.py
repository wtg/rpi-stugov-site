from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import Group
from django.db import models
from wagtail.admin.panels import FieldPanel, MultiFieldPanel


class OIDCGroupMapping(models.Model):
    """Map one exact OIDC group claim to Wagtail authorization."""

    claim_value = models.CharField(
        max_length=255,
        unique=True,
        help_text=(
            "Exact, case-sensitive value from the configured OIDC group claim, "
            "for example organization.1.member."
        ),
    )
    wagtail_groups = models.ManyToManyField(
        Group,
        blank=True,
        related_name="+",
        help_text=(
            "Wagtail/Django groups granted while this claim is present. "
            "Memberships granted here are synchronized at each SSO login."
        ),
    )
    grants_wagtail_admin = models.BooleanField(
        default=False,
        help_text=(
            "Grant full Wagtail permissions without granting access to "
            "Django admin."
        ),
    )
    enabled = models.BooleanField(
        default=True,
        help_text="Disabled mappings grant no access and are revoked at next login.",
    )

    panels = [
        FieldPanel("claim_value"),
        MultiFieldPanel(
            [
                FieldPanel("wagtail_groups"),
                FieldPanel("grants_wagtail_admin"),
            ],
            heading="Wagtail access",
        ),
        FieldPanel("enabled"),
    ]

    class Meta:
        ordering = ["claim_value"]
        verbose_name = "OIDC group mapping"
        verbose_name_plural = "OIDC group mappings"

    def __str__(self):
        return self.claim_value

    @admin.display(description="Wagtail groups")
    def mapped_group_names(self):
        names = self.wagtail_groups.order_by("name").values_list("name", flat=True)
        return ", ".join(names) or "—"


class OIDCManagedGroupMembership(models.Model):
    """Track memberships granted by OIDC so unrelated groups remain untouched."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="oidc_managed_group_memberships",
    )
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="+")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "group"],
                name="unique_oidc_managed_group_membership",
            )
        ]
        default_permissions = ()

