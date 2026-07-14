"""
Models for the Government Branches app.

This app contains all models related to the organizational structure of
RPI Student Government: the five branches, their member listings,
committees, class councils, and a flexible general-purpose page.

Key design decisions:
  - MemberProfile is a Snippet (not a Page) because members don't need
    their own URL — they're displayed within listing pages. Being a
    Snippet also makes them reusable across multiple pages (a person can
    serve on the Senate AND a committee).
  - BranchPage is a single model with a branch_type field rather than
    five separate models, because all branches share the same structure.
  - Orderable "placement" through-models (e.g. BranchMemberPlacement)
    sit between a page and a MemberProfile, carrying relationship-specific
    data like the person's role on that particular page.
"""

from datetime import date

from django import forms
from django.db import models

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.admin.forms.models import WagtailAdminModelForm
from wagtail.admin.forms.pages import WagtailAdminPageForm
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.images import get_image_model_string
from wagtail.models import Orderable, Page
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from stugov.blocks import STANDARD_STREAMFIELD_BLOCKS


# ---------------------------------------------------------------------------
# Choice constants
# ---------------------------------------------------------------------------
# Defined at module level so they can be referenced by models, templates,
# and template tags without importing model classes.

BRANCH_CHOICES = [
    ("senate", "Student Senate"),
    ("eboard", "Executive Board"),
    ("uc", "Undergraduate Council"),
    ("gc", "Graduate Council"),
    ("jboard", "Judicial Board"),
]

# Fraternity & Sorority Life association of the constituency a role represents.
FSL_CHOICES = [
    ("associated", "FSL-Associated"),
    ("independent", "Independent"),
    ("none", "No FSL Association"),
]


def constituency_class_choices():
    """
    Choices for the graduating class a Role represents.

    Returns the current four undergraduate graduating years plus "Graduate"
    and "None". This is a *callable* (Django 6.0 evaluates choices lazily),
    so the year window rolls forward automatically without generating a new
    migration each academic year.
    """
    current = date.today().year
    years = [(str(y), str(y)) for y in range(current, current + 5)]
    return years + [("graduate", "Graduate"), ("none", "None")]


# ---------------------------------------------------------------------------
# Membership hierarchy
# ---------------------------------------------------------------------------
# Defines how MemberListingPage groups member placements into sections.
# The presiding officer appears first, followed by officers of the body,
# then committee chairs, then voting members, then club financial advisors.
# Each Role snippet carries its own tier (see the Role model). If a member
# holds roles across multiple tiers, their card is shown once per tier.

HIERARCHY_TIERS = [
    {"key": "presiding", "label": "Presiding Officer"},
    {"key": "officers", "label": "Officers"},
    {"key": "chairs", "label": "Committee Chairs"},
    {"key": "members", "label": "Members"},
    {"key": "advisors", "label": "Non-voting Members"},
]

# Choices for the Role.tier field, derived from the hierarchy definition.
TIER_CHOICES = [(t["key"], t["label"]) for t in HIERARCHY_TIERS]
# Default tier for any role not explicitly categorized.
DEFAULT_TIER = "members"


# ===========================================================================
# SNIPPET: Role
# ===========================================================================

