"""Seed data for the "Your Representatives" prototype.

Nothing here is connected to Notion or Box. In production, ``PEOPLE`` and
``SEATS`` are entered on this site by each body's roster officer, ``ISSUES``
would be a read-only view of the Senate's Notion Issues database (Public rows
only), and the Senate's ``MEETINGS`` would come from its Notion; the
Executive Board's are entered on this site. Files stay in Box and are only
linked, never fetched (there is no Box API access).

Entries that carry ``cite`` are confirmed by the Rensselaer Union
Constitution (last amended 6 Feb 2026). Entries that carry ``draft`` are
things the Constitution leaves to bylaws, rules or staff.
"""

from datetime import date

from django.utils.text import slugify

# --------------------------------------------------------------------------
# Single source of truth: where each fact lives
# --------------------------------------------------------------------------

SYNC = {
    "notion_minutes_ago": 12,
    "wagtail_reviewed": date(2026, 10, 21),
    "roster_updated": date(2026, 8, 25),
    "eboard_entry_updated": date(2026, 8, 24),
}
# The demo is pinned to this day so staleness and "this week" never drift.
DEMO_TODAY = date(2026, 10, 21)
MOCK_NOTION = "https://www.notion.so/"  # every "Edit in Notion" link points here
MOCK_BOX = "https://rpi.box.com/"
MOCK_BOX_AGENDA = {
    "senate-12": "https://rpi.box.com/s/mock-senate-12-agenda",
    "eb-01": "https://rpi.box.com/s/mock-eb-01-agenda",
}

_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fmt_date(d):
    """21 Oct 2026 (no platform-specific strftime flags)."""
    return f"{d.day} {_MONTHS[d.month - 1]} {d.year}"


def _synced():
    return f"synced {SYNC['notion_minutes_ago']} min ago"


def build_sources():
    return {
        "roster": {
            "key": "roster",
            "line": (
                "Roster: entered on this site by each body's roster officer · "
                f"last change {fmt_date(SYNC['roster_updated'])}"
            ),
            "edit_label": "Edit on this site",
            "edit_url": "/admin/",
        },
        "issues": {
            "key": "issues",
            "line": f"Issues: Senate's Notion, items marked Public · {_synced()}",
            "edit_label": "Edit in Notion",
            "edit_url": MOCK_NOTION,
        },
        "meeting_senate": {
            "key": "meeting_senate",
            "line": f"Meeting record: Senate's Notion · {_synced()}",
            "edit_label": "Edit in Notion",
            "edit_url": MOCK_NOTION,
        },
        "meeting_eboard": {
            "key": "meeting_eboard",
            "line": (
                "Meeting record: entered on this site by the E-Board Secretary · "
                f"updated {fmt_date(SYNC['eboard_entry_updated'])}"
            ),
            "edit_label": "Edit on this site",
            "edit_url": "/admin/",
        },
        "folder_only": {
            "key": "folder_only",
            "line": "Records: files in this body's Box folder. It doesn't list meetings on this site.",
            "edit_label": "Open in Box",
            "edit_url": MOCK_BOX,
        },
        "document": {
            "key": "document",
            "line": "Agenda: Word file in Box, published as PDF",
            "edit_label": "Edit in Box",
            "edit_url": MOCK_BOX,
        },
        "quoted_budget": {
            "key": "quoted_budget",
            "line": (
                "Quoted from Executive Board Agenda 01, 25 Aug 2026 (a PDF in Box). "
                "This site does not update these figures."
            ),
            "edit_label": "Open in Box",
            "edit_url": MOCK_BOX,
        },
        "wagtail": {
            "key": "wagtail",
            "line": f"Written on this site · reviewed {fmt_date(SYNC['wagtail_reviewed'])}",
            "edit_label": "Edit in Wagtail",
            "edit_url": "/admin/",
        },
    }


SOURCES = build_sources()

AGENDA = {
    "senate": "Source: Student Senate agenda, 30 Jul 2026",
    "eb": "Source: Executive Board Agenda 01, 25 Aug 2026",
}

CONSTITUTION_AMENDED = "6 Feb 2026"

DRAFT_WHYS = (
    "Senate bylaws or rules",
    "Senate election rules",
    "E-Board bylaws",
    "Judicial Board bylaws",
    "Union staff process",
    "Site owner",
)

# --------------------------------------------------------------------------
# Constituencies
# --------------------------------------------------------------------------

CONSTITUENCIES = {
    "2027": {
        "label": "Class of 2027",
        "chooser": "'27",
        "kind": "class",
        "plain": "Undergraduates expected to graduate in 2027.",
        "senate_seats": 4,
        "seats_cite": "Art. VII §1",
        "election_note": "",
    },
    "2028": {
        "label": "Class of 2028",
        "chooser": "'28",
        "kind": "class",
        "plain": "Undergraduates expected to graduate in 2028.",
        "senate_seats": 4,
        "seats_cite": "Art. VII §1",
        "election_note": "",
    },
    "2029": {
        "label": "Class of 2029",
        "chooser": "'29",
        "kind": "class",
        "plain": "Undergraduates expected to graduate in 2029.",
        "senate_seats": 4,
        "seats_cite": "Art. VII §1",
        "election_note": "",
    },
    "2030": {
        "label": "Class of 2030",
        "chooser": "'30",
        "kind": "class",
        "plain": "First-year undergraduates, expected to graduate in 2030.",
        "senate_seats": 4,
        "seats_cite": "Art. VII §1",
        "election_note": (
            "Your class has 4 Senate seats. First-year senators and the first-year "
            "Class Council are elected in the fall semester. The latest roster we "
            "have (30 Jul 2026) is from before that election."
        ),
        "election_cite": "Art. VII §1; Art. VIII §3",
    },
    "graduate": {
        "label": "Graduate students",
        "chooser": "Grad",
        "kind": "graduate",
        "plain": "Students working toward a graduate degree.",
        "senate_seats": 7,
        "seats_cite": "Art. VII §1",
        "election_note": "",
    },
    "independent": {
        "label": "Not in a fraternity or sorority (Independent)",
        "chooser": "Independent",
        "kind": "independent",
        "plain": "Undergraduates who are not members of a fraternity or sorority.",
        "senate_seats": 3,
        "seats_cite": "Art. VII §1",
        "election_note": "",
    },
    "fsl": {
        "label": "In a fraternity or sorority (Fraternity and Sorority Life)",
        "chooser": "Fraternity & Sorority Life",
        "kind": "fsl",
        "plain": "Undergraduates who are members of a fraternity or sorority.",
        "senate_seats": 3,
        "seats_cite": "Art. VII §1",
        "election_note": "",
    },
    "clubs": {
        "label": "Club and organisation leaders",
        "chooser": "Club leader",
        "kind": "clubs",
        "plain": (
            "People who run or belong to a club or organisation. Clubs aren't a Senate "
            "constituency. Clubs have 5 to 7 seats on the Executive Board, but those "
            "reps are appointed by the President of the Union with 2/3 Senate "
            "approval, not elected by clubs."
        ),
        "senate_seats": 0,
        "seats_cite": "",
        "plain_cite": "Art. VII §2",
        "election_note": "",
    },
}

