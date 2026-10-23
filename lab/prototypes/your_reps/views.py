"""Views for the "Your Representatives" prototype.

Read-only. Nothing is stored or logged. Every view renders through ``page()``.
"""

from urllib.parse import quote

from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from . import data as d

TEMPLATE_DIR = "lab/your-reps/"

NAV = [
    ("Your reps", "home"),
    ("Raise an issue", "raise"),
    ("You said, we did", "loop"),
    ("How it works", "how"),
    ("Everyone A–Z", "people"),
]


def _url(name, *args):
    return reverse(f"lab:your_reps:{name}", args=args)


# --------------------------------------------------------------------------
# Optional database reads (all wrapped; the dev DB is empty)
# --------------------------------------------------------------------------


def _site_settings(request):
    """SiteSettings, or None when the database has none. Cached per request."""
    if hasattr(request, "_yr_settings"):
        return request._yr_settings
    settings_obj = None
    try:
        from home.models import SiteSettings

        settings_obj = SiteSettings.load(request_or_site=request)
    except (DatabaseError, ObjectDoesNotExist):  # no database, or no Site row in an empty one
        settings_obj = None
    request._yr_settings = settings_obj
    return settings_obj


def _contact_email(request):
    s = _site_settings(request)
    return (getattr(s, "contact_email", "") or "").strip() if s else ""


def _upcoming_events(today, within_days=7):
    """Upcoming non-meeting EventPages. Meetings come only from meeting records."""
    out = []
    try:
        from django.db.models import Q

        from events.models import EventPage
        from home.models import _upcoming_by_next_occurrence

        candidates = list(
            EventPage.objects.live().filter(
                Q(recurrence_frequency="none", start_date__gte=today)
                | Q(~Q(recurrence_frequency="none"), recurrence_end_date__gte=today)
            )
        )
        for event in _upcoming_by_next_occurrence(candidates, today, limit=10):
            if event.event_type == "meeting":
                continue
            when = getattr(event, "_display_date", None) or event.start_date
            if 0 <= (when - today).days <= within_days:
                out.append({"title": event.title, "date": when, "url": event.url})
    except DatabaseError:
        return []
    return out


# --------------------------------------------------------------------------
# Contact buttons: role inbox, else the Union office, else "not set up"
# --------------------------------------------------------------------------


def contact_for(request, seat):
    inbox = seat.get("inbox")
    if inbox:
        return {"mode": "inbox", "href": f"mailto:{inbox}", "label": "Email this seat", "note": ""}
    email = _contact_email(request)
    if email:
        return {
            "mode": "office",
            "href": f"mailto:{email}?subject={quote('For: ' + seat['seat'], safe='')}",
            "label": "Email the Union office",
            "note": "This seat doesn't have its own role inbox yet.",
        }
    return {"mode": "none", "href": "", "label": "Contact route not set up yet", "note": ""}


# --------------------------------------------------------------------------
# Presentation helpers
# --------------------------------------------------------------------------


def seat_card(request, seat, rollover=False):
    if rollover:
        seat = dict(seat, person_slug=None, status="vacant")
    person = d.PEOPLE.get(seat["person_slug"]) if seat["person_slug"] else None
    others = []
    if person:
        for role in person["roles"]:
            if role["seat_id"] != seat["id"] and role["seat"] not in others and role["seat"] != seat["seat"]:
                others.append(role["seat"])
    return {
        "seat": seat,
        "person": person,
        "others": others,
        "rule": d.rule_for(seat),
        "contact": contact_for(request, seat),
    }


def issue_view(issue, today):
    status = d.ISSUE_STATUS[issue["status"]]
    stale = (today - issue["last_update"]).days > d.STALE_DAYS and issue["status"] not in ("done", "not_possible")
    return {
        **issue,
        "status_label": status["label"],
        "chip": status["chip"],
        "topic_name": d.TOPIC_NAMES.get(issue["topic"], issue["topic"]),
        "updates": sorted(issue["updates"], key=lambda u: u["date"]),
        "stale": stale,
        "stale_label": f"No update since {d.fmt_date(issue['last_update'])}" if stale else "",
        "constituency_labels": [d.CONSTITUENCIES[k]["label"] for k in issue["constituencies"]],
    }


