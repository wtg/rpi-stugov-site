"""
Models for the Events & Calendar app.

This app provides a native event/calendar system. The EventIndexPage
serves as both a human-readable event listing AND a JSON API endpoint
(via RoutablePageMixin) that a JavaScript calendar widget can fetch
events from asynchronously.

Key design decisions:
  - RoutablePageMixin lets one page handle multiple URL patterns.
    The main URL (/events/) renders the calendar page, while
    /events/api/events/?month=3&year=2026 returns JSON for the
    calendar widget to consume without a full page reload.
  - Events are Page objects (not Snippets) because each event has
    its own URL and detail page.
  - The 'branch' field lets events be categorized by which government
    branch hosts them, enabling filtered views.
"""

from django.db import models
from django.http import JsonResponse
from django.utils import timezone

from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.contrib.routable_page.models import RoutablePageMixin, path
from wagtail.fields import RichTextField
from wagtail.models import Page
from wagtail.search import index


# Branch choices duplicated here to avoid importing from branches app.
# An alternative would be a shared constants module, but for 6 choices
# the duplication is simpler than the abstraction.
EVENT_BRANCH_CHOICES = [
    ("senate", "Student Senate"),
    ("eboard", "Executive Board"),
    ("uc", "Undergraduate Council"),
    ("gc", "Graduate Council"),
    ("jboard", "Judicial Board"),
    ("all", "All / General"),
]

EVENT_TYPE_CHOICES = [
    ("meeting", "Meeting"),
    ("hearing", "Hearing"),
    ("election", "Election"),
    ("social", "Social Event"),
    ("workshop", "Workshop"),
    ("symposium", "Symposium"),
    ("other", "Other"),
]


class EventIndexPage(RoutablePageMixin, Page):
    """
    Calendar / event listing page.

    RoutablePageMixin allows this single page to serve multiple URL patterns:
      /events/          -> the main calendar/listing view (default serve())
      /events/api/events/ -> JSON endpoint for the calendar JS widget

    Without RoutablePageMixin, you'd need a separate Django URL route and
    view function for the API, disconnected from the Wagtail page tree.
    With it, the API endpoint is "owned" by this page and automatically
    respects Wagtail's publish/unpublish workflow.
    """

    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = ["events.EventPage"]

    def get_context(self, request, *args, **kwargs):
        """
        Provide upcoming and recent past events to the template.

        The template uses 'upcoming_events' for the main listing and
        'past_events' for a "recent past" section. Limiting past events
        to 10 keeps the page from growing unbounded.
        """
        context = super().get_context(request, *args, **kwargs)
        today = timezone.now().date()

        context["upcoming_events"] = (
            EventPage.objects.live()
            .descendant_of(self)
            .filter(start_date__gte=today)
            .order_by("start_date", "start_time")
        )
        context["past_events"] = (
            EventPage.objects.live()
            .descendant_of(self)
            .filter(start_date__lt=today)
            .order_by("-start_date", "-start_time")[:10]
        )
        return context

    @path("api/events/")
    def events_api(self, request):
        """
        JSON API endpoint for the JavaScript calendar widget.

        The calendar widget makes fetch() requests to this URL with
        month/year query parameters. This endpoint returns matching
        events as JSON so the calendar can update without a full page
        reload.

        Example: GET /events/api/events/?month=3&year=2026
        Returns: { "events": [ { "title": "...", "start_date": "..." }, ... ] }
        """
        events = EventPage.objects.live().descendant_of(self)

        # Filter by month/year if provided
        month = request.GET.get("month")
        year = request.GET.get("year")
        if month and year:
            try:
                events = events.filter(
                    start_date__year=int(year),
                    start_date__month=int(month),
                )
            except (ValueError, TypeError):
                pass  # Invalid params — return all events

        # Filter by branch if provided
        branch = request.GET.get("branch")
        if branch and branch != "all":
            events = events.filter(branch=branch)

        data = [
            {
                "title": e.title,
                "start_date": e.start_date.isoformat(),
                "end_date": e.end_date.isoformat() if e.end_date else None,
                "start_time": e.start_time.isoformat() if e.start_time else None,
                "end_time": e.end_time.isoformat() if e.end_time else None,
                "location": e.location,
                "url": e.url,
                "branch": e.branch,
                "event_type": e.event_type,
            }
            for e in events.order_by("start_date", "start_time")
        ]
        return JsonResponse({"events": data})

    class Meta:
        verbose_name = "Event Index Page"


class EventPage(Page):
    """
    An individual event.

    Each event is a Page (not a Snippet) because it has its own URL
    and detail page. Events appear as children of the EventIndexPage
    in the page tree.

    The date/time fields are split (start_date is required, times are
    optional) because some events are all-day (just a date) while
    others have specific start/end times.
    """

    # -- Date & Time --
    start_date = models.DateField()
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Leave blank for single-day events.",
    )
    start_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Leave blank for all-day events.",
    )
    end_time = models.TimeField(null=True, blank=True)

    # -- Details --
    location = models.CharField(max_length=255, blank=True)
    description = RichTextField(blank=True)

    # -- Categorization --
    branch = models.CharField(
        max_length=20,
        choices=EVENT_BRANCH_CHOICES,
        default="all",
        help_text="Which branch hosts this event.",
    )
    event_type = models.CharField(
        max_length=30,
        choices=EVENT_TYPE_CHOICES,
        default="meeting",
    )

    # -- Recurrence --
    # True recurrence (auto-generating future events) is complex and
    # rarely worth the implementation cost. Instead, we use a simple
    # boolean flag and a human-readable note. Editors create individual
    # events for each occurrence.
    is_recurring = models.BooleanField(default=False)
    recurrence_note = models.CharField(
        max_length=255,
        blank=True,
        help_text="Informational only, e.g. 'Every Monday at 7pm'.",
    )

    # -- External link --
    external_link = models.URLField(
        blank=True,
        help_text="Link to Zoom, external event page, etc.",
    )

    # -- Admin panels --
    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("start_date"),
                FieldPanel("end_date"),
                FieldPanel("start_time"),
                FieldPanel("end_time"),
            ],
            heading="Date & Time",
        ),
        FieldPanel("location"),
        FieldPanel("description"),
        MultiFieldPanel(
            [
                FieldPanel("branch"),
                FieldPanel("event_type"),
            ],
            heading="Categorization",
        ),
        MultiFieldPanel(
            [
                FieldPanel("is_recurring"),
                FieldPanel("recurrence_note"),
            ],
            heading="Recurrence",
        ),
        FieldPanel("external_link"),
    ]

    # -- Search indexing --
    search_fields = Page.search_fields + [
        index.SearchField("description"),
        index.SearchField("location"),
        index.FilterField("start_date"),
        index.FilterField("branch"),
        index.FilterField("event_type"),
    ]

    parent_page_types = ["events.EventIndexPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Event"
        ordering = ["-start_date", "-start_time"]
