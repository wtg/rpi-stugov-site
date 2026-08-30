from importlib import import_module
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock, patch
from urllib.parse import parse_qs, urlsplit

from allauth.account.models import EmailAddress
from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.models import SocialAccount, SocialLogin
from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from wagtail.snippets.models import get_snippet_models

from .adapter import CampusSocialAccountAdapter
from .models import OIDCGroupMapping, OIDCManagedGroupMembership
from .oidc import append_query_parameters, claim_at_path, discovery_url, merged_claims


OIDC_SETTINGS = {
    "OIDC_PROVIDER_ID": "campus",
    "OIDC_ROLE_CLAIM_PATH": "realm_access.roles",
    "SOCIALACCOUNT_EMAIL_AUTHENTICATION": True,
}

PROVIDER_SETTINGS = {
    "openid_connect": {
        "APPS": [
            {
                "provider_id": "campus",
                "name": "CMS",
                "client_id": "test-client",
                "secret": "test-secret",
                "settings": {
                    "server_url": "https://idp.example.edu",
                    "scope": ("openid", "profile", "email"),
                    "oauth_pkce_enabled": True,
                    "verified_email": True,
                    "email_authentication": True,
                },
            }
        ]
    }
}


class OIDCHelperTests(SimpleTestCase):
    def test_discovery_url_accepts_issuer_or_explicit_metadata_url(self):
        self.assertEqual(
            discovery_url("https://idp.example.edu"),
            "https://idp.example.edu/.well-known/openid-configuration",
        )
        explicit = "https://idp.example.edu/.well-known/custom-configuration"
        self.assertEqual(discovery_url(explicit), explicit)

    def test_userinfo_claims_override_id_token_claims(self):
        claims = merged_claims(
            {
                "id_token": {"email": "old@example.edu", "sub": "123"},
                "userinfo": {"email": "new@example.edu"},
            }
        )
        self.assertEqual(claims, {"email": "new@example.edu", "sub": "123"})

    def test_nested_claim_path(self):
        claims = {"realm_access": {"roles": ["site-editor"]}}
        self.assertEqual(
            claim_at_path(claims, "realm_access.roles"), ["site-editor"]
        )
        self.assertIsNone(claim_at_path(claims, "missing.roles"))

    def test_logout_parameters_preserve_existing_query(self):
        url = append_query_parameters(
            "https://idp.example.edu/logout?source=wagtail",
            {
                "client_id": "site",
                "post_logout_redirect_uri": "https://sg.example.edu/",
            },
        )
        self.assertIn("source=wagtail", url)
        self.assertIn("client_id=site", url)
        self.assertIn(
            "post_logout_redirect_uri=https%3A%2F%2Fsg.example.edu%2F", url
        )


class OIDCMappingConfigurationTests(TestCase):
    def test_initial_mappings_match_current_cms_policy(self):
        expected = {
            "organization.1.member": ({"Editors"}, False),
            "organization.1.officer": ({"Moderators"}, False),
            "organization.408.tag.President": (set(), True),
        }

        for claim_value, (group_names, grants_admin) in expected.items():
            with self.subTest(claim_value=claim_value):
                mapping = OIDCGroupMapping.objects.get(claim_value=claim_value)
                self.assertTrue(mapping.enabled)
                self.assertEqual(mapping.grants_wagtail_admin, grants_admin)
                self.assertEqual(
                    set(mapping.wagtail_groups.values_list("name", flat=True)),
                    group_names,
                )

    def test_mapping_is_registered_as_a_wagtail_snippet(self):
        self.assertIn(OIDCGroupMapping, get_snippet_models())

    def test_initial_migration_backfills_previously_managed_memberships(self):
        user = get_user_model().objects.create_user(
            username="existing-sso-user",
            email="existing@example.edu",
        )
        editors = Group.objects.get(name="Editors")
        user.groups.add(editors)
        SocialAccount.objects.create(
            user=user,
            provider="campus",
            uid="existing-campus-user",
        )
        OIDCManagedGroupMembership.objects.filter(user=user).delete()
        migration = import_module("sso.migrations.0001_initial")

        migration.seed_oidc_mappings(apps, schema_editor=None)

        self.assertTrue(
            OIDCManagedGroupMembership.objects.filter(
                user=user,
                group=editors,
            ).exists()
        )

    def test_wagtail_only_superuser_can_manage_mappings(self):
        user = get_user_model().objects.create_user(
            username="oidc-admin",
            email="admin@example.edu",
            is_superuser=True,
            is_staff=False,
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse(f"{OIDCGroupMapping.snippet_viewset.url_namespace}:list")
        )

        self.assertEqual(response.status_code, 200)

    def test_editor_cannot_manage_mappings(self):
        user = get_user_model().objects.create_user(
            username="editor",
            email="editor@example.edu",
        )
        user.groups.add(Group.objects.get(name="Editors"))
        self.client.force_login(user)

        self.assertFalse(user.has_perm("sso.change_oidcgroupmapping"))
        response = self.client.get(
            reverse(f"{OIDCGroupMapping.snippet_viewset.url_namespace}:list")
        )
        self.assertNotEqual(response.status_code, 200)


