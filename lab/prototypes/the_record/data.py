"""Seed data and pure helpers for the "Public Record + Desk" prototype.

Nothing here connects to Box or Notion. Every sync time, link-check result and
health flag is seed data. The Rensselaer Union has no Box API, so the site only
ever uses Box *shared links* that a secretary pastes into the meeting record.

Facts confirmed by the Union Constitution (last amended 6 Feb 2026) carry a
``cite``. Things the Constitution leaves to someone else carry ``draft``.
Made-up values carry ``sample=True``.
"""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

NY = ZoneInfo("America/New_York")

# --------------------------------------------------------------------------
# Sync and source configuration
# --------------------------------------------------------------------------

SYNC = {
    "notion_minutes_ago": 12,
    "notion_last_success": datetime(2026, 10, 21, 13, 48, tzinfo=NY),
    "notion_next_run_minutes": 3,
    "notion_last_error": None,
    "webhook_last": "2 hours ago",
    "box_links_checked": date(2026, 10, 19),
    "wagtail_reviewed": date(2026, 10, 21),
    "eboard_entry_updated": date(2026, 8, 24),  # last edit of the E-Board's meeting entries on this site
    "roster_updated": date(2026, 8, 25),  # last roster change entered on this site
}
MOCK_NOTION = "https://www.notion.so/"
MOCK_BOX = "https://rpi.box.com/"

# Site-wide notice (alert slot on home). None means no notice.
NOTICE = None

DRAFT_WHY = (
    "Senate bylaws or rules",
    "Senate election rules",
    "E-Board bylaws",
    "Judicial Board bylaws",
    "Union staff process",
    "Site owner",
)


def fmt_date(d):
    """30 Jul 2026"""
    return f"{d.day} {d:%b %Y}"


def fmt_day_month(d):
    """24 Oct"""
    return f"{d.day} {d:%b}"


def fmt_time(dt):
    hour = dt.hour % 12 or 12
    return f"{hour}:{dt:%M} {'AM' if dt.hour < 12 else 'PM'}"


def fmt_long(dt):
    """Thursday 30 Jul 2026"""
    return f"{dt:%A} {dt.day} {dt:%b %Y}"


def minutes_ago_text(n):
    return "just now" if n == 0 else f"{n} min ago"


def build_sources(sync=None):
    sync = sync or SYNC
    synced = f"synced {minutes_ago_text(sync['notion_minutes_ago'])}"
    checked = fmt_date(sync["box_links_checked"])
    reviewed = fmt_date(sync["wagtail_reviewed"])
    eboard_updated = fmt_date(sync["eboard_entry_updated"])
    roster_updated = fmt_date(sync["roster_updated"])

    def src(key, line, label, url):
        return {"key": key, "line": line, "edit_label": label, "edit_url": url}

    return {
        "meeting_senate": src(
            "meeting_senate", f"Meeting record: Senate's Notion · {synced}", "Edit in Notion", MOCK_NOTION
        ),
        "meeting_eboard": src(
            "meeting_eboard",
            f"Meeting record: entered on this site by the E-Board Secretary · updated {eboard_updated}",
            "Edit on this site",
            "/admin/",
        ),
        "folder_only": src(
            "folder_only",
            "Records: files in this body's Box folder. It doesn't list meetings on this site.",
            "Open in Box",
            MOCK_BOX,
        ),
        "agenda_items_option": src(
            "agenda_items_option",
            "Agenda items: Senate's Notion agenda page · only if the Senate drafts agendas in Notion "
            f"(an option, not current practice) · {synced}",
            "Edit in Notion",
            MOCK_NOTION,
        ),
        "file": src(
            "file",
            f"Documents: Word files in Box, published as PDF · links checked {checked}",
            "Edit in Box",
            MOCK_BOX,
        ),
        "motions": src(
            "motions",
            "Motion status: Senate's Notion Motions table · the motion's text is in the linked Word file "
            f"· {synced}",
            "Edit in Notion",
            MOCK_NOTION,
        ),
        "in_minutes": src(
            "in_minutes",
            "Decisions: recorded in the minutes (a Word file in Box). This site doesn't retype them.",
            "Open in Box",
            MOCK_BOX,
        ),
        "roster": src(
            "roster",
            "Roster: entered on this site by each body's roster officer · last change " + roster_updated,
            "Edit on this site",
            "/admin/",
        ),
        "quoted_budget": src(
            "quoted_budget",
            "Quoted from Executive Board Agenda 01, 25 Aug 2026 (a PDF in Box). "
            "This site does not update these figures.",
            "Open in Box",
            MOCK_BOX,
        ),
        "wagtail": src("wagtail", f"Written on this site · reviewed {reviewed}", "Edit in Wagtail", "/admin/"),
    }


# --------------------------------------------------------------------------
# Box folders and naming
# --------------------------------------------------------------------------

BOX_FOLDERS = {
    "senate": {
        "label": "Student Senate, 57th Senate",
        "path": "Public Records/Senate/2026-27 Senate 57/",
        "shared_url": None,
    },
    "eboard": {
        "label": "Executive Board, FY27",
        "path": "Public Records/Executive Board/2026-27 EBoard FY27/",
        "shared_url": None,
    },
    "gc": {
        "label": "Graduate Council, 2026-27",
        "path": "Public Records/Graduate Council/2026-27 GC 2026-27/",
        "shared_url": None,
    },
    "uc": {
        "label": "Undergraduate Council, 2026-27",
        "path": "Public Records/Undergraduate Council/2026-27 UC 2026-27/",
        "shared_url": None,
    },
    "jboard": {
        "label": "Judicial Board, 2026-27",
        "path": "Public Records/Judicial Board/2026-27 JBoard 2026-27/",
        "shared_url": None,
    },
}

BOX_NAME_PATTERN = "YYYY-MM-DD <Body> <Term> #<nn> <Agenda|Minutes|Attachment - Title>.pdf"
BOX_BODY_CODES = ["Senate", "EBoard", "JBoard", "GC", "UC"]
RENAMES = [
    ("#12 07_30_26 57th Student Senate Meeting Agenda-1.pdf", "2026-07-30 Senate 57 #12 Agenda.pdf"),
    ("FY27 Agenda 1 - August 25, 2026.pdf", "2026-08-25 EBoard FY27 #01 Agenda.pdf"),
]


def box_embed_url(shared_url):
    """Only /s/ shared links can be embedded. Anything else returns None."""
    if shared_url and "/s/" in shared_url:
        return shared_url.replace("/s/", "/embed/s/", 1)
    return None


def box_folders_with_embeds():
    out = {}
    for key, folder in BOX_FOLDERS.items():
        out[key] = {**folder, "key": key, "embed_url": box_embed_url(folder["shared_url"])}
    return out


# --------------------------------------------------------------------------
# Bodies
# --------------------------------------------------------------------------

BODIES = {
    "senate": {
        "key": "senate",
        "name": "Student Senate",
        "short": "Senate",
        "term_slug": "57",
        "term_label": "57th Student Senate",
        "folder": "senate",
        "adapter": "notion",
        "adapter_label": "Senate's Notion",
        "records_officer": "Senate Secretary",
        "fix_label": "Fix in Notion",
        "fix_url": MOCK_NOTION,
        "example": False,
    },
    "eboard": {
        "key": "eboard",
        "name": "Executive Board",
        "short": "E-Board",
        "term_slug": "fy27",
        "term_label": "2026–27 Executive Board (FY27)",
        "folder": "eboard",
        "adapter": "site",
        "adapter_label": "Entered on this site",
        "records_officer": "E-Board Secretary",
        "fix_label": "Fix on this site",
        "fix_url": "/admin/",
        "example": True,
    },
}

