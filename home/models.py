"""
Models for the Home app.

This app contains:
  - HomePage: the site's landing page (enhanced with StreamField)
  - HomePageQuickLink: ordered quick-link buttons on the homepage
  - SiteSettings: global configuration (social links, contact info)

Key design decisions:
  - HomePage.body is upgraded from RichTextField to StreamField. This is a
    breaking change that requires a data migration (see migration 0004).
    StreamField gives editors structured content blocks instead of a single
    rich text blob, making the homepage layout more consistent and maintainable.
  - SiteSettings uses Wagtail's BaseGenericSetting (a singleton) rather than
    storing social links on the HomePage. This is because social links,
    contact info, and the Discord URL appear site-wide (in the footer/nav),
    not just on the homepage. BaseGenericSetting makes these values available
    in every template via a context processor.
  - HomePageQuickLink is an Orderable so the homepage can display 4-6
    prominent links (to Senate, E-Board, Get Involved, etc.) that admins
    can reorder via drag-and-drop.
"""

from django.db import models

from modelcluster.fields import ParentalKey

from wagtail import blocks
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.fields import RichTextField, StreamField
from wagtail.images import get_image_model_string
from wagtail.images.blocks import ImageChooserBlock
from wagtail.models import Orderable, Page

from stugov.blocks import CTABlock, InfoCardBlock


class HomePage(Page):
    """
    The site's main landing page.

    Displays a hero section, quick links to key pages, upcoming events
    (pulled in via get_context), and flexible body content via StreamField.

    max_count = 1 enforces that only one HomePage can exist in the page
    tree. This is a Wagtail convention for singleton pages.
    """

    # -- Hero section --
    hero_title = models.CharField(
        max_length=255,
        blank=True,
        default="RPI Student Government",
    )
    hero_subtitle = models.CharField(
        max_length=500,
        blank=True,
        help_text="Shown below the main title in the hero section.",
    )
    hero_image = models.ForeignKey(
        get_image_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    # -- Body content --
    # StreamField replaces the old RichTextField. Each block type in the
    # list becomes an option in the editor's block picker.
    body = StreamField(
        [
            ("heading", blocks.CharBlock(form_classname="title")),
            ("paragraph", blocks.RichTextBlock()),
            ("image", ImageChooserBlock()),
            (
                "info_cards",
                blocks.ListBlock(
                    InfoCardBlock(),
                    icon="grip",
                    label="Info Cards",
                ),
            ),
            ("call_to_action", CTABlock()),
        ],
        blank=True,
        use_json_field=True,
    )

    # -- Admin panels --
    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("hero_title"),
                FieldPanel("hero_subtitle"),
                FieldPanel("hero_image"),
            ],
            heading="Hero Section",
        ),
        FieldPanel("body"),
        InlinePanel("quick_links", label="Quick Links", max_num=6),
    ]

    # -- Page hierarchy --
    subpage_types = [
        "branches.BranchPage",
        "branches.FlexiblePage",
        "blog.BlogIndexPage",
        "events.EventIndexPage",
        "forms_ext.ComplaintFormPage",
        "records.RecordIndexPage",
    ]
    max_count = 1  # Only one homepage allowed

    def get_context(self, request, *args, **kwargs):
        """
        Add upcoming events to the homepage template context.

        This import is inside the method (not at module top) to avoid
        a circular import: home.models would import events.models, but
        events.models references home.HomePage in parent_page_types.
        Django resolves string references ("home.HomePage") lazily, but
        Python-level imports would create a cycle.
        """
        context = super().get_context(request, *args, **kwargs)

        from events.models import EventPage

        from django.utils import timezone

        context["upcoming_events"] = (
            EventPage.objects.live()
            .filter(start_date__gte=timezone.now().date())
            .order_by("start_date", "start_time")[:5]
        )
        return context

    class Meta:
        verbose_name = "Home Page"


class HomePageQuickLink(Orderable):
    """
    A prominent quick-link on the homepage (e.g., "Student Senate", "Get Involved").

    Orderable so admins can reorder them via drag-and-drop. Each link can
    point to either an internal Wagtail page or an external URL.
    """

    page = ParentalKey("home.HomePage", related_name="quick_links")
    link_text = models.CharField(max_length=100)
    link_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Internal page to link to. Takes priority over external URL.",
    )
    link_url = models.URLField(
        blank=True,
        help_text="External URL. Used only if no internal page is selected.",
    )
    icon_class = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional CSS/icon class for visual decoration.",
    )

    panels = [
        FieldPanel("link_text"),
        FieldPanel("link_page"),
        FieldPanel("link_url"),
        FieldPanel("icon_class"),
    ]

    @property
    def url(self):
        """Return the internal page URL if set, otherwise the external URL."""
        if self.link_page:
            return self.link_page.url
        return self.link_url


# ===========================================================================
# SITE SETTINGS (global configuration)
# ===========================================================================

@register_setting
class SiteSettings(BaseGenericSetting):
    """
    Global site settings accessible in every template.

    BaseGenericSetting creates a singleton object in the Wagtail admin
    (under Settings > Site Settings). There's exactly one instance of
    this model for the entire site.

    In templates, access these values with:
      {% load wagtailsettings_tags %}
      {{ settings.home.SiteSettings.discord_url }}

    The context processor we added to settings/base.py
    ("wagtail.contrib.settings.context_processors.settings") is what
    makes this work. Without it, you'd have to manually pass settings
    into every template's context.
    """

    # -- Social media --
    discord_url = models.URLField(blank=True, verbose_name="Discord Invite URL")
    instagram_url = models.URLField(blank=True, verbose_name="Instagram URL")
    facebook_url = models.URLField(blank=True, verbose_name="Facebook URL")
    twitter_url = models.URLField(blank=True, verbose_name="Twitter/X URL")

    # -- Contact --
    contact_email = models.EmailField(
        blank=True,
        verbose_name="General Contact Email",
        help_text="e.g. union_officers@union.lists.rpi.edu",
    )
    office_location = models.CharField(
        max_length=255,
        blank=True,
        help_text="e.g. 'Student Government Suite, 3rd Floor, Rensselaer Union'",
    )
    office_hours = models.CharField(
        max_length=255,
        blank=True,
        help_text="e.g. 'Mon-Fri 9am-5pm'",
    )

    # -- Footer --
    footer_text = RichTextField(
        blank=True,
        features=["bold", "italic", "link"],
    )

    # -- Box integration --
    box_archive_url = models.URLField(
        blank=True,
        verbose_name="Box Archive URL",
        help_text="Link to the main Box folder for archival documents.",
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("discord_url"),
                FieldPanel("instagram_url"),
                FieldPanel("facebook_url"),
                FieldPanel("twitter_url"),
            ],
            heading="Social Media Links",
        ),
        MultiFieldPanel(
            [
                FieldPanel("contact_email"),
                FieldPanel("office_location"),
                FieldPanel("office_hours"),
            ],
            heading="Contact Information",
        ),
        FieldPanel("footer_text"),
        FieldPanel("box_archive_url"),
    ]

    class Meta:
        verbose_name = "Site Settings"