@override_settings(**OIDC_SETTINGS)
class CampusAdapterTests(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/accounts/oidc/campus/login/callback/")
        SessionMiddleware(lambda request: None).process_request(self.request)
        self.request.session.save()
        self.adapter = CampusSocialAccountAdapter(self.request)
        self.editors, _ = Group.objects.get_or_create(name="Editors")
        self.moderators, _ = Group.objects.get_or_create(name="Moderators")
        editor_mapping, _ = OIDCGroupMapping.objects.update_or_create(
            claim_value="site-editor",
            defaults={"enabled": True, "grants_wagtail_admin": False},
        )
        editor_mapping.wagtail_groups.set([self.editors])
        moderator_mapping, _ = OIDCGroupMapping.objects.update_or_create(
            claim_value="site-moderator",
            defaults={"enabled": True, "grants_wagtail_admin": False},
        )
        moderator_mapping.wagtail_groups.set([self.moderators])

    def sociallogin(self, claims, *, user=None, saved_account=False, uid="campus-123"):
        if user is None:
            user = get_user_model()(
                username="student",
                email=claims.get("email", ""),
            )
        account = SocialAccount(
            user=user,
            provider="campus",
            uid=uid,
            extra_data={"userinfo": claims},
        )
        if saved_account:
            account.save()
        email = claims.get("email")
        addresses = (
            [EmailAddress(email=email, verified=True, primary=True)] if email else []
        )
        login = SocialLogin(user=user, account=account, email_addresses=addresses)
        login.provider = SimpleNamespace(app=None, get_settings=lambda: {})
        return login

    def claims(self, *roles, email="student@example.edu"):
        return {
            "sub": "campus-123",
            "email": email,
            "given_name": "Campus",
            "family_name": "Student",
            "realm_access": {"roles": list(roles)},
        }

    def test_new_editor_is_created_without_django_admin_access(self):
        login = self.sociallogin(self.claims("site-editor"))

        self.adapter.pre_social_login(self.request, login)
        user = self.adapter.save_user(self.request, login)

        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.has_usable_password())
        self.assertEqual(user.first_name, "Campus")
        self.assertEqual(user.last_name, "Student")
        self.assertEqual(set(user.groups.values_list("name", flat=True)), {"Editors"})
        self.assertTrue(
            OIDCManagedGroupMembership.objects.filter(
                user=user,
                group=self.editors,
            ).exists()
        )
        self.assertTrue(
            EmailAddress.objects.get(user=user, email="student@example.edu").verified
        )
        self.assertTrue(
            SocialAccount.objects.filter(
                user=user, provider="campus", uid="campus-123"
            ).exists()
        )

    def test_combined_roles_receive_both_managed_groups(self):
        login = self.sociallogin(self.claims("site-editor", "site-moderator"))

        self.adapter.pre_social_login(self.request, login)
        user = self.adapter.save_user(self.request, login)

        self.assertEqual(
            set(user.groups.values_list("name", flat=True)),
            {"Editors", "Moderators"},
        )

    def test_president_is_created_as_wagtail_only_superuser(self):
        login = self.sociallogin(self.claims("organization.408.tag.President"))

        self.adapter.pre_social_login(self.request, login)
        user = self.adapter.save_user(self.request, login)

        self.assertTrue(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.has_perm("wagtailadmin.access_admin"))
        self.assertEqual(set(user.groups.values_list("name", flat=True)), set())

    def test_admin_role_matching_is_case_sensitive(self):
        login = self.sociallogin(self.claims("organization.408.tag.president"))

        with self.assertRaises(ImmediateHttpResponse) as raised:
            self.adapter.pre_social_login(self.request, login)

        self.assertEqual(raised.exception.response.status_code, 403)

    def test_disabled_mapping_grants_no_access(self):
        OIDCGroupMapping.objects.filter(claim_value="site-editor").update(
            enabled=False
        )
        login = self.sociallogin(self.claims("site-editor"))

        with self.assertRaises(ImmediateHttpResponse) as raised:
            self.adapter.pre_social_login(self.request, login)

        self.assertEqual(raised.exception.response.status_code, 403)

    def test_mapping_can_grant_an_arbitrary_wagtail_group(self):
        reviewers = Group.objects.create(name="Reviewers")
        mapping = OIDCGroupMapping.objects.create(claim_value="site-reviewer")
        mapping.wagtail_groups.add(reviewers)
        login = self.sociallogin(self.claims("site-reviewer"))

        self.adapter.pre_social_login(self.request, login)
        user = self.adapter.save_user(self.request, login)

        self.assertEqual(
            set(user.groups.values_list("name", flat=True)), {"Reviewers"}
        )
        self.assertTrue(
            OIDCManagedGroupMembership.objects.filter(
                user=user,
                group=reviewers,
            ).exists()
        )

    def test_mapping_edit_replaces_only_previously_managed_groups(self):
        user = get_user_model().objects.create_user(
            username="existing",
            email="student@example.edu",
        )
        unrelated = Group.objects.create(name="Unrelated")
        reviewers = Group.objects.create(name="Reviewers")
        user.groups.add(self.editors, unrelated)
        OIDCManagedGroupMembership.objects.create(user=user, group=self.editors)
        OIDCGroupMapping.objects.get(claim_value="site-editor").wagtail_groups.set(
            [reviewers]
        )
        login = self.sociallogin(
            self.claims("site-editor"), user=user, saved_account=True
        )

        self.adapter.pre_social_login(self.request, login)

        self.assertEqual(
            set(user.groups.values_list("name", flat=True)),
            {"Reviewers", "Unrelated"},
        )
        self.assertEqual(
            set(
                OIDCManagedGroupMembership.objects.filter(user=user).values_list(
                    "group__name", flat=True
                )
            ),
            {"Reviewers"},
        )

    def test_existing_linked_president_can_log_in_repeatedly(self):
        user = get_user_model().objects.create_user(
            username="president",
            email="student@example.edu",
            is_superuser=True,
            is_staff=False,
        )
        login = self.sociallogin(
            self.claims("organization.408.tag.President"),
            user=user,
            saved_account=True,
        )

        self.adapter.pre_social_login(self.request, login)
        user.refresh_from_db()

        self.assertTrue(user.is_superuser)
        self.assertFalse(user.is_staff)

    def test_president_keeps_independently_mapped_groups(self):
        login = self.sociallogin(
            self.claims(
                "site-editor",
                "site-moderator",
                "organization.408.tag.President",
            )
        )

        self.adapter.pre_social_login(self.request, login)
        user = self.adapter.save_user(self.request, login)

        self.assertTrue(user.is_superuser)
        self.assertEqual(
            set(user.groups.values_list("name", flat=True)),
            {"Editors", "Moderators"},
        )

    def test_president_role_removal_downgrades_to_moderator(self):
        user = get_user_model().objects.create_user(
            username="president",
            email="student@example.edu",
            is_superuser=True,
            is_staff=False,
        )
        login = self.sociallogin(
            self.claims("site-moderator"), user=user, saved_account=True
        )

        self.adapter.pre_social_login(self.request, login)
        user.refresh_from_db()

        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertEqual(
            set(user.groups.values_list("name", flat=True)), {"Moderators"}
        )

    def test_existing_linked_user_roles_are_authoritatively_synchronized(self):
        user = get_user_model().objects.create_user(
            username="existing", email="student@example.edu"
        )
        unrelated = Group.objects.create(name="Unrelated")
        user.groups.add(self.editors, unrelated)
        OIDCManagedGroupMembership.objects.create(user=user, group=self.editors)
        login = self.sociallogin(
            self.claims("site-moderator"), user=user, saved_account=True
        )

        self.adapter.pre_social_login(self.request, login)

        self.assertEqual(
            set(user.groups.values_list("name", flat=True)),
            {"Moderators", "Unrelated"},
        )

    def test_role_removal_revokes_managed_groups_and_denies_login(self):
        user = get_user_model().objects.create_user(
            username="existing", email="student@example.edu"
        )
        unrelated = Group.objects.create(name="Unrelated")
        user.groups.add(self.editors, self.moderators, unrelated)
        OIDCManagedGroupMembership.objects.bulk_create(
            [
                OIDCManagedGroupMembership(user=user, group=self.editors),
                OIDCManagedGroupMembership(user=user, group=self.moderators),
            ]
        )
        login = self.sociallogin(self.claims(), user=user, saved_account=True)

        with self.assertRaises(ImmediateHttpResponse) as raised:
            self.adapter.pre_social_login(self.request, login)

        self.assertEqual(raised.exception.response.status_code, 403)
        self.assertEqual(
            set(user.groups.values_list("name", flat=True)), {"Unrelated"}
        )

    def test_role_removal_revokes_linked_president_and_denies_login(self):
        user = get_user_model().objects.create_user(
            username="president",
            email="student@example.edu",
            is_superuser=True,
            is_staff=False,
        )
        user.groups.add(self.editors)
        OIDCManagedGroupMembership.objects.create(user=user, group=self.editors)
        login = self.sociallogin(self.claims(), user=user, saved_account=True)

        with self.assertRaises(ImmediateHttpResponse) as raised:
            self.adapter.pre_social_login(self.request, login)

        user.refresh_from_db()
        self.assertEqual(raised.exception.response.status_code, 403)
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertEqual(set(user.groups.values_list("name", flat=True)), set())

    def test_denied_linked_break_glass_account_is_not_mutated(self):
        user = get_user_model().objects.create_user(
            username="break-glass",
            email="student@example.edu",
            is_superuser=True,
            is_staff=True,
        )
        user.groups.add(self.editors)
        login = self.sociallogin(self.claims(), user=user, saved_account=True)

        with self.assertRaises(ImmediateHttpResponse):
            self.adapter.pre_social_login(self.request, login)

        user.refresh_from_db()
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertEqual(
            set(user.groups.values_list("name", flat=True)), {"Editors"}
        )

    def test_missing_email_or_malformed_role_claim_is_denied(self):
        missing_email = self.sociallogin(self.claims("site-editor", email=""))
        malformed_roles = self.claims("site-editor")
        malformed_roles["realm_access"]["roles"] = "site-editor"

        for login in (missing_email, self.sociallogin(malformed_roles)):
            with self.subTest(extra_data=login.account.extra_data):
                with self.assertRaises(ImmediateHttpResponse) as raised:
                    self.adapter.pre_social_login(self.request, login)
                self.assertEqual(raised.exception.response.status_code, 403)

    def test_unique_active_non_staff_user_can_link_by_trusted_email(self):
        user = get_user_model().objects.create_user(
            username="existing", email="Student@Example.edu"
        )
        login = self.sociallogin(self.claims("site-editor"))

        matched_user, email = self.adapter.authenticate_by_email(login)

        self.assertEqual(matched_user, user)
        self.assertEqual(email, "student@example.edu")

    def test_staff_superuser_inactive_and_duplicate_email_links_are_rejected(self):
        User = get_user_model()
        restricted_accounts = (
            {"username": "staff", "is_staff": True},
            {"username": "superuser", "is_superuser": True},
            {"username": "inactive", "is_active": False},
        )
        for account in restricted_accounts:
            with self.subTest(account=account["username"]):
                User.objects.create_user(
                    email="student@example.edu",
                    **account,
                )
                login = self.sociallogin(
                    self.claims("site-editor"), uid=account["username"]
                )
                with self.assertRaises(PermissionDenied):
                    self.adapter.authenticate_by_email(login)
                User.objects.all().delete()

        User.objects.create_user("one", "student@example.edu")
        User.objects.create_user("two", "STUDENT@example.edu")
        with self.assertRaises(PermissionDenied):
            self.adapter.authenticate_by_email(
                self.sociallogin(self.claims("site-editor"))
            )

    def test_admin_claim_cannot_link_an_unrelated_local_superuser(self):
        get_user_model().objects.create_user(
            username="break-glass",
            email="student@example.edu",
            is_staff=True,
            is_superuser=True,
        )
        login = self.sociallogin(
            self.claims("organization.408.tag.President")
        )

        with self.assertRaises(PermissionDenied):
            self.adapter.authenticate_by_email(login)

    def test_existing_profile_sync_does_not_rename_username(self):
        user = get_user_model().objects.create_user(
            username="audit-stable", email="student@example.edu"
        )
        login = self.sociallogin(
            self.claims("site-editor"), user=user, saved_account=True
        )

        self.adapter.pre_social_login(self.request, login)
        user.refresh_from_db()

        self.assertEqual(user.username, "audit-stable")
        self.assertEqual(user.first_name, "Campus")
        self.assertEqual(user.last_name, "Student")

    def test_email_conflict_is_denied_before_group_changes(self):
        user = get_user_model().objects.create_user(
            username="linked", email="old@example.edu"
        )
        get_user_model().objects.create_user(
            username="other", email="student@example.edu"
        )
        user.groups.add(self.editors)
        login = self.sociallogin(
            self.claims("site-moderator"), user=user, saved_account=True
        )

        with self.assertRaises(ImmediateHttpResponse):
            self.adapter.pre_social_login(self.request, login)

        self.assertEqual(
            set(user.groups.values_list("name", flat=True)), {"Editors"}
        )


