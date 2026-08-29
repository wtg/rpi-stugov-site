import logging
from collections.abc import Sequence

from allauth.account.models import EmailAddress
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ImproperlyConfigured, PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.shortcuts import render

from .oidc import claim_at_path, merged_claims


logger = logging.getLogger(__name__)
MANAGED_GROUPS = frozenset({"Editors", "Moderators"})


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
        if not user.is_active or user.is_staff or user.is_superuser:
            raise PermissionDenied("OIDC cannot link to this local account")
        return user, email

    def pre_social_login(self, request, sociallogin):
        if sociallogin.account.provider != settings.OIDC_PROVIDER_ID:
            self._deny(request)

        claims = merged_claims(sociallogin.account.extra_data)
        email = self._validated_email(claims)
        if not email:
            self._deny(request)
        target_groups = self._target_groups(claims)

        if not target_groups:
            # Revoke only identities already bound by provider + sub. A first
            # rejected login must not mutate an unrelated email-matched user.
            if sociallogin.account.pk and sociallogin.user and sociallogin.user.pk:
                self._sync_groups(sociallogin.user, set())
            self._deny(request)

        user = sociallogin.user
        if user and user.pk:
            if not user.is_active or user.is_staff or user.is_superuser:
                self._deny(request)
            if self._email_conflicts(user, email):
                self._deny(request)

            # Passwords remain exclusively for unlinked break-glass staff.
            if not sociallogin.account.pk:
                user.set_unusable_password()
            self._sync_existing_user(user, claims, email, target_groups)

        # Mark the single trusted campus email as verified before allauth
        # persists a new user or attaches a SocialAccount.
        for address in sociallogin.email_addresses:
            address.verified = bool(address.email and address.email.lower() == email)

    def save_user(self, request, sociallogin, form=None):
        claims = merged_claims(sociallogin.account.extra_data)
        email = self._validated_email(claims)
        if not email:
            self._deny(request)
        target_groups = self._target_groups(claims)
        if not target_groups:
            self._deny(request)

        with transaction.atomic():
            user = super().save_user(request, sociallogin, form=form)
            user.is_active = True
            user.is_staff = False
            user.is_superuser = False
            user.set_unusable_password()
            self._apply_profile(user, claims, email)
            user.save()
            self._ensure_primary_email(user, email)
            self._sync_groups(user, target_groups)
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

    def _target_groups(self, claims):
        roles = claim_at_path(claims, settings.OIDC_ROLE_CLAIM_PATH)
        if (
            not isinstance(roles, Sequence)
            or isinstance(roles, (str, bytes))
            or any(not isinstance(role, str) for role in roles)
        ):
            return set()

        role_values = set(roles)
        groups = set()
        if role_values.intersection(settings.OIDC_EDITOR_ROLES):
            groups.add("Editors")
        if role_values.intersection(settings.OIDC_MODERATOR_ROLES):
            groups.add("Moderators")
        return groups

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

    def _sync_existing_user(self, user, claims, email, target_groups):
        with transaction.atomic():
            self._apply_profile(user, claims, email)
            user.save()
            self._ensure_primary_email(user, email)
            self._sync_groups(user, target_groups)

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

    def _sync_groups(self, user, target_groups):
        groups = {
            group.name: group
            for group in Group.objects.filter(name__in=MANAGED_GROUPS)
        }
        missing = MANAGED_GROUPS.difference(groups)
        if missing:
            raise ImproperlyConfigured(
                "Missing Wagtail SSO groups: " + ", ".join(sorted(missing))
            )

        user.groups.remove(*(groups[name] for name in MANAGED_GROUPS))
        user.groups.add(*(groups[name] for name in target_groups))

    def _deny(self, request):
        raise ImmediateHttpResponse(
            render(request, "sso/access_denied.html", status=403)
        )