@register_snippet
class Role(index.Indexed, models.Model):
    """
    A branch-specific role that can be assigned to members on a
    MemberListingPage (e.g. "Class of 2027 Representative").

    Roles are snippets (not a hardcoded list) so editors can manage them in
    the admin, so the same role name can exist in different branches while
    staying visibly distinct, and so each role can record the constituency
    it represents — enabling a future "who represents me?" search.

    Note: committees and class councils intentionally do NOT use this model;
    they keep their own role fields (CommitteeMemberPlacement.committee_role,
    ClassCouncilMemberPlacement.role).
    """

    name = models.CharField(
        max_length=255,
        help_text="Displayed role text, e.g. 'Class of 2027 Representative'.",
    )
    branch = models.CharField(
        max_length=20,
        choices=BRANCH_CHOICES,
        help_text="Which branch this role belongs to.",
    )
    tier = models.CharField(
        max_length=20,
        choices=TIER_CHOICES,
        default=DEFAULT_TIER,
        help_text="Display rank on the member listing page. "
                  "'Club Financial Advisors' sort to the bottom.",
    )
    constituency_class = models.CharField(
        max_length=20,
        choices=constituency_class_choices,
        default="none",
        help_text="Graduating class this role represents, if any.",
    )
    constituency_fsl = models.CharField(
        max_length=20,
        choices=FSL_CHOICES,
        blank=True,
        verbose_name="Constituency FSL association",
        help_text="FSL group this role represents, if any.",
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("branch"),
        FieldPanel("tier"),
        MultiFieldPanel(
            [
                FieldPanel("constituency_class"),
                FieldPanel("constituency_fsl"),
            ],
            heading="Constituency",
            help_text="Who this role represents. Used by the constituent "
                      "search to match students to their representatives.",
        ),
    ]

    search_fields = [
        index.SearchField("name"),
        index.FilterField("branch"),
        index.FilterField("tier"),
        index.FilterField("constituency_class"),
        index.FilterField("constituency_fsl"),
    ]

    class Meta:
        ordering = ["branch", "name"]
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self):
        # Include the branch so same-named roles stay distinct in the admin,
        # e.g. "Student Senate: Chair" vs "Executive Board: Chair".
        return f"{self.get_branch_display()}: {self.name}"


# ---------------------------------------------------------------------------
# Admin form plumbing for branch-scoped role dropdowns
# ---------------------------------------------------------------------------
# A MemberListingPage always lives under a BranchPage, so the roles offered to
# its members should be limited to that branch. Wagtail passes the page form's
# `parent_page` (the BranchPage) and modelcluster threads named kwargs down to
# child/grandchild forms via `inherit_kwargs`. We relay `parent_page` through
# the placement form and use it to filter the role dropdown's queryset.

class BranchScopedInlinePanel(InlinePanel):
    """InlinePanel that passes the page form's `parent_page` into each child
    form, so nested forms can scope their querysets to the branch.

    Stock InlinePanel ignores the child model's `base_form_class` (it only sets
    a custom form for the `defer_required_on_fields` case), so we also inject it
    here — otherwise our custom forms that accept `parent_page` are never used.
    """

    def get_form_options(self):
        opts = super().get_form_options()
        formset = opts["formsets"][self.relation_name]
        formset["inherit_kwargs"] = ["parent_page"]
        base_form = getattr(self.db_field.related_model, "base_form_class", None)
        if base_form is not None:
            formset["form"] = base_form
        return opts


class BranchMemberPlacementForm(WagtailAdminModelForm):
    """Relays `parent_page` so the nested role formset can inherit it."""

    def __init__(self, *args, parent_page=None, **kwargs):
        self.parent_page = parent_page
        super().__init__(*args, **kwargs)


class BranchMemberRoleForm(WagtailAdminModelForm):
    """Scopes the role dropdown to the listing page's branch."""

    def __init__(self, *args, parent_page=None, **kwargs):
        super().__init__(*args, **kwargs)
        if parent_page is not None:
            # Resolve branch_type once per page edit and cache it on the shared
            # parent_page object, rather than re-querying .specific per row.
            branch = getattr(parent_page, "_branch_type_cache", None)
            if branch is None:
                branch = parent_page.specific.branch_type
                parent_page._branch_type_cache = branch
            qs = Role.objects.filter(branch=branch)
        else:
            # Without a branch we can't scope safely, so offer nothing rather
            # than every branch's roles.
            qs = Role.objects.none()
        # Always keep this row's currently-assigned role selectable — even if it
        # now belongs to a different branch (e.g. the role was re-branched) — so
        # the row stays valid and the page remains editable.
        if self.instance and self.instance.role_id:
            qs = (qs | Role.objects.filter(pk=self.instance.role_id)).distinct()
        self.fields["role"].queryset = qs.order_by("tier", "name")


