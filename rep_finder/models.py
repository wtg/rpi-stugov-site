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

from django.conf import settings
from django.core.mail import send_mail
from django.db import models
from django import forms

from modelcluster.fields import ParentalKey

from branches.models import Role, MemberProfile, MemberRoleAssignment, class_choices, FSL_CHOICES
from wagtail.fields import RichTextField
from wagtail.models import Page
from django.shortcuts import render
from django.db.models import Q
from wagtail.admin.panels import FieldPanel




# class RepsFormField(AbstractFormField):
#     """
#     A single field in a form (e.g., "Your Name", "Description of Complaint").

#     AbstractFormField provides:
#       - label: the field's visible label
#       - field_type: dropdown of HTML input types (text, email, textarea,
#         dropdown, checkboxes, radio buttons, date, URL, number, etc.)
#       - required: whether the field must be filled in
#       - choices: comma-separated options for dropdowns/checkboxes/radios
#       - default_value: pre-filled value
#       - help_text: hint text below the field

#     The ParentalKey links this to a specific RepsFormPage, so each
#     form page has its own independent set of fields.
#     """

#     page = ParentalKey(
#         "rep_finder.RepsFormPage",
#         on_delete=models.CASCADE,
#         related_name="form_fields",
#     )

#     help_text = RichTextField(blank=True)

class RepsForm(forms.Form):
    your_class = forms.ChoiceField(label="Choose Your Class Year", choices=class_choices(), widget=forms.Select(attrs={"class":"my-class"}))
    your_fsl_status = forms.ChoiceField(label="Are you affiliated with Greek Life?", choices=FSL_CHOICES, widget=forms.Select(attrs={"class":"my-class"}))        

    def get_class(self):
        return dict(self.fields["your_class"].choices)[self.cleaned_data["your_class"]]
        
    def get_fsl_status(self):
        return dict(self.fields["your_fsl_status"].choices)[self.cleaned_data["your_fsl_status"]]

    def get_class_representatives(self):
        chosen_constituency = self.data["your_class"]

        role_list = Role.objects.filter(constituency=chosen_constituency)

        role_assignments_list = []
        for role in role_list:
            role_assignments_list += role.assignments.all()
        
        member_profile_list = []
        for role_assignment in role_assignments_list:
            if role_assignment.member not in member_profile_list:
                member_profile_list += [role_assignment.member]
        
        return [
            {
                "member": member,
                "roles": [assignment.role.get_display_name() for assignment in member.assignments.all() if assignment.role.constituency==chosen_constituency]
            } for member in member_profile_list
        ]

    def get_fsl_representatives(self):
        chosen_fsl_status = self.data["your_fsl_status"]

        role_list = Role.objects.filter(constituency=chosen_fsl_status)

        role_assignments_list = []
        for role in role_list:
            role_assignments_list += role.assignments.all()
        
        member_profile_list = []
        for role_assignment in role_assignments_list:
            if role_assignment.member not in member_profile_list:
                member_profile_list += [role_assignment.member]
        
        return [
            {
                "member": member,
                "roles": [assignment.role.get_display_name() for assignment in member.assignments.all() if assignment.role.constituency==chosen_fsl_status]
            } for member in member_profile_list
        ]

    

class RepsFormPage(Page):
    parent_page_types = ["home.HomePage"]
    subpage_types = []

    intro = RichTextField(
        blank=True,
        help_text="Text shown above the form explaining its purpose.",
    )
    thank_you_text = RichTextField(
        blank=True,
        help_text="Text shown after a successful submission.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro")
    ]

    def serve(self, request):
        # if this is a POST request we need to process the form data
        if request.method == "POST":
            # create a form instance and populate it with data from the request:
            # form = RepsFormPage(request.POST)
            self.form = RepsForm(request.POST)
            # check whether it's valid:
            if self.form.is_valid():
                # process the data in form.cleaned_data as required
                # ...
                # redirect to a new URL:
                return render(request, "rep_finder/reps_form_page_landing.html", {"form": self.form, "page": self})
    
        # if a GET (or any other method) we'll create a blank form
        else:
            self.form = RepsForm()
    
    
        return render(request, "rep_finder/reps_form_page.html", {"form": self.form, "page": self})
    
    class Meta:
        verbose_name = "Representative Finder Form"
