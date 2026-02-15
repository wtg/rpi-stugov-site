from django.db import models

from wagtail import blocks
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.fields import StreamField
from wagtail.images.blocks import ImageBlock
from wagtail.admin.panels import FieldPanel

class BlogIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + ["intro"]

class BlogPage(Page):
    author = models.CharField(max_length=255, default="John Doe")
    date = models.DateField("Post date")
    intro = models.CharField(max_length=250)
    body = StreamField([
        ("heading", blocks.CharBlock(form_classname="title")),
        ("paragraph", blocks.RichTextBlock()),
        ("image", ImageBlock())
    ], null=True)

    content_panels = Page.content_panels + [
        FieldPanel("author"),
        FieldPanel("date"),
        FieldPanel("intro"),
        FieldPanel("body")
    ]