class BranchListingPageForm(WagtailAdminPageForm):
    """Page form for MemberListingPage.

    WagtailAdminPageForm assigns ``self.parent_page`` *after* calling super,
    but the super call is where modelcluster builds the child formsets and
    reads ``parent_page`` via ``inherit_kwargs``. We set it first so the
    member-placement formset (and its nested role dropdowns) receive the
    branch page rather than ``None``.
    """

    def __init__(self, *args, parent_page=None, **kwargs):
        self.parent_page = parent_page
        super().__init__(*args, parent_page=parent_page, **kwargs)


# ===========================================================================
# SNIPPET: MemberProfile
# ===========================================================================

@register_snippet
class MemberProfile(index.Indexed, ClusterableModel):
    """
    A reusable profile for any student government member.

    This is a Wagtail Snippet — a content object that doesn't live in the
    page tree and doesn't have its own URL. Snippets are managed in the
    Wagtail admin under the "Snippets" sidebar menu.

    ClusterableModel is required (instead of plain models.Model) because
    Wagtail's admin interface uses modelcluster to handle draft editing.
    Without it, related objects couldn't be edited inline before saving.

    index.Indexed enables Wagtail's search to index these objects, so
    admins can search for members by name in the snippet chooser.
    """

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    photo = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Headshot or profile photo.",
    )
    class_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Graduation year, e.g. 2027",
    )
    major = models.CharField(max_length=200, blank=True)
    bio = RichTextField(
        blank=True,
        features=["bold", "italic", "link"],
        help_text="Short bio. Keep it to 2-3 sentences.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck when member leaves office. Inactive members "
                  "won't appear on public listings.",
    )

    # -- Admin panel layout --
    # MultiFieldPanel groups related fields under a collapsible heading
    # in the Wagtail admin editor. This makes the form scannable.
    panels = [
        MultiFieldPanel(
            [
                FieldPanel("first_name"),
                FieldPanel("last_name"),
                FieldPanel("email"),
                FieldPanel("photo"),
            ],
            heading="Basic Info",
        ),
        MultiFieldPanel(
            [
                FieldPanel("class_year"),
                FieldPanel("major"),
                FieldPanel("bio"),
            ],
            heading="Details",
        ),
        FieldPanel("is_active"),
    ]

    # -- Search index --
    # SearchField: full-text indexed for search queries.
    # FilterField: used for exact-match filtering (e.g. "only active members").
    search_fields = [
        index.SearchField("first_name"),
        index.SearchField("last_name"),
        index.FilterField("is_active"),
    ]

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name = "Member Profile"
        verbose_name_plural = "Member Profiles"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# ===========================================================================
# PAGE: BranchPage (landing page for each government branch)
# ===========================================================================

class BranchPage(Page):
    """
    Landing page for a government branch (Senate, E-Board, UC, GC, J-Board).

    There will be exactly five of these in the page tree, one per branch.
    Each serves as the parent for that branch's sub-pages (member listing,
    committees, records, etc.).

    The branch_type field is a simple choice rather than a separate model
    because branches are a fixed, known set. If RPI added a new branch,
    you'd add it to BRANCH_CHOICES and create a new BranchPage in the admin.
    """

    branch_type = models.CharField(
        max_length=20,
        choices=BRANCH_CHOICES,
        help_text="Which branch of student government this page represents.",
    )
    tagline = models.CharField(
        max_length=255,
        blank=True,
        help_text="Short description shown prominently on the landing page.",
    )
    image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Photo representing this branch (e.g. a group photo or meeting).",
    )
    body = StreamField(
        STANDARD_STREAMFIELD_BLOCKS,
        blank=True,
        use_json_field=True,
        help_text="Flexible content area for the branch landing page.",
    )
    contact_email = models.EmailField(blank=True)
    meeting_schedule = RichTextField(
        blank=True,
        help_text="Regular meeting times and location, e.g. 'Mondays 7pm, Union 3602'.",
    )

    # -- Admin panels --
    content_panels = Page.content_panels + [
        FieldPanel("branch_type"),
        FieldPanel("tagline"),
        FieldPanel("image"),
        FieldPanel("body"),
        MultiFieldPanel(
            [
                FieldPanel("contact_email"),
                FieldPanel("meeting_schedule"),
            ],
            heading="Contact & Meetings",
        ),
    ]

    # -- Page hierarchy constraints --
    # subpage_types: what page types can be created as CHILDREN of this page.
    # parent_page_types: what page types this page can live UNDER.
    # These enforce a valid page tree structure at the model level, preventing
    # admins from creating pages in the wrong place.
    subpage_types = [
        "branches.MemberListingPage",
        "branches.CommitteeIndexPage",
        "branches.ClassCouncilIndexPage",
        "branches.FlexiblePage",
        "records.RecordIndexPage",
    ]
    parent_page_types = ["home.HomePage"]

    class Meta:
        verbose_name = "Branch Page"


