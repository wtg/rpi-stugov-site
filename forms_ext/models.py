"""
Models for the Forms & Submissions app.

This app extends Wagtail's built-in form builder (wagtail.contrib.forms)
to create the Complaint Form and any future submission forms.

Key design decisions:
  - AbstractEmailForm (not AbstractForm) is used because submissions should
    be both stored in the database AND emailed to student government officers.
    AbstractForm only stores; AbstractEmailForm adds email notification.
  - FormField uses AbstractFormField which gives editors the power to
    add/remove/reorder form fields entirely through the Wagtail admin.
    No code changes needed to add a "Category" dropdown or rename a field.
  - The privacy_notice field lets admins display anonymity/privacy information
    near the form, which is important for a complaint submission system.

How Wagtail's form builder works:
  1. Admin creates a ComplaintFormPage in the page tree
  2. Admin adds FormField entries (name, email, textarea, dropdown, etc.)
     via InlinePanel — each FormField becomes one HTML input
  3. When a user submits the form, Wagtail:
     a) Validates the input
     b) Stores the submission in the database (viewable in Wagtail admin)
     c) Sends an email notification (if configured)
     d) Renders the thank_you_text as a landing page
"""

from django.db import models

from modelcluster.fields import ParentalKey

from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.fields import RichTextField


class FormField(AbstractFormField):
    """
    A single field in a form (e.g., "Your Name", "Description of Complaint").

    AbstractFormField provides:
      - label: the field's visible label
      - field_type: dropdown of HTML input types (text, email, textarea,
        dropdown, checkboxes, radio buttons, date, URL, number, etc.)
      - required: whether the field must be filled in
      - choices: comma-separated options for dropdowns/checkboxes/radios
      - default_value: pre-filled value
      - help_text: hint text below the field

    The ParentalKey links this to a specific ComplaintFormPage, so each
    form page has its own independent set of fields.
    """

    page = ParentalKey(
        "forms_ext.ComplaintFormPage",
        on_delete=models.CASCADE,
        related_name="form_fields",
    )

    help_text = RichTextField(blank=True)


class ComplaintFormPage(AbstractEmailForm):
    """
    Complaint/submission form page.

    AbstractEmailForm provides:
      - Form rendering and validation
      - Submission storage (viewable at Admin > Forms > [page name])
      - Email notification on submission
      - A process_form_submission() method you can override for custom logic

    The email fields (from_address, to_address, subject) are inherited
    from AbstractEmailForm and configured via the admin panels below.
    """

    intro = RichTextField(
        blank=True,
        help_text="Text shown above the form explaining its purpose.",
    )
    thank_you_text = RichTextField(
        blank=True,
        help_text="Text shown after a successful submission.",
    )
    privacy_notice = RichTextField(
        blank=True,
        help_text="Privacy/anonymity notice shown near the form. Important "
                  "for complaint forms where submitters may want assurance "
                  "of confidentiality.",
    )

    content_panels = AbstractEmailForm.content_panels + [
        FieldPanel("intro"),
        InlinePanel("form_fields", label="Form Fields"),
        FieldPanel("thank_you_text"),
        FieldPanel("privacy_notice"),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("from_address", classname="col6"),
                        FieldPanel("to_address", classname="col6"),
                    ]
                ),
                FieldPanel("subject"),
            ],
            heading="Email Notification Settings",
            help_text="Configure where submission notifications are sent. "
                      "Leave blank to disable email notifications.",
        ),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = []

    class Meta:
        verbose_name = "Complaint/Submission Form"
