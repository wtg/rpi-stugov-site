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

from __future__ import annotations

from collections import defaultdict

from datetime import date

from django.apps import apps
from django.db import models

from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel, PageChooserPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.images import get_image_model_string
from wagtail.models import Page, get_page_models
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

FSL_CHOICES = [
    ("associated", "FSL-Associated"),
    ("independent", "Independent"),
]

def class_choices():
    current = date.today().year
    years = [(str(y), str(y)) for y in range(current, current + 5)]
    return years + [("graduate", "Graduate")]

def constituency_choices():
    """
    Choices for the graduating class or FSL association a Role represents.

    Returns the current four undergraduate graduating years plus "Graduate",
    "FSL-Associated", "Independent", and "None". This is a *callable*
    (Django 6.0 evaluates choices lazily), so the year window rolls forward 
    automatically without generating a new migration each academic year.
    """
    return class_choices() + FSL_CHOICES + [("none", "None")]

class TierChoices(models.IntegerChoices):
    PRESIDING = 0, 'Presiding Officer'
    OFFICERS = 1, 'Officers'
    CHAIRS = 2, 'Committee Chairs'
    MEMBERS = 3, 'Voting Members'
    ADVISORS = 4, 'Non-voting Members'


# ===========================================================================
# MIXIN: MembershipDisplay
# ===========================================================================

class MembershipDisplay:
    """
    Mixin for pages with tiered membership displays.
    
    get_tiered_placements gets a list of tier dicts for placements and, if necessary,
    followed by a tier dict for vacancies. The returned list has the following structure:
    [{
        'tier_id': number, # e.g. 0, 1, ...   derived from TierChoices 
        'placements':
            [{
                'member': MemberProfile,
                'tier_name': string, # e.g. Presiding Officer, Members
                'roles': [ string, ... ] # e.g. Secretary, Representative
            }, ... ]
    }, ... , {
        'tier_id': vacancies_tier_id
        'vacancies':
            [{
                'positions': number, # Number of positions available
                'tier_name': string, # e.g. Vacancies
                'role': string # e.g. Secretary, Representative
            }, ... ]
    }]
    """
    
    vacancies_tier_id = 999
    
    def get_tiered_placements(self):
        placements = self.role_placements.select_related('role').order_by('tier')
        if not placements:
            return []

        role_to_tier = defaultdict(list)
        tier_names = {}
        configured_roles = {}
        
        for placement in placements:
            tier = placement.tier
            role_name = placement.display_name or placement.role.name
            role_to_tier[placement.role_id].append((tier, role_name))
            configured_roles[placement.role_id] = placement.role

            if tier not in tier_names:
                tier_names[tier] = placement.get_tier_display()

        MemberRoleAssignment = apps.get_model('branches', 'MemberRoleAssignment')
        assignments = MemberRoleAssignment.objects.filter(
            role_id__in=role_to_tier.keys()
        ).select_related('member', 'role')
        tier_member_roles = defaultdict(lambda: defaultdict(set))
        
        role_assignments = dict(
            MemberRoleAssignment.objects.filter(role_id__in=role_to_tier.keys())
            .values('role_id')
            .annotate(total=models.Count('id'))
            .values_list('role_id', 'total')
        )

        for assignment in assignments:
            member = assignment.member
            for tier, role_name in role_to_tier[assignment.role_id]:
                tier_member_roles[tier][member].add(role_name)

        result = []
        for tier in sorted(tier_member_roles.keys()):
            member_placements = []
            for member, role_names in tier_member_roles[tier].items():
                member_placements.append({
                    'member': member,
                    'roles': list(role_names)
                })

            member_placements.sort(key=lambda p: p['roles'][0])
            result.append({
                'tier_id': tier,
                'tier_name': tier_names.get(tier, f"Tier {tier}"),
                'placements': member_placements
            })

        vacancies = []
        for role_id, role in configured_roles.items():
            if not role.positions:
                continue

            open_positions = role.positions - role_assignments.get(role_id, 0)
            if open_positions > 0:

                role_name = next(name for t, name in role_to_tier[role_id])
                vacancies.append({
                    'role': role_name,
                    'positions': open_positions,
                })

        # Append vacancies tier if any vacancies exist
        if vacancies:
            result.append({
                'tier_id': self.vacancies_tier_id,
                'tier_name': "Vacancies",
                'vacancies': vacancies
            })

        return result


# ===========================================================================
# SNIPPET: Role
# ===========================================================================

@register_snippet
class Role(index.Indexed, ClusterableModel):
    """
    A role in government that can be assigned to members with a
    MemberRoleAssignment.

    Roles are snippets (not a hardcoded list) so editors can manage them in
    the admin, so the same role can be used in different branches, and so
    each role can record the constituency it represents, enabling a lookup
    for students to identify who represents them.

    Note: committees only use this model for the chair, allowing for greater
    customization of committee structure.
    """

    role_code = models.CharField(
        max_length=31,
        help_text="Unique identifier for this role.",
        unique=True,
    )
    name = models.CharField(
        max_length=255,
        help_text="Role name to be displayed on pages.",
    )
    positions = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of positions.",
    )
    constituency = models.CharField(
        max_length=20,
        choices=constituency_choices,
        default="none",
        help_text="Graduating class or FSL association this role represents, if any.",
    )

    panels = [
        FieldPanel("role_code"),
        FieldPanel("name"),
        FieldPanel("positions"),
	    FieldPanel("constituency"),
        InlinePanel("placements"),
    ]

    search_fields = [
        index.SearchField("name"),
        index.SearchField("role_code"),
    ]

    class Meta:
        ordering = ["name"]
        verbose_name = "Role"
        verbose_name_plural = "Roles"

    def __str__(self):
        return f"{self.name} ({self.role_code})"


