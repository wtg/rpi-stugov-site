"""Views for the "Public Record + Desk" prototype.

Everything is read-only. The only POST (the Desk's stand-in panel) renders a
preview and never saves, logs or emails anything.
"""

from datetime import datetime, time, timedelta, timezone as dt_timezone
from urllib.parse import quote, urlencode, urlparse
import json
import re

from django import forms
from django.db import DatabaseError
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

from . import data
from .data import NY

NS = "lab:the_record"

NAV = [
    ("Meetings", "meetings", None),
    ("Decisions", "decisions", None),
    ("Money", "money", None),
    ("Rules", "rules", None),
    ("Have your say", "meetings", "#speak"),
    ("Desk", "desk", None),
]

BOX_SHARED_RE = re.compile(r"^https://([a-z0-9-]+\.)*box\.com/s/[A-Za-z0-9]+")


def today_ny():
    """Today in the Union's time zone (settings.TIME_ZONE is UTC)."""
    return timezone.localdate(timezone=NY)


def url(name, *args, **kwargs):
    return reverse(f"{NS}:{name}", args=args, kwargs=kwargs)


# --------------------------------------------------------------------------
# Shared page helper
# --------------------------------------------------------------------------


def site_settings():
    """Read-only. SiteSettings.load() would create a row, so use .first()."""
    try:
        from home.models import SiteSettings

        return SiteSettings.objects.first()
    except DatabaseError:
        return None


def is_officer(request, force=False):
    flag = request.GET.get("officer")
    if flag == "1":
        officer = True
    elif flag == "0":
        officer = False
    else:
        officer = request.COOKIES.get("lab_officer") == "1"
    return officer or force


def page(request, template, ctx=None, force_officer=False):
    """Every view calls this. Adds sources, sync and officer to the context."""
    ctx = dict(ctx or {})
    flag = request.GET.get("officer")
    officer = is_officer(request, force_officer)

    query = request.GET.copy()
    query["officer"] = "0" if officer else "1"
    toggle_url = f"{request.path}?{urlencode(query, doseq=True)}"

    current = getattr(request.resolver_match, "url_name", "")
    ctx.update(
        sources=data.build_sources(),
        sync=data.SYNC,
        officer=officer,
        force_officer=force_officer,
        toggle_url=toggle_url,
        site=site_settings(),
        box_folders=data.box_folders_with_embeds(),
        notice=data.NOTICE,
        current=current,
        nav=[
            {
                "label": label,
                "href": url(name) + (anchor or ""),
                "current": current == name and anchor is None,
                "note": "For officers" if label == "Desk" else "",
            }
            for label, name, anchor in NAV
        ],
        search_q=request.GET.get("q", "") if current == "decisions" else "",
    )
    response = render(request, f"lab/the-record/{template}", ctx)
    if flag == "1":
        # Session cookie (no max_age), scoped to the lab.
        response.set_cookie("lab_officer", "1", path="/lab/", samesite="Lax")
    elif flag == "0":
        response.delete_cookie("lab_officer", path="/lab/", samesite="Lax")
    return response


# --------------------------------------------------------------------------
# Decorators for display
# --------------------------------------------------------------------------


def ics_uri(m):
    starts = m["starts"].astimezone(dt_timezone.utc)
    ends = starts + timedelta(hours=1)
    ref = data.meeting_ref(m)

    def esc(text):
        return text.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Rensselaer Union lab//the-record//EN",
        "BEGIN:VEVENT",
        f"UID:{m['body']}-{m['term_slug']}-{m['number']}@lab.invalid",
        f"DTSTAMP:{starts:%Y%m%dT%H%M%SZ}",
        f"DTSTART:{starts:%Y%m%dT%H%M%SZ}",
        f"DTEND:{ends:%Y%m%dT%H%M%SZ}",
        f"SUMMARY:{esc(data.BODIES[m['body']]['name'])} {esc(ref)}",
        f"LOCATION:{esc(m['location'])}",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    return "data:text/calendar;charset=utf-8," + quote("\r\n".join(lines))


