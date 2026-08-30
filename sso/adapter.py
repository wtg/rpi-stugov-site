import logging
from collections.abc import Sequence

from allauth.account.models import EmailAddress
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.shortcuts import render

from .models import OIDCGroupMapping, OIDCManagedGroupMembership
from .oidc import claim_at_path, merged_claims


logger = logging.getLogger(__name__)


class CampusSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Apply the campus identity and Wagtail authorization policy."""

    def authenticate_by_email(self, sociallogin):
        if sociallogin.account.provider != settings.OIDC_PROVIDER_ID:
            return super().authenticate_by_email(sociallogin)

        emails = {
            address.email.strip().lower()
            for address in sociallogin.email_addresses
            if address.verified and address.email
        }
        if len(emails) != 1:
            if len(emails) > 1:
                raise PermissionDenied("OIDC identity returned ambiguous email claims")
            return None

        email = emails.pop()
        if not self.can_authenticate_by_email(sociallogin, email):
            return None

        users = list(get_user_model().objects.filter(email__iexact=email)[:2])
        if not users:
            return None
        if len(users) != 1:
            raise PermissionDenied("Multiple local accounts use the OIDC email")

        user = users[0]
        account_is_linked = bool(
            sociallogin.account.pk and sociallogin.account.user_id == user.pk
        )
        if (
            not user.is_active
            or user.is_staff
            or (user.is_superuser and not account_is_linked)
        ):
            raise PermissionDenied("OIDC cannot link to this local account")
        return user, email

    def pre_social_login(self, request, sociallogin):
        if sociallogin.account.provider != settings.OIDC_PROVIDER_ID:
            self._deny(request)

        claims = merged_claims(sociallogin.account.extra_data)
        email = self._validated_email(claims)
        if not email:
            self._deny(request)
        target_groups, is_admin = self._target_access(claims)

        if not target_groups and not is_admin:
            # Revoke only identities already bound by provider + sub. A first
            # rejected login must not mutate an unrelated email-matched user.
            if (
                sociallogin.account.pk
                and sociallogin.user
                and sociallogin.user.pk
                and not sociallogin.user.is_staff
            ):
                self._sync_authorization(sociallogin.user, set(), is_admin=False)
            self._deny(request)

        user = sociallogin.user
        if user and user.pk:
            account_is_linked = bool(
                sociallogin.account.pk and sociallogin.account.user_id == user.pk
            )
            if (
                not user.is_active
                or user.is_staff
                or (user.is_superuser and not account_is_linked)
            ):
                self._deny(request)
            if self._email_conflicts(user, email):
                self._deny(request)

            # Passwords remain exclusively for unlinked break-glass staff.
            if not sociallogin.account.pk:
                user.set_unusable_password()
            self._sync_existing_user(
                user, claims, email, target_groups, is_admin=is_admin
            )

        # Mark the single trusted campus email as verified before allauth
        # persists a new user or attaches a SocialAccount.
        for address in sociallogin.email_addresses:
            address.verified = bool(address.email and address.email.lower() == email)

    def save_user(self, request, sociallogin, form=None):
        claims = merged_claims(sociallogin.account.extra_data)
        email = self._validated_email(claims)
        if not email:
            self._deny(request)
        target_groups, is_admin = self._target_access(claims)
        if not target_groups and not is_admin:
            self._deny(request)

        with transaction.atomic():
            user = super().save_user(request, sociallogin, form=form)
            user.is_active = True
            user.is_staff = False
            user.is_superuser = is_admin
            user.set_unusable_password()
            self._apply_profile(user, claims, email)
            user.save()
            self._ensure_primary_email(user, email)
            self._sync_authorization(user, target_groups, is_admin=is_admin)
        return user

    def on_authentication_error(
        self,
        request,
        provider,
        error=None,
        exception=None,
        extra_context=None,
    ):
        logger.warning("CMS authentication failed", exc_info=exception)
        raise ImmediateHttpResponse(
            render(request, "sso/authentication_error.html", status=401)
        )

    def _validated_email(self, claims):
        email = claims.get("email")
        if not isinstance(email, str) or "@" not in email:
            return ""
        email = email.strip().lower()
        try:
            validate_email(email)
        except ValidationError:
            return ""
        return email

    def _target_access(self, claims):
        roles = claim_at_path(claims, settings.OIDC_ROLE_CLAIM_PATH)
        if (
            not isinstance(roles, Sequence)
            or isinstance(roles, (str, bytes))
            or any(not isinstance(role, str) for role in roles)
        ):
            return set(), False

        role_values = set(roles)
        mappings = OIDCGroupMapping.objects.filter(
            enabled=True,
            claim_value__in=role_values,
        ).prefetch_related("wagtail_groups")
        groups = {
            group
            for mapping in mappings
            for group in mapping.wagtail_groups.all()
        }
        is_admin = any(mapping.grants_wagtail_admin for mapping in mappings)
        return groups, is_admin

    def _email_conflicts(self, user, email):
        if not email:
            return True
        User = get_user_model()
        return (
            User.objects.filter(email__iexact=email).exclude(pk=user.pk).exists()
            or EmailAddress.objects.filter(email__iexact=email)
            .exclude(user=user)
            .exists()
        )

    def _sync_existing_user(self, user, claims, email, target_groups, *, is_admin):
        with transaction.atomic():
            self._apply_profile(user, claims, email)
            user.save()
            self._ensure_primary_email(user, email)
            self._sync_authorization(user, target_groups, is_admin=is_admin)

    def _apply_profile(self, user, claims, email):
        user.email = email
        for field_name, claim_name in (
            ("first_name", "given_name"),
            ("last_name", "family_name"),
        ):
            value = claims.get(claim_name)
            if isinstance(value, str):
                field = user._meta.get_field(field_name)
                setattr(user, field_name, value.strip()[: field.max_length])

    def _ensure_primary_email(self, user, email):
        EmailAddress.objects.filter(user=user).exclude(email__iexact=email).update(
            primary=False
        )
        address, _ = EmailAddress.objects.update_or_create(
            user=user,
            email=email,
            defaults={"verified": True, "primary": True},
        )
        if not address.verified or not address.primary:
            address.verified = True
            address.primary = True
            address.save(update_fields=["verified", "primary"])

    def _sync_managed_groups(self, user, target_groups):
        target_group_ids = {group.pk for group in target_groups}
        tracked_memberships = list(
            OIDCManagedGroupMembership.objects.filter(user=user)
        )
        tracked_group_ids = {
            membership.group_id for membership in tracked_memberships
        }

        stale_group_ids = tracked_group_ids.difference(target_group_ids)
        if stale_group_ids:
            user.groups.remove(*stale_group_ids)
            OIDCManagedGroupMembership.objects.filter(
                user=user,
                group_id__in=stale_group_ids,
            ).delete()

        if target_group_ids:
            user.groups.add(*target_group_ids)
            OIDCManagedGroupMembership.objects.bulk_create(
                [
                    OIDCManagedGroupMembership(user=user, group_id=group_id)
                    for group_id in target_group_ids.difference(tracked_group_ids)
                ],
                ignore_conflicts=True,
            )

    def _sync_authorization(self, user, target_groups, *, is_admin):
        with transaction.atomic():
            self._sync_managed_groups(user, target_groups)
            update_fields = []
            if user.is_superuser != is_admin:
                user.is_superuser = is_admin
                update_fields.append("is_superuser")
            if user.is_staff:
                # SSO administrators are deliberately excluded from Django admin.
                user.is_staff = False
                update_fields.append("is_staff")
            if update_fields:
                user.save(update_fields=update_fields)

    def _deny(self, request):
        raise ImmediateHttpResponse(
            render(request, "sso/access_denied.html", status=403)
        )