CHOOSER_ROWS = [
    ["2027", "2028", "2029", "2030", "graduate"],
    ["independent", "fsl", "clubs"],
]

EVERYONE_LABEL = "All Union members"

RECONCILIATION_NOTE = (
    "The Senate agenda lists these six under one heading, 'Greek & Independent "
    "Senators'. Under the Union Constitution they are two separate groups of three "
    "seats: Independent Senators must not be in a fraternity or sorority, and FSL "
    "Senators must be. The Constitution is authoritative, so this site shows them "
    "separately. All six seats are filled."
)
RECONCILIATION_CITE = "Art. VII §1; Art. VIII §5"

# --------------------------------------------------------------------------
# Fill rules
# --------------------------------------------------------------------------

_ANSWERS_ALL = (
    "All students: a petition from 50% removes them; or 2/3 in a removal election "
    "where at least 20% vote, called by 2/3 of the Senate or by a 20% petition plus "
    "a Senate majority."
)
_ANSWERS_CLASS = (
    "{who}: a petition from 20%, or a Senate majority, starts a removal election; "
    "2/3 of voters removes them if at least 20% vote. The Senate can also remove any "
    "senator for good cause by 2/3 of all seats (20 of 29, derived)."
)

# Fill rules where students vote; the others are appointed or chosen by a body.
ELECTED_RULE_KEYS = ("gm", "pu", "class_senator", "elected_senator")

FILL_RULES = {
    "gm": {
        "key": "gm",
        "filled_by": (
            "Elected by all students in the spring; needs at least 40% of the vote. "
            "If vacant, the Senate appoints a replacement by 2/3 within two weeks."
        ),
        "answers_to": _ANSWERS_ALL,
        "cite": "Art. VIII §1, §10; Art. X §1; Art. XI §1",
    },
    "pu": {
        "key": "pu",
        "filled_by": (
            "Elected by all students in the spring; needs at least 40% of the vote. "
            "If vacant, the Executive Board appoints a replacement within two weeks "
            "and 2/3 of the Senate confirms."
        ),
        "answers_to": _ANSWERS_ALL,
        "cite": "Art. VIII §1, §10; Art. X §1; Art. XI §2",
    },
    "class_senator": {
        "key": "class_senator",
        "filled_by": (
            "Elected by the class (first-years in the fall, other classes in the "
            "spring). If vacant, the Class Council appoints someone; 20% of the class "
            "can force a special election by petition within two weeks of the "
            "announcement."
        ),
        "answers_to": _ANSWERS_CLASS.format(who="The class"),
        "cite": "Art. VIII §1, §3; Art. X §2; Art. XI §5, §6",
    },
    "elected_senator": {
        "key": "elected_senator",
        "filled_by": (
            "Elected in the spring. A vacant seat can be filled by appointment; 20% of "
            "the constituency can force a special election by petition within two "
            "weeks of the announcement."
        ),
        "answers_to": _ANSWERS_CLASS.format(who="Their constituents"),
        "cite": "Art. VIII §1, §9; Art. X §2; Art. XI §5",
        "draft": "Senate election rules",
    },
    "eb_appointed": {
        "key": "eb_appointed",
        "filled_by": (
            "Appointed by the President of the Union and approved by 2/3 of the "
            "Senate, not elected. Required seats within three weeks after spring "
            "elections; the first-year seat within three weeks after fall elections; "
            "optional seats by the end of the fourth week of fall."
        ),
        "answers_to": (
            "The Senate: removable by 2/3 of the Senate, or at the President's "
            "request with a Senate majority."
        ),
        "cite": "Art. VII §2; Art. VIII §12; Art. X §3",
        "draft": "E-Board bylaws",
    },
    "eb_peer": {
        "key": "eb_peer",
        "filled_by": (
            "Chosen by the body it represents (Senate, Graduate Council or "
            "Undergraduate Council) within three weeks after that body's elections."
        ),
        "answers_to": (
            "The body that chose them: removable by 2/3 of it, or at the President's "
            "request with its majority."
        ),
        "cite": "Art. VII §2; Art. VIII §12; Art. X §3",
    },
    "officer_title": {
        "key": "officer_title",
        "filled_by": "Set by the body's own bylaws.",
        "answers_to": "Set by the body's own bylaws.",
        "cite": "",
        "draft": "Senate bylaws or rules",
    },
}

_KIND_RULE = {
    "gm": "gm",
    "pu": "pu",
    "class_senator": "class_senator",
    "elected_senator": "elected_senator",
    "eb_class": "eb_appointed",
    "eb_club": "eb_appointed",
    "eb_atlarge": "eb_appointed",
    "eb_peer": "eb_peer",
}

# --------------------------------------------------------------------------
# Bodies and terms
# --------------------------------------------------------------------------

B_SENATE = "Student Senate"
B_SENATE_OFFICERS = "Senate officers"
B_SENATE_COMMITTEES = "Senate committees"
B_SENATE_PEERS = "Senate peer reports"
B_EB = "Executive Board"
B_EB_OFFICERS = "Executive Board officers"
B_EB_OTHER = "Executive Board chairs and staff"

SENATE_BODIES = (B_SENATE, B_SENATE_OFFICERS, B_SENATE_COMMITTEES, B_SENATE_PEERS)
EB_BODIES = (B_EB, B_EB_OFFICERS, B_EB_OTHER)

TERMS = {
    B_SENATE: "57th Student Senate",
    B_SENATE_OFFICERS: "57th Student Senate",
    B_SENATE_COMMITTEES: "57th Student Senate",
    B_SENATE_PEERS: "57th Student Senate",
    B_EB: "2026–27 Executive Board",
    B_EB_OFFICERS: "2026–27 Executive Board",
    B_EB_OTHER: "2026–27 Executive Board",
}