# Bodies with no meeting records on this site: their Box folder only.
FOLDER_BODIES = {
    "gc": {
        "key": "gc",
        "name": "Graduate Council",
        "short": "Graduate Council",
        "adapter": "folder",
        "adapter_label": "Box folder only",
        "records_officer": None,
        "records_confirmed": None,
        "folder": "gc",
        "example": True,
        "note": None,
        "draft": None,
    },
    "uc": {
        "key": "uc",
        "name": "Undergraduate Council",
        "short": "Undergraduate Council",
        "adapter": "folder",
        "adapter_label": "Box folder only",
        "records_officer": None,
        "records_confirmed": None,
        "folder": "uc",
        "example": True,
        "note": "Including the four Class Councils.",
        "draft": None,
    },
    "jboard": {
        "key": "jboard",
        "name": "Judicial Board",
        "short": "Judicial Board",
        "adapter": "folder",
        "adapter_label": "Box folder only",
        "records_officer": None,
        "records_confirmed": None,
        "folder": "jboard",
        "example": True,
        "note": "Its rulings on what the Constitution means are public. Its conduct and rights cases are confidential.",
        "draft": "Judicial Board bylaws",
    },
}


def _dt(y, mo, d, h=0, mi=0):
    return datetime(y, mo, d, h, mi, tzinfo=NY)


# --------------------------------------------------------------------------
# Glosses, meetings, agendas (real, from the two agendas)
# --------------------------------------------------------------------------

_SB = "Senate bylaws or rules"
_EB = "E-Board bylaws"


def _s(title, plain, items=None, cite=None, draft=None):
    return {"title": title, "plain": plain, "items": items or [], "cite": cite, "draft": draft}


def _i(title, who=None, type="report", plain=None, cite=None):
    item = {"title": title, "who": who, "type": type}
    if plain:
        item["plain"] = plain
        item["cite"] = cite
    return item


_SPEAK = "Time set aside for anyone, in the room or on Webex, to speak or ask questions."

WTG_CHAIR = "Web Technologies Group (WTG) chair"
VGMIA = "Vice Grand Marshal for Internal Affairs (VGMIA)"

SENATE_12_SECTIONS = [
    _s("Bookkeeping", "Routine housekeeping before the main agenda.", [_i("Polytechnic Statement of Recording", None, "notice")], draft=_SB),
    _s("Invitation to Speak and Press & Visitor Q/A", _SPEAK, draft=_SB),
    _s(
        "Grand Marshal Report",
        "An update from the Grand Marshal, the Union's chief spokesperson.",
        cite="Art. IV §1",
    ),
    _s(
        "Committee Reports",
        "Each committee chair says what their committee has been working on.",
        [
            _i("Academic Affairs", "Zach Nobles '27"),
            _i("Community Relations", "Mia Stryhalaleck '28"),
            _i("Elections Commission", "Lauren Antao '28"),
            _i("Facilities and Services", "Charlie Fowle '29"),
            _i("Residential Living and Dining", "Shruthi Anandraman '28"),
            _i("Rules and Administration", "Griffin Oliver '27"),
            _i("Student Life", "Stanley Goodwin '30G"),
            _i("Senate Communications and Engagement", "Emily Lin '29"),
            _i("Web Technologies Group", "Aaron Niyazov '28"),
            _i("Union Annual Report", "Samson Kempiak '28"),
        ],
        draft=_SB,
    ),
    _s(
        "Peer Body & Officer Reports",
        "Updates from the Senate's own officers and from other Union bodies.",
        [
            _i("Vice Grand Marshal for External Affairs", "Ryan Kilgore '27"),
            _i("Vice Grand Marshal for Internal Affairs", "Griffin Oliver '27"),
            _i("Executive Board", "Cee Ray '27"),
            _i("Graduate Council", "Melissa Flores 'G"),
            _i("Undergraduate Council", "Nick Castiglione '28"),
            _i("Interfraternity Council", "Vacant"),
            _i("Panhellenic Council", "Vacant"),
            _i("Multicultural Sorority and Fraternity Council", "Vacant"),
            _i("Senate Treasurer", "Cee Ray '27"),
            _i("Secretary", "Selena Tang '29"),
            _i("Parliamentarian", "Sasha Notkin '28"),
        ],
        draft=_SB,
    ),
    _s("Special Orders", "Items the Senate has given a set place on the agenda.", draft=_SB),
    _s("Old Business", "Items carried over from earlier meetings.", draft=_SB),
    _s("New Business", "New items for the Senate to discuss or vote on.", draft=_SB),
    _s("Invitation to Speak and Press & Visitor Q/A", _SPEAK, draft=_SB),
]

EBOARD_01_SECTIONS = [
    _s("Approval of Minutes", "The Board votes to accept the minutes of its previous meeting.", draft=_EB),
    _s(
        "Reports",
        "Updates from officers, advisers and committees.",
        [
            _i("President", "Kate Goldstein '26 '27G"),
            _i("VP Board Operations", "Gavin Finn '28"),
            _i("VP Club Relations", "Jesse Kim '26 '27G"),
            _i("VP Rules and Special Projects", "Blaine Rosenberg '28"),
            _i(
                "Director's Report",
                "Dr. Charlie Potts",
                plain="An update from the Director of the Union, a paid staff adviser who runs Union activities and funds.",
                cite="Art. V",
            ),
            _i("Student Senate", "Cee Ray '27"),
            _i("Undergraduate Council", "Vacant"),
            _i("Graduate Council", "Joydip Paul '29G"),
            _i("Committee report: Business Operations", "Grey Smith '27"),
            _i("Committee report: Club Operations", "Elijah Pulga '29"),
            _i("Committee report: Marketing & Strategy", "Vacant"),
            _i("Committee report: Executive Communication", "Vacant"),
            _i("Committee report: Multicultural Leadership Council", "Mariam Toure '28"),
            _i("Committee report: Union Annual Report", "Ava Cintula '29"),
            _i("Committee report: Union Programming and Activities Committee", "Lilu Kaufman '26"),
        ],
        draft=_EB,
    ),
    _s(
        "Proposals",
        "Requests that need a vote of the Board.",
        [
            _i("Special Ballroom Request, Society of Women Engineers", None, "proposal"),
            _i("Special Ballroom Request, RPI Admissions", None, "proposal"),
        ],
        draft=_EB,
    ),
    _s("Business", "Topics the Board discusses.", [_i("Rally Week Discussion", None, "discussion")], draft=_EB),
    _s("Invitation to Speak", _SPEAK, draft=_EB),
    _s("Press & Visitor Q/A", "Time set aside for reporters and visitors to ask questions.", draft=_EB),
]