def decorate_meeting(m, today, detail=True):
    out = dict(m)
    local = m["starts"].astimezone(NY)
    start_day = local.date()
    body = data.BODIES[m["body"]]
    out.update(
        ref=data.meeting_ref(m),
        body_short=body["short"],
        starts_iso=local.isoformat(),
        date_label=data.fmt_date(start_day),
        when_long=data.fmt_long(local),
        time_label=f"{data.fmt_time(local)} ET",
        past=start_day < today,
        days_since=(today - start_day).days,
        days_until=(start_day - today).days,
        agenda_state=data.agenda_state(m),
        minutes_state=data.minutes_state(m),
        ics=ics_uri(m),
        folder=body["folder"],
        approved_label=data.fmt_date(m["minutes_approved"]) if m.get("minutes_approved") else None,
        record_source=data.build_sources()["meeting_" + m["body"]],
        adapter=body["adapter"],
        adapter_label=body["adapter_label"],
        fix_label=body["fix_label"],
        fix_url=body["fix_url"],
        edited_label=(
            f"{data.fmt_date(m['record_edited'].astimezone(NY).date())}, {data.fmt_time(m['record_edited'].astimezone(NY))} ET"
            if m.get("record_edited")
            else "Just now (simulated)"
        ),
        document_name=m.get("document_name"),
        embed_url=data.box_embed_url(m.get("agenda_url")),
    )
    if detail:
        out["detail_url"] = url("meeting", m["body"], m["term_slug"], m["number"])
        out["speak_url"] = out["detail_url"] + "#speak"
    return out


def decorate_decision(d):
    out = dict(d)
    out["url"] = url("decision", d["id"])
    out["status_label"] = mark_safe(data.STATUS_LABELS[d["status"]])  # static text, no user input
    out["chip"] = data.STATUS_CHIP[d["status"]]
    out["body_name"] = data.BODIES[d["body"]]["name"]
    out["last"] = data.last_action(d)
    out["threshold_obj"] = data.THRESHOLDS.get(d["threshold"]) if d["threshold"] else None
    history = []
    for h in d["history"]:
        h = dict(h)
        h["date_label"] = data.fmt_date(h["date"])
        h["meeting_url"] = url("meeting", *h["meeting"]) if h.get("meeting") else None
        history.append(h)
    out["history"] = history
    out["last"] = history[-1] if history else None
    return out


def folder_bodies():
    """Bodies that publish records only as files, each with its Box folder (and embed link, if any)."""
    folders = data.box_folders_with_embeds()
    return [{**b, "folder_obj": folders[b["folder"]]} for b in data.FOLDER_BODIES.values()]


def decorated_meetings(today):
    return [decorate_meeting(m, today) for m in data.MEETINGS if m.get("public", True)]


# --------------------------------------------------------------------------
# Home
# --------------------------------------------------------------------------


def home(request):
    today = today_ny()
    meetings = decorated_meetings(today)
    cards = []
    for key, body in data.BODIES.items():
        upcoming = sorted((m for m in meetings if m["body"] == key and not m["past"]), key=lambda m: m["starts"])
        past = sorted((m for m in meetings if m["body"] == key and m["past"]), key=lambda m: m["starts"])
        cards.append(
            {
                "body": body,
                "next": upcoming[0] if upcoming else None,
                "last": past[-1] if past else None,
            }
        )
    decisions = sorted(
        (decorate_decision(d) for d in data.DECISIONS), key=lambda d: d["last"]["date"] if d["last"] else today, reverse=True
    )
    strip = sorted((m for m in meetings if m["past"]), key=lambda m: m["starts"], reverse=True)
    latest_eb = data.latest_eboard_meeting(today)
    return page(
        request,
        "home.html",
        {
            "cards": cards,
            "latest": decisions[:6],
            "strip": strip[:6],
            "strip_more": max(0, len(strip) - 6),
            "latest_eboard": decorate_meeting(latest_eb, today) if latest_eb else None,
            "budget": data.BUDGET,
            "bodies": data.BODY_DESCRIPTIONS,
            "folder_bodies": folder_bodies(),
        },
    )