def getMembershipDisplayPages():
    return [page_type for page_type in get_page_models() if issubclass(page_type, MembershipDisplay)]


class RolePlacement(ClusterableModel):
    """
    A child model of Role that defines on which MemberListingPages and with
    what configuration options the role is displayed.

    Roles are displayed in a tiered hierarchy, and roles can appear more than
    once on a page with different tiers and display names.
    """

    role = ParentalKey(
        'branches.Role',
        related_name='placements',
        on_delete=models.CASCADE
    )

    page = models.ForeignKey(
        'wagtailcore.Page',
        blank=False,
        on_delete=models.CASCADE,
        related_name='role_placements',
    )
    tier = models.IntegerField(
        choices=TierChoices.choices,
        default=TierChoices.MEMBERS,
        help_text="Display tier on page."
    )
    display_name = models.CharField(
        max_length=31,
        blank=True,
        help_text="Role name override on page."
    )

    panels = [
        PageChooserPanel("page", page_type=getMembershipDisplayPages()),
        FieldPanel("tier"),
        FieldPanel("display_name"),
    ]
    
    class Meta:
        verbose_name = "Role Placement"
        verbose_name_plural = "Role Placements"


# ===========================================================================
# SNIPPET: MemberProfile
# ===========================================================================

def member_class_choices():
    return class_choices() + [('','')]

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

    rcs_id = models.CharField(
        max_length=9,
        unique=True,
        verbose_name="RCS ID",
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    photo = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Headshot or profile photo.",
    )
    class_year = models.CharField(
        max_length=20,
        choices=member_class_choices,
        default='',
        blank=True,
        help_text="Class year, e.g. 2027 or Graduate",
    )
    major = models.CharField(max_length=200, blank=True)
    bio = RichTextField(
        blank=True,
        features=["bold", "italic", "link"],
        help_text="Short bio. Keep it to 2-3 sentences.",
    )

    # -- Admin panel layout --
    # MultiFieldPanel groups related fields under a collapsible heading
    # in the Wagtail admin editor. This makes the form scannable.
    panels = [
        MultiFieldPanel(
            [
                FieldPanel("first_name"),
                FieldPanel("last_name"),
                FieldPanel("rcs_id"),
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
    ]

    # -- Search index --
    # SearchField: full-text indexed for search queries.
    # FilterField: used for exact-match filtering (e.g. "only active members").
    search_fields = [
        index.SearchField("first_name"),
        index.SearchField("last_name"),
        index.FilterField("rcs_id"),
    ]

    class Meta:
        ordering = ["last_name", "first_name"]
        verbose_name = "Member Profile"
        verbose_name_plural = "Member Profiles"

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.rcs_id})"


# ===========================================================================
# SNIPPET: MemberRoleAssignment
# ===========================================================================

# Snippet registered in wagtail_hooks.py
class MemberRoleAssignment(ClusterableModel):
    """
    Link between  a MemberProfile and a Role.

    This says "<member> has the role of <role>" in one place that member
    listing and committee pages from any branch can reference and display.
    """
    member = models.ForeignKey(
        "branches.MemberProfile",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="assignments",
        # Get assignments from member with member.assignments
    )
    role = models.ForeignKey(
        "branches.Role",
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="assignments",
        # Get assignments from role with role.assignments
    )
    
    panels = [
        FieldPanel("member"),
        FieldPanel("role"),
    ]
    
    class Meta:
        ordering = ["member", "role"]
        verbose_name = "Member-Role Assignment"
        verbose_name_plural = "Member-Role Assignments"

    def __str__(self):
        return f"{self.member}: {self.role}"


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
    image_credit = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Image credit",
        help_text="Name the photographer, organization, or other image source.",
    )
    image_credit_url = models.URLField(
        blank=True,
        verbose_name="Image source URL",
        help_text="Optional link to the original image or source.",
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
        FieldPanel("image_credit"),
        FieldPanel("image_credit_url"),
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

class MemberListingPage(Page, MembershipDisplay):
    """
    'Meet the Senate' / 'Meet the E-Board' style page.

    Displays members grouped into tiers by role hierarchy:
      1. Presiding Officer (GM, Union President, Council President, etc.)
      2. Officers of the Body (VPs, Secretary, Treasurer, etc.)
      3. Committee Chairs
      4. Voting Members
      5. Non-voting Members

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

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
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


class CommitteePage(Page, MembershipDisplay):
    """
    Individual committee page with description, meeting info, and members.
    
    The chair is displayed with a RoleConfig similarly to the branch
    MemberListingPage and ClassCouncilPage, but members are stored with
    a less rigid CommitteeMemberPlacement, allowing for greater
    customization in committee structure.
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
    ]

    parent_page_types = ["branches.CommitteeIndexPage"]
    subpage_types = []


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


class ClassCouncilPage(Page, MembershipDisplay):
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
