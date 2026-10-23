"""Views for the Front Door prototype.

Every view builds its context from ``data.py`` (and a few optional,
read-only DB lookups in ``logic.py``) and renders through ``page()``.
There are no POST views and nothing here writes to the database.
"""

from django.http import Http404
from django.shortcuts import render
from django.template.defaultfilters import slugify
from django.utils.safestring import mark_safe

from . import data, logic
from .logic import url

TEMPLATE_DIR = "lab/front-door/"
OFFICER_COOKIE = "lab_officer"


def page(request, template, ctx=None, status=200):
    """Render a page with the shared context.

    Adds ``sources``, ``sync`` and ``officer``.  Officer mode is a mock
    (no login): ``?officer=1`` sets a session cookie, ``?officer=0`` clears it.
    """
    query = request.GET.get("officer")
    cookie_on = request.COOKIES.get(OFFICER_COOKIE) == "1"
    officer = query == "1" or (cookie_on and query != "0")
    context = {
        "sources": data.SOURCES,
        "sync": data.SYNC,
        "officer": officer,
        "agenda_src": data.AGENDA_SRC,
        "constitution_line": data.CONSTITUTION_LINE,
        "site": logic.site_settings(),
        "nav": [
            {"key": "issue", "label": "Raise an issue", "url": url("issue_index")},
            {"key": "funding", "label": "Funding", "url": url("funding")},
            {"key": "meetings", "label": "Meetings & decisions", "url": url("meetings")},
            {"key": "reps", "label": "Your reps", "url": url("reps_index")},
            {"key": "about", "label": "How the Union works", "url": url("about")},
        ],
        "take_part_url": url("take_part"),
        "website_issue_url": url("issue_topic:website"),
        "home_url": url("home"),
    }
    context.update(ctx or {})
    response = render(request, TEMPLATE_DIR + template, context, status=status)
    if query == "1":
        response.set_cookie(OFFICER_COOKIE, "1", path="/lab/", samesite="Lax")
    elif query == "0":
        response.delete_cookie(OFFICER_COOKIE, path="/lab/", samesite="Lax")
    return response


def _pills():
    return [{"key": k, "label": v["pill"], "title": v["title"], "url": url(f"reps:{k}")} for k, v in data.REPS_META.items()]


# --------------------------------------------------------------------------
# Home
# --------------------------------------------------------------------------

def home(request):
    today = logic.today()
    notice = data.NOTICE if data.NOTICE and data.NOTICE["expires"] >= today else None
    n_open = len(logic.open_seats())
    verbs = [
        ("Raise an issue", "Tell the right people about a problem: dining, housing, classes, clubs and more.", "issue_index"),
        ("Get money for your club", "How clubs request extra funding and travel money, and where to find the latest figures.", "funding"),
        ("Find out what was decided", "Senate motions, and every body's agendas and minutes.", "meetings#decided"),
        ("See who represents you", "Your senators and class representative, and how to reach them.", "reps_index"),
        ("Go to a meeting", "When and where the next meetings are. Anyone can speak.", "meetings"),
        ("Run for office or start a petition", f"{n_open} seats are open right now. Students can also force a vote, challenge an appointment, or remove an officer.", "take_part"),
    ]
    bodies = []
    for g in data.GLOSSARY:
        if g.get("body_id"):
            bodies.append({**g, "url": url("about") + "#" + g["body_id"]})
    return page(request, "home.html", {
        "section": "home",
        "title": "What do you need to do?",
        "description": "Raise an issue, find funding, see decisions, find your representatives, or run for office at the Rensselaer Union.",
        "notice": notice,
        "verbs": [{"title": t, "text": d, "url": url(u)} for t, d, u in verbs],
        "week_meetings": logic.this_week(today),
        "week_events": logic.db_events(today),
        "past_url": url("meetings"),
        "pills": _pills(),
        "decisions": logic.decisions()[:3],
        "bodies": bodies,
    })


# --------------------------------------------------------------------------
# Raise an issue
# --------------------------------------------------------------------------

