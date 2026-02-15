"""
Models for the Records & Documents app.

This app manages meeting minutes, the constitution, bylaws, resolutions,
and other official documents. It supports:
  - Box as the primary/single-source-of-truth for public documents
  - Embedded Box viewer for inline document preview
  - Fallback Wagtail document attachments for files not in Box
  - Categorization by type and academic year
  - Basic access control (public vs. logged-in-only)
  - Filtering on the index page

Key design decisions:
  - Box is the Single Source of Truth for public records. This means
    officers update documents in Box and the website automatically
    reflects the latest version. This eliminates the "forgot to update
    the website" problem that student government turnover causes.
  - RecordPage has a box_url field that, when populated, renders an
    embedded Box viewer on the page. The Box viewer handles previewing,
    versioning, and downloading natively — no need to duplicate that
    functionality in Wagtail.
  - RecordDocument (Wagtail file attachments) is kept as a fallback
    for documents that don't belong in Box — internal drafts, files
    too sensitive for a shared Box folder, or records where Box isn't
    practical. The template shows Box embed first, then falls back to
    direct downloads.
  - RecordIndexPage can live under HomePage (for the site-wide "The Record"
    section) OR under a BranchPage (for branch-specific records).
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
    An attached document file for a RecordPage (fallback when not using Box).

    This is the secondary option — use it when a document doesn't belong
    in Box (internal drafts, sensitive files, or one-off attachments).
    For most public records, the Box embed on RecordPage is preferred
    because Box handles versioning, previewing, and downloading natively.

    Kept as an Orderable so multiple files can be attached to a single
    record, with drag-and-drop reordering in the admin.
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

    Document sourcing strategy (in priority order):
      1. Box embed (box_url) — the primary approach for public records.
         When set, the page renders an embedded Box viewer that lets
         visitors preview and download directly from Box. Box is the
         Single Source of Truth: officers update documents in Box, and
         the website automatically reflects the latest version.
      2. Wagtail attachments (RecordDocument) — the fallback for files
         not in Box. Used for internal drafts, sensitive files, or
         records where Box embedding isn't practical.
      3. Body text — for records that are pure text content rather than
         a document file (e.g., a resolution's full text).

    The template checks these in order: Box embed first, then Wagtail
    attachments, then body text. A record can use any combination.

    Access control:
      - is_public=True (default): anyone can view the record page.
        Note: the Box document itself has its own sharing permissions
        in Box — the is_public flag only controls the Wagtail page.
      - is_public=False: only logged-in users can view (serve() redirects).
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

    # -- Box integration (primary document source) --
    box_url = models.URLField(
        blank=True,
        verbose_name="Box shared link",
        help_text="Paste the Box shared link for this document. The page will "
                  "show an embedded viewer so visitors can preview and download "
                  "directly from Box. This is the preferred approach for public "
                  "records — Box is the single source of truth.",
    )
    box_embed_height = models.PositiveIntegerField(
        default=600,
        help_text="Height in pixels for the embedded Box viewer.",
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
        # -- Box embed is the PRIMARY document source, so it comes first --
        # Editors see Box fields before Wagtail attachments, reinforcing
        # that Box is the preferred approach.
        MultiFieldPanel(
            [
                FieldPanel("box_url"),
                FieldPanel("box_embed_height"),
            ],
            heading="Box Document (preferred)",
            help_text="Paste a Box shared link to embed the document viewer. "
                      "This is the recommended approach for public records. "
                      "Box handles versioning and previewing automatically.",
        ),
        # -- Wagtail attachments are the FALLBACK, shown after Box --
        InlinePanel(
            "documents",
            label="Direct File Attachments (fallback)",
            help_text="Only use this if the document is NOT in Box. For most "
                      "public records, paste the Box link above instead.",
        ),
        FieldPanel("body"),
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

    @property
    def box_embed_url(self):
        """
        Convert a Box shared link to an embeddable URL.

        Box shared links look like:
            https://rpi.box.com/s/abc123xyz
        The embeddable version is:
            https://rpi.box.com/embed/s/abc123xyz

        The embed URL renders Box's built-in document viewer (PDF preview,
        download button, etc.) inside an iframe. This is the same viewer
        Box uses on its own site — it supports PDFs, Office docs, images,
        and many other file types.

        If the URL is already an embed URL or doesn't match the expected
        pattern, we return it as-is and let Box handle any errors.
        """
        if not self.box_url:
            return ""
        url = self.box_url.strip()
        # Convert /s/ shared links to /embed/s/ embed links
        if "/s/" in url and "/embed/" not in url:
            url = url.replace("/s/", "/embed/s/", 1)
        return url

    @property
    def has_box_document(self):
        """Check whether this record has a Box link configured."""
        return bool(self.box_url)

    @property
    def has_wagtail_documents(self):
        """Check whether this record has Wagtail file attachments."""
        return self.documents.exists()

    def serve(self, request, *args, **kwargs):
        """
        Override serve() to enforce access control for non-public records.

        Wagtail calls serve() when a page is requested. By overriding it,
        we can check permissions before rendering. If the record is private
        and the user isn't logged in, we redirect to the login page with
        a ?next= parameter so they're sent back after authenticating.

        Note: this only controls access to the Wagtail page. The Box
        document itself has its own sharing permissions managed in Box.
        If the Box link is set to "anyone with the link," the document
        is accessible regardless of this flag. To truly restrict a
        document, set it to private in BOTH Box AND Wagtail.
        """
        if not self.is_public and not request.user.is_authenticated:
            login_url = reverse("wagtailadmin_login")
            return redirect(f"{login_url}?next={self.url}")
        return super().serve(request, *args, **kwargs)

    class Meta:
        verbose_name = "Record"
        ordering = ["-date_published"]