MEETINGS = [
    {
        "body": "senate",
        "body_name": "Student Senate",
        "term_slug": "57",
        "term_label": "57th Student Senate",
        "number": 12,
        "starts": _dt(2026, 7, 30, 20, 0),
        "location": "Webex",
        "remote": True,
        "agenda_url": None,
        "minutes_url": None,
        "minutes_approved": None,
        "public": True,
        "record_edited": _dt(2026, 7, 28, 21, 10),
        "voting_listed": 19,
        "quorum": 13,
        "nonvoting": 10,
        "seats_constitution": 29,
        "seats_cite": "Art. VII §1",
        "agenda_source": "Student Senate Meeting Agenda #12, 30 Jul 2026",
        "prototype_note": "Prototype note: the real agenda PDF exists in Box; its shared link was never pasted, "
        "so the site can't show it.",
        "sample": False,
        "sections": SENATE_12_SECTIONS,
    },
    {
        "body": "eboard",
        "body_name": "Executive Board",
        "term_slug": "fy27",
        "term_label": "2026–27 Executive Board (FY27)",
        "number": 1,
        "starts": _dt(2026, 8, 25, 19, 0),
        "location": "Rensselaer Union, room 3202",
        "remote": False,
        "agenda_url": None,
        "minutes_url": None,
        "minutes_approved": None,
        "public": True,
        "record_edited": _dt(2026, 8, 24, 16, 2),
        "voting_listed": 12,
        "quorum": 8,
        "nonvoting": 7,
        "seats_constitution": "15 to 20",
        "seats_cite": "Art. VII §2",
        "agenda_source": "Executive Board Agenda 01, 25 Aug 2026",
        "prototype_note": "Prototype note: the real agenda PDF exists in Box; its shared link was never pasted, "
        "so the site can't show it.",
        "sample": False,
        "sections": EBOARD_01_SECTIONS,
    },
    {
        # SAMPLE: shows the honest "Agenda not posted yet" state.
        "body": "senate",
        "body_name": "Student Senate",
        "term_slug": "57",
        "term_label": "57th Student Senate",
        "number": 16,
        "starts": _dt(2026, 10, 26, 19, 0),
        "location": "Location to be confirmed",
        "remote": False,
        "agenda_url": None,
        "minutes_url": None,
        "minutes_approved": None,
        "public": True,
        "record_edited": _dt(2026, 10, 19, 18, 30),
        "voting_listed": None,
        "quorum": None,
        "nonvoting": None,
        "seats_constitution": 29,
        "seats_cite": "Art. VII §1",
        "agenda_source": None,
        "sample": True,
        "sections": [],
    },
    {
        # SAMPLE: both links present; PDF-only agenda (written in Word).
        "body": "senate",
        "body_name": "Student Senate",
        "term_slug": "57",
        "term_label": "57th Student Senate",
        "number": 11,
        "starts": _dt(2026, 7, 16, 20, 0),
        "location": "Webex",
        "remote": True,
        "agenda_url": MOCK_BOX + "s/sample-senate-57-11-agenda",
        "minutes_url": MOCK_BOX + "s/sample-senate-57-11-minutes",
        "minutes_approved": date(2026, 7, 30),
        "public": True,
        "record_edited": _dt(2026, 7, 31, 10, 5),
        "voting_listed": None,
        "quorum": None,
        "nonvoting": None,
        "seats_constitution": 29,
        "seats_cite": "Art. VII §1",
        "agenda_source": None,
        "sample": True,
        "sections": [],
    },
]


def agenda_document_name(body, number, starts):
    """The Box file name the convention gives an agenda, e.g. 2026-08-25 EBoard FY27 #01 Agenda.pdf."""
    return f"{starts:%Y-%m-%d} {'Senate 57' if body == 'senate' else 'EBoard FY27'} #{number:02d} Agenda.pdf"


for _m in MEETINGS:
    _m["document_name"] = agenda_document_name(_m["body"], _m["number"], _m["starts"])


def _sample_past_meeting(body, number, starts, location, remote):
    """A made-up past meeting record: no links, no agenda items (same as a freshly synced row)."""
    info = BODIES[body]
    return {
        "body": body,
        "body_name": info["name"],
        "term_slug": info["term_slug"],
        "term_label": info["term_label"],
        "number": number,
        "starts": starts,
        "location": location,
        "remote": remote,
        "agenda_url": None,
        "minutes_url": None,
        "minutes_approved": None,
        "public": True,
        "record_edited": starts - timedelta(days=1),
        "document_name": agenda_document_name(body, number, starts),
        "voting_listed": None,
        "quorum": None,
        "nonvoting": None,
        "seats_constitution": 29 if body == "senate" else "15 to 20",
        "seats_cite": "Art. VII §1" if body == "senate" else "Art. VII §2",
        "agenda_source": None,
        "sample": True,
        "sections": [],
    }


# Made-up meetings that the sample decisions cite, so every decision belongs to a meeting record.
# Senate numbering continues after #12 (30 Jul); E-Board after #1 (25 Aug).
MEETINGS += [
    _sample_past_meeting("senate", 13, _dt(2026, 9, 9, 20, 0), "Webex", True),
    _sample_past_meeting("senate", 14, _dt(2026, 9, 23, 20, 0), "Webex", True),
    _sample_past_meeting("senate", 15, _dt(2026, 10, 14, 20, 0), "Webex", True),
    _sample_past_meeting("eboard", 2, _dt(2026, 9, 15, 19, 0), "Rensselaer Union, room 3202", False),
    _sample_past_meeting("eboard", 3, _dt(2026, 9, 22, 19, 0), "Rensselaer Union, room 3202", False),
    _sample_past_meeting("eboard", 4, _dt(2026, 10, 6, 19, 0), "Rensselaer Union, room 3202", False),
]


def meeting_ref(m):
    if m["body"] == "senate":
        return f"Senate {m['term_slug']} #{m['number']}"
    return f"E-Board {m['term_slug'].upper()} #{m['number']}"


def find_meeting(body, term, number):
    for m in MEETINGS:
        if m["body"] == body and m["term_slug"] == term and m["number"] == number:
            return m
    return None


def is_past(m, today):
    return m["starts"].astimezone(NY).date() < today


def meetings_for_body(body):
    return sorted((m for m in MEETINGS if m["body"] == body), key=lambda m: m["starts"])


def agenda_state(m):
    """linked | missing. Without the Box API the site only knows whether a link was pasted."""
    return "linked" if m.get("agenda_url") else "missing"


def minutes_state(m):
    """linked | missing."""
    return "linked" if m.get("minutes_url") else "missing"


# --------------------------------------------------------------------------
# Thresholds, petitions, named records, transparency rules
# --------------------------------------------------------------------------

DERIVED_TITLE = "Our arithmetic, assuming all 29 Senate seats count"


def _t(slug, action, body, needs, derived, cite, draft=None):
    return {
        "slug": slug,
        "action": action,
        "body": body,
        "needs": needs,
        "derived": derived,
        "cite": cite,
        "draft": draft,
    }


_THRESHOLD_LIST = [
    _t("senate_bylaws", "Pass or change Senate bylaws", "Senate", "2/3 of all voting seats", "20 of 29", "Art. VII §1"),
    _t("activity_fee", "Set the Union Activity Fee", "Senate", "2/3 of all voting seats", "20 of 29", "Art. VII §1"),
    _t("eb_appointment", "Approve the President's Executive Board appointments", "Senate", "2/3 of the Senate", None, "Art. VII §2"),
    _t(
        "eb_replacement",
        "Replace an Executive Board member mid-year",
        "E-Board then Senate",
        "President appoints; majority of the E-Board, then 2/3 of the Senate",
        None,
        "Art. VII §2",
    ),
    _t(
        "eb_bylaws",
        "Pass Executive Board bylaws",
        "E-Board then Senate",
        "2/3 of all E-Board voting seats, then a Senate majority",
        None,
        "Art. VII §2",
    ),
    _t(
        "pu_other_appointment",
        "Ratify the President's appointments other than E-Board members",
        "E-Board",
        "2/3 of the E-Board",
        None,
        "Art. IV §2",
    ),
    _t(
        "gm_nullify",
        "Cancel an appointment made by the Grand Marshal",
        "Senate",
        "Majority of all voting seats",
        "15 of 29",
        "Art. IV §1",
    ),
    _t(
        "jb_appointment",
        "Approve a new Judicial Board member",
        "Judicial Board then Senate",
        "2/3 of the Judicial Board, then 2/3 of the Senate",
        None,
        "Art. VII §3",
    ),
    _t("referendum_ballot", "Put a question to a student vote", "Senate", "2/3 vote", None, "Art. XII §1"),
    _t(
        "referendum_reject",
        "Refuse a referendum petition signed by 10% of students",
        "Senate",
        "2/3 of all voting seats",
        "20 of 29",
        "Art. XII §1",
    ),
    _t(
        "removal_call",
        "Call a removal election for the Grand Marshal, President of the Union, or a Council President",
        "Senate",
        "2/3 vote, or a Senate majority after a 20% petition",
        None,
        "Art. X §1",
    ),
    _t("senator_remove", "Remove a senator for good cause", "Senate", "2/3 of all voting seats", "20 of 29", "Art. X §2"),
    _t(
        "class_dues",
        "Change class dues",
        "Council then Senate",
        "Undergraduate Council majority (or 2/3 of the Graduate Council for graduate dues), then 2/3 of all Senate voting seats",
        "20 of 29",
        "Art. VII §4, §5",
    ),
    _t(
        "gm_vacancy",
        "Appoint a new Grand Marshal if the post falls vacant",
        "Senate",
        "2/3 of the Senate, within two weeks",
        None,
        "Art. XI §1",
    ),
    _t(
        "pu_vacancy",
        "Appoint a new President of the Union if the post falls vacant",
        "E-Board then Senate",
        "E-Board appoints within two weeks; 2/3 of the Senate confirms",
        None,
        "Art. XI §2",
    ),
    _t(
        "amendment",
        "Amend the Constitution",
        "Senate then all students",
        "2/3 of the Senate, then a majority of students voting, with at least 20% turnout",
        None,
        "Art. XIII §1",
    ),
    _t(
        "ordinary",
        "Everything else",
        "any body",
        "Not set by the Constitution. Robert's Rules of Order apply wherever a body's own rules are silent.",
        None,
        "Art. VII §6",
        draft=_SB,
    ),
]
THRESHOLDS = {t["slug"]: t for t in _THRESHOLD_LIST}
THRESHOLD_ORDER = [t["slug"] for t in _THRESHOLD_LIST]