def issues_where(today, **filters):
    out = []
    for issue in d.ISSUES:
        if not issue.get("public"):
            continue
        if filters.get("status") and issue["status"] != filters["status"]:
            continue
        if filters.get("topic") and issue["topic"] != filters["topic"]:
            continue
        if filters.get("constituency") and filters["constituency"] not in issue["constituencies"]:
            continue
        out.append(issue_view(issue, today))
    return out


def topic_route(topic):
    """Who a topic goes to, as plain data for the template."""
    seat = d.seat_by_label(topic["owner_seat"]) if topic.get("owner_seat") else None
    person = d.PEOPLE.get(seat["person_slug"]) if seat and seat["person_slug"] else None
    route = {"topic": topic, "seat": seat, "person": person, "text": ""}
    if seat and not person:
        route["text"] = f"{topic.get('person_word') or 'Seat'}: seat open"
    elif not seat:
        route["text"] = topic.get("no_chair_text", "")
    return route


def reps_preview(key, limit=4):
    """Up to ``limit`` people who represent a remembered constituency."""
    if key not in d.CONSTITUENCIES:
        return []
    seats = [s for s in d.seats_for(key, d.B_SENATE) if s["person_slug"]]
    if not seats:
        seats = [s for s in d.seats_for(key, d.B_EB, "eb_club") if s["person_slug"]]
    return [d.PEOPLE[s["person_slug"]] for s in seats[:limit]]


def _today():
    """The pinned demo day, so staleness and "this week" are the same for every tester."""
    return d.DEMO_TODAY


# --------------------------------------------------------------------------
# The one render helper
# --------------------------------------------------------------------------


def page(request, template, ctx):
    """Render a template with the shared context and handle the mock officer toggle."""
    param = request.GET.get("officer")
    officer = param == "1" or (request.COOKIES.get("lab_officer") == "1" and param != "0")

    toggle_query = request.GET.copy()
    toggle_query["officer"] = "0" if officer else "1"
    site = _site_settings(request)

    current = getattr(getattr(request, "resolver_match", None), "url_name", "")
    context = {
        "sources": d.SOURCES,
        "sync": d.SYNC,
        "officer": officer,
        "officer_toggle_url": "?" + toggle_query.urlencode(),
        "agenda": d.AGENDA,
        "nav": [{"label": label, "url": _url(name), "current": name == current} for label, name in NAV],
        "constituencies": d.CONSTITUENCIES,
        "chip_data": {
            k: {"label": c["label"], "url": _url("reps", k)} for k, c in d.CONSTITUENCIES.items()
        },
        "site_contact_email": _contact_email(request),
        "site_office_hours": (getattr(site, "office_hours", "") or "") if site else "",
        "site_office_location": (getattr(site, "office_location", "") or "") if site else "",
        "safety_line": d.SAFETY_LINE,
        "everyone_label": d.EVERYONE_LABEL,
        "lab_index_url": reverse("lab:index"),
        **ctx,
    }
    response = render(request, TEMPLATE_DIR + template, context)
    if param == "1":
        response.set_cookie("lab_officer", "1", path="/lab/", samesite="Lax", httponly=True)
    elif param == "0":
        response.delete_cookie("lab_officer", path="/lab/", samesite="Lax")
    return response


# --------------------------------------------------------------------------
# Views
# --------------------------------------------------------------------------


def home(request):
    today = _today()
    meetings_soon = [m for m in d.MEETINGS if 0 <= (m["date"] - today).days <= 7]
    # One source line per body that has a meeting this week; the Senate's when none.
    meeting_sources = []
    for m in meetings_soon:
        src = d.SOURCES[m["source_key"]]
        if src not in meeting_sources:
            meeting_sources.append(src)
    meeting_sources = meeting_sources or [d.SOURCES["meeting_senate"]]
    recent = sorted(d.ISSUES, key=lambda i: i["last_update"], reverse=True)[:3]
    ctx = {
        "chooser_rows": [[(k, d.CONSTITUENCIES[k]) for k in row] for row in d.CHOOSER_ROWS],
        "meetings_soon": meetings_soon,
        "meeting_sources": meeting_sources,
        "events_soon": _upcoming_events(timezone.localdate()),  # the real clock: events come from the database
        "last_senate": d.fmt_date(d.LAST_SENATE_MEETING),
        "recent_issues": [issue_view(i, today) for i in recent],
        "home_topics": [d.TOPIC_BY_SLUG[s] for s in d.HOME_TOPIC_SLUGS],
    }
    return page(request, "home.html", ctx)