@override_settings(
    ROOT_URLCONF="sso.test_urls",
    OIDC_SERVER_URL="https://idp.example.edu",
    OIDC_CLIENT_ID="student-government",
    OIDC_POST_LOGOUT_REDIRECT_URI="https://sg.example.edu/",
    SOCIALACCOUNT_REQUESTS_TIMEOUT=5,
)
class OIDCLogoutTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="editor", password="local-test-password"
        )
        self.client.force_login(self.user)

    @patch("sso.views.requests.get")
    def test_logout_clears_session_and_redirects_to_provider(self, mock_get):
        discovery_response = Mock()
        discovery_response.raise_for_status.return_value = None
        discovery_response.json.return_value = {
            "end_session_endpoint": "https://idp.example.edu/logout"
        }
        mock_get.return_value = discovery_response

        response = self.client.post(reverse("sso_logout"))

        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(response.status_code, 302)
        self.assertIn("client_id=student-government", response.url)
        self.assertIn(
            "post_logout_redirect_uri=https%3A%2F%2Fsg.example.edu%2F",
            response.url,
        )

    @patch("sso.views.requests.get", side_effect=RuntimeError("unexpected"))
    def test_non_network_programming_errors_are_not_hidden(self, mock_get):
        with self.assertRaises(RuntimeError):
            self.client.post(reverse("sso_logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

    @patch("sso.views.requests.get")
    def test_discovery_failure_still_completes_local_logout(self, mock_get):
        mock_get.side_effect = __import__("requests").RequestException("offline")

        with self.assertLogs("sso.views", level="WARNING"):
            response = self.client.post(reverse("sso_logout"))

        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertRedirects(
            response,
            "https://sg.example.edu/",
            fetch_redirect_response=False,
        )

    def test_logout_requires_post(self):
        self.assertEqual(self.client.get(reverse("sso_logout")).status_code, 405)


@override_settings(SOCIALACCOUNT_PROVIDERS=PROVIDER_SETTINGS)
class OIDCInitiationTests(TestCase):
    @patch(
        "allauth.socialaccount.adapter.DefaultSocialAccountAdapter.get_requests_session"
    )
    def test_login_uses_discovery_pkce_and_safe_callback(self, get_session):
        session = MagicMock()
        session.__enter__.return_value = session
        discovery_response = Mock()
        discovery_response.raise_for_status.return_value = None
        discovery_response.json.return_value = {
            "authorization_endpoint": "https://idp.example.edu/authorize",
            "token_endpoint": "https://idp.example.edu/token",
            "userinfo_endpoint": "https://idp.example.edu/userinfo",
            "jwks_uri": "https://idp.example.edu/jwks",
            "issuer": "https://idp.example.edu",
            "token_endpoint_auth_methods_supported": ["client_secret_post"],
        }
        session.get.return_value = discovery_response
        get_session.return_value = session

        response = self.client.get(
            "/accounts/oidc/campus/login/?next=/admin/"
        )

        self.assertEqual(response.status_code, 302)
        parsed = urlsplit(response.url)
        parameters = parse_qs(parsed.query)
        self.assertEqual(
            f"{parsed.scheme}://{parsed.netloc}{parsed.path}",
            "https://idp.example.edu/authorize",
        )
        self.assertEqual(parameters["client_id"], ["test-client"])
        self.assertEqual(parameters["response_type"], ["code"])
        self.assertEqual(
            set(parameters["scope"][0].split()), {"openid", "profile", "email"}
        )
        self.assertEqual(
            parameters["redirect_uri"],
            ["http://testserver/accounts/oidc/campus/login/callback/"],
        )
        self.assertEqual(parameters["code_challenge_method"], ["S256"])
        self.assertIn("code_challenge", parameters)
        self.assertIn("state", parameters)
        state = self.client.session["socialaccount_states"][parameters["state"][0]][0]
        self.assertEqual(state["next"], "/admin/")


class WagtailLoginRoutingTests(TestCase):
    @override_settings(
        WAGTAILADMIN_LOGIN_URL="/accounts/oidc/campus/login/"
    )
    def test_admin_redirects_to_sso_and_preserves_next(self):
        response = self.client.get("/admin/")
        self.assertRedirects(
            response,
            "/accounts/oidc/campus/login/?next=/admin/",
            fetch_redirect_response=False,
        )

    def test_local_break_glass_login_remains_available(self):
        response = self.client.get("/admin/login/")
        self.assertEqual(response.status_code, 200)