PETITIONS = [
    {
        "goal": "Force a student vote (referendum) on anything except the Constitution",
        "signatures": "10% of all Union members",
        "deadline": "Vote held within 45 days (excluding vacations) or at the next regular election, whichever is sooner; at least 14 days after approval; not during exams",
        "result": "Binding if a majority votes yes and at least 20% of affected students vote; the Senate must enact it",
        "cite": "Art. XII §1–§4",
    },
    {
        "goal": "Force an election for a seat that was filled by appointment",
        "signatures": "20% of that seat's constituency",
        "deadline": "Received by the Senate within two weeks of the announcement",
        "result": "Special election",
        "cite": "Art. XI §5",
    },
    {
        "goal": "Start a removal election for the Grand Marshal, President of the Union, or a Council President",
        "signatures": "20% of their constituents, then a Senate majority",
        "deadline": "None set",
        "result": "Removed by 2/3 of voters if at least 20% vote",
        "cite": "Art. X §1",
    },
    {
        "goal": "Remove the Grand Marshal, President of the Union, or a Council President outright",
        "signatures": "50% of their constituents",
        "deadline": "None set",
        "result": "Removed",
        "cite": "Art. X §1",
    },
    {
        "goal": "Recall an elected senator",
        "signatures": "20% of their constituents",
        "deadline": "None set",
        "result": "Removed by 2/3 of voters if at least 20% vote",
        "cite": "Art. X §2",
    },
]

NAMED_RECORDS = [
    {
        "name": "Rensselaer Union Constitution (last amended 6 Feb 2026)",
        "what": "The Union's founding rules",
        "published_here": "Not linked yet",
        "cite": "Art. XIII §5",
    },
    {"name": "Student Senate bylaws", "what": "The Senate's own rules", "published_here": "Not linked yet", "cite": "Art. VII §1"},
    {"name": "Executive Board bylaws", "what": "The Board's own rules", "published_here": "Not linked yet", "cite": "Art. VII §2"},
    {"name": "Judicial Board bylaws", "what": "The Board's own rules", "published_here": "Not linked yet", "cite": "Art. VII §3"},
    {"name": "Graduate Council bylaws", "what": "The Council's own rules", "published_here": "Not linked yet", "cite": "Art. VII §4"},
    {"name": "Undergraduate Council bylaws", "what": "The Council's own rules", "published_here": "Not linked yet", "cite": "Art. VII §5"},
    {
        "name": "Rensselaer Student Bill of Rights",
        "what": "Rights the Judicial Board enforces",
        "published_here": "Not linked yet",
        "cite": "Art. VII §3",
    },
    {
        "name": "Senate election procedure and rules",
        "what": "Ballot access, groupings for FSL seats, extra eligibility rules",
        "published_here": "Not linked yet",
        "cite": "Art. VIII §5, §6, §13",
    },
    {
        "name": "Union budget and records of extra spending and allocations",
        "what": "Public documents under the Constitution",
        "published_here": "Not linked yet",
        "cite": "Art. VII §2",
    },
]

TRANSPARENCY_RULES = [
    {"text": "The budget and records of all extra spending and allocations are public documents.", "cite": "Art. VII §2"},
    {"text": "RPI's Treasurer holds the Union's money and gets a copy of every financial transaction.", "cite": "Art. VI"},
    {"text": "No Union money may be spent without an Executive Board requisition (a formal spending approval).", "cite": "Art. XIV"},
    {
        "text": "The exact wording of a constitutional amendment must be published campus-wide at least two weeks before the vote.",
        "cite": "Art. XIII §3",
    },
    {"text": "The Senate must give adequate notice of all elections.", "cite": "Art. VIII §6"},
    {"text": "Senators must report regularly to their councils.", "cite": "Art. VII §1"},
]
TRANSPARENCY_HONEST_LINE = (
    "The Constitution does not require meeting agendas or minutes to be public. "
    "Publishing them here is a Union practice, not a constitutional duty."
)

BODY_DESCRIPTIONS = [
    {
        "name": "Student Senate",
        "text": "The Union's main lawmaking body: 29 voting seats, chaired by the Grand Marshal. Passes its own rules, sets the Activity Fee, and approves many appointments.",
        "cite": "Art. VII §1",
    },
    {
        "name": "Executive Board",
        "text": "The budgeting body: prepares and approves the budget, hands out Union money, and classifies clubs. Chaired by the President of the Union.",
        "cite": "Art. VII §2",
    },
    {
        "name": "Judicial Board",
        "text": "The student court for rights and conduct cases, and the only body that interprets the Constitution. It can rule other bodies' decisions unconstitutional.",
        "cite": "Art. VII §3",
    },
    {
        "name": "Graduate Council",
        "text": "The advocacy body for graduate students: the 7 Graduate Senators plus at least 5 at-large members. Controls graduate class dues.",
        "cite": "Art. VII §4",
    },
    {
        "name": "Undergraduate Council",
        "text": "The advocacy body for undergraduates: the President and Vice President of each Class Council. Oversees the four Class Councils and approves their class-dues spending.",
        "cite": "Art. VII §5",
    },
]

# --------------------------------------------------------------------------
# Decisions
# --------------------------------------------------------------------------

STATUS_LABELS = {
    "on_agenda": "On the agenda",
    "waiting": "Waiting on a vote",
    "passed": "Passed",
    "failed": "Didn't pass",
    "tabled": "Postponed",
    "done": "Done: here's what changed",
    "not_recorded": "Outcome not recorded yet",
    "overturned": "Ruled unconstitutional",
}
# CSS chip class per status
STATUS_CHIP = {
    "on_agenda": "waiting",
    "waiting": "waiting",
    "passed": "passed",
    "failed": "failed",
    "tabled": "tabled",
    "done": "done",
    "not_recorded": "tabled",
    "overturned": "overturned",
}
STAGES = ["On the agenda", "Voted", "Outcome recorded", "Done"]
# Index of the current step in STAGES
STATUS_STAGE = {
    "on_agenda": 0,
    "waiting": 0,
    "not_recorded": 0,
    "passed": 2,
    "failed": 2,
    "tabled": 2,
    "done": 3,
    "overturned": 4,
}

TERM_LABEL = {"senate": "57th Senate", "eboard": "FY27 (2026–27)"}