EB_ROSTER_WARNING = (
    "Roster may be out of date: the Executive Board membership block on the agenda is "
    "headed 2025-2026."
)

# --------------------------------------------------------------------------
# Seats and people
# --------------------------------------------------------------------------

SEATS = []
PEOPLE = {}


def person_slug(name):
    return slugify(name)


def initials(name):
    parts = [p for p in name.replace("-", " ").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][0].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _person(name, class_label):
    slug = person_slug(name)
    if slug not in PEOPLE:
        PEOPLE[slug] = {
            "name": name,
            "slug": slug,
            "initials": initials(name),
            "class_label": class_label,
            "roles": [],
            # Nobody has opted in, and we never invent profile data.
            "public_profile": False,
            "profile_reviewed": None,
            "photo": None,
            "bio": None,
            "pronouns": None,
            "major": None,
            "office_hours": None,
        }
    return slug


def _group(body, seat, constituency, kind, people=(), vacant=0, fall=0, voting=True, draft=None):
    """Add seats. ``people`` is a sequence of (name, class_label)."""
    rule = _KIND_RULE.get(kind, "officer_title")
    entries = [(p, "filled") for p in people] + [(None, "vacant")] * vacant + [(None, "elect_fall")] * fall
    for name_cls, status in entries:
        slug = None
        if name_cls:
            slug = _person(*name_cls)
        n = len(SEATS) + 1
        seat_dict = {
            "id": f"seat-{n:03d}",
            "body": body,
            "seat": seat,
            "constituency": constituency,
            "person_slug": slug,
            "status": status,
            "kind": kind,
            "voting": voting,
            "fill_rule": rule,
            "inbox": None,  # no role inboxes exist yet; never invent one
            "draft": draft if rule == "officer_title" else None,
            "term": TERMS[body],
        }
        SEATS.append(seat_dict)
        if slug:
            PEOPLE[slug]["roles"].append(
                {
                    "seat_id": seat_dict["id"],
                    "body": body,
                    "seat": seat,
                    "constituency": constituency,
                    "note": "",
                    "term": TERMS[body],
                    "fill_rule": rule,
                    "draft": seat_dict["draft"],
                    "kind": kind,
                }
            )


def _sen(seat, cons, kind, people=(), vacant=0, fall=0):
    _group(B_SENATE, seat, cons, kind, people, vacant, fall)


def _officer(body, seat, name, cls, constituency=None, draft=None):
    _group(body, seat, constituency, "officer", [(name, cls)] if name else (), 0 if name else 1,
           voting=False, draft=draft or ("E-Board bylaws" if body in EB_BODIES else "Senate bylaws or rules"))


def _build():
    # ---- Student Senate (voting seats: Grand Marshal + 29)
    _sen("Grand Marshal", "everyone", "gm", [("Jordan Krishnayah", "'28")])
    _sen("Graduate Senator", "graduate", "elected_senator",
         [("Batuhan Yalcin", ""), ("Alexander Neimeth", ""), ("Paul Lea", ""), ("Stanley Goodwin", "'30G")],
         vacant=3)
    _sen("Class of 2027 Senator", "2027", "class_senator",
         [("Ghea Chaw", "'27"), ("Griffin Oliver", "'27"), ("Rachel Schneider", "'27"), ("Adam Choi", "'27")])
    _sen("Class of 2028 Senator", "2028", "class_senator",
         [("Aaron Nam", "'28"), ("Nick Castiglione", "'28")], vacant=2)
    _sen("Class of 2029 Senator", "2029", "class_senator",
         [("Jaewon Yoon", "'29"), ("Melissa DeLuise", "'29"), ("Aarushi Kumar", "'29"), ("Riley Sanders", "'29")])
    _sen("Class of 2030 Senator", "2030", "class_senator", fall=4)
    _sen("Independent Senator", "independent", "elected_senator",
         [("Shruthi Anandraman", "'28"), ("Ryan Kilgore", "'27"), ("Ashley Wong", "'27")])
    _sen("Fraternity and Sorority Life (FSL) Senator", "fsl", "elected_senator",
         [("Mischa Fedak", ""), ("Andrew Donilon", ""), ("Radhika Manvar", "")])

    # ---- Senate officers (titles set by Senate bylaws, not the Constitution)
    _officer(B_SENATE_OFFICERS, "Senate Treasurer", "Cee Ray", "'27")
    _officer(B_SENATE_OFFICERS, "Parliamentarian", "Sasha Notkin", "'28")
    _officer(B_SENATE_OFFICERS, "Secretary", "Selena Tang", "'29")
    _officer(B_SENATE_OFFICERS, "Vice Grand Marshal for Internal Affairs", "Griffin Oliver", "'27")
    _officer(B_SENATE_OFFICERS, "Vice Grand Marshal for External Affairs", "Ryan Kilgore", "'27")

    # ---- Senate committee chairs (the Constitution names no committees)
    for seat, name, cls in [
        ("Chair, Academic Affairs Committee", "Zach Nobles", "'27"),
        ("Chair, Community Relations Committee", "Mia Stryhalaleck", "'28"),
        ("Elections Commissioner (acting)", "Lauren Antao", "'28"),
        ("Chair, Facilities and Services Committee", "Charlie Fowle", "'29"),
        ("Chair, Senate Communications and Engagement Committee", "Emily Lin", "'29"),
        ("Chair, Union Annual Report Committee (acting)", "Samson Kempiak", "'28"),
        ("Chair, Web Technologies Group", "Aaron Niyazov", "'28"),
        ("Chair, Student Life Committee", "Stanley Goodwin", "'30G"),
        ("Chair, Rules and Administration Committee", "Griffin Oliver", "'27"),
        ("Chair, Residential Living and Dining Committee (RLDC)", "Shruthi Anandraman", "'28"),
    ]:
        _officer(B_SENATE_COMMITTEES, seat, name, cls)

    # ---- Peer reports to the Senate
    _officer(B_SENATE_PEERS, "Graduate Council report", "Melissa Flores", "'G")
    _officer(B_SENATE_PEERS, "Undergraduate Council report", "Nick Castiglione", "'28")

    # ---- Executive Board
    _group(B_EB, "President of the Union", "everyone", "pu", [("Kate Goldstein", "'26 '27G")])
    _officer(B_EB_OFFICERS, "Vice President for Board Operations", "Gavin Finn", "'28")
    _officer(B_EB_OFFICERS, "Vice President for Club Relations", "Jesse Kim", "'26 '27G")
    _officer(B_EB_OFFICERS, "Vice President for Rules and Special Projects", "Blaine Rosenberg", "'28")

    _group(B_EB, "Class Representative (Graduate)", "graduate", "eb_class", vacant=1)
    _group(B_EB, "Class Representative (Class of 2027)", "2027", "eb_class", [("Jacob Bloecher", "'27")])
    _group(B_EB, "Class Representative (Class of 2028)", "2028", "eb_class", [("Mariam Toure", "'28")])
    _group(B_EB, "Class Representative (Class of 2029)", "2029", "eb_class", [("Ava Cintula", "'29")])
    _group(B_EB, "Class Representative (Class of 2030)", "2030", "eb_class", vacant=1)

    _group(B_EB, "Club and Organisation Representative", "clubs", "eb_club",
           [("Grey Smith", "'27"), ("Elijah Pulga", "'29"), ("Samson Kempiak", "'28"),
            ("Valerie Rosa-Sanclemente", "'28")], vacant=3)
    _group(B_EB, "Member-at-Large", "everyone", "eb_atlarge",
           [("Ahmed Shoaib", "'29"), ("Aaron Brown", "'29"), ("Sumaya Moumita", "'28"), ("William Liu", "'29")],
           vacant=1)

    # Council and Senate seats: voting under the Constitution, although the agenda
    # prints them as "Peer Body Representatives".
    _group(B_EB, "Senate–E-Board Liaison (chosen by the Senate)", None, "eb_peer", [("Cee Ray", "'27")])
    _group(B_EB, "Graduate Council representative", "graduate", "eb_peer", [("Joydip Paul", "'29G")])
    _group(B_EB, "Undergraduate Council representative", None, "eb_peer", vacant=1)

    # Non-voting, from the agenda
    _officer(B_EB_OTHER, "Chair, Business Operations", "Grey Smith", "'27")
    _officer(B_EB_OTHER, "Chair, Club Operations", "Elijah Pulga", "'29")
    _officer(B_EB_OTHER, "Chair, Multicultural Leadership Council", "Mariam Toure", "'28")
    _officer(B_EB_OTHER, "Chair, Union Annual Report", "Ava Cintula", "'29")
    _group(B_EB_OTHER, "Club Financial Advisor", "clubs", "advisor",
           [("Soloman Liao", "'29"), ("Axo Ojeda-Ericksen", "'27")], voting=False, draft="E-Board bylaws")
    _officer(B_EB_OTHER, "Secretary", "Eleonora Romani", "")
    _officer(B_EB_OTHER, "Chair, Union Programming and Activities Committee (UPAC)", "Lilu Kaufman", "'26")
    _officer(B_EB_OTHER, "Parliamentarian", None, "")
    _officer(B_EB_OTHER, "Chair, Marketing and Strategy", None, "")
    _officer(B_EB_OTHER, "Chair, Executive Communications", None, "")


