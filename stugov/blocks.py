"""
Shared StreamField blocks used across all apps.

This module exists to avoid circular imports. Multiple apps (home, branches,
events, records) need the same block types. If blocks were defined inside
one app's models.py, other apps would need to import from it, risking
circular dependency chains. By defining them here in the project package,
all apps import from a neutral location.

StreamField blocks are the building blocks of flexible page content in Wagtail.
Each block defines:
  - What data it holds (fields)
  - How it appears in the admin editor (form)
  - How it renders on the frontend (template)
"""

from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.documents.blocks import DocumentChooserBlock


class CTABlock(blocks.StructBlock):
    """
    Call-to-action block — renders a styled button or link.

    Used on landing pages, branch pages, and flexible pages to direct
    users to important resources (forms, documents, external sites).

    Editors can link to either an internal Wagtail page OR an external URL.
    The 'style' field controls visual presentation (primary = bold color,
    secondary = outline, link = plain text link).
    """

    text = blocks.CharBlock(
        required=True,
        max_length=100,
        help_text="Button/link text, e.g. 'Get Involved' or 'View Constitution'",
    )
    url = blocks.URLBlock(
        required=False,
        help_text="External URL. Leave blank if linking to an internal page.",
    )
    page = blocks.PageChooserBlock(
        required=False,
        help_text="Internal page link. Takes precedence over external URL if both are set.",
    )
    style = blocks.ChoiceBlock(
        choices=[
            ("primary", "Primary Button"),
            ("secondary", "Secondary Button"),
            ("link", "Text Link"),
        ],
        default="primary",
    )

    class Meta:
        icon = "link"
        label = "Call to Action"
        template = "blocks/cta_block.html"


class InfoCardBlock(blocks.StructBlock):
    """
    Card block for displaying info items in a grid layout.

    Used to present branch overviews on the homepage, resource links on
    the club resources page, or any content that benefits from a
    card-based visual layout.
    """

    title = blocks.CharBlock(required=True)
    text = blocks.RichTextBlock(required=False)
    icon = blocks.CharBlock(
        required=False,
        help_text="Optional icon name (e.g., a Heroicon name for Tailwind)",
    )
    link = blocks.URLBlock(required=False)
    link_page = blocks.PageChooserBlock(required=False)

    class Meta:
        icon = "doc-full"
        label = "Info Card"
        template = "blocks/info_card_block.html"


class DocumentListBlock(blocks.StructBlock):
    """
    Block for listing downloadable documents.

    Renders a section heading followed by a list of document download links.
    Uses Wagtail's document chooser so editors pick from uploaded files
    rather than typing URLs.
    """

    heading = blocks.CharBlock(required=False)
    documents = blocks.ListBlock(DocumentChooserBlock())

    class Meta:
        icon = "doc-full-inverse"
        label = "Document List"
        template = "blocks/document_list_block.html"


class BoxEmbedBlock(blocks.StructBlock):
    """
    Block for embedding a Box folder or file viewer.

    The infrastructure plan uses Box for larger archival storage.
    This block lets editors embed a Box shared folder view directly
    into a page, giving students access to archived documents without
    leaving the site.
    """

    box_url = blocks.URLBlock(
        required=True,
        help_text="Box shared link URL for the folder or file to embed.",
    )
    height = blocks.IntegerBlock(
        default=500,
        help_text="Height of the embedded viewer in pixels.",
    )
    caption = blocks.CharBlock(
        required=False,
        help_text="Optional caption below the embed.",
    )

    class Meta:
        icon = "folder-open-inverse"
        label = "Box Embed"
        template = "blocks/box_embed_block.html"


# ---------------------------------------------------------------------------
# STANDARD_STREAMFIELD_BLOCKS
# ---------------------------------------------------------------------------
# This list is the "palette" of blocks available in StreamField-based pages.
# Every page that uses StreamField for its body content should reference this
# list so that editors have a consistent set of content blocks across the site.
#
# To add a new block type site-wide, add it here and it becomes available
# everywhere. To add a block to only one page type, define it in that
# page's model instead.
# ---------------------------------------------------------------------------

STANDARD_STREAMFIELD_BLOCKS = [
    ("heading", blocks.CharBlock(form_classname="title")),
    ("paragraph", blocks.RichTextBlock()),
    ("image", ImageChooserBlock()),
    ("document_list", DocumentListBlock()),
    ("call_to_action", CTABlock()),
    ("info_cards", blocks.ListBlock(InfoCardBlock(), icon="grip")),
    ("box_embed", BoxEmbedBlock()),
    ("raw_html", blocks.RawHTMLBlock(
        help_text="Use sparingly. For embedding widgets, iframes, or custom HTML.",
    )),
    ("blockquote", blocks.BlockQuoteBlock()),
]