def _sample_decision(id, ref, title, plain, body, type, requested_by, status, threshold, history, outcome_note=None):
    """history: list of (meeting number or None, date or None, text).

    A meeting number links the row to that meeting record (same body and term).
    None means a follow-up that is not a meeting action; it needs a date.
    """
    rows = []
    for number, when, text in history:
        if number is None:
            rows.append(
                {"date": when, "meeting_ref": "Follow-up, not a meeting", "meeting": None, "text": text}
            )
            continue
        m = find_meeting(body, BODIES[body]["term_slug"], number)
        rows.append(
            {
                "date": m["starts"].astimezone(NY).date(),
                "meeting_ref": meeting_ref(m),
                "meeting": (m["body"], m["term_slug"], m["number"]),
                "text": text,
            }
        )
    last_meeting = next(r["meeting"] for r in reversed(rows) if r["meeting"])
    last_row = next(r for r in reversed(rows) if r["meeting"])
    return {
        "id": id,
        "ref": ref,
        "title": title,
        "plain_summary": plain,
        "body": body,
        "term_slug": BODIES[body]["term_slug"],
        "term_label": TERM_LABEL[body],
        "type": type,
        "requested_by": requested_by,
        "status": status,
        "threshold": threshold,
        "draft": _SB if body == "senate" else _EB,
        "history": rows,
        "outcome_note": outcome_note,
        "agenda_source": None,
        "meeting_key": last_meeting,
        "motion_file": MOCK_BOX + "s/sample-motion-" + id,
        "motion_file_name": f"{last_row['date']:%Y-%m-%d} Senate 57 #{last_meeting[2]} Motion - {title}.pdf",
        "sample": True,
    }


SAMPLE_DECISIONS = [
    _sample_decision(
        "sample-senate-appointment",
        "Senate 57 #14, item 4a",
        "Appointment of two Members-at-Large to the Executive Board",
        "Approves the President of the Union's appointment of two Members-at-Large to the Executive Board.",
        "senate",
        "appointment",
        "Executive Board",
        "passed",
        "eb_appointment",
        [
            (13, None, "Introduced under New Business"),
            (14, None, "Voted on and passed"),
        ],
    ),
    _sample_decision(
        "sample-senate-bylaw",
        "Senate 57 #15, item 7a",
        "Changes to Senate bylaws on committee reporting",
        "Changes the Senate's bylaws on committee reporting.",
        "senate",
        "bylaw",
        "Rules and Administration Committee",
        "waiting",
        "senate_bylaws",
        [(15, None, "First reading under Old Business")],
    ),
    _sample_decision(
        "sample-senate-failed",
        "Senate 57 #13, item 8a",
        "Motion to move regular Senate meetings to Mondays",
        "Moves regular Senate meetings to Monday evenings.",
        "senate",
        "motion",
        "Rules and Administration Committee",
        "failed",
        None,
        [(13, None, "Moved under New Business, voted on, and did not pass")],
    ),
    _sample_decision(
        "sample-senate-tabled",
        "Senate 57 #14, item 6a",
        "Review of the Senate attendance rules",
        "Moves the review of the Senate attendance rules to a later meeting.",
        "senate",
        "motion",
        "Rules and Administration Committee",
        "tabled",
        None,
        [(14, None, "Postponed to a later meeting")],
    ),
    _sample_decision(
        "sample-senate-done",
        "Senate 57 #14, item 8b",
        "Webex link on every Senate meeting notice",
        "Puts the Webex link and the full date on every Senate meeting notice.",
        "senate",
        "resolution",
        "Senate Communications and Engagement Committee",
        "done",
        None,
        [
            (13, None, "Moved under New Business"),
            (14, None, "Voted on and passed"),
            (None, date(2026, 10, 15), "Meeting notices now include the link"),
        ],
        outcome_note="Senate meeting notices sent after 15 Oct 2026 include the Webex link and the full date.",
    ),
]

DECISIONS = SAMPLE_DECISIONS


def find_decision(did):
    for d in DECISIONS:
        if d["id"] == did:
            return d
    return None


def last_action(d):
    return d["history"][-1] if d["history"] else None


# --------------------------------------------------------------------------
# Budget (a quotation from one agenda, not a maintained figure)
# --------------------------------------------------------------------------


def _money(v):
    if v is None:
        return "Not listed"
    if float(v).is_integer():
        return f"${v:,.0f}"
    return f"${v:,.2f}"


_BUDGET_RAW = [
    ("Club Contingencies", 100000, 100000, "Extra money clubs can request during the year", _EB),
    ("Travel Contingencies", 60000, 60000, "Money clubs can request for travel", _EB),
    ("Facilities", 166150, 166150, "Money for Union facilities", None),
    ("Facilities Reserves", None, 126635.47, "Savings held for facilities", None),
]
BUDGET = {
    "as_of": date(2026, 8, 25),
    "source": "Executive Board Agenda 01, 25 Aug 2026",
    "lines": [
        {
            "fund": fund,
            "plain": plain,
            "initial": initial,
            "current": current,
            "initial_label": _money(initial),
            "current_label": _money(current),
            "draft": draft,
        }
        for fund, initial, current, plain, draft in _BUDGET_RAW
    ],
}

# --------------------------------------------------------------------------
# Membership snapshots
# --------------------------------------------------------------------------


def _g(label, seats, filled, vacant, elect_fall=0, note=None):
    return {
        "label": label,
        "seats": seats,
        "filled": filled,
        "vacant": vacant,
        "elect_fall": elect_fall,
        "note": note,
    }


SNAPSHOTS = {
    "senate": {
        "body": "senate",
        "title": "Student Senate membership",
        "seats_constitution": 29,
        "cite": "Art. VII §1",
        "roster_date": date(2026, 7, 30),
        "roster_label": "the 30 Jul 2026 roster",
        "groups": [
            _g("Graduate", 7, 4, 3),
            _g("Class of 2027", 4, 4, 0),
            _g("Class of 2028", 4, 2, 2),
            _g("Class of 2029", 4, 4, 0),
            _g("Class of 2030 (first-years)", 4, 0, 0, 4),
            _g("Independent", 3, 3, 0),
            _g("Fraternity and Sorority Life", 3, 3, 0),
        ],
        "owner_vacancy": VGMIA,
        "presiding": "The Grand Marshal presides and votes only on ties.",
        "presiding_cite": "Art. IV §1",
        "notes": [
            {
                "text": "First-year senators are elected in the fall; the 30 Jul 2026 roster predates that election.",
                "cite": "Art. VIII §3",
            },
            {
                "text": "The agenda lists the Independent and FSL senators under one heading, 'Greek & Independent Senators'. "
                "The Union Constitution, as amended in 2023 and Feb 2026, makes them two separate groups of three seats. "
                "The Constitution is authoritative, so this record shows them separately.",
                "cite": "Art. VII §1; Art. VIII §5",
            },
        ],
        "agenda_header_note": "The roster lists 20 filled voting seats; the difference is unexplained in the source. "
        "The Constitution does not set quorum.",
        "nonvoting": "Non-voting officers (titles set by Senate bylaws): Senate Treasurer and Senate–E-Board Liaison Cee Ray '27, "
        "Parliamentarian Sasha Notkin '28, Secretary Selena Tang '29, and the committee chairs.",
        "nonvoting_draft": _SB,
    },
    "eboard": {
        "body": "eboard",
        "title": "Executive Board membership",
        "seats_constitution": "15 to 20",
        "cite": "Art. VII §2",
        "roster_date": date(2026, 8, 25),
        "roster_label": "the 25 Aug 2026 roster",
        "groups": [
            _g("Class representatives (Graduate, 2027–2030)", 5, 3, 2, note="Vacant: Graduate, 2030"),
            _g("Club and organisation representatives (5 required + 2 optional)", 7, 4, 3),
            _g("Members-at-large (2 required + 3 optional)", 5, 4, 1),
            _g("Senate–E-Board Liaison (chosen by the Senate)", 1, 1, 0, note="Cee Ray '27"),
            _g("Graduate Council representative (chosen by the Graduate Council)", 1, 1, 0, note="Joydip Paul '29G"),
            _g("Undergraduate Council representative (chosen by the Undergraduate Council)", 1, 0, 1),
        ],
        "owner_vacancy": "President of the Union",
        "presiding": "The President presides and votes only on ties.",
        "presiding_cite": "Art. IV §2",
        "notes": [
            {
                "text": "The agenda prints the three Council and Senate representatives as 'Peer Body Representatives' "
                "and lists three Vice Presidents separately. Under the Constitution the three representatives are voting "
                "members, and there are no separate VP seats. The agenda header says 12 voting members.",
                "cite": None,
            }
        ],
        "officers": [
            ("VP Board Operations", "Gavin Finn '28"),
            ("VP Club Relations", "Jesse Kim '26 '27G"),
            ("VP Rules and Special Projects", "Blaine Rosenberg '28"),
        ],
        "officers_draft": _EB,
        "nonvoting": "Other non-voting roles from the agenda: Club Financial Advisors, Secretary, Parliamentarian (Vacant), "
        "committee chairs. Advisers under the Constitution: the Director of the Union and assistants.",
        "nonvoting_cite": "Art. VII §2",
    },
}