# ===========================================================================
# PAGE: MemberListingPage ("Meet the Senate", etc.)
# ===========================================================================

class BranchMemberPlacement(Orderable, ClusterableModel):
    """
    Through model linking a MemberListingPage to a MemberProfile.

    This is the "glue" that says "Jane Doe serves as President on the
    Meet the Senate page." The role is stored here (not on MemberProfile)
    because the same person could have different roles in different contexts.

    Orderable gives this a sort_order field, enabling drag-and-drop
    reordering in the Wagtail admin. ParentalKey (instead of ForeignKey)
    is required for Wagtail's draft/publish workflow to work correctly
    with InlinePanel.
    """

    page = ParentalKey(
        "branches.MemberListingPage",
        related_name="member_placements",
    )
    member = models.ForeignKey(
        "branches.MemberProfile",
        on_delete=models.CASCADE,
        related_name="+",
        # related_name="+" means Django won't create a reverse relation.
        # We don't need MemberProfile.memberlistingpage_set because we
        # always query from the page side, not the member side.
    )

    # The custom form relays `parent_page` to the nested role formset (below)
    # so each role dropdown can be scoped to this listing's branch.
    base_form_class = BranchMemberPlacementForm

    panels = [
        FieldPanel("member"),
        # A nested InlinePanel of single-role dropdowns: editors add a variable
        # number of roles per member, each chosen from a branch-scoped <select>.
        BranchScopedInlinePanel("role_assignments", label="Roles"),
    ]


class BranchMemberRole(Orderable):
    """
    A single role held by a member on a MemberListingPage.

    This is a grandchild of MemberListingPage (ParentalKey -> placement, which
    has a ParentalKey -> page). Each row is one branch-scoped role dropdown, so
    a member can hold a variable number of roles without a wall of checkboxes.
    """

    placement = ParentalKey(
        "branches.BranchMemberPlacement",
        related_name="role_assignments",
    )
    role = models.ForeignKey(
        "branches.Role",
        on_delete=models.CASCADE,
        related_name="+",
    )

    base_form_class = BranchMemberRoleForm

    # forms.Select renders the snippet FK as a plain dropdown instead of the
    # default chooser modal; the form scopes its options to the branch.
    panels = [
        FieldPanel("role", widget=forms.Select),
    ]