_build()


def rule_for(seat):
    """FILL_RULES entry for a seat, with the seat's own draft label applied."""
    rule = dict(FILL_RULES[seat["fill_rule"]])
    rule["elected"] = seat["fill_rule"] in ELECTED_RULE_KEYS
    if seat.get("draft"):
        rule["draft"] = seat["draft"]
    return rule


def seat_by_label(label):
    for s in SEATS:
        if s["seat"] == label:
            return s
    return None


def seat_by_id(seat_id):
    for s in SEATS:
        if s["id"] == seat_id:
            return s
    return None


def seats_for(key, body=None, kind=None):
    return [
        s for s in SEATS
        if s["constituency"] == key
        and (body is None or s["body"] == body)
        and (kind is None or s["kind"] == kind)
    ]


def senate_voting_seats():
    """The 29 voting Senate seats (the Grand Marshal is excluded)."""
    return [s for s in SEATS if s["body"] == B_SENATE and s["kind"] != "gm"]


def eb_voting_seats():
    """The 20 voting E-Board seats (the President and the VP titles are excluded)."""
    return [s for s in SEATS if s["body"] == B_EB and s["kind"] != "pu"]


def role_summary(person):
    """Short role list for directories: 'Class of 2027 Senator, Chair, RLDC'."""
    seen, out = set(), []
    for r in person["roles"]:
        if r["seat"] not in seen:
            seen.add(r["seat"])
            out.append(r["seat"])
    return out


# --------------------------------------------------------------------------
# Topics (the router)
# --------------------------------------------------------------------------

SAFETY_LINE = "If anyone is in danger, contact RPI Public Safety now."

_SB = "Senate bylaws or rules"

