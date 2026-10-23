"""Helpers that turn the seed data (and optional read-only DB rows) into
what the templates need.  Nothing here writes to the database."""

import re
from datetime import timedelta
from urllib.parse import quote

from django.db import DatabaseError
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape
from django.utils.safestring import mark_safe

from . import data

NS = "lab:front_door:"

DERIVED_HTML = '<abbr title="Our arithmetic, assuming all 29 seats count">(derived)</abbr>'


def today():
    """Today's date at the Union (Eastern time).  The server runs on UTC, so
    ``timezone.localdate()`` would already say tomorrow after 8 PM Eastern,
    which is exactly when the Senate meets."""
    return timezone.localdate(timezone=data.ET)


# --------------------------------------------------------------------------
# URLs
# --------------------------------------------------------------------------

def url(spec):
    """Resolve "name", "name#frag", "name:arg" or "meeting:body/term/n"."""
    frag = ""
    if "#" in spec:
        spec, frag = spec.split("#", 1)
        frag = "#" + frag
    name, _, arg = spec.partition(":")
    args = []
    if arg:
        args = arg.split("/")
        if name == "meeting":
            args[2] = int(args[2])
    return reverse(NS + name, args=args) + frag


def resolve_links(pairs):
    return [{"label": label, "url": url(spec)} for label, spec in pairs]


# --------------------------------------------------------------------------
# Text
# --------------------------------------------------------------------------

def mark(text):
    """Turn the [[derived]] token into the "(derived)" marker."""
    if isinstance(text, str) and "[[derived]]" in text:
        return mark_safe(escape(text).replace("[[derived]]", DERIVED_HTML))
    return text


def mark_deep(obj):
    if isinstance(obj, str):
        return mark(obj)
    if isinstance(obj, list):
        return [mark_deep(o) for o in obj]
    if isinstance(obj, tuple):
        return tuple(mark_deep(o) for o in obj)
    if isinstance(obj, dict):
        return {k: mark_deep(v) for k, v in obj.items()}
    return obj


def money(value):
    if value is None:
        return None
    if float(value).is_integer():
        return f"${value:,.0f}"
    return f"${value:,.2f}"


def short_date(d):
    return f"{d.day} {d.strftime('%b %Y')}"


def initials(name):
    if not name:
        return ""
    words = [w for w in re.sub(r"[^\w\s'.-]", "", name).split() if not w.startswith("'") and w.lower() not in ("dr.",)]
    if not words:
        return ""
    if len(words) == 1:
        return words[0][0].upper()
    return (words[0][0] + words[-1][0]).upper()


# --------------------------------------------------------------------------
# Optional read-only DB reads (each one falls back to the seed)
# --------------------------------------------------------------------------

SETTING_FIELDS = ("contact_email", "office_location", "office_hours", "discord_url", "instagram_url", "box_archive_url")


def site_settings():
    """Blank values for anything missing.  Uses a plain read: SiteSettings.load()
    would create the row on first use, and this prototype never writes."""
    row = None
    try:
        from home.models import SiteSettings

        row = SiteSettings.objects.first()
    except DatabaseError:
        row = None
    return {f: (getattr(row, f, "") or "") for f in SETTING_FIELDS}


def db_events(now_date):
    """Non-meeting EventPages whose next occurrence is within 7 days."""
    try:
        from events.models import EventPage
        from home.models import _upcoming_by_next_occurrence

        events = list(EventPage.objects.live().exclude(event_type="meeting"))
        upcoming = _upcoming_by_next_occurrence(events, now_date, limit=5)
    except DatabaseError:
        return []
    out = []
    for e in upcoming:
        when = e.display_date
        if not (0 <= (when - now_date).days <= 7):
            continue
        try:
            link = e.url
        except Exception:  # no Site configured, for example
            link = None
        out.append({"title": e.title, "url": link, "date": when, "date_short": f"{when.strftime('%a')} {short_date(when)}",
                    "time": e.start_time.strftime("%-I:%M %p") if e.start_time else "", "location": e.location})
    return out