def issue_index(request):
    q = request.GET.get("q", "").strip()
    topics = data.TOPICS
    if q:
        needle = q.lower()
        topics = [t for t in topics if needle in t["question"].lower() or needle in t["owner_label"].lower()
                  or any(needle in e.lower() for e in t["examples"])]
    return page(request, "issue_index.html", {
        "section": "issue",
        "title": "Raise an issue",
        "description": "Pick what your issue is about and see who handles it and what student government can and can't change.",
        "topics": [{**t, "url": url(f"issue_topic:{t['slug']}")} for t in topics],
        "q": q,
    })


def issue_topic(request, topic):
    t = data.TOPIC_BY_SLUG.get(topic)
    if t is None:
        raise Http404("Unknown topic")
    site = logic.site_settings()
    name = t["slug"].replace("-", " ").title()
    from urllib.parse import quote

    subject = quote(f"For: {logic.topic_owner_title(t)}: {name} issue")
    inbox = logic.topic_inbox(t)
    if inbox:
        email = {"href": f"mailto:{inbox}?subject={subject}", "text": inbox, "kind": "inbox"}
    elif site["contact_email"]:
        email = {"href": f"mailto:{site['contact_email']}?subject={subject}", "text": "Email the Union office", "kind": "office"}
    else:
        email = {"href": None, "text": "Contact address to be confirmed", "kind": "none"}
    # The public meeting to point students at belongs to the body that owns the topic.
    meeting_body = "eboard" if t["owner_body"] == "Executive Board" else "senate"
    return page(request, "issue_topic.html", {
        "section": "issue",
        "topic_meeting": logic.latest_meeting(meeting_body, logic.today()),
        "title": t["question"],
        "description": f"Who handles this at the Rensselaer Union, and what student government can do: {t['question']}",
        "topic": t,
        "chair": logic.topic_chair(t),
        "email": email,
        "meetings_url": url("meetings"),
        "index_url": url("issue_index"),
        "referendum_url": url("take_part#referendum"),
        "judicial_url": url("take_part#judicial-board"),
        "safety": data.SAFETY_LINE,
    })


# --------------------------------------------------------------------------
# Your reps
# --------------------------------------------------------------------------

def _everyone(site):
    seats = [s for s in data.SEATS if s["fill_rule"] in ("gm", "pu") or s.get("kind") == "at_large"]
    return logic.cards(seats, site)