def snapshot_totals(body):
    groups = SNAPSHOTS[body]["groups"]
    return {
        "seats": sum(g["seats"] for g in groups),
        "filled": sum(g["filled"] for g in groups),
        "vacant": sum(g["vacant"] for g in groups),
        "elect_fall": sum(g["elect_fall"] for g in groups),
    }


def snapshot_with_totals(body):
    snap = dict(SNAPSHOTS[body])
    snap["totals"] = snapshot_totals(body)
    return snap


def distinct_people():
    """Distinct non-vacant names on the two real agendas (stand-in for the People database)."""
    names = set()
    for m in MEETINGS:
        for section in m["sections"]:
            for item in section["items"]:
                who = item.get("who")
                if who and who != "Vacant":
                    names.add(who.split(" '")[0].split(" 'G")[0].replace("Dr. ", ""))
    return len(names)


# --------------------------------------------------------------------------
# Health checks
# --------------------------------------------------------------------------

SEVERITY_LABELS = {
    "overdue": "Overdue",
    "soon": "Due soon",
    "check": "Check",
    "waiting": "Waiting",
    "ok": "OK",
}
SEVERITY_ORDER = {"overdue": 0, "soon": 1, "check": 2, "waiting": 3, "ok": 4}

LINK_CHECKS = [
    {
        "item": "Senate 57 #11 · Agenda",
        "kind": "agenda",
        "url": MOCK_BOX + "s/sample-senate-57-11-agenda",
        "result": "ok",
        "checked": date(2026, 10, 19),
    },
    {
        "item": "Senate 57 #11 · Minutes",
        "kind": "minutes",
        "url": MOCK_BOX + "s/sample-senate-57-11-minutes",
        "result": "login",
        "checked": date(2026, 10, 19),
    },
]

NOT_CHECKED = [
    "File names, and whether every file in Box has a meeting record: these need the Box API, which the Union doesn't have.",
    "Attachments: they show in the folder embed and aren't linked one by one.",
    "Attendance: private in the Senate's Notion, never synced.",
    "What's inside the Graduate Council, Undergraduate Council and Judicial Board folders: without the Box API "
    "the site can't see their files, so it relies on each records officer confirming.",
    "Whether a PDF is tagged for accessibility, or whether a file's contents match its record.",
]


def link_summary():
    n = len(LINK_CHECKS)
    login = sum(1 for c in LINK_CHECKS if c["result"] == "login")
    nf = sum(1 for c in LINK_CHECKS if c["result"] == "404")
    checked = fmt_date(LINK_CHECKS[0]["checked"]) if LINK_CHECKS else "never"
    return (
        f"{n} pasted links checked on {checked} · {login} opens a login page · {nf} return 404."
    )


def link_result(m, kind):
    """For the health table: 'Linked', 'Missing', or 'Login page (failed check)'."""
    url = m.get(f"{kind}_url")
    if not url:
        return "Missing"
    for c in LINK_CHECKS:
        if c["url"] == url and c["result"] == "login":
            return "Login page (failed check)"
        if c["url"] == url and c["result"] == "404":
            return "Dead link (404)"
    return "Linked"


def _check(
    area, check, item, severity, owner_role, fix_label, fix_url, since=None, days=None, age=None, body=None, **extra
):
    row = {
        "area": area,
        "check": check,
        "item": item,
        "since": since,
        "days": days if days is not None else 0,
        "age": age,
        "owner_role": owner_role,
        "severity": severity,
        "severity_label": SEVERITY_LABELS[severity],
        "fix_label": fix_label,
        "fix_url": fix_url,
        "body": body,
        "sample": False,
        "cite": None,
        "draft": None,
    }
    row.update(extra)
    if row["age"] is None:
        row["age"] = f"{row['days']} days" if row["since"] else "-"
    return row


def _until_text(until):
    if until == 0:
        return "today"
    if until == 1:
        return "tomorrow"
    return f"in {until} days"


def meeting_checks(today):
    rows = []
    for m in sorted(MEETINGS, key=lambda m: m["starts"]):
        start_day = m["starts"].astimezone(NY).date()
        ref = meeting_ref(m)
        info = BODIES[m["body"]]
        secretary = f"{info['short']} Secretary"
        fix_label, fix_url = info["fix_label"], info["fix_url"]
        past = start_day < today
        common = {"body": m["body"], "sample": m["sample"], "ref": ref, "number": m["number"]}
        if info["adapter"] == "notion" and not m.get("public", True):
            rows.append(
                _check(
                    "Meetings",
                    "Not shown on the site: Public is unticked in Notion",
                    f"{ref} · {fmt_date(start_day)}",
                    "check",
                    secretary,
                    fix_label,
                    fix_url,
                    kind="public",
                    **common,
                )
            )
        if past:
            since_days = (today - start_day).days
            if not m.get("minutes_url"):
                if since_days > 14:
                    rows.append(
                        _check(
                            "Meetings",
                            "Minutes link missing",
                            f"{ref} · {fmt_date(start_day)} · {since_days} days (Standard: 14 days)",
                            "overdue",
                            secretary,
                            fix_label,
                            fix_url,
                            since=start_day,
                            days=since_days,
                            kind="minutes",
                            **common,
                        )
                    )
                else:
                    due = start_day + timedelta(days=14)
                    rows.append(
                        _check(
                            "Meetings",
                            f"Minutes due by {fmt_date(due)}",
                            f"{ref} · {fmt_date(start_day)}",
                            "soon",
                            secretary,
                            fix_label,
                            fix_url,
                            since=start_day,
                            days=since_days,
                            kind="minutes",
                            due=due,
                            **common,
                        )
                    )
            if not m.get("agenda_url"):
                rows.append(
                    _check(
                        "Meetings",
                        "No agenda link on the meeting record",
                        f"{ref} · {fmt_date(start_day)}",
                        "check",
                        secretary,
                        fix_label,
                        fix_url,
                        since=start_day,
                        days=since_days,
                        kind="agenda_past",
                        **common,
                    )
                )
        elif not m.get("agenda_url"):
            until = (start_day - today).days
            flag = start_day - timedelta(days=2)
            if until <= 1:
                severity, text = "overdue", "Agenda due 24 hours before the meeting: link missing"
            elif until == 2:
                severity, text = "soon", "Agenda link missing: meeting in 2 days"
            else:
                severity, text = "waiting", f"Agenda link not added yet · flagged from {fmt_day_month(flag)}"
            rows.append(
                _check(
                    "Meetings",
                    text,
                    f"{ref} · {fmt_date(start_day)}",
                    severity,
                    secretary,
                    fix_label,
                    fix_url,
                    age=_until_text(until) if severity != "waiting" else f"meeting in {until} days",
                    kind="agenda_upcoming",
                    flag=flag,
                    until=until,
                    **common,
                )
            )
    return rows