def roster_db_count():
    """How many MemberRoleAssignment rows exist (0 in the empty dev DB)."""
    try:
        from branches.models import MemberRoleAssignment

        return MemberRoleAssignment.objects.count()
    except DatabaseError:
        return 0


# --------------------------------------------------------------------------
# Meetings
# --------------------------------------------------------------------------

def decorate_meeting(m, now_date):
    d = dict(m)
    starts = m["starts"]
    d["date"] = starts.date()
    d["date_short"] = f"{starts.strftime('%a')} {short_date(starts.date())}"
    d["date_long"] = f"{starts.strftime('%A')} {starts.day} {starts.strftime('%B %Y')}"
    d["time"] = f"{starts.strftime('%-I:%M %p')} ET"
    d["days_since"] = (now_date - starts.date()).days
    d["url"] = reverse(NS + "meeting", args=[m["body"], m["term_slug"], m["number"]])
    d["title"] = f"{m['body_name']} meeting #{m['number']}"
    # Agenda and minutes status come only from whether a link exists.
    d["has_file_link"] = bool(m.get("agenda_url") or m.get("minutes_url"))
    d["folder"] = box_folder(m["body"])
    d["speak_phrase"] = speak_phrase(m)
    d["speak_draft"] = "E-Board bylaws" if m["body"] == "eboard" else "Senate bylaws or rules"
    # Each body keeps its meeting records its own way; the source lines follow.
    d["records"] = data.BODY_RECORDS[m["body"]]
    d["record_source"] = data.SOURCES["meeting_" + m["body"]]
    d["file_missing_source"] = data.SOURCES["file_missing_" + m["body"]]
    d["record_label"] = d["records"]["adapter_label"]
    d["is_senate"] = m["body"] == "senate"
    agenda = m.get("agenda_url") or ""
    d["agenda_embed_url"] = agenda.replace("/s/", "/embed/s/") if "/s/" in agenda else None
    return d


def speak_phrase(m):
    """Where anyone may speak, worked out from where the Invitation to Speak
    sections sit on this meeting's agenda: "at the start and end", "at the end",
    "at the start", or None if the agenda has none."""
    sections = m["sections"]
    half = len(sections) / 2
    spots = {("start" if i < half else "end") for i, sec in enumerate(sections) if sec["title"].startswith("Invitation to Speak")}
    if spots == {"start", "end"}:
        return "at the start and end"
    if spots:
        return f"at the {spots.pop()}"
    return None


def all_meetings(now_date):
    ms = [decorate_meeting(m, now_date) for m in data.MEETINGS if m["public"]]
    return sorted(ms, key=lambda m: m["starts"], reverse=True)


def this_week(now_date):
    return [m for m in reversed(all_meetings(now_date)) if 0 <= (m["date"] - now_date).days <= 7]


def past_meetings(now_date):
    return [m for m in all_meetings(now_date) if m["date"] < now_date]


def upcoming_meetings(now_date):
    return [m for m in reversed(all_meetings(now_date)) if m["date"] >= now_date]


def latest_meeting(body, now_date):
    """The most recent public meeting of a body (the next one once it is listed)."""
    ms = [m for m in all_meetings(now_date) if m["body"] == body]
    return ms[0] if ms else None


def find_meeting(body, term, number, now_date):
    for m in data.MEETINGS:
        if m["public"] and (m["body"], m["term_slug"], m["number"]) == (body, term, number):
            return decorate_meeting(m, now_date)
    return None


def decisions():
    """Senate motions (the projection of the Senate's Notion Motions table),
    newest first.  Other bodies' decisions stay in their minutes."""
    out = [dict(d) for d in data.SAMPLE_DECISIONS]
    for d in out:
        d["status_label"] = data.STATUS_LABELS[d["status"]]
        d["date_short"] = short_date(d["date"])
    return sorted(out, key=lambda d: d["date"], reverse=True)


def box_folders(site):
    out = []
    for key, f in data.BOX_FOLDERS.items():
        shared = f["shared_url"]
        embed = shared.replace("/s/", "/embed/s/") if shared and "/s/" in shared else None
        out.append({**f, "key": key, "embed_url": embed})
    return out