# --------------------------------------------------------------------------
# Meetings
# --------------------------------------------------------------------------


def meetings(request):
    today = today_ny()
    body = request.GET.get("body", "all")
    term = request.GET.get("term", "all")
    if body not in ("all", "senate", "eboard") + tuple(data.FOLDER_BODIES):
        body = "all"
    if term not in ("all", "57", "fy27"):
        term = "all"
    rows = decorated_meetings(today)
    folder_body = None
    if body in data.FOLDER_BODIES:
        # A folder-only body has no meeting records on this site.
        folder_body = {**data.FOLDER_BODIES[body], "folder_obj": data.box_folders_with_embeds()[body]}
        rows = []
    elif body != "all":
        rows = [m for m in rows if m["body"] == body]
    if term != "all":
        rows = [m for m in rows if m["term_slug"] == term]
    upcoming = sorted((m for m in rows if not m["past"]), key=lambda m: m["starts"])
    past = sorted((m for m in rows if m["past"]), key=lambda m: m["starts"], reverse=True)
    return page(
        request,
        "meetings.html",
        {
            "upcoming": upcoming,
            "past": past,
            "f_body": body,
            "f_term": term,
            "body_options": [("all", "All bodies"), ("senate", "Student Senate"), ("eboard", "Executive Board")]
            + [(k, b["name"]) for k, b in data.FOLDER_BODIES.items()],
            "term_options": [("all", "All terms"), ("57", "57th Senate"), ("fy27", "FY27 (2026–27)")],
            "folder_body": folder_body,
            "folder_bodies": folder_bodies(),
            "folder_keys": ["senate", "eboard"],
        },
    )


def meeting(request, body, term, number):
    raw = data.find_meeting(body, term, number)
    if raw is None or not raw.get("public", True):
        raise Http404("No such meeting")
    today = today_ny()
    m = decorate_meeting(raw, today)
    same_body = data.meetings_for_body(body)
    idx = same_body.index(raw)
    prev_m = decorate_meeting(same_body[idx - 1], today) if idx > 0 else None
    next_m = decorate_meeting(same_body[idx + 1], today) if idx < len(same_body) - 1 else None

    snap = data.snapshot_with_totals(body)
    key = (raw["body"], raw["term_slug"], raw["number"])
    assoc = [
        decorate_decision(d) for d in data.DECISIONS if any(h.get("meeting") == key for h in d["history"])
    ]
    if body == "senate":
        chair = ("Chaired by the Grand Marshal, who votes only to break a tie.", "Art. IV §1")
    else:
        chair = (
            "Chaired by the President of the Union, who votes only to break a tie. The Director of the Union advises but cannot veto.",
            "Art. IV §2; Art. V",
        )
    agenda_view = "items" if body == "senate" and request.GET.get("agenda") == "items" else "document"
    return page(
        request,
        "meeting.html",
        {
            "agenda_view": agenda_view,
            "items_url": request.path + "?agenda=items",
            "m": m,
            "prev_m": prev_m,
            "next_m": next_m,
            "snap": snap,
            "assoc": assoc,
            "chair": chair,
            "folder": data.box_folders_with_embeds()[data.BODIES[body]["folder"]],
            "body_info": data.BODIES[body],
        },
    )


# --------------------------------------------------------------------------
# Decisions
# --------------------------------------------------------------------------


