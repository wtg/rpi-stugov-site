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

from django.db import models

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

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

ROLE_CHOICES = [
    # Executive roles (used across most branches)
    ("president_union", "President of the Union"),
    ("vice_president", "Vice President"),
    ("secretary", "Secretary"),
    ("treasurer", "Treasurer"),
    # Senate-specific
    ("grand_marshall", "Grand Marshall")
    ("senator", "Senator"),
    # UC/GC-specific
    ("council_president", "Council President"),
    ("representative", "Representative"),
    # Committee roles
    ("chair", "Committee Chair"),
    ("vice_chair", "Vice Chair"),
    ("member", "Member"),
    # Judicial Board
    ("chief_justice", "Chief Justice"),
    ("justice", "Justice"),
]


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

class BranchMemberPlacement(Orderable):
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
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    role_title_override = models.CharField(
        max_length=100,
        blank=True,
        help_text="Custom title that overrides the role dropdown, e.g. "
                  "'President of the Senate' instead of just 'President'.",
    )

    panels = [
        FieldPanel("member"),
        FieldPanel("role"),
        FieldPanel("role_title_override"),
    ]

    @property
    def display_role(self):
        """Return the custom title if set, otherwise the human-readable role name."""
        return self.role_title_override or self.get_role_display()


class MemberListingPage(Page):
    """
    'Meet the Senate' / 'Meet the E-Board' style page.

    Displays a grid of member cards. The members are managed via InlinePanel
    which renders the BranchMemberPlacement through-model as an inline
    editor in the Wagtail admin — admins can add/remove/reorder members
    right on this page's edit screen.
    """

    intro = RichTextField(
        blank=True,
        help_text="Introductory text shown above the member grid.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        InlinePanel("member_placements", label="Members"),
    ]

    parent_page_types = ["branches.BranchPage"]
    subpage_types = []  # Leaf node — nothing can be created under this page.

    class Meta:
        verbose_name = "Member Listing Page"


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