def box_folder(key):
    return next(f for f in box_folders(None) if f["key"] == key)


def folder_bodies():
    """Bodies that publish records as files only, each with its Box folder."""
    return [
        {**r, "key": k, "folder": box_folder(k), "note": data.FOLDER_ONLY_NOTES.get(k)}
        for k, r in data.BODY_RECORDS.items()
        if r["adapter"] == "folder"
    ]


def meeting_body_folders():
    """Box folders of the bodies that list meetings on this site."""
    return [f for f in box_folders(None) if data.BODY_RECORDS[f["key"]]["adapter"] != "folder"]


# --------------------------------------------------------------------------
# Seats
# --------------------------------------------------------------------------

def voting_senate_seats():
    return [s for s in data.SEATS if s["body"] == "senate" and s["fill_rule"] != "gm"]


def voting_eboard_seats():
    return [s for s in data.SEATS if s["body"] == "eboard" and s["fill_rule"] != "pu" and s["constituency"] != "officers"]


def senate_counts():
    seats = voting_senate_seats()
    c = {
        "total": len(seats),
        "filled": sum(s["status"] == "filled" for s in seats),
        "vacant": sum(s["status"] == "vacant" for s in seats),
        "fall": sum(s["status"] == "elect_fall" for s in seats),
    }
    c["line"] = (f"{c['total']} voting seats (Constitution) · {c['filled']} filled on the 30 Jul 2026 roster · "
                 f"{c['vacant']} vacant · {c['fall']} first-year seats to be elected this fall")
    return c


def eboard_counts():
    seats = voting_eboard_seats()
    return {"total": len(seats), "vacant": sum(s["status"] == "vacant" for s in seats)}


def open_seats():
    return [s for s in data.SEATS if s["holder"] is None and s["body"] in ("senate", "eboard")]


def contact_for(seat, site):
    if seat.get("inbox"):
        return {"href": f"mailto:{seat['inbox']}", "text": seat["inbox"], "note": ""}
    subject = quote(f"For: {seat['seat']}")
    if site.get("contact_email"):
        return {"href": f"mailto:{site['contact_email']}?subject={subject}", "text": "Union office",
                "note": " (this seat has no role inbox yet)"}
    return {"href": None, "text": "Union office", "note": " (this seat has no role inbox yet)", "needs_draft": True}


# What a student can do about a vacant seat depends on how it gets filled.
SEAT_ACTIONS = {
    "gm": ("Run for office", "take_part#run"),
    "pu": ("Run for office", "take_part#run"),
    "class_senator": ("Run for office", "take_part#run"),
    "elected_appointed": ("Run for office", "take_part#run"),
    "eb_appointed": ("How appointments work", "take_part#appointed"),
    # eb_peer: chosen by another body, so there is nothing for a student to start
}


def seat_action(seat):
    spec = SEAT_ACTIONS.get(seat["fill_rule"])
    return {"label": spec[0], "url": url(spec[1])} if spec else None


def card(seat, site, note=None):
    c = dict(seat)
    c["action"] = seat_action(seat)
    c["initials"] = initials(seat["holder"])
    c["fill"] = data.FILL_RULES.get(seat["fill_rule"])
    c["contact"] = contact_for(seat, site)
    c["note"] = note
    return c


def cards(seats, site, note=None):
    return [card(s, site, note) for s in seats]


def group_seats(seats):
    """[(group name, [seats])] in order of first appearance."""
    order, groups = [], {}
    for s in seats:
        if s["group"] not in groups:
            groups[s["group"]] = []
            order.append(s["group"])
        groups[s["group"]].append(s)
    return [(g, groups[g]) for g in order]


def open_seat_groups():
    """Open seats grouped by seat type, with the fill rule for each."""
    out = []
    for g, seats in group_seats(open_seats()):
        s0 = seats[0]
        vacant = sum(s["status"] == "vacant" for s in seats)
        fall = sum(s["status"] == "elect_fall" for s in seats)
        body = "Student Senate" if s0["body"] == "senate" else "Executive Board"
        out.append({"group": g, "body": body, "vacant": vacant, "fall": fall, "count": len(seats), "fill": data.FILL_RULES.get(s0["fill_rule"])})
    return out