def decisions(request):
    q = request.GET.get("q", "").strip()
    body = request.GET.get("body", "all")
    status = request.GET.get("status", "all")
    term = request.GET.get("term", "all")
    rows = [decorate_decision(d) for d in data.DECISIONS]
    if q:
        needle = q.lower()
        rows = [d for d in rows if needle in d["title"].lower() or needle in d["plain_summary"].lower()]
    if body in data.BODIES:
        rows = [d for d in rows if d["body"] == body]
    else:
        body = "all"
    if status in data.STATUS_LABELS:
        rows = [d for d in rows if d["status"] == status]
    else:
        status = "all"
    if term in ("57", "fy27"):
        rows = [d for d in rows if d["term_slug"] == term]
    else:
        term = "all"
    rows.sort(key=lambda d: d["last"]["date"] if d["last"] else datetime.min.date(), reverse=True)
    return page(
        request,
        "decisions.html",
        {
            "eboard_panel": body == "eboard",
            "other_bodies_line": (
                "The Executive Board, Graduate Council, Undergraduate Council and Judicial Board record decisions "
                "in their minutes and rulings, published as files."
            ),
            "rows": rows,
            "count": len(rows),
            "q": q,
            "f_body": body,
            "f_status": status,
            "f_term": term,
            "body_options": [("all", "All bodies"), ("senate", "Student Senate"), ("eboard", "Executive Board")],
            "status_options": [("all", "Any status")] + list(data.STATUS_LABELS.items()),
            "term_options": [("all", "All terms"), ("57", "57th Senate"), ("fy27", "FY27 (2026–27)")],
        },
    )


def decision(request, id):
    raw = data.find_decision(id)
    if raw is None:
        raise Http404("No such decision")
    d = decorate_decision(raw)
    idx = data.STATUS_STAGE[d["status"]]
    labels = list(data.STAGES)
    if d["status"] == "overturned":
        labels.append(data.STATUS_LABELS["overturned"])
    steps = []
    for i, label in enumerate(labels):
        state = "done" if i < idx else "current" if i == idx else "todo"
        steps.append({"label": label, "state": state})

    meeting_obj = None
    if raw.get("meeting_key"):
        mraw = data.find_meeting(*raw["meeting_key"])
        if mraw:
            meeting_obj = decorate_meeting(mraw, today_ny())
    return page(
        request,
        "decision.html",
        {
            "d": d,
            "steps": steps,
            "meeting_obj": meeting_obj,
            "share_url": request.build_absolute_uri(d["url"]),
            "derived_title": data.DERIVED_TITLE,
        },
    )


# --------------------------------------------------------------------------
# Money and rules
# --------------------------------------------------------------------------


def money(request):
    today = today_ny()
    latest_eb = data.latest_eboard_meeting(today)
    stale = bool(latest_eb) and latest_eb["starts"].astimezone(NY).date() > data.BUDGET["as_of"]
    return page(
        request,
        "money.html",
        {
            "budget": data.BUDGET,
            "budget_as_of": data.fmt_date(data.BUDGET["as_of"]),
            "latest_eboard": decorate_meeting(latest_eb, today) if latest_eb else None,
            "budget_stale": stale,
        },
    )


def rules(request):
    return page(
        request,
        "rules.html",
        {
            "thresholds": [data.THRESHOLDS[s] for s in data.THRESHOLD_ORDER],
            "petitions": data.PETITIONS,
            "records": data.NAMED_RECORDS,
            "transparency": data.TRANSPARENCY_RULES,
            "honest_line": data.TRANSPARENCY_HONEST_LINE,
            "derived_title": data.DERIVED_TITLE,
        },
    )


# --------------------------------------------------------------------------
# Desk
# --------------------------------------------------------------------------