def reps(request, key):
    c = d.CONSTITUENCIES.get(key)
    if c is None:
        raise Http404("Unknown group")
    today = _today()
    rollover = request.GET.get("term") == "next"

    def cards(seats):
        return [seat_card(request, s, rollover) for s in seats]

    senators = cards(d.seats_for(key, d.B_SENATE)) if c["senate_seats"] else []
    eb_class = cards(d.seats_for(key, d.B_EB, "eb_class"))
    everyone = cards(
        [d.seat_by_label("Grand Marshal"), d.seat_by_label("President of the Union")]
        + d.seats_for("everyone", d.B_EB, "eb_atlarge")
    )
    club_reps = cards(d.seats_for("clubs", d.B_EB, "eb_club")) if key == "clubs" else []
    vp_clubs = cards([d.seat_by_label("Vice President for Club Relations")]) if key == "clubs" else []
    advisors = cards(d.seats_for("clubs", d.B_EB_OTHER, "advisor")) if key == "clubs" else []

    # The fill rule behind "Your say over these seats"
    if senators:
        say_rule = senators[0]["rule"]
    elif club_reps:
        say_rule = club_reps[0]["rule"]
    else:
        say_rule = None
    any_vacant = any(card["seat"]["status"] == "vacant" for card in senators)

    ctx = {
        "key": key,
        "c": c,
        "rollover": rollover,
        "senators": senators,
        "senators_open": len([x for x in senators if x["seat"]["status"] != "filled"]),
        "eb_class": eb_class,
        "everyone": everyone,
        "club_reps": club_reps,
        "vp_clubs": vp_clubs,
        "advisors": advisors,
        "is_class": c["kind"] == "class",
        "is_grad": key == "graduate",
        "is_clubs": key == "clubs",
        "show_reconciliation": key in ("independent", "fsl"),
        "reconciliation_note": d.RECONCILIATION_NOTE,
        "reconciliation_cite": d.RECONCILIATION_CITE,
        "empty_class": key == "2030" and not rollover,
        "say_rule": say_rule,
        "say_challenge": any_vacant and key != "clubs",
        "issues": issues_where(today, constituency=key),
        "eb_warning": d.EB_ROSTER_WARNING,
        "other_groups": [
            (k, name)
            for k, name in (("independent", "Independent"), ("fsl", "Fraternity and Sorority Life"))
            if k != key
        ],
        "gc_rep": d.PEOPLE.get(d.person_slug("Joydip Paul")),
        "gc_report": d.PEOPLE.get(d.person_slug("Melissa Flores")),
    }
    return page(request, "reps.html", ctx)


def people(request):
    q = (request.GET.get("q") or "").strip()[:80]
    items = []
    for person in d.PEOPLE.values():
        if q:
            hay = " ".join([person["name"]] + d.role_summary(person)).lower()
            if q.lower() not in hay:
                continue
        items.append(person)
    items.sort(key=lambda p: (p["name"].split()[-1].lower(), p["name"].lower()))

    letters, grouped = [], {}
    for person in items:
        letter = person["name"].split()[-1][0].upper()
        if letter not in grouped:
            grouped[letter] = []
            letters.append(letter)
        grouped[letter].append({"person": person, "roles": d.role_summary(person)})
    ctx = {
        "q": q,
        "letters": letters,
        "groups": [(letter, grouped[letter]) for letter in letters],
        "total": len(items),
        "all_total": len(d.PEOPLE),
    }
    return page(request, "people.html", ctx)