TOPICS = [
    {
        "slug": "dining",
        "question": "Problem with dining or meal plans?",
        "owner_label": "Residential Living and Dining Committee",
        "owner_seat": "Chair, Residential Living and Dining Committee (RLDC)",
        "person_word": "Chair",
        "remit": "Takes student concerns about residence halls and dining to RPI.",
        "remit_draft": _SB,
        "outside_sg": "RPI's dining service runs meal plans; the committee raises student concerns with them.",
    },
    {
        "slug": "housing",
        "question": "Problem with your residence hall?",
        "owner_label": "Residential Living and Dining Committee",
        "owner_seat": "Chair, Residential Living and Dining Committee (RLDC)",
        "person_word": "Chair",
        "remit": "Takes student concerns about residence halls and dining to RPI.",
        "remit_draft": _SB,
        "outside_sg": "Residence Life runs housing day to day.",
    },
    {
        "slug": "buildings",
        "question": "Broken, inaccessible or unsafe building?",
        "owner_label": "Facilities and Services Committee",
        "owner_seat": "Chair, Facilities and Services Committee",
        "person_word": "Chair",
        "remit": "Takes student concerns about campus buildings and services to RPI.",
        "remit_draft": _SB,
        "outside_sg": "For urgent repairs contact RPI Facilities directly.",
    },
    {
        "slug": "academics",
        "question": "Problem with classes, advising or academic policy?",
        "owner_label": "Academic Affairs Committee",
        "owner_seat": "Chair, Academic Affairs Committee",
        "person_word": "Chair",
        "remit": "Takes student concerns about classes and academic policy to RPI.",
        "remit_draft": _SB,
        "outside_sg": "",
    },
    {
        "slug": "student-life",
        "question": "Something about campus life you'd like changed?",
        "owner_label": "Student Life Committee",
        "owner_seat": "Chair, Student Life Committee",
        "person_word": "Chair",
        "remit": "Takes student concerns about everyday campus life to RPI.",
        "remit_draft": _SB,
        "outside_sg": "",
    },
    {
        "slug": "troy",
        "question": "Off-campus or Troy community issue?",
        "owner_label": "Community Relations Committee",
        "owner_seat": "Chair, Community Relations Committee",
        "person_word": "Chair",
        "remit": "Handles the Union's relationship with Troy and the neighbourhoods around campus.",
        "remit_draft": _SB,
        "outside_sg": "",
    },
    {
        "slug": "clubs",
        "question": "Club rules, registration or money?",
        "owner_label": "Executive Board, Vice President for Club Relations",
        "owner_seat": "Vice President for Club Relations",
        "person_word": "Vice President for Club Relations",
        "owner_draft": "E-Board bylaws",
        "body_fact": "The Executive Board decides how clubs are classified and hands out Union money.",
        "body_cite": "Art. VII §2",
        "outside_sg": "",
        "default_for": "clubs",
    },
    {
        "slug": "grad",
        "question": "Stipends, grad housing, TA workload?",
        "owner_label": "Graduate Council and Graduate Senators",
        "owner_seat": None,
        "person_word": "",
        "no_chair_text": "see your Graduate Senators below",
        "body_fact": (
            "The Graduate Council is the Union's advocacy body for graduate students: "
            "the 7 Graduate Senators plus at least 5 at-large members."
        ),
        "body_cite": "Art. VII §4",
        "outside_sg": "",
        "default_for": "graduate",
    },
    {
        "slug": "class",
        "question": "Class events or class dues?",
        "owner_label": "Your Class Council (graduate students: the Graduate Council)",
        "owner_seat": None,
        "person_word": "Chair",
        "no_chair_text": "Chair: Roster not listed yet",
        "body_fact": (
            "Each class elects a Class Council, which recommends how class dues are "
            "spent; the Undergraduate Council approves that spending."
        ),
        "body_cite": "Art. VII §5",
        "outside_sg": "",
    },
    {
        "slug": "rights",
        "question": "Think a Union body broke the Constitution, or your student rights were violated?",
        "owner_label": "Judicial Board",
        "owner_seat": None,
        "person_word": "Chair",
        "no_chair_text": "Chair: Roster not listed yet",
        "body_fact": (
            "The Judicial Board is the Union's student court. It hears charges that the "
            "Union Constitution, the Rensselaer Student Bill of Rights, or student "
            "conduct rules were violated, and can rule other bodies' decisions "
            "unconstitutional."
        ),
        "body_cite": "Art. VII §3",
        "outside_sg": "",
        "no_form": True,
        "how_to_file_draft": "Judicial Board bylaws",
    },
    {
        "slug": "elections",
        "question": "Question about running or voting in an election?",
        "owner_label": "Elections Commission",
        "owner_seat": "Elections Commissioner (acting)",
        "person_word": "Acting commissioner",
        "owner_draft": "Senate election rules",
        "owner_draft_note": "The Constitution leaves election procedure to the Senate (Art. VIII §6).",
        "outside_sg": "",
    },
    {
        "slug": "website",
        "question": "Problem with this website?",
        "owner_label": "Web Technologies Group",
        "owner_seat": "Chair, Web Technologies Group",
        "person_word": "Chair",
        "remit": "Looks after the Union's website.",
        "remit_draft": _SB,
        "outside_sg": "",
    },
    {
        "slug": "other",
        "question": "Something else?",
        "owner_label": "Grand Marshal's office",
        "owner_seat": "Grand Marshal",
        "person_word": "Grand Marshal",
        "body_fact": "The Grand Marshal is the leader and chief spokesperson for the whole Union.",
        "body_cite": "Art. IV §1",
        "outside_sg": "",
    },
]

TOPIC_BY_SLUG = {t["slug"]: t for t in TOPICS}
HOME_TOPIC_SLUGS = ["dining", "housing", "buildings", "academics", "clubs", "grad"]

# --------------------------------------------------------------------------
# Sample "You said, we did" issues. All SAMPLE: made up.
# These stand in for the Senate's Notion Issues database, and every owner seat
# is a Senate seat. Each key is a whitelisted field of that database. There is
# no field for a student's original message or name.
# --------------------------------------------------------------------------

ISSUE_STATUS = {
    "heard": {"label": "Heard", "chip": "bg-blue-50 text-blue-900 border-blue-900"},
    "assigned": {"label": "Owner assigned", "chip": "bg-amber-50 text-amber-900 border-amber-900"},
    "working": {"label": "Working on it", "chip": "bg-amber-50 text-amber-900 border-amber-900"},
    "brought": {"label": "Brought to a meeting", "chip": "bg-amber-50 text-amber-900 border-amber-900"},
    "decided": {"label": "Decided", "chip": "bg-purple-50 text-purple-900 border-purple-900"},
    "done": {"label": "Done", "chip": "bg-green-50 text-green-900 border-green-900"},
    "not_possible": {"label": "Not possible", "chip": "bg-gray-100 text-gray-900 border-gray-900"},
}

_ALL_UG = ["2027", "2028", "2029", "2030", "independent", "fsl"]

