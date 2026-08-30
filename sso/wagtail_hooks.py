from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet

from .models import OIDCGroupMapping


class OIDCGroupMappingViewSet(SnippetViewSet):
    model = OIDCGroupMapping
    icon = "group"
    list_display = (
        "claim_value",
        "mapped_group_names",
        "grants_wagtail_admin",
        "enabled",
    )
    list_filter = ("grants_wagtail_admin", "enabled")
    search_fields = ("claim_value",)
    inspect_view_enabled = True


register_snippet(OIDCGroupMapping, viewset=OIDCGroupMappingViewSet)

