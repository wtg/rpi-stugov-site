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
  - Recurring events store a frequency + end date. Occurrences are
    computed dynamically (no duplicate pages). The JSON API expands
    them so the calendar widget shows dots on every occurrence day.
"""

import calendar as cal_mod
import datetime

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

RECURRENCE_CHOICES = [
    ("none", "Does not repeat"),
    ("daily", "Daily"),
    ("weekly", "Weekly"),
    ("biweekly", "Every two weeks"),
    ("monthly", "Monthly"),
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

        For recurring events, an event's start_date may be in the past
        but it still has upcoming occurrences. We include those by
        checking recurrence_end_date >= today as well.
        """
        context = super().get_context(request, *args, **kwargs)
        today = timezone.now().date()

        all_events = EventPage.objects.live().descendant_of(self)

        # Upcoming: non-recurring with future start_date OR recurring
        # events whose recurrence range extends past today
        context["upcoming_events"] = (
            all_events.filter(
                models.Q(recurrence_frequency="none", start_date__gte=today)
                | models.Q(
                    ~models.Q(recurrence_frequency="none"),
                    recurrence_end_date__gte=today,
                )
            )
            .order_by("start_date", "start_time")
        )

        # Past: non-recurring events in the past, and recurring events
        # whose recurrence has fully ended
        context["past_events"] = (
            all_events.filter(
                models.Q(recurrence_frequency="none", start_date__lt=today)
                | models.Q(
                    ~models.Q(recurrence_frequency="none"),
                    recurrence_end_date__lt=today,
                )
            )
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

        For recurring events, this endpoint expands occurrences: a
        weekly event will produce 4-5 JSON entries per month, each
        with the correct start_date for that occurrence.

        Example: GET /events/api/events/?month=3&year=2026
        Returns: { "events": [ { "title": "...", "start_date": "..." }, ... ] }
        """
        month = request.GET.get("month")
        year = request.GET.get("year")

        # We need all events that *could* have occurrences in this month,
        # not just those whose start_date falls in this month. A recurring
        # event starting in January with end_date in June should show up
        # in every month from Jan-Jun.
        events_qs = EventPage.objects.live().descendant_of(self)

        # Filter by branch if provided
        branch = request.GET.get("branch")
        if branch and branch != "all":
            events_qs = events_qs.filter(branch=branch)

        data = []

        if month and year:
            try:
                m, y = int(month), int(year)
            except (ValueError, TypeError):
                m, y = None, None

            if m and y:
                # For this month, find:
                # 1. Non-recurring events whose start_date is in this month
                # 2. Recurring events whose range overlaps this month
                _, days_in_month = cal_mod.monthrange(y, m)
                month_end = datetime.date(y, m, days_in_month)
                month_start = datetime.date(y, m, 1)

                candidates = events_qs.filter(
                    models.Q(recurrence_frequency="none", start_date__year=y, start_date__month=m)
                    | models.Q(
                        ~models.Q(recurrence_frequency="none"),
                        start_date__lte=month_end,
                        recurrence_end_date__gte=month_start,
                    )
                )

                for e in candidates.order_by("start_date", "start_time"):
                    for occ_date in e.occurrences(y, m):
                        data.append({
                            "title": e.title,
                            "start_date": occ_date.isoformat(),
                            "end_date": e.end_date.isoformat() if e.end_date else None,
                            "start_time": e.start_time.isoformat() if e.start_time else None,
                            "end_time": e.end_time.isoformat() if e.end_time else None,
                            "location": e.location,
                            "url": e.url,
                            "branch": e.branch,
                            "event_type": e.event_type,
                        })

                data.sort(key=lambda x: (x["start_date"], x["start_time"] or ""))
            else:
                # Invalid params — fall through to non-filtered
                data = self._serialize_events(events_qs)
        else:
            data = self._serialize_events(events_qs)

        return JsonResponse({"events": data})

    @staticmethod
    def _serialize_events(queryset):
        """Serialize a queryset of EventPages to a list of dicts (no recurrence expansion)."""
        return [
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
            for e in queryset.order_by("start_date", "start_time")
        ]

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
    # Instead of creating duplicate pages for each occurrence, we store
    # a recurrence rule here. The occurrences() method computes dates
    # dynamically, and the JSON API expands them for the calendar widget.
    recurrence_frequency = models.CharField(
        max_length=20,
        choices=RECURRENCE_CHOICES,
        default="none",
        help_text="How often this event repeats.",
    )
    recurrence_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="When the recurrence stops. Required for repeating events.",
    )
    recurrence_note = models.CharField(
        max_length=255,
        blank=True,
        help_text="Human-readable note, e.g. 'Every Monday at 7pm during Fall semester'.",
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
                FieldPanel("recurrence_frequency"),
                FieldPanel("recurrence_end_date"),
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

    @property
    def is_recurring(self):
        """Convenience check for templates and code."""
        return self.recurrence_frequency != "none"

    def occurrences(self, year, month):
        """
        Compute all occurrence dates for this event within a given month.

        For non-recurring events, returns [self.start_date] if it falls
        in the requested month, otherwise [].

        For recurring events, walks from start_date by the recurrence
        interval, collecting dates that land in the requested month and
        are before recurrence_end_date.

        Returns a list of datetime.date objects, sorted ascending.
        """
        if self.recurrence_frequency == "none":
            if self.start_date.year == year and self.start_date.month == month:
                return [self.start_date]
            return []

        end = self.recurrence_end_date or self.start_date
        # Bounds of the requested month
        month_start = datetime.date(year, month, 1)
        _, days_in_month = cal_mod.monthrange(year, month)
        month_end = datetime.date(year, month, days_in_month)

        # If the recurrence ends before this month or starts after, skip
        if end < month_start or self.start_date > month_end:
            return []

        freq = self.recurrence_frequency
        results = []
        current = self.start_date

        if freq == "monthly":
            # For monthly recurrence, jump directly to the target month
            # to avoid iterating through potentially hundreds of months.
            day = self.start_date.day
            try:
                candidate = datetime.date(year, month, day)
            except ValueError:
                # Day doesn't exist in this month (e.g. 31st in April).
                # Use last day of month.
                candidate = month_end
            if candidate >= self.start_date and candidate <= end:
                results.append(candidate)
        else:
            # daily / weekly / biweekly — step from start_date
            if freq == "daily":
                delta = datetime.timedelta(days=1)
            elif freq == "weekly":
                delta = datetime.timedelta(weeks=1)
            elif freq == "biweekly":
                delta = datetime.timedelta(weeks=2)
            else:
                return []

            # Fast-forward to the start of the month (or start_date)
            if current < month_start:
                # Calculate how many steps to skip
                days_behind = (month_start - current).days
                steps = days_behind // delta.days
                current += delta * steps
                # current might be just before month_start, step once more
                if current < month_start:
                    current += delta

            while current <= month_end and current <= end:
                if current >= month_start:
                    results.append(current)
                current += delta

        return sorted(results)

    def next_occurrence(self, after=None):
        """
        Return the next occurrence date on or after the given date.

        For non-recurring events, returns start_date if it's on or after
        `after`, otherwise None.

        Useful for the upcoming events listing — a weekly event whose
        start_date is in the past still has future occurrences.
        """
        if after is None:
            after = timezone.now().date()

        if self.recurrence_frequency == "none":
            return self.start_date if self.start_date >= after else None

        end = self.recurrence_end_date or self.start_date
        if end < after:
            return None

        freq = self.recurrence_frequency
        current = self.start_date

        if freq == "monthly":
            # Jump forward month by month
            y, m = after.year, after.month
            day = self.start_date.day
            # Try current month
            for _ in range(24):  # safety bound: 2 years
                try:
                    candidate = datetime.date(y, m, day)
                except ValueError:
                    _, last = cal_mod.monthrange(y, m)
                    candidate = datetime.date(y, m, last)
                if candidate >= after and candidate >= self.start_date and candidate <= end:
                    return candidate
                # Next month
                m += 1
                if m > 12:
                    m = 1
                    y += 1
            return None
        else:
            if freq == "daily":
                delta = datetime.timedelta(days=1)
            elif freq == "weekly":
                delta = datetime.timedelta(weeks=1)
            elif freq == "biweekly":
                delta = datetime.timedelta(weeks=2)
            else:
                return None

            # Fast-forward
            if current < after:
                days_behind = (after - current).days
                steps = days_behind // delta.days
                current += delta * steps
                if current < after:
                    current += delta

            return current if current <= end else None

    class Meta:
        verbose_name = "Event"
        ordering = ["-start_date", "-start_time"]