ISSUES = [
    {
        "id": "iss-001",
        "public": True,
        "title": "Commons dining hall closes too early on weekends",
        "topic": "dining",
        "constituencies": _ALL_UG,
        "owner_seat": "Chair, Residential Living and Dining Committee (RLDC)",
        "source": "Senate survey",
        "raised_on": date(2026, 2, 9),
        "status": "done",
        "updates": [
            {"date": date(2026, 2, 23), "text": "Committee asked RPI Dining for the weekend hours and the reason for them."},
            {"date": date(2026, 4, 6), "text": "Brought to a Senate meeting. RPI Dining agreed to a trial of later hours."},
            {"date": date(2026, 9, 14), "text": "Trial hours started for the fall semester."},
        ],
        "outcome": "Weekend closing time moved from 8 PM to 10 PM. The committee will check usage in December.",
        "last_update": date(2026, 9, 14),
    },
    {
        "id": "iss-002",
        "public": True,
        "title": "Lower the price of the meal plan",
        "topic": "dining",
        "constituencies": _ALL_UG,
        "owner_seat": "Chair, Residential Living and Dining Committee (RLDC)",
        "source": "Email",
        "raised_on": date(2026, 3, 2),
        "status": "not_possible",
        "updates": [
            {"date": date(2026, 3, 30), "text": "Committee asked RPI Dining how meal plan prices are set."},
        ],
        "outcome": (
            "RPI controls this. RPI Dining Services sets meal plan prices, and Student "
            "Government cannot change them. Contact RPI Dining Services directly; the "
            "committee passed your concern on."
        ),
        "last_update": date(2026, 3, 30),
    },
    {
        "id": "iss-003",
        "public": True,
        "title": "Elevator out of order in an academic building for weeks",
        "topic": "buildings",
        "constituencies": ["2027", "2028", "2029", "2030", "graduate"],
        "owner_seat": "Chair, Facilities and Services Committee",
        "source": "Discord",
        "raised_on": date(2026, 7, 20),
        "status": "working",
        "updates": [
            {"date": date(2026, 7, 27), "text": "Reported to RPI Facilities by the committee."},
            {"date": date(2026, 8, 14), "text": "Facilities said a part is on order."},
        ],
        "outcome": "",
        "last_update": date(2026, 8, 14),
    },
    {
        "id": "iss-004",
        "public": True,
        "title": "The club funding request form is confusing",
        "topic": "clubs",
        "constituencies": ["clubs"],
        "owner_seat": "Senate–E-Board Liaison (chosen by the Senate)",
        "source": "Speak at a meeting",
        "raised_on": date(2026, 10, 12),
        "status": "heard",
        "updates": [],
        "outcome": "",
        "last_update": date(2026, 10, 12),
    },
    {
        "id": "iss-005",
        "public": True,
        "title": "Graduate stipend payments arrive late",
        "topic": "grad",
        "constituencies": ["graduate"],
        "owner_seat": "Graduate Senators",
        "source": "Senate survey",
        "raised_on": date(2026, 9, 8),
        "status": "brought",
        "updates": [
            {"date": date(2026, 9, 22), "text": "Assigned to the Graduate Senators."},
            {"date": date(2026, 10, 6), "text": "Raised at a Senate meeting; the Graduate Council was asked for a written answer."},
        ],
        "outcome": "",
        "last_update": date(2026, 10, 6),
    },
    {
        "id": "iss-006",
        "public": True,
        "title": "More late-night study space on campus",
        "topic": "academics",
        "constituencies": ["2027", "2028", "2029", "2030", "graduate"],
        "owner_seat": "Chair, Academic Affairs Committee",
        "source": "Speak at a meeting",
        "raised_on": date(2026, 8, 31),
        "status": "decided",
        "updates": [
            {"date": date(2026, 9, 18), "text": "Committee drafted a request for extended building hours."},
            {"date": date(2026, 10, 9), "text": "Senate voted to send the request to RPI."},
        ],
        "outcome": "The Senate approved sending the request. RPI has not answered yet.",
        "last_update": date(2026, 10, 9),
    },
]

ISSUE_SOURCES = ["Senate survey", "Speak at a meeting", "Email", "Discord"]
STALE_DAYS = 60

# --------------------------------------------------------------------------
# Meeting records, per body: the Senate's from its Notion, the E-Board's entered on this site.
# Agendas are Word files in Box, published as PDF.
# --------------------------------------------------------------------------

MEETINGS = [
    {
        "key": "senate-12",
        "body": "senate",
        "source_key": "meeting_senate",
        "name": "Student Senate #12",
        "date": date(2026, 7, 30),
        "time": "8 PM",
        "place": "Webex",
        "agenda": "Student Senate agenda, 30 Jul 2026",
        "agenda_url": MOCK_BOX_AGENDA["senate-12"],
        "minutes": "Minutes not posted",
    },
    {
        "key": "eb-01",
        "body": "eboard",
        "source_key": "meeting_eboard",
        "name": "Executive Board meeting 01",
        "date": date(2026, 8, 25),
        "time": "7 PM",
        "place": "Rensselaer Union, room 3202",
        "agenda": "Executive Board Agenda 01, 25 Aug 2026",
        "agenda_url": MOCK_BOX_AGENDA["eb-01"],
        "minutes": "Minutes not posted",
    },
]
LAST_SENATE_MEETING = date(2026, 7, 30)

# Bodies that publish their records as files in a Box folder only.
FOLDER_BODIES = [
    {"key": "gc", "name": "Graduate Council",
     "path": "Public Records/Graduate Council/2026-27 GC 2026-27/", "note": None},
    {"key": "uc", "name": "Undergraduate Council",
     "path": "Public Records/Undergraduate Council/2026-27 UC 2026-27/",
     "note": "Including the four Class Councils."},
    {"key": "jboard", "name": "Judicial Board",
     "path": "Public Records/Judicial Board/2026-27 JBoard 2026-27/",
     "note": "Its rulings on what the Constitution means are public. Its conduct and rights cases are confidential."},
]

# --------------------------------------------------------------------------
# Who tracks issues publicly (shown in the raise routing panel)
# --------------------------------------------------------------------------

ISSUE_TRACKING = {
    "senate": "Yes. Senate committees log issues in the Senate's Notion, and items they mark Public appear on You said, we did.",
    "eboard": "No. The Executive Board doesn't publish an issue tracker. What it decides appears in its minutes.",
    "gc": "Graduate Senators can log it in the Senate's tracker. The Graduate Council doesn't publish one.",
    "uc": "No. Class Councils and the Undergraduate Council don't publish an issue tracker.",
    "jboard": "No. Judicial Board cases are confidential.",
}
# Topic slug to the body that owns it; every other topic goes to the Senate.
TOPIC_BODY = {"clubs": "eboard", "grad": "gc", "class": "uc", "rights": "jboard"}
BODY_NAMES = {
    "eboard": "Executive Board",
    "gc": "Graduate Council",
    "uc": "Undergraduate Council",
    "jboard": "Judicial Board",
}

# --------------------------------------------------------------------------
# Glossary
# --------------------------------------------------------------------------