def standard_checks(today):
    """Checks against the Public Records Standard that don't come from a meeting record."""
    rows = []
    for key, info in FOLDER_BODIES.items():
        rows.append(
            _check(
                "Standard",
                "Folder only: can't check deadlines automatically · records last confirmed complete: never "
                "· no records officer named",
                f"{info['name']}",
                "check",
                f"{info['name']} (records officer not named)",
                "Fix on this site",
                "/admin/",
                age="-",
                body=key,
                sample=True,
            )
        )
    for key, folder in BOX_FOLDERS.items():
        if folder["shared_url"] is not None:
            continue
        info = BODIES.get(key) or FOLDER_BODIES[key]
        rows.append(
            _check(
                "Links",
                "Box folder shared link not added",
                f"{folder['label']} · {folder['path']}",
                "check",
                info["records_officer"] or f"{info['name']} records officer",
                "Fix in Box",
                MOCK_BOX,
                age="-",
                body=key,
            )
        )
    return rows


def budget_checks(today):
    """The quoted budget is a typed copy of one agenda; the site can tell when a newer E-Board meeting exists."""
    as_of = BUDGET["as_of"]
    newer = [
        m
        for m in MEETINGS
        if m["body"] == "eboard" and m.get("public", True) and m["starts"].astimezone(NY).date() <= today
    ]
    if not newer:
        return []
    latest = max(newer, key=lambda m: m["starts"])
    latest_day = latest["starts"].astimezone(NY).date()
    if latest_day <= as_of:
        return []
    return [
        _check(
            "Site",
            "Quoted budget is older than the newest E-Board meeting record",
            f"Quote is from {fmt_date(as_of)}; newest record is {meeting_ref(latest)} · {fmt_date(latest_day)}",
            "check",
            WTG_CHAIR,
            "Fix in Wagtail",
            "/admin/",
            since=as_of,
            days=(today - as_of).days,
            sample=latest["sample"],
        )
    ]


def latest_eboard_meeting(today):
    past = [
        m
        for m in MEETINGS
        if m["body"] == "eboard" and m.get("public", True) and m["starts"].astimezone(NY).date() <= today
    ]
    return max(past, key=lambda m: m["starts"]) if past else None


def membership_checks(today):
    rows = []
    labels = {"senate": "Senate", "eboard": "E-Board"}
    for body, snap in SNAPSHOTS.items():
        since = snap["roster_date"]
        days = (today - since).days
        for g in snap["groups"]:
            if g["vacant"] <= 0:
                continue
            seat_word = "seat" if g["vacant"] == 1 else "seats"
            group_label = g["label"].split(" (")[0]
            rows.append(
                _check(
                    "Roster",
                    "Seats vacant more than 60 days" if days > 60 else "Seats vacant",
                    f"{labels[body]} · {group_label}: {g['vacant']} {seat_word}",
                    "check",
                    snap["owner_vacancy"],
                    "Record on this site when filled",
                    "/admin/",
                    since=since,
                    days=days,
                    age=f"{days} days",
                    since_note=f"vacant on every roster since at least {fmt_date(since)}",
                    cite=snap["cite"],
                )
            )
    return rows


def seeded_checks(today):
    rows = [
        _check(
            "Sync",
            "Schema change: Senate Motions property 'Status' (id `qT%3Fb`) not found. Renamed columns are fine, "
            "but this one was deleted or its type changed. Motion statuses are hidden until it's fixed.",
            "Senate's Notion · Motions",
            "check",
            WTG_CHAIR,
            "Fix in Notion",
            MOCK_NOTION,
            since=date(2026, 10, 19),
            days=(today - date(2026, 10, 19)).days,
            sample=True,
        )
    ]
    for c in LINK_CHECKS:
        if c["result"] == "login":
            rows.append(
                _check(
                    "Links",
                    "Opens an RPI login page. Set the shared link to 'People with the link'.",
                    c["item"],
                    "overdue",
                    "Senate Secretary",
                    "Fix in Box",
                    MOCK_BOX,
                    since=c["checked"],
                    days=(today - c["checked"]).days,
                    body="senate",
                    sample=True,
                )
            )
        elif c["result"] == "404":
            rows.append(
                _check(
                    "Links",
                    "Returns 404. The file was moved or deleted in Box.",
                    c["item"],
                    "overdue",
                    "Senate Secretary",
                    "Fix in Box",
                    MOCK_BOX,
                    since=c["checked"],
                    days=(today - c["checked"]).days,
                    sample=True,
                )
            )
    rows += [
        _check(
            "Roster",
            "Class of 2030 Senate seats: fall election results not entered",
            "Senate · Class of 2030 (first-years): 4 seats",
            "check",
            "Elections Commission",
            "Fix on this site",
            "/admin/",
            since=date(2026, 9, 1),
            days=(today - date(2026, 9, 1)).days,
            draft="Senate election rules",
            since_note="actual election date set by the Senate election rules",
        ),
        _check(
            "Roster",
            "E-Board first-year member: due within three weeks of the fall elections",
            "E-Board · Class representative, 2030",
            "waiting",
            "President of the Union",
            "Fix on this site",
            "/admin/",
            age="Waiting on fall election",
            cite="Art. VIII §12",
        ),
        _check(
            "Roster",
            "Seats: the three E-Board Council and Senate seats are marked non-voting, but the Constitution counts them as voting",
            "E-Board · seats on this site (tick Voting on those seats)",
            "check",
            "VP Rules and Special Projects",
            "Fix on this site",
            "/admin/",
            age="-",
            cite="Art. VII §2",
        ),
        _check(
            "Roster",
            "Term rollover: not due. Senate 57 and EBoard FY27 are the current terms.",
            "Roster on this site",
            "ok",
            WTG_CHAIR,
            "Fix on this site",
            "/admin/",
        ),
        _check(
            "Sync",
            f"Roster copy in the Senate's Notion: up to date (pushed {minutes_ago_text(SYNC['notion_minutes_ago'])})",
            "Senate's Notion · Senators (from website)",
            "ok",
            WTG_CHAIR,
            "Fix on this site",
            "/admin/",
        ),
        _check(
            "Site",
            "Union Constitution and bylaws: no Box link on the governing-documents block",
            "Rules page · Records the Constitution names",
            "check",
            WTG_CHAIR,
            "Fix in Wagtail",
            "/admin/",
            age="-",
        ),
        _check("Site", "Expired site notices: none", "Site notices", "ok", WTG_CHAIR, "Fix in Wagtail", "/admin/"),
        _check(
            "Site", "Pages past their review date: none", "Wagtail pages", "ok", WTG_CHAIR, "Fix in Wagtail", "/admin/"
        ),
        _check(
            "Links",
            "Box links returning 404: none",
            "Pasted links",
            "ok",
            "Each body's Secretary",
            "Fix in Box",
            MOCK_BOX,
            sample=True,
        ),
    ]
    return rows


def sort_checks(rows):
    return sorted(rows, key=lambda r: (SEVERITY_ORDER[r["severity"]], -r["days"], r["area"], r["item"]))


def all_checks(today):
    return sort_checks(
        meeting_checks(today)
        + standard_checks(today)
        + budget_checks(today)
        + membership_checks(today)
        + seeded_checks(today)
    )


def problems(today):
    return [r for r in all_checks(today) if r["severity"] != "ok"]


def all_clear(today):
    return [r for r in all_checks(today) if r["severity"] == "ok"]