class MeetingRowForm(forms.Form):
    """A stand-in for one meeting record. Never saved.

    path "notion": a stand-in for one row of the Senate's Notion Meetings database (Senate only).
    path "site": the form a body that chose "entered on this site" would use (the E-Board, as an example).
    A folder-only body has no form at all.
    """

    BODY_CHOICES = [("senate", "Senate"), ("eboard", "E-Board")]
    TERM_CHOICES = [("57", "57"), ("fy27", "FY27 (2026–27)")]

    body = forms.ChoiceField(label="Body", choices=BODY_CHOICES, initial="senate")
    term = forms.ChoiceField(label="Term", choices=TERM_CHOICES, initial="57")
    number = forms.IntegerField(label="Number", min_value=1, max_value=999)
    date = forms.DateField(label="Date", widget=forms.DateInput(attrs={"type": "date"}))
    time = forms.TimeField(label="Time", initial="20:00", widget=forms.TimeInput(attrs={"type": "time"}))
    location = forms.CharField(label="Location", initial="Webex", max_length=120)
    agenda = forms.URLField(label="Agenda", required=False)
    public = forms.BooleanField(label="Public", required=False)

    HINTS = {
        "body": "Which body is meeting.",
        "term": "Follows the body: 57 for the Senate, FY27 (the 2026–27 year) for the E-Board.",
        "number": "Prefilled from the existing row for the next meeting.",
        "date": "The day of the meeting.",
        "time": "Eastern Time.",
        "location": "A room, or Webex.",
        "agenda": "Paste the Box shared link to the agenda PDF.",
        "public": "Only rows with Public ticked appear on the site.",
    }

    def __init__(self, *args, path="notion", **kwargs):
        super().__init__(*args, **kwargs)
        self.path = path
        if path == "site":
            self.fields["body"].choices = [("eboard", "E-Board")]
            self.fields["body"].initial = "eboard"
            self.fields["term"].choices = [("fy27", "FY27 (2026–27)")]
            self.fields["term"].initial = "fy27"
            self.fields["location"].initial = "Rensselaer Union, room 3202"
            self.fields["time"].initial = "19:00"
            del self.fields["public"]
        else:
            self.fields["body"].choices = [("senate", "Senate")]
            self.fields["term"].choices = [("57", "57")]
        self.fields["agenda"].widget.attrs["placeholder"] = "https://rpi.box.com/s/…"
        for name, field in self.fields.items():
            attrs = field.widget.attrs
            attrs["autocomplete"] = "off"
            describedby = []
            if name in self.HINTS:
                describedby.append(f"hint_{name}")
            if self.is_bound and name in self.errors:
                describedby.append(f"err_{name}")
                attrs["aria-invalid"] = "true"
            if describedby:
                attrs["aria-describedby"] = " ".join(describedby)
            if field.required:
                attrs["required"] = "required"

    def clean(self):
        cleaned = super().clean()
        body, term = cleaned.get("body"), cleaned.get("term")
        if body and term and data.BODIES[body]["term_slug"] != term:
            self.add_error("term", f"Use {data.BODIES[body]['term_slug'].upper()} for the {data.BODIES[body]['short']}.")
        return cleaned


def initial_row(body="senate"):
    """Prefill the stand-in panel. The Senate's comes from its next meeting already in the record, so the
    officer only adds the agenda link. The E-Board's new entry gets the next number and its usual room and time."""
    today = today_ny()
    if body == "eboard":
        return {
            "body": "eboard",
            "term": "fy27",
            "number": next_number("eboard"),
            "time": time(19, 0),
            "location": "Rensselaer Union, room 3202",
        }
    upcoming = sorted(
        (m for m in data.MEETINGS if m["body"] == "senate" and not data.is_past(m, today)), key=lambda m: m["starts"]
    )
    if not upcoming:
        return {"number": next_number("senate")}
    m = upcoming[0]
    local = m["starts"].astimezone(NY)
    return {
        "body": m["body"],
        "term": m["term_slug"],
        "number": m["number"],
        "date": local.date(),
        "time": local.time().replace(second=0, microsecond=0),
        "location": m["location"],
        "public": True,
    }


def next_number(body):
    today = today_ny()
    past = [m["number"] for m in data.MEETINGS if m["body"] == body and data.is_past(m, today)]
    return (max(past) if past else 0) + 1


def parse_elapsed(raw):
    try:
        secs = int(raw)
    except (TypeError, ValueError):
        return None
    if secs <= 0 or secs > 86400:
        return None
    return secs