GLOSSARY = [
    {"term": "Rensselaer Union",
     "text": "Every enrolled RPI student who has paid the Union Activity Fee, and the organisation they form.",
     "cite": "Art. I; Art. II"},
    {"term": "Student Senate",
     "text": "The Union's main lawmaking body, with 29 voting seats. Passes its own rules, sets the Activity Fee and approves many appointments.",
     "cite": "Art. VII §1"},
    {"term": "Executive Board (E-Board)",
     "text": "The Union's budgeting body: prepares and approves the budget, hands out Union money and classifies clubs.",
     "cite": "Art. VII §2"},
    {"term": "Judicial Board",
     "text": "The Union's student court for rights and conduct cases, and the only body that interprets the Constitution.",
     "cite": "Art. VII §3"},
    {"term": "Graduate Council",
     "text": "The advocacy body for graduate students: the 7 Graduate Senators plus at least 5 at-large members. Elects its own President.",
     "cite": "Art. VII §4; Amendment V"},
    {"term": "Undergraduate Council",
     "text": "The advocacy body for undergraduates: the President and Vice President of each Class Council. Oversees the Class Councils.",
     "cite": "Art. VII §5"},
    {"term": "Class Council",
     "text": "Your class's own elected council: Class President, Vice President, at least 8 Representatives and your 4 Class Senators. Recommends how class dues are spent.",
     "cite": "Art. VII §5"},
    {"term": "Grand Marshal",
     "text": "The Union's leader and chief spokesperson, elected by all students. Chairs the Senate and votes only to break a tie.",
     "cite": "Art. IV §1"},
    {"term": "President of the Union",
     "text": "Chairs the Executive Board and appoints most of its members, with 2/3 Senate approval.",
     "cite": "Art. IV §2; Art. VII §2"},
    {"term": "Director of the Union",
     "text": "A paid staff member who runs Union activities and funds. Advises the Executive Board but cannot veto it.",
     "cite": "Art. V"},
    {"term": "Class Representative (Executive Board)",
     "text": "One E-Board seat per class, appointed by the President of the Union with 2/3 Senate approval. Not the same as a Class Council Representative, who is elected.",
     "cite": "Art. VII §2, §5"},
    {"term": "Member-at-Large",
     "text": "An E-Board seat that can represent any Union member; 2 required, up to 3 more.",
     "cite": "Art. VII §2"},
    {"term": "Recall",
     "text": "A student vote to remove someone you elected before their term ends.",
     "cite": "Art. X §1, §2"},
    {"term": "Referendum",
     "text": "A binding student vote on a question, forced by a 10% petition or put on the ballot by 2/3 of the Senate. It counts if at least 20% vote.",
     "cite": "Art. XII"},
    {"term": "Ex-officio",
     "text": "Holding a seat automatically because of another office."},
    {"term": "Quorum",
     "text": "The minimum number of voting members needed for a meeting to act. The Constitution leaves it to each body's rules; the latest Senate agenda lists 13.",
     "agenda": AGENDA["senate"],
     "draft": "Senate bylaws or rules"},
    {"term": "Invitation to Speak",
     "text": "Time at the start and end of every meeting when anyone may speak.",
     "draft": "Senate bylaws or rules"},
    {"term": "Senate Treasurer",
     "text": "A Senate officer from the agendas. Not the Constitution's 'Treasurer', which is RPI's own Treasurer who holds the Union's money.",
     "cite": "Art. VI"},
]

# --------------------------------------------------------------------------
# Powers
# --------------------------------------------------------------------------


def _open_class_senate_seats(key):
    return len([s for s in seats_for(key, B_SENATE) if s["status"] == "vacant"])


_n2028 = _open_class_senate_seats("2028")

POWERS = [
    {
        "id": "recall",
        "title": "Remove someone you elected",
        "text": (
            "A petition from 20% of a senator's constituents (or a Senate majority) "
            "starts a removal election; 2/3 of those voting removes them, if at least "
            "20% vote. For the Grand Marshal, President of the Union, and the Graduate "
            "and Undergraduate Council Presidents, a petition from 50% of their "
            "constituents removes them outright."
        ),
        "not_set": "What counts as good cause; how removal elections are run",
        "not_set_why": "Senate bylaws or rules",
        "cite": "Art. X §1, §2",
    },
    {
        "id": "challenge",
        "title": "Force an election for an appointed seat",
        "text": (
            "If an elected seat is filled by appointment, a petition from 20% of that "
            "constituency, received by the Senate within two weeks of the announcement, "
            f"forces a special election. Example: Class of 2028 has {_n2028} open Senate "
            "seats; if its Class Council appoints people to them, 20% of the class can "
            "force an election."
        ),
        "not_set": "Petition format and where to hand it in",
        "not_set_why": "Senate bylaws or rules",
        "cite": "Art. XI §5, §6",
    },
    {
        "id": "referendum",
        "title": "Make students vote on it",
        "text": (
            "A petition signed by 10% of all Union members makes the Senate hold a "
            "binding student vote on anything except the Constitution, unless 2/3 of "
            "all Senate seats (20 of 29, derived) reject it. The vote is within 45 days "
            "(excluding vacations) or at the next regular election, at least 14 days "
            "after approval, never during exams. It passes by majority if at least 20% "
            "of affected students vote, and the Senate must then carry it out."
        ),
        "not_set": "Petition format; how signatures are checked; how many students 10% is",
        "not_set_why": "Senate bylaws or rules",
        "cite": "Art. XII §1–§4",
    },
    {
        "id": "judicial-board",
        "title": "Bring a case to the Judicial Board",
        "text": (
            "Any charge that the Constitution, the Rensselaer Student Bill of Rights, "
            "or student conduct rules were violated can be referred to the Judicial "
            "Board. It can rule a Senate, Executive Board or council decision "
            "unconstitutional."
        ),
        "not_set": "Who may file, how, deadlines and appeals",
        "not_set_why": "Judicial Board bylaws",
        "cite": "Art. VII §3",
    },
    {
        "id": "amend",
        "title": "Change the Constitution",
        "text": (
            "Ask your senators: an amendment needs 2/3 of the Senate, then a majority "
            "in a campus vote where at least 20% of students vote. A petition alone "
            "can't amend it. The wording must be published campus-wide at least two "
            "weeks before the vote."
        ),
        "not_set": "",
        "not_set_why": "",
        "cite": "Art. XII §1; Art. XIII §1, §3",
    },
    {
        "id": "run",
        "title": "Take the seat yourself",
        "text": (
            "Any Union member can run, subject to RPI's eligibility rules and the "
            "Senate's. General elections are in the spring; first-year seats in the fall."
        ),
        "not_set": "How to get on the ballot, signatures, dates",
        "not_set_why": "Senate election rules",
        "cite": "Art. VIII §1, §3, §4, §6, §13",
    },
]

# --------------------------------------------------------------------------
# Ownership (how#site)
# --------------------------------------------------------------------------

_FOLDER_ONLY_RECORDS = "None: files in its Box folder only"
_FOLDER_ONLY_ROSTER = "This site, once a roster officer is named (Roster not listed yet)"