def reps(request, key=None):
    site = logic.site_settings()
    ctx = {
        "section": "reps",
        "pills": _pills(),
        "roster_db_count": logic.roster_db_count(),
        "seat_source_note": data.SEAT_SOURCE_NOTE,
        "reconciliation": data.RECONCILIATION,
    }
    if key is None:
        ctx.update(title="Who represents you", description="Pick your group to see your Student Senate and Executive Board representatives.", key=None)
        return page(request, "reps.html", ctx)
    meta = data.REPS_META.get(key)
    if meta is None:
        raise Http404("Unknown group")
    kind = meta["kind"]
    senate = [s for s in data.SEATS if s["body"] == "senate" and s["constituency"] == key]
    eb_class = [s for s in data.SEATS if s["body"] == "eboard" and s.get("kind") == "class_rep" and s["constituency"] == key]
    fallback = bool(senate) and all(s["status"] == "elect_fall" for s in senate)

    intro = {
        "class": "Your class has 4 Senate seats under the Union Constitution.",
        "graduate": "Graduate students have 7 Senate seats under the Union Constitution.",
        "independent": "There are 3 Independent Senate seats under the Union Constitution.",
        "fsl": "There are 3 Fraternity and Sorority Life Senate seats under the Union Constitution.",
    }.get(kind)

    eb_note = None
    if fallback:
        eb_note = {"text": "Vacant: appointed within three weeks after the fall elections", "cite": "Art. VIII §12"}

    club_seats = [s for s in data.SEATS if s["body"] == "eboard" and s.get("kind") == "clubs"] if kind == "clubs" else []
    vp_seat = [s for s in data.SEATS if s["seat"] == "VP for Club Relations"] if kind == "clubs" else []

    has_elected = any(s["status"] == "filled" for s in senate)
    has_vacant = any(s["status"] == "vacant" for s in senate)
    say_draft = "Senate election rules" if kind in ("independent", "fsl") else None

    grad_report, grad_meeting = logic.agenda_reporter("senate", "Graduate Council") if kind == "graduate" else (None, None)

    ctx.update(
        grad_report=grad_report,
        grad_meeting=grad_meeting,
        grad_eb_rep=logic.holder_name("eb_grad_council_rep") if kind == "graduate" else None,
        key=key,
        meta=meta,
        kind=kind,
        title=meta["h1"],
        description=f"Your representatives at the Rensselaer Union: {meta['title']}.",
        senate_cards=logic.cards(senate, site),
        senate_intro=intro,
        fallback=fallback,
        eb_cards=logic.cards(eb_class, site, eb_note),
        eb_note_cite="Art. VII §2",
        club_cards=logic.cards(club_seats, site),
        vp_cards=logic.cards(vp_seat, site),
        everyone_cards=_everyone(site),
        has_elected=has_elected,
        has_vacant=has_vacant,
        say_draft=say_draft,
        show_reconciliation=kind in ("independent", "fsl"),
        class_council=kind == "class",
        take_part_run=url("take_part#run"),
        funding_url=url("funding"),
        grad_topic_url=url("issue_topic:grad"),
        index_url=url("reps_index"),
    )
    return page(request, "reps.html", ctx)


# --------------------------------------------------------------------------
# Meetings
# --------------------------------------------------------------------------

def meetings(request):
    today = logic.today()
    past = logic.past_meetings(today)
    return page(request, "meetings.html", {
        "section": "meetings",
        "title": "Meetings and decisions",
        "description": "Upcoming and past Student Senate and Executive Board meetings, decisions, and where to find agendas and minutes.",
        "upcoming": logic.upcoming_meetings(today),
        "week_meetings": logic.this_week(today),
        "week_events": logic.db_events(today),
        "past": past,
        "decisions": logic.decisions(),
        "box_folders": logic.meeting_body_folders(),
        "folder_bodies": logic.folder_bodies(),
        "file_example": data.MEETING_FILE_NAMING,
        "senate_sections": data.MEETINGS[0]["sections"],
        "past_url": url("meetings"),
    })


def meeting(request, body, term, number):
    today = logic.today()
    site = logic.site_settings()
    m = logic.find_meeting(body, term, number, today)
    if m is None:
        raise Http404("No such meeting")
    is_senate = body == "senate"
    if is_senate:
        snapshot = logic.group_seats(logic.voting_senate_seats())
        presiding = [s for s in data.SEATS if s["fill_rule"] == "gm"]
    else:
        snapshot = logic.group_seats([s for s in data.SEATS if s["body"] == "eboard"])
        presiding = []
    return page(request, "meeting.html", {
        "section": "meetings",
        "title": f"{m['body_name']} meeting #{m['number']}",
        "description": f"{m['term_label']}, {m['date_long']}, {m['time']}: agenda, minutes, who is on the body and how to speak.",
        "m": m,
        "is_senate": is_senate,
        "senate_counts": logic.senate_counts(),
        "eboard_counts": logic.eboard_counts(),
        "snapshot": snapshot,
        "presiding": presiding,
        "senate_nonvoting": logic.senate_nonvoting(),
        "senate_nonvoting_note": data.SENATE_NONVOTING_NOTE,
        "reconciliation": data.RECONCILIATION,
        "eboard_roster_note": data.EBOARD_ROSTER_NOTE,
        "motions_here": [],  # no sample motion belongs to Senate meeting #12
        "folder": logic.box_folder(body),
        "site": site,
        "meetings_url": url("meetings"),
        "seat_source_note": data.SEAT_SOURCE_NOTE,
    })