def challenge_example():
    best = None
    for key in ("2027", "2028", "2029", "2030"):
        n = sum(1 for s in data.SEATS if s["body"] == "senate" and s["constituency"] == key and s["status"] == "vacant")
        if n and (best is None or n > best[1]):
            best = (key, n)
    if not best:
        return ""
    key, n = best
    seats = "seat" if n == 1 else "seats"
    return (f"Right now the Class of {key} has {n} vacant Senate {seats}. If its Class Council appoints "
            f"{'someone' if n == 1 else 'people'} to {'it' if n == 1 else 'them'}, 20% of the class can force an election.")


# --------------------------------------------------------------------------
# Roster lookups (the only way content here refers to a person)
# --------------------------------------------------------------------------

def seat_for(role):
    """Look up a seat or role by its role key.  Returns a dict with ``title``,
    ``holder`` (None if vacant), ``acting`` and ``inbox``, or None for an
    unknown key.  Seats win over other role assignments."""
    for s in data.SEATS:
        if s.get("role") == role:
            return {"role": role, "title": s["seat"], "holder": s["holder"], "acting": False, "unlisted": False, "inbox": s["inbox"]}
    return data.ROLE_BY_KEY.get(role)


def holder_name(role):
    r = seat_for(role)
    return r["holder"] if r else None


def person_text(role, with_title=False):
    """"Name", "Name, acting" or "Name (Title)" for a role; None if no holder."""
    r = seat_for(role)
    if not r or not r["holder"]:
        return None
    text = r["holder"] + (", acting" if r["acting"] else "")
    if with_title:
        text += f" ({r['title']})"
    return text


def chair_cell(role):
    """Chair column text: the holder, "(acting)" if so, else None (vacant)."""
    r = seat_for(role)
    if not r or not r["holder"]:
        return None
    return r["holder"] + (" (acting)" if r["acting"] else "")


def committees_with_chairs():
    rows = []
    for c in data.COMMITTEES:
        label = f"{c['code']} {c['name']}".strip()
        rows.append({"label": label, "handles": c["handles"], "chair": chair_cell(c["chair_role"])})
    return rows


def eb_committees_with_chairs():
    return [{"name": c["name"], "handles": c["handles"], "chair": chair_cell(c["chair_role"])} for c in data.EB_COMMITTEES]


def topic_chair(topic):
    """The owner seat's holder for the "Chair:" line, or "Roster not listed yet"."""
    r = seat_for(topic["owner_seat"])
    if r is None:
        return None
    if r.get("unlisted"):
        return "Roster not listed yet"
    if not r["holder"]:
        return None
    text = r["holder"] + (" (acting)" if r["acting"] else "")
    if not r["title"].lower().endswith("chair"):
        text += f" ({r['title']})"
    return text


def topic_inbox(topic):
    """The owner seat's role inbox (always None in the seed)."""
    r = seat_for(topic["owner_seat"])
    return r["inbox"] if r else None


def topic_owner_title(topic):
    r = seat_for(topic["owner_seat"])
    return r["title"] if r else topic["owner_seat"]


def vp_club_relations():
    return holder_name("vp_club_relations")


def senate_nonvoting():
    return [{"title": n["title"], "holder": holder_name(n["role"])} for n in data.SENATE_NONVOTING]


def body_leader(body):
    """"Name (Title)" for a body's leader, looked up from the roster."""
    role = body.get("leader_role")
    return person_text(role, with_title=True) if role else None


def agenda_reporter(body, item_title):
    """Who gave a named report at a body's latest listed meeting, read from
    the meeting's own agenda items.  Returns (name or None, meeting dict)."""
    for m in data.MEETINGS:
        if m["body"] != body:
            continue
        for section in m["sections"]:
            for item in section["items"]:
                if item["title"] == item_title:
                    return item["who"], decorate_meeting(m, today())
    return None, None