def _plural(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def standard_by_body(today):
    """One row per body: how its records are held and how it stands against the Public Records Standard."""
    checks = all_checks(today)
    out = []
    for key, info in list(BODIES.items()) + list(FOLDER_BODIES.items()):
        mine = [r for r in checks if r.get("body") == key]
        worst = min((r["severity"] for r in mine), key=SEVERITY_ORDER.get) if mine else "ok"
        folder_link = "Not added" if BOX_FOLDERS[info["folder"]]["shared_url"] is None else "Added"
        if info["adapter"] == "folder":
            agendas = "Can't check: folder only"
            minutes = "Can't check: folder only; records last confirmed: never"
        else:
            upcoming = [m for m in meetings_for_body(key) if not is_past(m, today)]
            if not upcoming:
                agendas = "No upcoming meeting listed"
            else:
                nxt = upcoming[0]
                row = next((r for r in mine if r.get("kind") == "agenda_upcoming" and r["number"] == nxt["number"]), None)
                if row is None:
                    agendas = f"Next: {meeting_ref(nxt)}, agenda linked"
                elif row["severity"] == "waiting":
                    agendas = f"Next: {row['ref']}, link not added · flagged from {fmt_day_month(row['flag'])}"
                elif row["severity"] == "soon":
                    agendas = f"Next: {row['ref']}, link missing: meeting in {row['until']} days"
                else:
                    agendas = f"Next: {row['ref']}, agenda due 24 hours before the meeting: link missing"
            late = [r for r in mine if r.get("kind") == "minutes" and r["severity"] == "overdue"]
            soon = [r for r in mine if r.get("kind") == "minutes" and r["severity"] == "soon"]
            if late:
                oldest = max(late, key=lambda r: r["days"])
                minutes = (
                    f"{_plural(len(late), 'meeting')} past 14 days with no minutes link "
                    f"(oldest: #{oldest['number']}, {oldest['days']} days)"
                )
            else:
                minutes = "No meetings past 14 days with no minutes link"
            for r in soon:
                minutes += f" · #{r['number']} due by {fmt_date(r['due'])}"
        out.append(
            {
                "key": key,
                "body": info["name"],
                "adapter_label": info["adapter_label"],
                "example": info["example"],
                "records_officer": info["records_officer"] or "Not named",
                "agendas": agendas,
                "minutes": minutes,
                "folder_link": folder_link,
                "severity": worst,
                "severity_label": SEVERITY_LABELS[worst],
            }
        )
    return out


# --------------------------------------------------------------------------
# Desk content
# --------------------------------------------------------------------------

RECORDS_STANDARD = [
    {
        "rule": "Agenda in the body's public Box folder 24 hours before the meeting",
        "check": "From the agenda link on the meeting record; flagged from 2 days out",
    },
    {
        "rule": "Draft or approved minutes in the folder within 14 days",
        "check": "From the minutes link",
    },
    {
        "rule": "Approved minutes within 3 days of approval, uploaded as a new version of the draft",
        "check": "From the Minutes approved date",
    },
    {
        "rule": "Motion text in the folder before the vote",
        "check": "Senate only: the file link on the Motions row",
    },
    {
        "rule": "PDFs exported from Word with accessibility tags; never printed to PDF or scanned",
        "check": "Not checked automatically",
    },
    {
        "rule": "Files named `YYYY-MM-DD <Body> <Term> #<nn> <Agenda|Minutes|Motion - Title>.pdf`; "
        "corrections use Upload New Version",
        "check": "Pasted links are checked against the pattern",
    },
    {
        "rule": "Each body names a records officer",
        "check": "From the body settings on this site",
    },
    {
        "rule": "Folder-only bodies confirm once a month that their folder is complete",
        "check": "From the 'records last confirmed' date",
    },
]
RECORDS_STANDARD_JBOARD_NOTE = {
    "text": "The Judicial Board publishes its rulings on what the Constitution means. "
    "Its conduct and rights cases are confidential.",
    "draft": "Judicial Board bylaws",
}

RECORDS_BY_BODY = [
    {
        "body": "Senate",
        "example": False,
        "meetings": "Senate's Notion",
        "files": "Word in Box as PDF, link in the Notion row",
        "decisions": "Notion Motions status plus the file",
        "roster": f"This site ({VGMIA}), copied to the Senate's Notion",
        "issues": "Senate's Notion Issues",
    },
    {
        "body": "Executive Board",
        "example": True,
        "meetings": "Entered on this site",
        "files": "Word in Box as PDF, link on this site",
        "decisions": "In its minutes",
        "roster": "This site (VP Rules and Special Projects)",
        "issues": "Not tracked publicly",
    },
    {
        "body": "Graduate Council",
        "example": True,
        "meetings": "None, Box folder only",
        "files": "Their folder",
        "decisions": "In their minutes or rulings",
        "roster": "This site once named",
        "issues": "Not tracked publicly",
    },
    {
        "body": "Undergraduate Council",
        "example": True,
        "meetings": "None, Box folder only",
        "files": "Their folder",
        "decisions": "In their minutes or rulings",
        "roster": "This site once named",
        "issues": "Not tracked publicly",
    },
    {
        "body": "Judicial Board",
        "example": True,
        "meetings": "None, Box folder only",
        "files": "Their folder",
        "decisions": "In their minutes or rulings",
        "roster": "This site once named",
        "issues": "Not tracked publicly",
    },
]

SHARED_WHERE = [
    {
        "what": "Budget figures",
        "where": "Business Operations and Union finance; printed on E-Board agendas",
        "who": "E-Board Business Operations",
        "how": "Link to the newest E-Board agenda. Never retyped.",
        "wagtail": False,
    },
    {
        "what": "Rules page, body descriptions, glosses, vote and petition tables",
        "where": "This site",
        "who": WTG_CHAIR,
        "how": "Native (Wagtail)",
        "wagtail": True,
    },
    {
        "what": "Site notices",
        "where": "This site, with an expiry date",
        "who": WTG_CHAIR,
        "how": "Native (Wagtail)",
        "wagtail": True,
    },
    {
        "what": "Voting members and quorum (the agenda header figures), proposed",
        "where": 'Senate\'s Notion "Meetings" (two new properties) or this site\'s meeting entry for the E-Board',
        "who": "Each body's Secretary",
        "how": "Not in the current schema, so the site doesn't show them as a record yet.",
        "wagtail": False,
    },
    {
        "what": "Senate attendance, contacts, internal notes",
        "where": "The Senate's Notion",
        "who": "Senate officers",
        "how": "Never shown",
        "wagtail": False,
    },
]

NEVER_LIST = [
    "a 'post a meeting' form for the Senate: its meetings come from its Notion",
    "retyping or parsing a Word agenda, motion or minutes",
    "editing in this site anything the Senate's Notion owns",
    "requiring any body other than the Senate to use Notion",
    "retyped budget numbers",
    "calendar entries made by hand for meetings",
    "a second file host: no PDFs uploaded to this site",
]

OFFICER_RULES = [
    "Fix files with Upload New Version in Box.",
    "Set shared links to 'People with the link'.",
    "Name files `YYYY-MM-DD <Body> <Term> #<nn> <Agenda|Minutes|Attachment - Title>.pdf`.",
    "Export Word documents to PDF with accessibility tags (File, Save As, PDF); never Print to PDF.",
    "If something here looks wrong, use the Edit link and fix it at the source.",
]

ROLLOVER_STEPS = [
    "Set end dates on last term's assignments.",
    "Set the body's new term as current on this site. Every seat on the site then shows Vacant automatically, "
    "and last year's names never carry over.",
    "Make sure the four first-year Senate seats show 'To be elected this fall'.",
    "Enter new assignments as results come in.",
    "Check the seat groups still match the Constitution's current Art. VII (29 Senate seats, 15–20 E-Board seats), "
    "and re-check the vote thresholds on the Rules page after any amendment.",
    "Audit who can edit the site admin and the Senate's Notion workspace (at least two owners, on a shared role "
    "account). The Senate's Notion copy of the roster updates itself.",
]

MOTIONS_MOCK = [
    {
        "motion": "Committee reporting bylaws",
        "meeting": "Senate 57 #15",
        "status": "Waiting on a vote",
        "file": "2026-10-14 Senate 57 #15 Motion - Committee reporting bylaws.pdf",
        "public": "☑",
    },
    {
        "motion": "Webex link on meeting notices",
        "meeting": "Senate 57 #14",
        "status": "Passed",
        "file": "2026-09-23 Senate 57 #14 Motion - Webex link on notices.pdf",
        "public": "☑",
    },
]
