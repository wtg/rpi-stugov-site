from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet
from django.contrib.auth.models import Permission
from django.urls import path, reverse
from wagtail import hooks
from wagtail.admin.action_menu import ActionMenuItem
from branches.models import CommitteeReportPage
from branches.views import bump_report_view

from .models import MemberRoleAssignment

# Register view for editing MemberRoleAssignment snippets
class MemberRoleAssignmentViewSet(SnippetViewSet):
    model = MemberRoleAssignment
    icon = "link"
    list_display = ["member", "role"]
    list_filter = ["member", "role"]

register_snippet(MemberRoleAssignmentViewSet)


# Register 'bump page' action for CommitteeReportPage pages
@hooks.register("register_admin_urls")
def register_custom_action_url():
    return [
        path(
            "pages/<int:page_id>/bump-report/",
            bump_report_view,
            name="bump_report",
        ),
    ]

class BumpReportMenuItem(ActionMenuItem):
    name = "bump-report"
    label = "Bump Page"
    icon_name = "order-up"

    def get_url(self, context):
        page = context.get("page")
        if page and page.pk:
            return reverse("bump_report", args=[page.pk])
        return "#"

@hooks.register("construct_page_action_menu")
def add_bump_report_menu_item(menu_items, request, context):
    page = context.get("page")
    if isinstance(page, CommitteeReportPage) and page.pk:
        menu_items.append(BumpReportMenuItem(order=100))

# Register permission for ignoring bump cooldown
@hooks.register("register_permissions")
def register_custom_permissions():
    return Permission.objects.filter(
        content_type__app_label="branches",
        codename="ignore_bump_cooldown",
    )