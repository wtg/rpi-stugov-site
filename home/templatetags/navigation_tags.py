"""
Template tags for site navigation.

This module provides the {% main_navigation %} tag used in base.html
to render the site's hierarchical navigation menu.

How it works:
  1. The tag finds the current Wagtail site's root page (the HomePage).
  2. It gets the root page's children that have "Show in menus" checked.
     (This is a built-in Wagtail Page field on the Promote tab.)
  3. For each top-level item, it also gets one level of children (for
     dropdown menus — e.g., "Student Senate" drops down to show
     "Meet the Senate", "Committees", etc.).
  4. It passes this tree structure to the navigation.html template.

Why a custom template tag instead of building the nav in base.html?
  - Keeps the navigation logic out of the base template (separation
    of concerns).
  - The @register.inclusion_tag decorator automatically renders a
    sub-template, keeping base.html clean.
  - The tag can be reused in other templates (e.g., a mobile nav
    drawer, a sitemap page).

Usage in templates:
  {% load navigation_tags %}
  {% main_navigation %}
"""

from django import template
from wagtail.models import Site

register = template.Library()


@register.inclusion_tag("includes/navigation.html", takes_context=True)
def main_navigation(context):
    """
    Build and render the site's main navigation menu.

    takes_context=True gives us access to the request object, which
    Wagtail needs to determine which site we're on (for multi-site
    setups, though we only have one site).

    The resulting template receives:
      - nav_items: list of dicts with 'page' and 'children' keys
      - request: the current HTTP request (for highlighting active items)
    """
    request = context.get("request")
    if not request:
        return {"nav_items": [], "request": request}

    site = Site.find_for_request(request)
    if not site:
        return {"nav_items": [], "request": request}

    root = site.root_page

    # .in_menu() filters to pages where "Show in menus" is checked.
    # This lets admins control which pages appear in the nav without
    # touching code — just uncheck "Show in menus" in the Promote tab.
    top_level = root.get_children().live().in_menu()

    nav_items = []
    for item in top_level:
        # Get one level of children for dropdown menus
        children = item.get_children().live().in_menu()
        nav_items.append(
            {
                "page": item,
                "children": children,
                # .specific gives us the actual page type (BranchPage, etc.)
                # instead of the base Page class, so templates can access
                # type-specific fields like branch_type.
                "specific": item.specific,
            }
        )

    return {
        "nav_items": nav_items,
        "request": request,
    }
