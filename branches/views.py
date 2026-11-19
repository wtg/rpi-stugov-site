from branches.models import CommitteeReportPage
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from wagtail.admin import messages


"""
Define behavior for when a committee report page is bumped
in the Wagtail admin menu.

Enforces a 1-day bump 'cooldown' unless the user has the
ignore_bump_cooldown permission.
"""
def bump_report_view(request, page_id):
    page = get_object_or_404(CommitteeReportPage, id=page_id).specific

    now = timezone.now()
    last_bump = page.last_bumped
    cooldown = timedelta(days=1)

    if not request.user.has_perm("branches.ignore_bump_cooldown") and last_bump and now - last_bump < cooldown:
        messages.error(
            request, f"This page can only be bumped once every 24 hours ({str(cooldown - (now - last_bump)).split('.')[0]} remaining)"
        )

    else:
        page.last_bumped = now
        page.save()

        messages.success(
            request, f"'{page.title}' has been bumped."
        )
    
    return redirect("wagtailadmin_pages:edit", page_id)