def build_preview(cd, path, elapsed):
    today = today_ny()
    starts = datetime.combine(cd["date"], cd["time"], tzinfo=NY)
    body = data.BODIES[cd["body"]]
    agenda = cd.get("agenda") or ""
    raw = {
        "body": cd["body"],
        "body_name": body["name"],
        "term_slug": cd["term"],
        "term_label": body["term_label"],
        "number": cd["number"],
        "starts": starts,
        "location": cd["location"],
        "agenda_url": None,
    }
    card = decorate_meeting(raw, today, detail=False)
    card["agenda_state"] = "host" if agenda else "missing"
    card["agenda_host"] = urlparse(agenda).hostname if agenda else None
    card["speak_url"] = url("meetings") + "#speak"
    card["detail_url"] = None

    public = cd.get("public") if path == "notion" else True
    sources = data.build_sources()
    if path == "notion":
        source = {**sources["meeting_senate"], "line": "Meeting record: Senate's Notion · synced just now (simulated)"}
    else:
        source = {
            **sources["meeting_eboard"],
            "line": "Meeting record: entered on this site by the E-Board Secretary · just now",
        }

    checks = []
    existing = data.find_meeting(cd["body"], cd["term"], cd["number"])
    if existing is not None:
        same_day = existing["starts"].astimezone(NY).date() == starts.date()
        same_place = existing["location"].strip().lower() == cd["location"].strip().lower()
        if not (same_day and same_place):
            ref = data.meeting_ref(existing)
            if path == "notion":
                checks.append(
                    (
                        "check",
                        f"Check: {ref} already has a row in Meetings. Edit that row instead of adding a second one.",
                    )
                )
            else:
                checks.append(
                    (
                        "check",
                        f"Check: {ref} already exists on this site. Edit that meeting instead of adding a second one.",
                    )
                )
    until = card["days_until"]
    ref_day = data.fmt_day_month(starts.date() - timedelta(days=2))
    if not agenda:
        if until < 0:
            checks.append(("check", "Check: no agenda link on the meeting record."))
        elif until <= 1:
            checks.append(("overdue", "Overdue: agenda due 24 hours before the meeting"))
        elif until == 2:
            checks.append(("soon", "Due soon: agenda due 24 hours before the meeting, and the link is still missing"))
        else:
            checks.append(("waiting", f"Waiting: flagged from {ref_day} if still missing"))
    elif BOX_SHARED_RE.match(agenda):
        checks.append(
            ("ok", "OK: looks like a Box shared link. The weekly check will confirm it opens without an RPI login.")
        )
    else:
        checks.append(
            (
                "check",
                "Check: this isn't a Box shared link (…/s/…). Students may hit a login page or a dead link.",
            )
        )
    if until < 0:
        checks.append(("info", "The date has passed: the minutes link will be flagged 14 days after the meeting."))

    if elapsed:
        time_text = f"Time taken: {elapsed // 60} min {elapsed % 60} s · Target: under 2 minutes, Box upload included."
    else:
        time_text = "Time not measured"
    return {
        "public": public,
        "card": card,
        "source": source,
        "checks": [{"severity": s, "text": mark_safe(t)} for s, t in checks],  # static text
        "time_text": time_text,
    }


