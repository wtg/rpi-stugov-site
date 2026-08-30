import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


SEEDED_MAPPINGS = (
    ("organization.1.member", "Editors", False),
    ("organization.1.officer", "Moderators", False),
    ("organization.408.tag.President", None, True),
)


def seed_oidc_mappings(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    OIDCGroupMapping = apps.get_model("sso", "OIDCGroupMapping")
    OIDCManagedGroupMembership = apps.get_model(
        "sso", "OIDCManagedGroupMembership"
    )
    SocialAccount = apps.get_model("socialaccount", "SocialAccount")
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))

    seeded_group_ids = []
    for claim_value, group_name, grants_wagtail_admin in SEEDED_MAPPINGS:
        mapping, _ = OIDCGroupMapping.objects.update_or_create(
            claim_value=claim_value,
            defaults={
                "enabled": True,
                "grants_wagtail_admin": grants_wagtail_admin,
            },
        )
        if group_name:
            group, _ = Group.objects.get_or_create(name=group_name)
            mapping.wagtail_groups.add(group)
            seeded_group_ids.append(group.pk)

    # Editors and Moderators assigned by the previous environment-based SSO
    # mapper need tracking rows so future logins can revoke them correctly.
    linked_user_ids = SocialAccount.objects.filter(provider="campus").values_list(
        "user_id", flat=True
    )
    existing_memberships = User.groups.through.objects.filter(
        user_id__in=linked_user_ids,
        group_id__in=seeded_group_ids,
    ).values_list("user_id", "group_id")
    OIDCManagedGroupMembership.objects.bulk_create(
        [
            OIDCManagedGroupMembership(user_id=user_id, group_id=group_id)
            for user_id, group_id in existing_memberships
        ],
        ignore_conflicts=True,
    )


def remove_seeded_oidc_mappings(apps, schema_editor):
    OIDCGroupMapping = apps.get_model("sso", "OIDCGroupMapping")
    OIDCGroupMapping.objects.filter(
        claim_value__in=[mapping[0] for mapping in SEEDED_MAPPINGS]
    ).delete()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("socialaccount", "0006_alter_socialaccount_extra_data"),
    ]

    operations = [
        migrations.CreateModel(
            name="OIDCGroupMapping",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "claim_value",
                    models.CharField(
                        help_text=(
                            "Exact, case-sensitive value from the configured OIDC "
                            "group claim, for example organization.1.member."
                        ),
                        max_length=255,
                        unique=True,
                    ),
                ),
                (
                    "grants_wagtail_admin",
                    models.BooleanField(
                        default=False,
                        help_text=(
                            "Grant full Wagtail permissions without granting access "
                            "to Django admin."
                        ),
                    ),
                ),
                (
                    "enabled",
                    models.BooleanField(
                        default=True,
                        help_text=(
                            "Disabled mappings grant no access and are revoked at "
                            "next login."
                        ),
                    ),
                ),
                (
                    "wagtail_groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text=(
                            "Wagtail/Django groups granted while this claim is "
                            "present. Memberships granted here are synchronized at "
                            "each SSO login."
                        ),
                        related_name="+",
                        to="auth.group",
                    ),
                ),
            ],
            options={
                "verbose_name": "OIDC group mapping",
                "verbose_name_plural": "OIDC group mappings",
                "ordering": ["claim_value"],
            },
        ),
        migrations.CreateModel(
            name="OIDCManagedGroupMembership",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="auth.group",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="oidc_managed_group_memberships",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"default_permissions": ()},
        ),
        migrations.AddConstraint(
            model_name="oidcmanagedgroupmembership",
            constraint=models.UniqueConstraint(
                fields=("user", "group"),
                name="unique_oidc_managed_group_membership",
            ),
        ),
        migrations.RunPython(
            seed_oidc_mappings,
            reverse_code=remove_seeded_oidc_mappings,
        ),
    ]