class MemberListingPage(Page):
    """
    'Meet the Senate' / 'Meet the E-Board' style page.

    Displays members grouped into tiers by role hierarchy:
      1. Presiding Officer (GM, Union President, Council President, etc.)
      2. Officers of the Body (VPs, Secretary, Treasurer, etc.)
      3. Committee Chairs
      4. Voting Members

    The members are managed via InlinePanel which renders the
    BranchMemberPlacement through-model as an inline editor in the Wagtail
    admin — admins can add/remove/reorder members right on this page's
    edit screen. The grouping happens at render time in get_member_hierarchy().

    Members with roles spanning multiple tiers appear once per tier. For
    example, a Grand Marshal who also chairs a committee shows up in both
    "Presiding Officer" and "Committee Chairs" sections.
    """

    intro = RichTextField(
        blank=True,
        help_text="Introductory text shown above the member grid.",
    )

    # Custom form fixes parent_page ordering so role dropdowns scope to branch.
    base_form_class = BranchListingPageForm

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        # BranchScopedInlinePanel threads parent_page (this page's BranchPage)
        # down to each placement form, which in turn relays it to the nested
        # role dropdowns so they only offer this branch's roles.
        BranchScopedInlinePanel("member_placements", label="Members", classname="collapsed"),
    ]

    parent_page_types = ["branches.BranchPage"]
    subpage_types = []  # Leaf node — nothing can be created under this page.

    class Meta:
        verbose_name = "Member Listing Page"

    def get_member_hierarchy(self):
        """
        Group active member placements into hierarchy tiers.

        Returns a list of non-empty tiers in hierarchy order:
            [
                {"key": "presiding", "label": "Presiding Officer", "entries": [...]},
                {"key": "officers", "label": "Officers", "entries": [...]},
                ...
            ]

        Each entry is a dict with:
            "placement": the BranchMemberPlacement instance
            "roles":     the names of the member's roles that belong to this
                         tier, shown one per line on the card

        Each Role snippet carries its own tier, so a member whose roles span
        multiple tiers appears once per tier, and a member with several roles
        in the same tier gets one card listing each role. Placements with no
        roles fall into the "members" tier by default.

        Entries within a tier are sorted deterministically by first role
        name, then member last/first name.
        """
        tiers = {t["key"]: {"label": t["label"], "entries": []} for t in HIERARCHY_TIERS}

        placements = (
            self.member_placements
            .select_related("member")
            .prefetch_related("role_assignments__role")
            .all()
        )
        for placement in placements:
            if not placement.member.is_active:
                continue

            # Bucket the placement's roles by their tier, preserving each
            # role's name for multi-line display.
            tier_roles = {}
            for assignment in placement.role_assignments.all():
                role = assignment.role
                tier_key = role.tier if role.tier in tiers else DEFAULT_TIER
                tier_roles.setdefault(tier_key, []).append(role.name)

            # No roles set → still show the member, in the default tier.
            if not tier_roles:
                tier_roles[DEFAULT_TIER] = []

            for tier_key, role_names in tier_roles.items():
                tiers[tier_key]["entries"].append({
                    "placement": placement,
                    "roles": role_names,
                })

        # Deterministic ordering within each tier: first role name, then
        # member last name, then first name (all case-insensitive).
        for tier_data in tiers.values():
            tier_data["entries"].sort(
                key=lambda e: (
                    (e["roles"][0].lower() if e["roles"] else ""),
                    e["placement"].member.last_name.lower(),
                    e["placement"].member.first_name.lower(),
                )
            )

        # Return non-empty tiers in hierarchy order
        return [
            {
                "key": t["key"],
                "label": tiers[t["key"]]["label"],
                "entries": tiers[t["key"]]["entries"],
            }
            for t in HIERARCHY_TIERS
            if tiers[t["key"]]["entries"]
        ]


# ===========================================================================
# PAGES: CommitteeIndexPage and CommitteePage
# ===========================================================================

class CommitteeIndexPage(Page):
    """
    Index page listing all committees for a branch.

    This is a "container" page — its main job is to be the parent of
    CommitteePage children. The template iterates over its children
    to render the committee list.
    """

    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["branches.BranchPage"]
    subpage_types = ["branches.CommitteePage"]

    def get_context(self, request, *args, **kwargs):
        """
        Add child committees to the template context.

        get_context() is Wagtail's hook for adding extra variables to the
        template. The template receives everything returned here plus the
        default 'self' and 'page' variables.

        .live() filters to only published pages (excludes drafts).
        """
        context = super().get_context(request, *args, **kwargs)
        context["committees"] = self.get_children().live().order_by("title")
        return context

    class Meta:
        verbose_name = "Committee Index Page"


