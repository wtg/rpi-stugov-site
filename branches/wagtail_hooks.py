from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import MemberRoleAssignment

class MemberRoleAssignmentViewSet(SnippetViewSet):
    model = MemberRoleAssignment
    icon = "link"
    list_display = ["member", "role"]
    list_filter = ["member", "role"]


register_snippet(MemberRoleAssignmentViewSet)