def person(request, slug):
    p = d.PEOPLE.get(slug)
    if p is None:
        raise Http404("No such person")
    roles = []
    represents = []
    for role in p["roles"]:
        seat = d.seat_by_id(role["seat_id"])
        roles.append({**role, "rule": d.rule_for(seat), "seat_obj": seat})
        cons = role["constituency"]
        if cons and cons not in [r["key"] for r in represents]:
            if cons == "everyone":
                represents.append({"key": cons, "label": d.EVERYONE_LABEL, "url": ""})
            else:
                represents.append({"key": cons, "label": d.CONSTITUENCIES[cons]["label"], "url": _url("reps", cons)})
    my_seat_names = {r["seat"] for r in p["roles"]}
    today = _today()
    working_on = [i for i in (issue_view(i, today) for i in d.ISSUES if i.get("public")) if i["owner_seat"] in my_seat_names]
    first_seat = roles[0]["seat_obj"] if roles else None
    ctx = {
        "p": p,
        "initials": d.initials(p["name"]),
        "roles": roles,
        "represents": represents,
        "working_on": working_on,
        "contact": contact_for(request, first_seat) if first_seat else None,
        "contact_seat": first_seat,
        "in_eb": any(r["body"] in d.EB_BODIES for r in p["roles"]),
        "in_senate": any(r["body"] in d.SENATE_BODIES for r in p["roles"]),
        "senate_copy_note": any(r["body"] in d.SENATE_BODIES for r in p["roles"]),
        "eb_warning": d.EB_ROSTER_WARNING,
    }
    return page(request, "person.html", ctx)


class RaiseForm(forms.Form):
    topic = forms.ChoiceField(
        choices=[(t["slug"], t["name"]) for t in d.TOPICS if not t.get("no_form")],
        error_messages={"required": "Choose what it's about first.", "invalid_choice": "Choose what it's about first."},
    )
    description = forms.CharField(
        label="Describe the problem",
        min_length=20,
        max_length=1000,
        widget=forms.Textarea(attrs={"rows": 6, "maxlength": 1000}),
        error_messages={
            "required": "Describe the problem in at least 20 characters.",
            "min_length": "Write at least %(limit_value)d characters (you wrote %(show_value)d).",
            "max_length": "Keep it to %(limit_value)d characters or fewer (you wrote %(show_value)d).",
        },
    )
    group = forms.ChoiceField(
        label="Which group are you in?",
        required=False,
        choices=[("", "Prefer not to say")] + [(k, c["label"]) for k, c in d.CONSTITUENCIES.items()],
    )
    publish = forms.ChoiceField(
        label="May we publish an anonymised summary on You said, we did?",
        choices=[("yes", "Yes"), ("no", "No")],
        widget=forms.RadioSelect,
        error_messages={"required": "Choose yes or no.", "invalid_choice": "Choose yes or no."},
    )


FIELD_IDS = {
    "topic": "topic-step",
    "description": "id_description",
    "group": "id_group",
    "publish": "id_publish_yes",
}
FIELD_LABELS = {
    "topic": "What it's about",
    "description": "Describe the problem",
    "group": "Which group are you in?",
    "publish": "May we publish an anonymised summary",
}


def raise_issue(request):
    for_key = request.GET.get("for") or ""
    topic = None
    confirmation = None
    form = None
    errors = []

    if request.method == "POST":
        form = RaiseForm(request.POST)
        topic = d.TOPIC_BY_SLUG.get(request.POST.get("topic", ""))
        if form.is_valid():
            description = form.cleaned_data["description"]
            confirmation = {
                "length": len(description),  # only the count is ever shown
                "publish": form.cleaned_data["publish"] == "yes",
                "group": d.CONSTITUENCIES.get(form.cleaned_data["group"], {}).get("label", ""),
            }
        else:
            for name, msgs in form.errors.items():
                errors.append({"field": name, "id": FIELD_IDS[name], "label": FIELD_LABELS[name], "message": msgs[0]})
    else:
        topic = d.TOPIC_BY_SLUG.get(request.GET.get("topic", ""))
        form = RaiseForm(initial={"publish": "no", "topic": topic["slug"] if topic else ""})

    if for_key not in d.CONSTITUENCIES:
        for_key = ""
    if topic and not for_key:
        for_key = topic.get("default_for", "")

    route = topic_route(topic) if topic else None
    body_key = d.TOPIC_BODY.get(topic["slug"], "senate") if topic else ""
    ctx = {
        "tracking": d.ISSUE_TRACKING[body_key] if body_key else "",
        "tracking_body": body_key,
        "tracking_body_name": d.BODY_NAMES.get(body_key, ""),
        "topics": d.TOPICS,
        "topic": topic,
        "route": route,
        "for_key": for_key,
        "for_label": d.CONSTITUENCIES[for_key]["label"] if for_key else "",
        "also_reps": reps_preview(for_key) if topic and for_key else [],
        "form": form,
        "errors": errors,
        "confirmation": confirmation,
        "show_form": bool(topic) and not topic.get("no_form") and confirmation is None,
        "dest_name": topic["owner_label"] if topic else "",
        "desc_value": (form.data.get("description", "") if (form is not None and form.is_bound) else ""),
        "publish_value": (form.data.get("publish", "") if form.is_bound else "no") if form is not None else "no",
        "group_value": (form.data.get("group", "") if form.is_bound else "") if form is not None else "",
        "rights_info": d.TOPIC_BY_SLUG["rights"],
    }
    return page(request, "raise.html", ctx)


