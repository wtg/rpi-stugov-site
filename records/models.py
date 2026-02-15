"""
Models for the Records & Documents app.

This app manages meeting minutes, the constitution, bylaws, resolutions,
and other official documents. It supports:
  - Categorization by type and academic year
  - Multiple file attachments per record (for version history)
  - Basic access control (public vs. logged-in-only)
  - Filtering on the index page

Key design decisions:
  - RecordIndexPage can live under HomePage (for the site-wide "The Record"
    section) OR under a BranchPage (for branch-specific records). This
    avoids needing separate models for site-wide vs. branch records.
  - RecordDocument is an Orderable attached to RecordPage, allowing
    multiple file versions per record. This handles the infrastructure
    plan's requirement for version history on the constitution and bylaws.
  - The is_public field with a serve() override provides simple view-level
    access control without needing Wagtail's full group permissions system.
"""

from django.db import models
from django.shortcuts import redirect
from django.urls import reverse

from modelcluster.fields import ParentalKey

from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Orderable, Page
from wagtail.search import index


RECORD_TYPE_CHOICES = [
    ("minutes", "Meeting Minutes"),
    ("constitution", "Constitution"),
    ("bylaws", "Bylaws"),
    ("resolution", "Resolution"),
    ("report", "Report"),
    ("policy", "Policy Document"),
    ("budget", "Budget"),
    ("other", "Other"),
]

RECORD_BRANCH_CHOICES = [
    ("senate", "Student Senate"),
    ("eboard", "Executive Board"),
    ("uc", "Undergraduate Council"),
    ("gc", "Graduate Council"),
    ("jboard", "Judicial Board"),
    ("general", "General / All"),
]


class RecordIndexPage(Page):
    """
    Index page for records/documents.

    Provides a filterable listing of child RecordPages. The filtering
    is done via query parameters (e.g. /the-record/?type=minutes&year=2025-2026)
    which the get_context() method reads and applies.

    Can live under:
      - HomePage: for the site-wide "The Record" section
      - BranchPage: for branch-specific records (e.g. "Senate Records")
    """

    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = [
        "home.HomePage",
        "branches.BranchPage",
    ]
    subpage_types = ["records.RecordPage"]

    def get_context(self, request, *args, **kwargs):
        """
        Build the filtered record listing for the template.

        Query parameters:
          ?type=minutes     -> filter by record type
          ?year=2025-2026   -> filter by academic year

        The template receives 'records', 'record_types' (for the filter
        dropdown), and 'active_type'/'active_year' (to highlight the
        current filter selection).
        """
        context = super().get_context(request, *args, **kwargs)
        records = RecordPage.objects.live().descendant_of(self)

        # Apply filters from query params
        record_type = request.GET.get("type")
        if record_type:
            records = records.filter(record_type=record_type)

        year = request.GET.get("year")
        if year:
            records = records.filter(academic_year=year)

        context["records"] = records.order_by("-date_published")
        context["record_types"] = RECORD_TYPE_CHOICES
        context["active_type"] = record_type
        context["active_year"] = year

        # Build a list of unique academic years for the year filter dropdown
        context["available_years"] = (
            RecordPage.objects.live()
            .descendant_of(self)
            .exclude(academic_year="")
            .values_list("academic_year", flat=True)
            .distinct()
            .order_by("-academic_year")
        )

        return context

    class Meta:
        verbose_name = "Record Index Page"


class RecordDocument(Orderable):
    """
    An attached document file for a RecordPage.

    This is an Orderable (not a standalone model) because document
    attachments only make sense in the context of a specific record.
    Using Orderable + InlinePanel lets admins upload multiple files
    per record and reorder them via drag-and-drop.

    The version_label field enables explicit version tracking:
      - "v1.0 (Original)"
      - "v1.1 (Amended March 2025)"
      - "v2.0 (Rewritten January 2026)"

    This is simpler than Wagtail's built-in page revision system
    (which tracks every edit) because it gives editors control over
    which versions are meaningful to publish.
    """

    page = ParentalKey(
        "records.RecordPage",
        related_name="documents",
    )
    document = models.ForeignKey(
        "wagtaildocs.Document",
        on_delete=models.CASCADE,
        related_name="+",
    )
    version_label = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g. 'v2.1' or 'Amended 2025-03'.",
    )

    panels = [
        FieldPanel("document"),
        FieldPanel("version_label"),
    ]


class RecordPage(Page):
    """
    An individual record/document (meeting minutes, constitution, etc.).

    Each record has metadata (type, date, academic year, branch),
    optional body text, and one or more attached document files.

    The is_public field provides simple access control:
      - True (default): anyone can view
      - False: only logged-in users can view (serve() redirects to login)

    This is intentionally simple. For more granular permissions (e.g.
    "only Senate members can see Senate budgets"), you'd use Wagtail's
    group-based page permissions, but that's overkill for the initial launch.
    """

    record_type = models.CharField(
        max_length=20,
        choices=RECORD_TYPE_CHOICES,
        default="minutes",
    )
    date_published = models.DateField(
        help_text="Date the record was published or approved.",
    )
    academic_year = models.CharField(
        max_length=9,
        blank=True,
        help_text="e.g. '2025-2026'. Used for filtering.",
    )
    summary = RichTextField(
        blank=True,
        help_text="Brief summary of the record's contents.",
    )
    body = RichTextField(
        blank=True,
        help_text="Full text content (if the record isn't just an attached file).",
    )
    branch = models.CharField(
        max_length=20,
        choices=RECORD_BRANCH_CHOICES,
        default="general",
    )
    is_public = models.BooleanField(
        default=True,
        help_text="Uncheck to restrict viewing to logged-in users only.",
    )

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("record_type"),
                FieldPanel("date_published"),
                FieldPanel("academic_year"),
                FieldPanel("branch"),
            ],
            heading="Record Metadata",
        ),
        FieldPanel("summary"),
        FieldPanel("body"),
        InlinePanel(
            "documents",
            label="Attached Documents",
            help_text="Upload document files. Add multiple entries for version history.",
        ),
        FieldPanel("is_public"),
    ]

    search_fields = Page.search_fields + [
        index.SearchField("summary"),
        index.SearchField("body"),
        index.FilterField("record_type"),
        index.FilterField("date_published"),
        index.FilterField("branch"),
        index.FilterField("is_public"),
    ]

    parent_page_types = ["records.RecordIndexPage"]
    subpage_types = []

    def serve(self, request, *args, **kwargs):
        """
        Override serve() to enforce access control for non-public records.

        Wagtail calls serve() when a page is requested. By overriding it,
        we can check permissions before rendering. If the record is private
        and the user isn't logged in, we redirect to the login page with
        a ?next= parameter so they're sent back after authenticating.

        This is the standard Wagtail pattern for view-level access control
        on individual pages. It's simpler than middleware-based approaches
        because the logic lives right on the model that needs it.
        """
        if not self.is_public and not request.user.is_authenticated:
            login_url = reverse("wagtailadmin_login")
            return redirect(f"{login_url}?next={self.url}")
        return super().serve(request, *args, **kwargs)

    class Meta:
        verbose_name = "Record"
        ordering = ["-date_published"]