def desk(request):
    today = today_ny()
    path = request.POST.get("path") or request.GET.get("path") or "notion"
    if path == "wagtail":
        path = "site"
    if path not in ("notion", "site", "folder"):
        path = "notion"

    result = None
    form = None
    if path == "folder":
        # A folder-only body has no form: nothing to post.
        pass
    elif request.method == "POST":
        form = MeetingRowForm(request.POST, path=path)
        if form.is_valid():
            result = build_preview(form.cleaned_data, path, parse_elapsed(request.POST.get("elapsed")))
    else:
        form = MeetingRowForm(path=path, initial=initial_row("senate" if path == "notion" else "eboard"))

    problems = data.problems(today)
    jobs = problems[:8]
    fields = {name: form[name] for name in form.fields} if form else {}
    error_list = []
    if form is not None and form.is_bound and form.errors:
        # Field order, then form-wide errors, so "Term" comes before "Agenda".
        names = [n for n in form.fields if n in form.errors] + [n for n in form.errors if n not in form.fields]
        for name in names:
            error_list.append(
                {
                    "id": f"id_{name}" if name in form.fields else "",
                    "label": form.fields[name].label if name in form.fields else "Form",
                    "messages": list(form.errors[name]),
                }
            )
    result_anchor = "error-summary" if error_list else ("result-heading" if result else "")
    sync = data.SYNC
    return page(
        request,
        "desk.html",
        {
            "path": path,
            "form": form,
            "fields": fields,
            "hints": MeetingRowForm.HINTS,
            "error_list": error_list,
            "result_anchor": result_anchor,
            "result": result,
            "jobs": jobs,
            "more_jobs": max(0, len(problems) - len(jobs)),
            "renames": data.RENAMES,
            "name_pattern": data.BOX_NAME_PATTERN,
            "body_codes": data.BOX_BODY_CODES,
            "motions": data.MOTIONS_MOCK,
            "rollover": data.ROLLOVER_STEPS,
            "records_standard": data.RECORDS_STANDARD,
            "records_standard_jboard": data.RECORDS_STANDARD_JBOARD_NOTE,
            "records_by_body": data.RECORDS_BY_BODY,
            "shared_where": data.SHARED_WHERE,
            "folder_bodies": folder_bodies(),
            "eboard_next_name": f"YYYY-MM-DD EBoard FY27 #{next_number('eboard'):02d} Agenda.pdf",
            "never": data.NEVER_LIST,
            "officer_rules": data.OFFICER_RULES,
            "next_numbers_json": json.dumps({"senate": next_number("senate"), "eboard": next_number("eboard")}),
            "mock_box": data.MOCK_BOX,
            "mock_notion": data.MOCK_NOTION,
            "sync_line": (
                f"Senate's Notion sync: last success {data.minutes_ago_text(sync['notion_minutes_ago'])} · "
                f"next run in {sync['notion_next_run_minutes']} min · "
                + ("no errors" if not sync["notion_last_error"] else f"last error: {sync['notion_last_error']}")
            ),
        },
        force_officer=True,
    )


# --------------------------------------------------------------------------
# Health
# --------------------------------------------------------------------------


def health(request):
    today = today_ny()
    sync = data.SYNC
    rows = []
    for m in sorted(data.MEETINGS, key=lambda m: m["starts"], reverse=True):
        d = decorate_meeting(m, today)
        d["agenda_result"] = data.link_result(m, "agenda")
        d["minutes_result"] = data.link_result(m, "minutes")
        rows.append(d)
    last = sync["notion_last_success"].astimezone(NY)
    schema_row = next(r for r in data.seeded_checks(today) if r["area"] == "Sync" and r["severity"] != "ok")
    senate_meetings = sum(1 for m in data.MEETINGS if m["body"] == "senate")
    return page(
        request,
        "health.html",
        {
            "rows": rows,
            "problems": data.problems(today),
            "all_clear": data.all_clear(today),
            "not_checked": data.NOT_CHECKED,
            "link_summary": data.link_summary(),
            "link_checks": data.LINK_CHECKS,
            "standard_rows": data.standard_by_body(today),
            "records_standard": data.RECORDS_STANDARD,
            "records_standard_jboard": data.RECORDS_STANDARD_JBOARD_NOTE,
            "counts": {"meetings": senate_meetings, "motions": len(data.DECISIONS)},
            "last_success_label": f"{data.fmt_date(last.date())}, {data.fmt_time(last)} ET",
            "last_success_ago": data.minutes_ago_text(sync["notion_minutes_ago"]),
            "box_checked": data.fmt_date(sync["box_links_checked"]),
            "schema_rows": [schema_row],
        },
        force_officer=True,
    )