def loop(request):
    today = _today()
    status = request.GET.get("status", "")
    topic = request.GET.get("topic", "")
    cons = request.GET.get("constituency", "")
    status = status if status in d.ISSUE_STATUS else ""
    topic = topic if topic in d.TOPIC_BY_SLUG else ""
    cons = cons if cons in d.CONSTITUENCIES else ""
    issues = issues_where(today, status=status, topic=topic, constituency=cons)
    ctx = {
        "issues": issues,
        "total": len([i for i in d.ISSUES if i.get("public")]),
        "f_status": status,
        "f_topic": topic,
        "f_cons": cons,
        "status_options": [(k, v["label"]) for k, v in d.ISSUE_STATUS.items()],
        "topic_options": [(t["slug"], t["name"]) for t in d.TOPICS],
        "cons_options": [(k, c["label"]) for k, c in d.CONSTITUENCIES.items()],
        "filtered": bool(status or topic or cons),
    }
    return page(request, "loop.html", ctx)


FILL_RULE_LABELS = {
    "gm": "Grand Marshal",
    "pu": "President of the Union",
    "class_senator": "Class Senator",
    "elected_senator": "Graduate, Independent and Fraternity and Sorority Life (FSL) Senator",
    "eb_appointed": "Executive Board class, club and member-at-large seat",
    "eb_peer": "Executive Board seat for the Senate, Graduate Council or Undergraduate Council",
    "officer_title": "Officer titles: VPs, Senate officers, committee chairs",
}


def _open_seats():
    groups = {}
    order = []
    for s in d.SEATS:
        if s["status"] == "filled":
            continue
        key = (s["body"], s["seat"], s["status"])
        if s["body"] not in groups:
            groups[s["body"]] = {}
            order.append(s["body"])
        groups[s["body"]][key] = groups[s["body"]].get(key, 0) + 1
    out = []
    for body in order:
        items = []
        for (_, seat, status), count in groups[body].items():
            items.append(
                {
                    "seat": seat,
                    "count": count,
                    "text": "To be elected this fall" if status == "elect_fall" else "Seat open",
                }
            )
        out.append({"body": body, "items": items, "total": sum(i["count"] for i in items)})
    return out


def how(request):
    glossary = {g["term"]: g for g in d.GLOSSARY}
    bodies = [{**b, "glossary_entry": glossary[b["glossary"]]} for b in d.BODIES]
    ctx = {
        "bodies": bodies,
        "five_officers": d.FIVE_OFFICERS,
        "meetings": [{**m, "source": d.SOURCES[m["source_key"]]} for m in d.MEETINGS],
        "folder_bodies": d.FOLDER_BODIES,
        "fill_rules": [{"label": FILL_RULE_LABELS[k], **d.FILL_RULES[k]} for k in FILL_RULE_LABELS],
        "open_seats": _open_seats(),
        "powers": d.POWERS,
        "glossary": d.GLOSSARY,
        "ownership_by_body": d.OWNERSHIP_BY_BODY,
        "ownership_shared": d.OWNERSHIP_SHARED,
        "reconciliation_note": d.RECONCILIATION_NOTE,
        "reconciliation_cite": d.RECONCILIATION_CITE,
        "eb_warning": d.EB_ROSTER_WARNING,
        "elections_commissioner": d.PEOPLE.get(d.person_slug("Lauren Antao")),
        "rollover_url": _url("reps", "2028") + "?term=next",
        "senate_count": len(d.senate_voting_seats()),
        "eb_count": len(d.eb_voting_seats()),
    }
    return page(request, "how.html", ctx)