# --------------------------------------------------------------------------
# Funding
# --------------------------------------------------------------------------

def funding(request):
    funds = []
    for f in data.BUDGET["funds"]:
        funds.append({**f, "initial_text": logic.money(f["initial"]) or "Not applicable", "current_text": logic.money(f["current"])})
    return page(request, "funding.html", {
        "section": "funding",
        "title": "Get money for your club",
        "description": "How the Executive Board hands out Union money to clubs, what the Constitution says, and what we still need to confirm.",
        "rules": data.BUDGET_RULES,
        "funds": funds,
        "budget": data.BUDGET,
        "folder": logic.box_folder("eboard"),
        "vp": logic.vp_club_relations(),
        "meetings_url": url("meetings"),
        "eboard_meeting_url": url("meeting:eboard/fy27/1"),
        "start_url": url("about#funding-owner"),
        "ballroom_source": data.AGENDA_SRC["eboard"],
    })


# --------------------------------------------------------------------------
# Take part
# --------------------------------------------------------------------------

def take_part(request):
    processes = []
    for p in data.PROCESSES:
        p = logic.mark_deep(p)
        p["who_links"] = logic.resolve_links(p.get("who_links", []))
        if p["id"] == "challenge":
            p["example"] = logic.challenge_example()
        if p["id"] == "run":
            p["see_seats_url"] = url("about#get-involved")
        processes.append(p)
    return page(request, "take_part.html", {
        "section": "take_part",
        "elections_chair": logic.person_text("elections_chair"),
        "title": "Run for office or start a petition",
        "description": "Things any Union member can start under the Rensselaer Union Constitution: run for office, petition, referendum, recall and more.",
        "processes": processes,
    })


# --------------------------------------------------------------------------
# About
# --------------------------------------------------------------------------

def about(request):
    bodies = []
    for b in data.BODIES:
        b = logic.mark_deep(b)
        b["links"] = logic.resolve_links(b.get("links", []))
        b["leader"] = logic.body_leader(b)
        bodies.append(b)
    glossary = [{**logic.mark_deep(g), "slug": slugify(g["term"])} for g in data.GLOSSARY]
    by_term = {g["term"]: g for g in glossary}
    officer_terms = [by_term[t] for t in data.OFFICER_TERMS]
    native_pages = [
        ("The homepage verbs and \"This week\"", "home"),
        ("Raise an issue (the topic router)", "issue_index"),
        ("Get money for your club (a start page; its quoted table is the exception)", "funding"),
        ("Run for office or start a petition", "take_part"),
        ("How the Union works (bodies, officers, committees, glossary)", "about"),
    ]
    return page(request, "about.html", {
        "section": "about",
        "title": "How the Union works",
        "description": "Plain-language guide to the Rensselaer Union's bodies, officers, committees and terms, and how this site is maintained.",
        "bodies": bodies,
        "officers_text": data.OFFICERS_TEXT,
        "officer_terms": officer_terms,
        "committees": logic.committees_with_chairs(),
        "eb_committees": logic.eb_committees_with_chairs(),
        "elections_chair": logic.person_text("elections_chair"),
        "gm_ex_officio": data.GM_EX_OFFICIO,
        "glossary": glossary,
        "open_groups": logic.open_seat_groups(),
        "senate_counts": logic.senate_counts(),
        "ownership_by_body": data.OWNERSHIP_BY_BODY,
        "ownership_shared": data.OWNERSHIP_SHARED,
        "records_standard": [{**r, "text": mark_safe(r["text"])} for r in data.RECORDS_STANDARD],
        "native_pages": logic.resolve_links(native_pages),
        "publish_steps_by_adapter": [
            {"label": g["label"], "steps": [mark_safe(s) for s in g["steps"]]} for g in data.PUBLISH_STEPS_BY_ADAPTER
        ],
        "officer_rules": data.OFFICER_RULES,
        "rollover": data.TERM_ROLLOVER,
        "take_part_url": url("take_part"),
    })