OWNERSHIP_BY_BODY = [
    {
        "body": "Student Senate",
        "example": False,
        "meetings": "Senate's Notion",
        "roster": (
            "This site (Vice Grand Marshal for Internal Affairs); the Senate's Notion "
            "gets a read-only copy for attendance"
        ),
        "issues": 'Senate\'s Notion "Issues", Public rows only (not built)',
    },
    {
        "body": "Executive Board",
        "example": True,
        "meetings": "Entered on this site by its Secretary",
        "roster": "This site (Vice President for Rules and Special Projects)",
        "issues": "Not tracked publicly; decisions are in its minutes",
    },
    {
        "body": "Graduate Council",
        "example": True,
        "meetings": _FOLDER_ONLY_RECORDS,
        "roster": _FOLDER_ONLY_ROSTER,
        "issues": "Not tracked publicly",
    },
    {
        "body": "Undergraduate Council and Class Councils",
        "example": True,
        "meetings": _FOLDER_ONLY_RECORDS,
        "roster": _FOLDER_ONLY_ROSTER,
        "issues": "Not tracked publicly",
    },
    {
        "body": "Judicial Board",
        "example": True,
        "meetings": "None: public rulings in its Box folder; cases are confidential",
        "roster": _FOLDER_ONLY_ROSTER,
        "issues": "Not applicable",
    },
]

OWNERSHIP_SHARED = [
    {
        "what": "Seats, people and term assignments, for every body",
        "lives_in": "This site",
        "who_edits": "Each body's roster officer",
        "how_site_gets_it": (
            "Native (Wagtail). The Senate's Notion receives a read-only copy "
            "(name, seat, term, voting) for attendance."
        ),
        "native": True,
    },
    {
        "what": "Photo, bio, pronouns, major, office hours",
        "lives_in": 'This site, only with "Public profile" ticked',
        "who_edits": "Each member, or their roster officer",
        "how_site_gets_it": "Native; removed at once if consent is withdrawn",
        "native": True,
    },
    {
        "what": "Chooser, constituency descriptions, topic router, fill rules, powers, glossary",
        "lives_in": "This site",
        "who_edits": "Web Technologies Group chair",
        "how_site_gets_it": "Native (Wagtail)",
        "native": True,
    },
    {
        "what": "Agendas and minutes",
        "lives_in": "Word files in each body's public Box folder, published as PDF",
        "who_edits": "Each body's records officer",
        "how_site_gets_it": "Linked, never retyped",
        "native": False,
    },
    {
        "what": "Senate attendance, contacts (CRM), internal notes",
        "lives_in": "The Senate's Notion",
        "who_edits": "Senate officers",
        "how_site_gets_it": "Never shown on the site",
        "native": False,
    },
]

# --------------------------------------------------------------------------
# Bodies (how#bodies)
# --------------------------------------------------------------------------

BODIES = [
    {
        "id": "senate",
        "name": "Student Senate",
        "glossary": "Student Senate",
        "who": "7 Graduate, 4 per class, 3 Independent, 3 FSL = 29 voting seats",
        "chair": "The Grand Marshal chairs and votes only to break a tie.",
        "cite": "Art. VII §1",
        "roster": "senate",
    },
    {
        "id": "eb",
        "name": "Executive Board",
        "glossary": "Executive Board (E-Board)",
        "who": (
            "15 to 20 voting members: 5 class reps, 5 to 7 club and organisation reps, "
            "2 to 5 members-at-large, and one rep each chosen by the Senate, the "
            "Graduate Council and the Undergraduate Council. The latest roster lists "
            "20 seats"
        ),
        "chair": "The President of the Union chairs and votes only to break a tie.",
        "cite": "Art. VII §2",
        "roster": "eb",
    },
    {
        "id": "jb",
        "name": "Judicial Board",
        "glossary": "Judicial Board",
        "who": "6 voting members and 5 alternates",
        "chair": "The Judicial Board Chairperson.",
        "cite": "Art. VII §3",
        "roster": None,
    },
    {
        "id": "gc",
        "name": "Graduate Council",
        "glossary": "Graduate Council",
        "who": "The 7 Graduate Senators plus at least 5 at-large members",
        "chair": "Its own President, elected from among its members.",
        "cite": "Art. VII §4; Amendment V",
        "roster": None,
    },
    {
        "id": "ugc",
        "name": "Undergraduate Council",
        "glossary": "Undergraduate Council",
        "who": "The President and Vice President of each Class Council: 8 members",
        "who_derived": True,
        "chair": "The Undergraduate Council President.",
        "cite": "Art. VII §5",
        "roster": None,
    },
    {
        "id": "cc",
        "name": "Class Councils",
        "glossary": "Class Council",
        "who": "Class President, Vice President, at least 8 Representatives and 4 Class Senators",
        "chair": "Each Class Council's President.",
        "cite": "Art. VII §5",
        "roster": None,
    },
]

FIVE_OFFICERS = [
    "Grand Marshal",
    "President of the Union",
    "Judicial Board Chairperson",
    "Graduate Council President",
    "Undergraduate Council President",
]

TOPIC_NAMES = {
    "dining": "Dining",
    "housing": "Housing",
    "buildings": "Buildings",
    "academics": "Academics",
    "student-life": "Student life",
    "troy": "Troy and off campus",
    "clubs": "Clubs",
    "grad": "Graduate students",
    "class": "Class events and dues",
    "rights": "Rights and the Constitution",
    "elections": "Elections",
    "website": "This website",
    "other": "Something else",
}
for _t in TOPICS:
    _t["name"] = TOPIC_NAMES[_t["slug"]]


# --------------------------------------------------------------------------
# "(derived)" markup: our own arithmetic gets a visible, explained tag
# --------------------------------------------------------------------------

from django.utils.html import escape  # noqa: E402
from django.utils.safestring import mark_safe  # noqa: E402

DERIVED_TITLE = "Our arithmetic, assuming all 29 Senate seats count"
_DERIVED_TAG = f'<span class="derived" title="{DERIVED_TITLE}">(20 of 29, derived)</span>'


def derive(text):
    """Escape ``text`` and wrap the '(20 of 29, derived)' phrase in a titled tag."""
    return mark_safe(escape(text).replace("(20 of 29, derived)", _DERIVED_TAG))


for _rule in FILL_RULES.values():
    _rule["answers_to"] = derive(_rule["answers_to"])
for _power in POWERS:
    _power["text"] = derive(_power["text"])
