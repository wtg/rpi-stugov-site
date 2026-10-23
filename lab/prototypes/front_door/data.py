"""Seed facts for the Front Door prototype, as plain Python.

Real values come from two agendas (Student Senate #12, 30 Jul 2026;
Executive Board Agenda 01, 25 Aug 2026) and the Rensselaer Union
Constitution (as amended 6 Feb 2026).  Anything made up is marked
``sample=True`` and rendered with the Sample badge.  Entries backed by the
Constitution carry ``cite``.  Entries the Constitution leaves to someone
else carry ``draft="<who decides>"``.

Nothing here connects to Box or Notion.  Sync times and link checks are
seed data.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

CONSTITUTION = {"name": "Rensselaer Union Constitution", "amended": date(2026, 2, 6)}
CONSTITUTION_LINE = "Rensselaer Union Constitution, last amended 6 Feb 2026"

AGENDA_SRC = {
    "senate": "Student Senate agenda, 30 Jul 2026",
    "eboard": "Executive Board Agenda 01, 25 Aug 2026",
}

# --------------------------------------------------------------------------
# Single source of truth (see docs/redesign/data-architecture.md)
# --------------------------------------------------------------------------

SYNC = {
    "notion_minutes_ago": 12,
    "box_links_checked": date(2026, 10, 19),
    "wagtail_reviewed": date(2026, 10, 21),
    "eboard_entry_updated": date(2026, 8, 24),
    "roster_updated": date(2026, 8, 25),
}
MOCK_NOTION = "https://www.notion.so/"
MOCK_BOX = "https://rpi.box.com/"


def _d(value):
    return f"{value.day} {value.strftime('%b %Y')}"


def build_sources(sync=SYNC):
    """Build the SOURCES dict from SYNC, never hard-coding the numbers."""
    synced = f"synced {sync['notion_minutes_ago']} min ago"
    checked = _d(sync["box_links_checked"])
    reviewed = _d(sync["wagtail_reviewed"])
    eboard_updated = _d(sync["eboard_entry_updated"])
    roster_updated = _d(sync["roster_updated"])
    missing_line = "Document: Box · no link added to the meeting record yet"
    rows = [
        ("meeting_senate", f"Meeting record: Senate's Notion · {synced}", "Edit in Notion", MOCK_NOTION),
        (
            "meeting_eboard",
            f"Meeting record: entered on this site by the E-Board Secretary · updated {eboard_updated}",
            "Edit on this site",
            "/admin/",
        ),
        (
            "folder_only",
            "Records: files in this body's Box folder. It doesn't list meetings on this site.",
            "Open in Box",
            MOCK_BOX,
        ),
        ("file", f"Document: Word file in Box, published as PDF · link checked {checked}", "Edit in Box", MOCK_BOX),
        ("file_missing_senate", missing_line, "Add the link in Notion", MOCK_NOTION),
        ("file_missing_eboard", missing_line, "Add the link on this site", "/admin/"),
        ("folder_missing", "Folder: Box · shared link not added yet", "Share it in Box", MOCK_BOX),
        (
            "agenda_items_option",
            "Agenda items: Senate's Notion agenda page · only if the Senate drafts agendas in Notion "
            f"(an option, not current practice) · {synced}",
            "Edit in Notion",
            MOCK_NOTION,
        ),
        (
            "motions",
            "Motion status: Senate's Notion Motions table · the motion's text is in the linked Word file "
            f"· {synced}",
            "Edit in Notion",
            MOCK_NOTION,
        ),
        (
            "in_minutes",
            "Decisions: recorded in the minutes (a Word file in Box). This site doesn't retype them.",
            "Open in Box",
            MOCK_BOX,
        ),
        (
            "roster",
            f"Roster: entered on this site by each body's roster officer · last change {roster_updated}",
            "Edit on this site",
            "/admin/",
        ),
        (
            "quoted_budget",
            "Quoted from Executive Board Agenda 01, 25 Aug 2026 (a PDF in Box). "
            "This site does not update these figures.",
            "Open in Box",
            MOCK_BOX,
        ),
        ("wagtail", f"Written on this site · reviewed {reviewed}", "Edit in Wagtail", "/admin/"),
    ]
    return {
        key: {"key": key, "line": line, "edit_label": label, "edit_url": url}
        for key, line, label, url in rows
    }


SOURCES = build_sources()

BOX_FOLDERS = {
    "senate": {"label": "Student Senate, 57th Senate", "path": "Public Records/Senate/2026-27 Senate 57/", "shared_url": None},
    "eboard": {"label": "Executive Board, FY27", "path": "Public Records/Executive Board/2026-27 EBoard FY27/", "shared_url": None},
    "gc": {"label": "Graduate Council, 2026–27", "path": "Public Records/Graduate Council/2026-27 GC 2026-27/", "shared_url": None},
    "uc": {"label": "Undergraduate Council, 2026–27", "path": "Public Records/Undergraduate Council/2026-27 UC 2026-27/", "shared_url": None},
    "jboard": {"label": "Judicial Board, 2026–27", "path": "Public Records/Judicial Board/2026-27 JBoard 2026-27/", "shared_url": None},
}

# How each body keeps its meeting records (revision of 21 Oct 2026).  Only the
# Senate is adopting Notion; the other choices are examples until each body
# decides.  A body's meetings live in one place, never two.
BODY_RECORDS = {
    "senate": {"name": "Student Senate", "adapter": "notion", "adapter_label": "Senate's Notion", "records_officer": "Senate Secretary", "folder": "senate", "example": False},
    "eboard": {"name": "Executive Board", "adapter": "site", "adapter_label": "Entered on this site", "records_officer": "E-Board Secretary", "folder": "eboard", "example": True},
    "gc": {"name": "Graduate Council", "adapter": "folder", "adapter_label": "Box folder only", "records_officer": None, "folder": "gc", "example": True},
    "uc": {"name": "Undergraduate Council", "adapter": "folder", "adapter_label": "Box folder only", "records_officer": None, "folder": "uc", "example": True},
    "jboard": {"name": "Judicial Board", "adapter": "folder", "adapter_label": "Box folder only", "records_officer": None, "folder": "jboard", "example": True},
}

FOLDER_ONLY_NOTES = {
    "jboard": {"text": "Its rulings on what the Constitution means are public. Its conduct and rights cases are confidential.", "draft": "Judicial Board bylaws"},
}

# Site notice. Shown only while ``expires`` is today or later.
NOTICE = None
# NOTICE = {
#     "text": "The Union office is closed on Monday for a holiday.",
#     "expires": date.today() + timedelta(days=14),   # a notice always needs an expiry date
# }

OWNERSHIP_BY_BODY = [
    {"body": "Student Senate", "example": False,
     "meetings": 'Senate\'s Notion "Meetings" (synced every 15 min, Public rows)',
     "files": "Word files in its Box folder, published as PDF; link pasted into the Notion row",
     "decisions": 'Status in the Senate\'s Notion "Motions"; the motion\'s text is in the linked Word file',
     "roster": "This site (VGMIA); the Senate's Notion gets a read-only copy for attendance",
     "issues": 'Senate\'s Notion "Issues", Public rows only (not built)'},
    {"body": "Executive Board", "example": True,
     "meetings": "Entered on this site by its Secretary: number, date, time, place, two Box links",
     "files": "Word files in its Box folder, published as PDF; link pasted on this site",
     "decisions": "In its minutes (a file)",
     "roster": "This site (VP for Rules and Special Projects)",
     "issues": "Not tracked publicly"},
    {"body": "Graduate Council", "example": True,
     "meetings": "None: files in its Box folder only",
     "files": "Its Box folder",
     "decisions": "In its minutes (a file)",
     "roster": "This site, once a roster officer is named",
     "issues": "Not tracked publicly"},
    {"body": "Undergraduate Council and Class Councils", "example": True,
     "meetings": "None: files in its Box folder only",
     "files": "Its Box folder",
     "decisions": "In its minutes (a file)",
     "roster": "This site, once a roster officer is named",
     "issues": "Not tracked publicly"},
    {"body": "Judicial Board", "example": True,
     "meetings": "None: files in its Box folder only",
     "files": "Public rulings in its Box folder; cases are confidential",
     "decisions": "In its rulings (files)",
     "roster": "This site, once a roster officer is named",
     "issues": "Not applicable"},
]

OWNERSHIP_SHARED = [
    {"what": "Photo, bio, pronouns, office hours", "lives_in": 'This site, only if the member ticks "Public profile"', "who_edits": "Each member, or their roster officer", "how_site_gets_it": "Native; removed at once if consent is withdrawn", "native": True},
    {"what": "Contact routes", "lives_in": "This site (a role inbox per seat)", "who_edits": "Each body's roster officer", "how_site_gets_it": "Native; never a personal address", "native": True},
    {"what": "Budget figures", "lives_in": "Business Operations and Union finance; printed on E-Board agendas", "who_edits": "E-Board Business Operations", "how_site_gets_it": "Link to the agenda in Box. Never retyped.", "native": False},
    {"what": 'Start pages, funding steps, "Run for office or start a petition"', "lives_in": "This site", "who_edits": "WTG chair, with a named page owner and a review date", "how_site_gets_it": "Native (Wagtail)", "native": True},
    {"what": 'Glossary, "How the Union works", topic router', "lives_in": "This site", "who_edits": "WTG chair", "how_site_gets_it": "Native (Wagtail)", "native": True},
    {"what": "Site notices", "lives_in": "This site, with a required expiry date", "who_edits": "WTG chair", "how_site_gets_it": "Native (Wagtail)", "native": True},
    {"what": "Non-meeting events", "lives_in": "This site (EventPage)", "who_edits": "Event organiser", "how_site_gets_it": "Native (Wagtail). Meetings never get EventPages.", "native": True},
    {"what": "Announcements", "lives_in": "Discord", "who_edits": "Anyone with posting rights", "how_site_gets_it": "Link only", "native": False},
    {"what": "Senate attendance, contacts (CRM), internal notes", "lives_in": "The Senate's Notion", "who_edits": "Senate officers", "how_site_gets_it": "Never shown on the site", "native": False},
]

RECORDS_STANDARD = [
    {"text": "Every body publishes its agendas, draft and approved minutes, motion texts and bylaws in its public Box folder. The Executive Board also publishes its budget and allocation records, which the Constitution makes public.", "cite": "Art. VII §2"},
    {"text": "Agendas are in the folder 24 hours before the meeting. Minutes (draft or approved) are there within 14 days."},
    {"text": "Files are PDFs exported from Word with accessibility tags (File, Save As, PDF), never printed to PDF or scanned. Headings use Word's heading styles, and images have alt text."},
    {"text": "Files are named <code>YYYY-MM-DD &lt;Body&gt; &lt;Term&gt; #&lt;nn&gt; &lt;Agenda|Minutes|Motion - Title&gt;.pdf</code>, and corrections use Upload New Version so links never break."},
    {"text": "Each body names a records officer (normally its Secretary) who answers for these deadlines. This site's officer health page shows every body's standing."},
    {"text": "The Judicial Board publishes its rulings on what the Constitution means. Its conduct and rights cases are confidential.", "draft": "Judicial Board bylaws"},
]

# --------------------------------------------------------------------------
# Meetings (Senate: projection of the Senate's Notion; E-Board: entered on this site)
# --------------------------------------------------------------------------

MEETINGS = [
    {
        "body": "senate",
        "body_name": "Student Senate",
        "term_slug": "57",
        "term_label": "57th Student Senate",
        "number": 12,
        "document_name": "2026-07-30 Senate 57 #12 Agenda.pdf",
        "starts": datetime(2026, 7, 30, 20, 0, tzinfo=ET),
        "location": "Webex",
        "remote": True,
        "agenda_url": None,
        "minutes_url": None,
        "public": True,
        "voting_listed": 19,
        "quorum": 13,
        "nonvoting": 10,
        "seats_constitution": 29,
        "seats_cite": "Art. VII §1",
        "agenda_src": AGENDA_SRC["senate"],
        "sections": [
            {"title": "Bookkeeping", "plain": "Opening business, including a statement that the meeting is recorded by The Polytechnic.", "items": []},
            {"title": "Invitation to Speak and Press & Visitor Q/A", "plain": "Anyone can speak or ask questions here.", "draft": "Senate bylaws or rules", "items": []},
            {"title": "Grand Marshal Report", "plain": "An update from the Grand Marshal, the Union's chief spokesperson, who runs Senate meetings.", "cite": "Art. IV §1", "items": []},
            {
                "title": "Committee Reports",
                "plain": "Each Senate committee tells the Senate what it has been working on.",
                "items": [
                    {"title": "Academic Affairs", "who": "Zach Nobles '27", "type": "report"},
                    {"title": "Community Relations", "who": "Mia Stryhalaleck '28", "type": "report"},
                    {"title": "Elections Commission", "who": "Lauren Antao '28", "type": "report"},
                    {"title": "Facilities and Services", "who": "Charlie Fowle '29", "type": "report"},
                    {"title": "Residential Living and Dining", "who": "Shruthi Anandraman '28", "type": "report"},
                    {"title": "Rules and Administration", "who": "Griffin Oliver '27", "type": "report"},
                    {"title": "Student Life", "who": "Stanley Goodwin '30G", "type": "report"},
                    {"title": "Senate Communications and Engagement", "who": "Emily Lin '29", "type": "report"},
                    {"title": "Web Technologies Group", "who": "Aaron Niyazov '28", "type": "report"},
                    {"title": "Union Annual Report", "who": "Samson Kempiak '28", "type": "report"},
                ],
            },
            {
                "title": "Peer Body & Officer Reports",
                "plain": "Updates from other Union bodies and from Senate officers.",
                "items": [
                    {"title": "VGM External Affairs", "who": "Ryan Kilgore '27", "type": "report"},
                    {"title": "VGM Internal Affairs", "who": "Griffin Oliver '27", "type": "report"},
                    {"title": "Executive Board", "who": "Cee Ray '27", "type": "report"},
                    {"title": "Graduate Council", "who": "Melissa Flores 'G", "type": "report"},
                    {"title": "Undergraduate Council", "who": "Nick Castiglione '28", "type": "report"},
                    {"title": "Interfraternity Council", "who": None, "type": "report"},
                    {"title": "Panhellenic Council", "who": None, "type": "report"},
                    {"title": "Multicultural Sorority and Fraternity Council", "who": None, "type": "report"},
                    {"title": "Senate Treasurer", "who": "Cee Ray '27", "type": "report"},
                    {"title": "Secretary", "who": "Selena Tang '29", "type": "report"},
                    {"title": "Parliamentarian", "who": "Sasha Notkin '28", "type": "report"},
                ],
            },
            {"title": "Special Orders", "plain": "Items the Senate has scheduled for a set time.", "items": []},
            {"title": "Old Business", "plain": "Items carried over from earlier meetings.", "items": []},
            {"title": "New Business", "plain": "New items for the Senate to discuss or vote on.", "items": []},
            {"title": "Invitation to Speak and Press & Visitor Q/A", "plain": "Anyone can speak or ask questions again before the meeting ends.", "draft": "Senate bylaws or rules", "items": []},
        ],
    },
    {
        "body": "eboard",
        "body_name": "Executive Board",
        "term_slug": "fy27",
        "term_label": "2026–27 Executive Board (FY27)",
        "number": 1,
        "document_name": "2026-08-25 EBoard FY27 #01 Agenda.pdf",
        "starts": datetime(2026, 8, 25, 19, 0, tzinfo=ET),
        "location": "RU 3202",
        "remote": False,
        "agenda_url": None,
        "minutes_url": None,
        "public": True,
        "voting_listed": 12,
        "quorum": 8,
        "nonvoting": 7,
        "seats_constitution": "15 to 20",
        "seats_cite": "Art. VII §2",
        "agenda_src": AGENDA_SRC["eboard"],
        "sections": [
            {"title": "Approval of Minutes", "plain": "The board votes to accept the written record of its last meeting.", "items": []},
            {
                "title": "Reports",
                "plain": "Officers, committees and peer bodies update the board.",
                "items": [
                    {"title": "President", "who": "Kate Goldstein '26 '27G", "type": "report"},
                    {"title": "VP Board Operations", "who": "Gavin Finn '28", "type": "report"},
                    {"title": "VP Club Relations", "who": "Jesse Kim '26 '27G", "type": "report"},
                    {"title": "VP Rules and Special Projects", "who": "Blaine Rosenberg '28", "type": "report"},
                    {"title": "Director's Report", "who": "Dr. Charlie Potts, Union Director, professional staff", "type": "report"},
                    {"title": "Student Senate", "who": "Cee Ray '27", "type": "report"},
                    {"title": "Undergraduate Council", "who": None, "type": "report"},
                    {"title": "Graduate Council", "who": "Joydip Paul '29G", "type": "report"},
                    {"title": "Committee: Business Operations", "who": "Grey Smith '27", "type": "report"},
                    {"title": "Committee: Club Operations", "who": "Elijah Pulga '29", "type": "report"},
                    {"title": "Committee: Marketing & Strategy", "who": None, "type": "report"},
                    {"title": "Committee: Executive Communication", "who": None, "type": "report"},
                    {"title": "Committee: Multicultural Leadership Council", "who": "Mariam Toure '28", "type": "report"},
                    {"title": "Committee: Union Annual Report", "who": "Ava Cintula '29", "type": "report"},
                    {"title": "Committee: Union Programming and Activities Committee", "who": "Lilu Kaufman '26", "type": "report"},
                ],
            },
            {
                "title": "Proposals",
                "plain": "Requests the board votes on.",
                "items": [
                    {"title": "Special Ballroom Request – Society of Women Engineers", "who": None, "type": "proposal", "plain": "Request to book the Union Ballroom"},
                    {"title": "Special Ballroom Request – RPI Admissions", "who": None, "type": "proposal", "plain": "Request to book the Union Ballroom"},
                ],
            },
            {"title": "Business", "plain": "Other items for discussion.", "items": [{"title": "Rally Week Discussion", "who": None, "type": "discussion"}]},
            {"title": "Invitation to Speak", "plain": "Anyone can speak.", "draft": "E-Board bylaws", "items": []},
            {"title": "Press & Visitor Q/A", "plain": "Press and visitors can ask questions.", "draft": "E-Board bylaws", "items": []},
        ],
    },
]

STATUS_LABELS = {
    "passed": "Passed",
    "failed": "Didn't pass",
    "waiting": "Waiting on a vote",
    "done": "Done: here's what changed",
}

# Decisions are Senate motions only: the projection of the Senate's Notion
# Motions table.  The motion's text stays in the linked Word file.  Every row
# below is made up.
SAMPLE_DECISIONS = [
    {"body": "Student Senate", "date": date(2026, 10, 14), "summary": "Asks the Institute to extend library hours during finals", "status": "passed", "sample": True,
     "motion_file": MOCK_BOX + "s/sample-motion-library-hours", "motion_file_name": "2026-10-14 Senate 57 #15 Motion - Library hours during finals.pdf"},
    {"body": "Student Senate", "date": date(2026, 10, 14), "summary": "Asks RPI Dining to publish weekend hours a semester ahead", "status": "waiting", "sample": True,
     "motion_file": MOCK_BOX + "s/sample-motion-dining-hours", "motion_file_name": "2026-10-14 Senate 57 #15 Motion - Dining hours published ahead.pdf"},
    {"body": "Student Senate", "date": date(2026, 9, 23), "summary": "Adds the Webex link and full date to every Senate meeting notice", "status": "done", "sample": True,
     "motion_file": MOCK_BOX + "s/sample-motion-webex-notices", "motion_file_name": "2026-09-23 Senate 57 #14 Motion - Webex link on notices.pdf"},
]

# --------------------------------------------------------------------------
# Budget: a quotation from one agenda, never a maintained figure
# --------------------------------------------------------------------------

BUDGET = {
    "as_of": date(2026, 8, 25),
    "source": "Executive Board Agenda 01, 25 Aug 2026",
    "funds": [
        {"name": "Club Contingencies", "initial": 100000, "current": 100000, "plain": "Extra money clubs can request during the year.", "draft": "E-Board bylaws"},
        {"name": "Travel Contingencies", "initial": 60000, "current": 60000, "plain": "Money clubs can request for travel.", "draft": "E-Board bylaws"},
        {"name": "Facilities", "initial": 166150, "current": 166150, "plain": "Money for Union facilities."},
        {"name": "Facilities Reserves", "initial": None, "current": 126635.47, "plain": "Savings held for facilities."},
    ],
}

BUDGET_RULES = [
    {"text": "The Executive Board prepares and approves the Union budget, and hands out Union money.", "cite": "Art. VII §2"},
    {"text": "The budget and the records of all extra spending and allocations are public documents.", "cite": "Art. VII §2"},
    {"text": "No Union money can be spent without a requisition from the Executive Board or its authorised agent.", "cite": "Art. XIV"},
]

# --------------------------------------------------------------------------
# Seats (projection of Notion "Seats" + current-term "Assignments")
# --------------------------------------------------------------------------

REPS_META = {
    "2027": {"pill": "'27", "title": "Class of 2027", "h1": "Class of 2027: your representatives", "kind": "class"},
    "2028": {"pill": "'28", "title": "Class of 2028", "h1": "Class of 2028: your representatives", "kind": "class"},
    "2029": {"pill": "'29", "title": "Class of 2029", "h1": "Class of 2029: your representatives", "kind": "class"},
    "2030": {"pill": "'30", "title": "Class of 2030", "h1": "Class of 2030: your representatives", "kind": "class"},
    "graduate": {"pill": "Grad", "title": "Graduate students", "h1": "Graduate students: your representatives", "kind": "graduate"},
    "independent": {"pill": "Independent", "title": "Independent students", "h1": "Independent students: your representatives", "kind": "independent"},
    "fsl": {"pill": "Fraternity & Sorority Life", "title": "Fraternity and Sorority Life (FSL)", "h1": "Fraternity and Sorority Life (FSL): your representatives", "kind": "fsl"},
    "clubs": {"pill": "Clubs", "title": "Clubs and organizations", "h1": "Clubs and organizations: your representatives", "kind": "clubs"},
}

SENATE_AGENDA = AGENDA_SRC["senate"]
EBOARD_AGENDA = AGENDA_SRC["eboard"]


def _seat(body, seat, constituency, holder, group, fill_rule, also=None, status=None, role=None, **extra):
    if status is None:
        status = "filled" if holder else "vacant"
    return {
        "body": body,
        "seat": seat,
        "constituency": constituency,
        "holder": holder,
        "also": also,
        "status": status,
        "fill_rule": fill_rule,
        "role": role,  # key used by logic.seat_for(); content looks holders up by it
        "inbox": None,  # no role inboxes exist yet; never invent one
        "group": group,
        **extra,
    }


def _build_seats():
    seats = []
    add = seats.append

    # --- Student Senate -----------------------------------------------
    add(_seat("senate", "Grand Marshal", "everyone", "Jordan Krishnayah '28", "Grand Marshal", "gm", role="gm", kind="presiding"))

    grad = [("Batuhan Yalcin", None), ("Alexander Neimeth", None), ("Paul Lea", None), ("Stanley Goodwin '30G", "SLC chair")]
    for name, also in grad:
        add(_seat("senate", "Graduate Senator", "graduate", name, "Graduate Senators", "elected_appointed", also))
    for _ in range(3):
        add(_seat("senate", "Graduate Senator", "graduate", None, "Graduate Senators", "elected_appointed"))

    classes = {
        "2027": [("Ghea Chaw", None), ("Griffin Oliver", "VGMIA, RAC chair"), ("Rachel Schneider", None), ("Adam Choi", None)],
        "2028": [("Aaron Nam", None), ("Nick Castiglione", None), (None, None), (None, None)],
        "2029": [("Jaewon Yoon", None), ("Melissa DeLuise", None), ("Aarushi Kumar", None), ("Riley Sanders", None)],
    }
    for year, people in classes.items():
        for name, also in people:
            label = f"{name} '{year[2:]}" if name else None
            add(_seat("senate", f"Class of {year} Senator", year, label, f"Class of {year} Senators", "class_senator", also))
    for _ in range(4):
        add(_seat("senate", "Class of 2030 Senator", "2030", None, "Class of 2030 Senators", "class_senator", status="elect_fall"))

    for name, yr, also in [("Shruthi Anandraman", "'28", "RLDC chair"), ("Ryan Kilgore", "'27", "VGMEA"), ("Ashley Wong", "'27", None)]:
        add(_seat("senate", "Independent Senator", "independent", f"{name} {yr}", "Independent Senators", "elected_appointed", also))
    for name in ["Mischa Fedak", "Andrew Donilon", "Radhika Manvar"]:
        add(_seat("senate", "Fraternity and Sorority Life (FSL) Senator", "fsl", name, "Fraternity and Sorority Life (FSL) Senators", "elected_appointed"))

    # --- Executive Board ----------------------------------------------
    add(_seat("eboard", "President of the Union", "everyone", "Kate Goldstein '26 '27G", "President of the Union", "pu", role="pu", kind="presiding"))
    for role, name, title in [("vp_board_ops", "Gavin Finn '28", "VP for Board Operations"), ("vp_club_relations", "Jesse Kim '26 '27G", "VP for Club Relations"), ("vp_rules", "Blaine Rosenberg '28", "VP for Rules and Special Projects")]:
        add(_seat("eboard", title, "officers", name, "Officers", None, role=role, kind="officer", draft="E-Board bylaws"))

    for const, name, also in [("graduate", None, None), ("2027", "Jacob Bloecher", None), ("2028", "Mariam Toure", "MLC chair"), ("2029", "Ava Cintula", "UAR chair"), ("2030", None, None)]:
        label = "Graduate Class Representative" if const == "graduate" else f"Class of {const} Representative"
        add(_seat("eboard", label, const, name, "Class Representatives", "eb_appointed", also, kind="class_rep"))

    clubs = [("Grey Smith '27", "Business Ops chair"), ("Elijah Pulga '29", "Club Ops chair"), ("Samson Kempiak '28", None), ("Valerie Rosa-Sanclemente '28", None), (None, None), (None, None), (None, None)]
    for name, also in clubs:
        add(_seat("eboard", "Club & Organization Representative", "clubs", name, "Club & Organization Representatives", "eb_appointed", also, kind="clubs"))

    for name in ["Ahmed Shoaib '29", "Aaron Brown '29", "Sumaya Moumita '28", "William Liu '29", None]:
        add(_seat("eboard", "Member-at-Large", "everyone", name, "Members-at-Large", "eb_appointed", kind="at_large"))

    add(_seat("eboard", "Senate–E-Board Liaison", "peer", "Cee Ray '27", "Council and Senate seats", "eb_peer", role="eb_senate_liaison", kind="peer", chosen_by="the Senate"))
    add(_seat("eboard", "Graduate Council representative", "peer", "Joydip Paul '29G", "Council and Senate seats", "eb_peer", role="eb_grad_council_rep", kind="peer", chosen_by="the Graduate Council"))
    add(_seat("eboard", "Undergraduate Council representative", "peer", None, "Council and Senate seats", "eb_peer", kind="peer", chosen_by="the Undergraduate Council"))
    return seats


SEATS = _build_seats()

# --------------------------------------------------------------------------
# Roles that are not voting seats (projection of Notion "Assignments")
#
# Chairs, officers and the like.  Content on this site refers to a person
# only by role key (see ``logic.seat_for``), so a change in Notion is the
# only edit needed.  ``unlisted=True`` means the roster has no holder yet.
# --------------------------------------------------------------------------

def _role(role, title, holder, acting=False, unlisted=False):
    return {"role": role, "title": title, "holder": holder, "acting": acting, "unlisted": unlisted, "inbox": None}


ROLE_ASSIGNMENTS = [
    _role("aac_chair", "AAC chair", "Zach Nobles '27"),
    _role("crc_chair", "CRC chair", "Mia Stryhalaleck '28"),
    _role("elections_chair", "Elections Commission chair", "Lauren Antao '28", acting=True),
    _role("fsc_chair", "FSC chair", "Charlie Fowle '29"),
    _role("rldc_chair", "RLDC chair", "Shruthi Anandraman '28"),
    _role("rac_chair", "RAC chair", "Griffin Oliver '27"),
    _role("slc_chair", "SLC chair", "Stanley Goodwin '30G"),
    _role("scec_chair", "SCEC chair", "Emily Lin '29"),
    _role("wtg_chair", "WTG chair", "Aaron Niyazov '28"),
    _role("uar_chair", "UAR chair", "Samson Kempiak '28", acting=True),
    _role("eb_business_ops_chair", "Business Operations chair", "Grey Smith '27"),
    _role("eb_club_ops_chair", "Club Operations chair", "Elijah Pulga '29"),
    _role("eb_marketing_chair", "Marketing & Strategy chair", None),
    _role("eb_exec_comm_chair", "Executive Communication chair", None),
    _role("eb_mlc_chair", "MLC chair", "Mariam Toure '28"),
    _role("eb_uar_chair", "UAR chair", "Ava Cintula '29"),
    _role("eb_upac_chair", "UPAC chair", "Lilu Kaufman '26"),
    _role("parliamentarian", "Parliamentarian", "Sasha Notkin '28"),
    _role("secretary", "Secretary", "Selena Tang '29"),
    _role("judicial_chair", "Judicial Board Chairperson", None, unlisted=True),
    _role("grad_council", "Graduate Council", None, unlisted=True),
    _role("class_council", "Class Council", None, unlisted=True),
]
ROLE_BY_KEY = {r["role"]: r for r in ROLE_ASSIGNMENTS}


SENATE_NONVOTING = [
    {"title": "Senate Treasurer and Senate–E-Board Liaison", "role": "eb_senate_liaison"},
    {"title": "Parliamentarian", "role": "parliamentarian"},
    {"title": "Secretary", "role": "secretary"},
]
SENATE_NONVOTING_NOTE = "These titles are set by Senate bylaws, not the Constitution."

SEAT_SOURCE_NOTE = "Prototype data: Senate agenda 30 Jul 2026 / E-Board agenda 25 Aug 2026."

RECONCILIATION = {
    "text": (
        "The Senate agenda lists these six under one heading, 'Greek & Independent Senators'. "
        "Under the Union Constitution they are two separate groups of three seats: Independent "
        "Senators must not be in a fraternity or sorority, and FSL Senators must be. The "
        "Constitution is authoritative, so this site shows them as two groups. All six seats are filled."
    ),
    "cite": "Art. VII §1; Art. VIII §5",
}

EBOARD_ROSTER_NOTE = "The E-Board membership block on the agenda is headed 2025-2026 although the agenda is for 2026–27. Roster may be out of date."

FILL_RULES = {
    "gm": {"key": "gm", "text": "Elected by all students in the spring. Needs at least 40% of the vote. If the post falls vacant, the Senate appoints a replacement by a 2/3 vote within two weeks.", "cite": "Art. VIII §1, §10; Art. XI §1"},
    "pu": {"key": "pu", "text": "Elected by all students in the spring. Needs at least 40% of the vote. If the post falls vacant, the Executive Board appoints a replacement within two weeks and the Senate confirms by 2/3.", "cite": "Art. VIII §1, §10; Art. XI §2"},
    "class_senator": {"key": "class_senator", "text": "Elected by the class (first-years in the fall, other classes in the spring). If a seat falls vacant, the Class Council appoints someone. If 20% of the class signs a petition within two weeks of the announcement, there must be a special election instead.", "cite": "Art. VIII §1, §3; Art. XI §5, §6"},
    "elected_appointed": {"key": "elected_appointed", "text": "Elected in the spring. A vacant seat can be filled by appointment. If 20% of the constituency signs a petition within two weeks of the announcement, there must be a special election instead.", "cite": "Art. VIII §1, §9; Art. XI §5", "draft": "Senate bylaws or rules", "draft_note": "who makes the appointment"},
    "eb_appointed": {"key": "eb_appointed", "text": "Appointed by the President of the Union and approved by 2/3 of the Senate. Required seats are filled within three weeks after the spring elections; the first-year seat within three weeks after the fall elections; optional seats by the end of the fourth week of the fall semester.", "cite": "Art. VII §2; Art. VIII §12", "draft": "E-Board bylaws", "draft_note": "how to apply"},
    "eb_peer": {"key": "eb_peer", "text": "Chosen by the body it represents (the Senate, Graduate Council or Undergraduate Council) within three weeks after that body's elections.", "cite": "Art. VII §2; Art. VIII §12"},
}

# --------------------------------------------------------------------------
# Committees (set by each body's bylaws; the Constitution lists none)
# --------------------------------------------------------------------------

COMMITTEES = [
    {"code": "AAC", "name": "Academic Affairs", "chair_role": "aac_chair", "handles": "Classes, advising and academic policy."},
    {"code": "CRC", "name": "Community Relations", "chair_role": "crc_chair", "handles": "Relations with the Troy community and off-campus life."},
    {"code": "", "name": "Elections Commission", "chair_role": "elections_chair", "handles": "Student elections."},
    {"code": "FSC", "name": "Facilities and Services", "chair_role": "fsc_chair", "handles": "Buildings, spaces and campus services."},
    {"code": "RLDC", "name": "Residential Living and Dining", "chair_role": "rldc_chair", "handles": "Housing, residence halls and dining."},
    {"code": "RAC", "name": "Rules and Administration", "chair_role": "rac_chair", "handles": "The Senate's own rules and administration."},
    {"code": "SLC", "name": "Student Life", "chair_role": "slc_chair", "handles": "Wellbeing, campus life and student services."},
    {"code": "SCEC", "name": "Senate Communications and Engagement", "chair_role": "scec_chair", "handles": "How the Senate talks with students."},
    {"code": "WTG", "name": "Web Technologies Group", "chair_role": "wtg_chair", "handles": "Union websites and web tools."},
    {"code": "UAR", "name": "Union Annual Report", "chair_role": "uar_chair", "handles": "The yearly report on the Union."},
]
COMMITTEE_BY_NAME = {c["name"]: c for c in COMMITTEES}  # name and remit only; chairs come from the roster

EB_COMMITTEES = [
    {"name": "Business Operations", "chair_role": "eb_business_ops_chair", "handles": "Union budget and money matters."},
    {"name": "Club Operations", "chair_role": "eb_club_ops_chair", "handles": "Clubs and organizations."},
    {"name": "Marketing & Strategy", "chair_role": "eb_marketing_chair", "handles": "Promotion and planning."},
    {"name": "Executive Communication", "chair_role": "eb_exec_comm_chair", "handles": "Communication from the Executive Board."},
    {"name": "Multicultural Leadership Council (MLC)", "chair_role": "eb_mlc_chair", "handles": "Multicultural leadership."},
    {"name": "Union Annual Report (UAR)", "chair_role": "eb_uar_chair", "handles": "The yearly report on the Union."},
    {"name": "Union Programming and Activities Committee (UPAC)", "chair_role": "eb_upac_chair", "handles": "Union programs and activities."},
]
GM_EX_OFFICIO = {"text": "The Grand Marshal is an automatic (ex-officio) member of every Senate committee.", "cite": "Art. IV §1"}

# --------------------------------------------------------------------------
# Topic router (Wagtail-owned)
# --------------------------------------------------------------------------

# ``owner_seat`` is a roster role key.  The chair, title and inbox are looked up
# from the roster (logic.seat_for), never typed here.
TOPICS = [
    {"slug": "dining", "question": "Problem with dining or meal plans?", "examples": ["meal swipes", "dining hall hours", "dietary needs"],
     "owner_label": "Residential Living and Dining Committee (RLDC)", "owner_body": "Student Senate", "owner_seat": "rldc_chair", "committee": "Residential Living and Dining",
     "can_do": "RLDC brings student concerns about dining to the Senate and to the offices that run dining. It can ask questions, collect student input and recommend changes. It does not run dining services.",
     "outside_sg": "RPI's dining service runs meal plans and dining halls; RLDC raises student concerns with them."},
    {"slug": "housing", "question": "Problem with your residence hall or housing?", "examples": ["room problems", "roommates", "residence hall rules"],
     "owner_label": "Residential Living and Dining Committee (RLDC)", "owner_body": "Student Senate", "owner_seat": "rldc_chair", "committee": "Residential Living and Dining",
     "can_do": "RLDC brings student concerns about residence halls to the Senate and to Residence Life. It can ask questions, collect student input and recommend changes. It does not run housing.",
     "outside_sg": "Residence Life runs housing day to day."},
    {"slug": "buildings", "question": "Broken, inaccessible, or unsafe building or space?", "examples": ["broken elevator", "accessibility", "lighting"],
     "owner_label": "Facilities and Services Committee (FSC)", "owner_body": "Student Senate", "owner_seat": "fsc_chair", "committee": "Facilities and Services",
     "can_do": "FSC brings student concerns about buildings and spaces to the Senate and to campus facilities staff. It can collect reports and recommend fixes. It does not do repairs.",
     "outside_sg": "For urgent repairs contact RPI Facilities directly."},
    {"slug": "academics", "question": "Concern about classes, advising, or academic policy?", "examples": ["course scheduling", "advising", "grading policy"],
     "owner_label": "Academic Affairs Committee (AAC)", "owner_body": "Student Senate", "owner_seat": "aac_chair", "committee": "Academic Affairs",
     "can_do": "AAC brings student concerns about classes and academic policy to the Senate and to Institute offices. It can collect input and recommend changes. It does not set academic policy."},
    {"slug": "student-life", "question": "Wellbeing, campus life, or student services?", "examples": ["student services", "campus events", "wellbeing"],
     "owner_label": "Student Life Committee (SLC)", "owner_body": "Student Senate", "owner_seat": "slc_chair", "committee": "Student Life",
     "can_do": "SLC brings student concerns about campus life and services to the Senate. It can collect input and recommend changes. It does not run student services."},
    {"slug": "troy", "question": "Off-campus or Troy community issue?", "examples": ["off-campus housing", "city services", "neighbors"],
     "owner_label": "Community Relations Committee (CRC)", "owner_body": "Student Senate", "owner_seat": "crc_chair", "committee": "Community Relations",
     "can_do": "CRC brings student concerns about the Troy community to the Senate. It can collect input and recommend next steps. It does not govern the city."},
    {"slug": "clubs", "question": "Club rules, registration, or club money?", "examples": ["club registration", "club classification", "funding"],
     "owner_label": "Executive Board", "owner_body": "Executive Board", "owner_seat": "vp_club_relations",
     "route_draft": "E-Board bylaws",
     "fact": {"text": "The Executive Board decides how clubs are classified and hands out Union money.", "cite": "Art. VII §2"}},
    {"slug": "grad", "question": "Grad-specific: stipends, grad housing, TA workload?", "examples": ["stipends", "graduate housing", "TA workload"],
     "owner_label": "Graduate Council and Graduate Senators", "owner_body": "Graduate Council", "owner_seat": "grad_council",
     "fact": {"text": "The Graduate Council is the Union's advocacy body for graduate students. Its voting members are the 7 Graduate Senators plus at least 5 at-large members.", "cite": "Art. VII §4"}},
    {"slug": "class", "question": "About your class: class events or class dues?", "examples": ["class events", "class dues", "class council"],
     "owner_label": "Your Class Council (undergraduates) or the Graduate Council (graduate class dues)", "owner_body": "Class Councils", "owner_seat": "class_council",
     "fact": {"text": "Each class elects a Class Council. It recommends how class dues are spent, and the Undergraduate Council must approve that spending by majority.", "cite": "Art. VII §5"}},
    {"slug": "rights", "question": "Think a Union body broke the Constitution, or your student rights were violated?", "examples": ["student rights", "constitution question", "conduct"],
     "owner_label": "Judicial Board", "owner_body": "Judicial Board", "owner_seat": "judicial_chair",
     "fact": {"text": "The Judicial Board is the Union's student court. It hears charges that the Union Constitution, the Rensselaer Student Bill of Rights, or student conduct rules were violated, and it can rule Senate, Executive Board or council decisions unconstitutional.", "cite": "Art. VII §3"}},
    {"slug": "elections", "question": "Question about elections?", "examples": ["running for office", "voting", "election dates"],
     "owner_label": "Elections Commission", "owner_body": "Student Senate", "owner_seat": "elections_chair", "committee": "Elections Commission",
     "can_do": "The Elections Commission runs Senate elections. It can answer questions about how elections work and who may run.",
     "can_do_draft": "Senate election rules"},
    {"slug": "website", "question": "Problem with this website?", "examples": ["broken link", "wrong information", "accessibility"],
     "owner_label": "Web Technologies Group (WTG)", "owner_body": "Student Senate", "owner_seat": "wtg_chair", "committee": "Web Technologies Group",
     "can_do": "WTG looks after Union websites. It can fix broken pages and wrong information on this site."},
    {"slug": "other", "question": "Something else", "examples": ["anything not listed"],
     "owner_label": "Student Senate (Grand Marshal's office)", "owner_body": "Student Senate", "owner_seat": "gm",
     "fact": {"text": "The Grand Marshal is the leader and chief spokesperson for the whole Union.", "cite": "Art. IV §1"}},
]
TOPIC_BY_SLUG = {t["slug"]: t for t in TOPICS}

SAFETY_LINE = "If anyone is in danger, contact RPI Public Safety now."

# --------------------------------------------------------------------------
# Glossary
# --------------------------------------------------------------------------

GLOSSARY = [
    {"term": "Rensselaer Union", "text": "Every enrolled RPI student, graduate or undergraduate, who has paid the Union Activity Fee, and the organisation they form.", "cite": "Art. I; Art. II"},
    {"term": "Union Activity Fee", "text": "The fee that makes you a Union member. The Senate sets the amount by a 2/3 vote of all its voting seats.", "cite": "Art. II; Art. VII §1"},
    {"term": "Student Senate", "body_id": "senate", "text": "The Union's main lawmaking body. It has 29 voting seats, passes its own rules, sets the Activity Fee, and approves many appointments.", "cite": "Art. VII §1"},
    {"term": "Executive Board (E-Board)", "body_id": "eboard", "text": "The Union's budgeting body. It prepares and approves the budget, hands out Union money, and decides how clubs are classified.", "cite": "Art. VII §2"},
    {"term": "Judicial Board", "body_id": "judicial-board", "text": "The Union's student court. It decides cases about student rights and conduct, and it is the only body that can say what the Constitution means.", "cite": "Art. VII §3"},
    {"term": "Graduate Council", "body_id": "graduate-council", "text": "The advocacy body for graduate students: the 7 Graduate Senators plus at least 5 at-large members.", "cite": "Art. VII §4"},
    {"term": "Undergraduate Council", "body_id": "undergraduate-council", "text": "The advocacy body for undergraduates. Its voting members are the President and Vice President of each of the four Class Councils, and it oversees those councils.", "cite": "Art. VII §5"},
    {"term": "Class Council", "text": "The elected council for one undergraduate class: the Class President, the Vice President, at least 8 Representatives and the class's 4 Senators. It recommends how class dues are spent.", "cite": "Art. VII §5"},
    {"term": "Grand Marshal", "text": "The Union's leader and chief spokesperson, elected by all students. Runs Senate meetings and votes only to break a tie. An RPI-specific title.", "cite": "Art. IV §1"},
    {"term": "President of the Union", "text": "Runs the Executive Board and appoints most of its members, with 2/3 Senate approval. Votes only to break a tie.", "cite": "Art. IV §2; Art. VII §2"},
    {"term": "Director of the Union", "text": "A paid staff member who runs Union activities and funds day to day. Advises the Executive Board but cannot veto it.", "cite": "Art. V"},
    {"term": "Senate Treasurer", "text": "A Senate officer listed on the agendas. Not the same as the 'Treasurer' in the Constitution, which is RPI's own Treasurer, who holds the Union's money.", "cite": "Art. VI", "draft": "Senate bylaws or rules"},
    {"term": "Class dues", "text": "Money collected from the members of a class and spent through that class's council.", "cite": "Art. VII §4, §5"},
    {"term": "Referendum", "text": "A vote of all affected students on a question. It is binding if a majority votes yes and at least 20% of those students vote.", "cite": "Art. XII §1, §3, §4"},
    {"term": "Petition", "text": "A signed request from students. Depending on the goal it needs 10%, 20% or 50% of the students concerned.", "cite": "Art. X; Art. XI §5; Art. XII §1"},
    {"term": "Recall (removal election)", "text": "A student vote to remove an elected officer or senator before the term ends.", "cite": "Art. X §1, §2"},
    {"term": "Ex-officio", "text": "Holding a seat automatically because of another office you hold."},
    {"term": "Plurality", "text": "The most votes, even if that is less than half."},
    {"term": "Quorum", "text": "The minimum number of voting members who must be present for a meeting to act. The Constitution leaves this to each body's own rules; the latest Senate agenda lists 13.", "draft": "Senate bylaws or rules", "source": AGENDA_SRC["senate"]},
    {"term": "Bylaws", "text": "A body's own detailed rules, passed under the Constitution. The Senate, Executive Board, Judicial Board, Graduate Council and Undergraduate Council each have them.", "cite": "Art. VII"},
    {"term": "Robert's Rules of Order", "text": "The standard meeting rulebook the Union uses wherever the Constitution and a body's own rules are silent.", "cite": "Art. VII §6"},
    {"term": "Parliamentarian", "text": "The officer who advises a meeting on its rules.", "draft": "Senate bylaws or rules"},
    {"term": "Contingency", "text": "A pool of money clubs can ask the Executive Board for during the year.", "draft": "E-Board bylaws"},
    {"term": "Invitation to Speak", "text": "Time set aside on a meeting's agenda when anyone may speak. Each meeting page says where it falls.", "draft": "Senate bylaws or rules"},
    {"term": "Minutes", "text": "The official written record of a meeting."},
]

# --------------------------------------------------------------------------
# Processes (take_part). [[derived]] becomes the "(derived)" marker.
# --------------------------------------------------------------------------

PROCESSES = [
    {
        "id": "run", "title": "Run for office",
        "lead": "Most Union seats are elected by students. You can run if you're a Union member when the election is held.",
        "who": "Any Union member, as long as you meet RPI's eligibility rules and any extra rules the Senate sets. Grand Marshal, President of the Union and Judicial Board Chairperson need at least one full semester at RPI. Independent Senators must not be in a fraternity or sorority; FSL Senators must be.",
        "needs": "Grand Marshal and President of the Union need at least 40% of the vote. Most other seats go to whoever gets the most votes. A tie means a new election between the tied candidates.",
        "timing": "General elections are in the spring. First-year Senators and the first-year Class Council are elected in the fall. Winners take office within one week of the results.",
        "then": "You serve until the next general election for your seat. Nobody may serve more than two full terms combined as Grand Marshal and/or President of the Union. You can't run for both of those at once, or for two seats on the same council.",
        "not_set": ["How to get your name on the ballot, including any signatures", "Election dates and campaign rules"],
        "not_set_why": "Senate election rules",
        "cite": "Art. IV §6; Art. VIII §1, §3, §4, §5, §8, §10–§13; Art. IX",
    },
    {
        "id": "appointed", "title": "Get appointed instead",
        "lead": "Some seats are appointed rather than elected.",
        "who": "Executive Board class, club and at-large seats: appointed by the President of the Union and approved by 2/3 of the Senate. Judicial Board members: proposed by its Chairperson, then approved by 2/3 of the Judicial Board and 2/3 of the Senate.",
        "needs": "", "timing": "Optional Executive Board seats are filled by the end of the fourth week of the fall semester.", "then": "",
        "not_set": ["How to apply, and who to send it to"], "not_set_why": "E-Board bylaws",
        "cite": "Art. VII §2, §3; Art. VIII §12",
    },
    {
        "id": "referendum", "title": "Make students vote on something (referendum)",
        "lead": "If enough students sign a petition, the Senate must hold a student vote on almost any question.",
        "who": "Any Union member can start one. It can be about anything except changing the Constitution.",
        "needs": "Signatures from at least 10% of all Union members. The Senate can only refuse by a 2/3 vote of all its voting seats, which is 20 of 29 [[derived]]. The Senate can also put a question on the ballot itself by a 2/3 vote.",
        "timing": "The vote is held within 45 days (not counting vacations) or at the next regular election, whichever is sooner, but never less than 14 days after approval and never during exams.",
        "then": "It passes with a majority of votes, but only counts if at least 20% of the affected students vote. Once passed it is binding: the Senate must pass whatever is needed to carry it out, and only another referendum can undo it.",
        "not_set": ["Petition format and where to hand it in", "How signatures are checked", "How many students 10% is right now"], "not_set_why": "Senate bylaws or rules",
        "cite": "Art. XII §1–§4",
    },
    {
        "id": "challenge", "title": "Challenge an appointment to an elected seat",
        "lead": "When an elected seat is filled by appointment instead of election, students can force an election.",
        "who": "Students in the constituency for that seat.",
        "needs": "A petition signed by 20% of that constituency.",
        "timing": "The Senate must receive it within two weeks of the appointment being announced. If students are away from campus, the two weeks start when it is announced to the full campus.",
        "then": "A special election is held for the seat.",
        "not_set": ["Petition format and where to hand it in"], "not_set_why": "Senate bylaws or rules",
        "cite": "Art. XI §5, §6",
    },
    {
        "id": "recall", "title": "Remove an elected officer or senator",
        "lead": "Students can remove the people they elected before their term ends.",
        "who": "", "needs": "", "timing": "", "then": "",
        "table": {
            "caption": "How removal works",
            "head": ["Who", "How it starts", "What removes them"],
            "rows": [
                ["Grand Marshal, President of the Union, Graduate or Undergraduate Council President", "A 2/3 Senate vote, or a petition from 20% of their constituents followed by a Senate majority", "A petition signed by 50% of their constituents, or 2/3 of those voting in a removal election where at least 20% vote"],
                ["An elected senator", "A petition from 20% of their constituents, or a Senate majority", "2/3 of those voting in a removal election where at least 20% vote"],
                ["Any voting senator, for good cause", "The Senate", "2/3 of all Senate voting seats, which is 20 of 29 [[derived]]"],
                ["A Graduate or Class Council member, for good cause", "A majority \"impeachment\" vote at a council meeting; the removal vote is at the next meeting", "2/3 of that council; the member can't vote"],
            ],
        },
        "not_set": ["What counts as 'good cause'", "How removal elections are run"], "not_set_why": "Senate bylaws or rules",
        "cite": "Art. X §1, §2, §5",
    },
    {
        "id": "judicial-board", "title": "Bring a case to the Judicial Board",
        "lead": "The Judicial Board is the Union's student court.",
        "who": "The Constitution says any charge can be referred to it. It does not say who may file.",
        "needs": "A charge that names a violation of the Union Constitution, the Rensselaer Student Bill of Rights, or RPI's rules on student conduct.",
        "timing": "",
        "then": "The Board decides the case. It can rule that a decision of the Senate, Executive Board, Graduate Council, Undergraduate Council or a Class Council is unconstitutional. It is the only body that can interpret the Constitution.",
        "how_to_file": "How to file: not published yet",
        "not_set": ["Who may file and how", "Deadlines, hearings and appeals", "Who currently chairs the Board"], "not_set_why": "Judicial Board bylaws",
        "cite": "Art. VII §3",
    },
    {
        "id": "amend", "title": "Change the Constitution",
        "lead": "Students vote on every change to the Constitution, but the Senate has to propose it first. A petition alone can't amend it.",
        "who": "Ask a senator to propose it, or raise it at a meeting.",
        "who_links": [("Find your senators", "reps_index"), ("Go to a meeting", "meetings")],
        "needs": "2/3 of the Senate, then a majority of students voting in a campus election where at least 20% of eligible students vote.",
        "timing": "The proposal goes to RPI's President one month before the vote; RPI's President may refer it to the Board of Trustees. The exact wording must be published campus-wide at least two weeks before the vote. No votes during exams.",
        "then": "",
        "not_set": [], "not_set_why": "",
        "cite": "Art. XII §1; Art. XIII §1–§4",
    },
]

# --------------------------------------------------------------------------
# About page: the governing bodies
# --------------------------------------------------------------------------

BODIES = [
    {"id": "senate", "term": "Student Senate", "sits": "29 voting seats: 7 Graduate, 4 per undergraduate class, 3 Independent, 3 Fraternity and Sorority Life", "chair": "Grand Marshal", "chair_note": "votes only to break a tie", "cite": "Art. VII §1",
     "leader_role": "gm", "links": [("Raise an issue", "issue_index"), ("Go to a meeting", "meeting:senate/57/12"), ("See who represents you", "reps_index")]},
    {"id": "eboard", "term": "Executive Board (E-Board)", "sits": "15 to 20 voting members: 5 class reps, 5–7 club and organisation reps, 2–5 members-at-large, and one seat each for the Senate, Graduate Council and Undergraduate Council", "chair": "President of the Union", "chair_note": "votes only to break a tie", "cite": "Art. VII §2",
     "leader_role": "pu", "links": [("Get money for your club", "funding"), ("See an Executive Board meeting", "meeting:eboard/fy27/1")]},
    {"id": "judicial-board", "term": "Judicial Board", "sits": "6 voting members and 5 alternates", "chair": "Judicial Board Chairperson", "chair_note": "votes only to break a tie", "cite": "Art. VII §3",
     "leader_role": None, "links": [("Bring a case to the Judicial Board", "take_part#judicial-board")], "roster_unlisted": True, "records_files": True},
    {"id": "graduate-council", "term": "Graduate Council", "sits": "the 7 Graduate Senators and at least 5 at-large members, so at least 12 [[derived]]", "chair": "Graduate Council President", "chair_note": "voting rights set by the Graduate Council's bylaws", "cite": "Art. VII §4",
     "leader_role": None, "links": [("Raise a graduate issue", "issue_topic:grad"), ("Graduate representatives", "reps:graduate")], "roster_unlisted": True, "records_files": True},
    {"id": "undergraduate-council", "term": "Undergraduate Council", "sits": "the President and Vice President of each Class Council, so 8 [[derived]]", "chair": "Undergraduate Council President", "chair_note": "votes only to break a tie", "cite": "Art. VII §5",
     "leader_role": None, "links": [("Raise a class issue", "issue_topic:class")], "roster_unlisted": True, "records_files": True},
    {"id": "class-councils", "term": "Class Councils", "sits": "Class President, Vice President, at least 8 Representatives and the class's 4 Senators", "chair": "Class President", "chair_note": "votes only to break a tie", "cite": "Art. VII §5",
     "leader_role": None, "links": [("Find your class", "reps_index")], "roster_unlisted": True,
     "text": "Each undergraduate class elects its own council. It recommends how class dues are spent and appoints replacements when a Class Senator seat falls vacant."},
]

OFFICERS_TEXT = "The Union has five officers: the Grand Marshal, the President of the Union, the Judicial Board Chairperson, the Graduate Council President and the Undergraduate Council President. They must meet regularly to coordinate."
OFFICER_TERMS = ["Grand Marshal", "President of the Union", "Director of the Union", "Senate Treasurer"]

TERM_ROLLOVER = [
    "Set end dates on last term's assignments.",
    "Set the body's new term as current on this site. Every seat on this site then shows Vacant automatically.",
    "Make sure the four first-year Senate seats show \"To be elected this fall\".",
    "Enter new assignments as results come in.",
    "Check the seat groups still match the Constitution (29 Senate seats, 15–20 E-Board seats). Re-check after any amendment.",
    "Audit who can edit the site admin and the Senate's Notion workspace (at least two owners, on a shared role account). The Senate's Notion copy of the roster updates itself.",
]

_PDF_STEP = "Export the Word agenda as a PDF with accessibility tags (File, Save As, PDF). Never use Print to PDF."
_LINK_STEP = "Set its shared link to \"People with the link\". Otherwise students hit an RPI login."

PUBLISH_STEPS_BY_ADAPTER = [
    {"label": "Student Senate (its Notion)", "steps": [
        _PDF_STEP,
        "Save it in the Senate's Box term folder named <code>2026-10-26 Senate 57 #16 Agenda.pdf</code>.",
        _LINK_STEP,
        "In the Senate's Notion Meetings database, open or duplicate the meeting row, paste the link into Agenda, and tick Public. It appears here within 15 minutes.",
    ]},
    {"label": "Entered on this site (the Executive Board, as an example)", "steps": [
        _PDF_STEP,
        "Save it in the Executive Board's Box term folder named <code>2026-11-03 EBoard FY27 #05 Agenda.pdf</code>.",
        _LINK_STEP,
        "Use Post the next meeting on this site (prefilled from the last meeting) and paste the link. It appears immediately.",
    ]},
    {"label": "Box folder only (Graduate Council, Undergraduate Council, Judicial Board)", "steps": [
        _PDF_STEP,
        "Save it in the body's Box term folder named like <code>2026-11-03 GC 2026-27 #05 Agenda.pdf</code>.",
        _LINK_STEP,
        "Once a month, confirm on this site that the folder is complete.",
    ]},
]

OFFICER_RULES = [
    "To fix a file, use Upload New Version in Box. Don't upload a second copy: the link stays the same and this site follows automatically.",
    "Never retype what's in a Word document (agenda items, motion text, outcomes): link the file.",
    "Export Word documents to PDF with accessibility tags; never Print to PDF.",
    "Budget figures are linked, never retyped.",
    "If something here looks wrong, use the Edit link shown to officers and fix it at the source.",
]

MEETING_FILE_NAMING = "2026-07-30 Senate 57 #12 Agenda.pdf"