class CommitteeMemberPlacement(Orderable):
    """Through model for committee members (same pattern as BranchMemberPlacement)."""

    page = ParentalKey(
        "branches.CommitteePage",
        related_name="committee_members",
    )
    member = models.ForeignKey(
        "branches.MemberProfile",
        on_delete=models.CASCADE,
        related_name="+",
    )
    committee_role = models.CharField(
        max_length=50,
        choices=[
            ("chair", "Chair"),
            ("vice_chair", "Vice Chair"),
            ("member", "Member"),
        ],
        default="member",
    )

    panels = [
        FieldPanel("member"),
        FieldPanel("committee_role"),
    ]


class CommitteePage(Page):
    """
    Individual committee page with description, meeting info, and members.
    """

    description = RichTextField(blank=True)
    meeting_time = models.CharField(
        max_length=200,
        blank=True,
        help_text="e.g. 'Tuesdays 5pm'",
    )
    meeting_location = models.CharField(
        max_length=200,
        blank=True,
        help_text="e.g. 'Union Room 3602'",
    )

    content_panels = Page.content_panels + [
        FieldPanel("description"),
        MultiFieldPanel(
            [
                FieldPanel("meeting_time"),
                FieldPanel("meeting_location"),
            ],
            heading="Meeting Info",
        ),
        InlinePanel("committee_members", label="Committee Members"),
    ]

    parent_page_types = ["branches.CommitteeIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Committee Page"


# ===========================================================================
# PAGES: ClassCouncilIndexPage and ClassCouncilPage (UC-specific)
# ===========================================================================

class ClassCouncilIndexPage(Page):
    """
    Index page for class councils under the Undergraduate Council.

    Only used under the UC branch. The parent_page_types constraint
    limits it to BranchPage, and in practice an admin would only create
    it under the UC branch page.
    """

    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["branches.BranchPage"]
    subpage_types = ["branches.ClassCouncilPage"]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        # Order by class year descending so newest class appears first
        context["councils"] = (
            self.get_children().live().specific().order_by("-classcouncilpage__class_year")
        )
        return context

    class Meta:
        verbose_name = "Class Council Index Page"


class ClassCouncilMemberPlacement(Orderable):
    """Through model for class council members."""

    page = ParentalKey(
        "branches.ClassCouncilPage",
        related_name="council_members",
    )
    member = models.ForeignKey(
        "branches.MemberProfile",
        on_delete=models.CASCADE,
        related_name="+",
    )
    role = models.CharField(
        max_length=100,
        help_text="Role within the class council, e.g. 'President' or 'Social Chair'.",
    )

    panels = [
        FieldPanel("member"),
        FieldPanel("role"),
    ]


class ClassCouncilPage(Page):
    """
    Individual class council page (e.g., 'Class of 2027').
    """

    class_year = models.PositiveIntegerField(
        help_text="Graduation year, e.g. 2027",
    )
    description = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("class_year"),
        FieldPanel("description"),
        InlinePanel("council_members", label="Council Members"),
    ]

    parent_page_types = ["branches.ClassCouncilIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Class Council Page"
        ordering = ["-class_year"]


# ===========================================================================
# PAGE: FlexiblePage (general-purpose content page)
# ===========================================================================

class FlexiblePage(Page):
    """
    A general-purpose page with StreamField content.

    Used for pages that don't fit neatly into the other models:
    - "Get Involved" (under HomePage)
    - "Club Resources" (under E-Board BranchPage)
    - "Research Symposium" (under GC BranchPage)

    StreamField lets editors build these pages from structured blocks
    rather than dumping everything into a single rich text editor.
    The subtitle field provides an optional secondary heading.
    """

    subtitle = models.CharField(max_length=255, blank=True)
    body = StreamField(
        STANDARD_STREAMFIELD_BLOCKS,
        blank=True,
        use_json_field=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("subtitle"),
        FieldPanel("body"),
    ]

    # Can live under the homepage OR under a branch page, giving it
    # maximum flexibility for placement in the page tree.
    parent_page_types = [
        "home.HomePage",
        "branches.BranchPage",
    ]
    # Can also nest — useful if "Club Resources" needs sub-pages.
    subpage_types = ["branches.FlexiblePage"]

    class Meta:
        verbose_name = "Flexible Page"
