# Prototype spec: Front Door

**Slug:** `front-door`  
**Recommended:** True  
**Thesis:** A task-first site over an honest record. Six plain-language verbs come first, then 'This week', then a reps lookup. The org chart is one level down, each meeting is the unit of record, and no door is built without a real process behind it.

# Prototype: Front Door (`front-door`, recommended)

## 0. Ground rules (read first)

This builds one self-contained prototype inside the existing `lab` app of a Wagtail 7.3 / Django 6.0 site, at `/Users/aaron/src/stugov-site`. Run all commands with `env/bin/python` (not `python`).

**Do not touch these:**
- `lab/urls.py`, `lab/views.py`, `lab/prototypes/__init__.py`.
- Anything under `stugov/`, `home/`, `branches/`, `events/`, `records/`.
- Any model. Create no migrations and add no dependencies.

**Files to create:**
```
lab/prototypes/front_door/__init__.py   # META only
lab/prototypes/front_door/urls.py
lab/prototypes/front_door/views.py
lab/prototypes/front_door/data.py       # all seed facts below, as plain Python
lab/prototypes/front_door/tests.py      # smoke tests
lab/templates/lab/front-door/*.html     # includes _sample.html, _draft.html, _cite.html, _source.html, _box_folder.html
```

**`__init__.py`:**
```python
META = {"name": "Front Door", "thesis": "Task-first: six plain-language verbs, then this week, then your reps. Org chart one level down.", "recommended": True}
```

**How the app is wired:**
- The lab discovers this package automatically and mounts it at `/lab/front-door/`.
- URL namespace is `lab:front_door`, so reverse with `{% url 'lab:front_door:home' %}`.

**Database access:**
- The default dev DB (`data/db.sqlite3`) is EMPTY (0 bytes, no tables).
- Every DB read must be wrapped in `try/except DatabaseError` (`from django.db import DatabaseError`) and fall back to `data.py`.
- The prototype must render fully with no DB.
- DB access is read-only: never `.save()`, `.create()`, or send email.

**Content labelling:**
- **Prototype banner.** Every page carries a thin top banner: "Prototype layout for testing. Not the official site. Items marked Sample are made up." plus a link "All prototypes" to `/lab/`.
- **Sample badge.** Any fabricated value is rendered next to `{% include 'lab/front-door/_sample.html' %}`. That include outputs a small bordered pill with the visible text "Sample".
- **Source line.** Values taken from the real agendas get a muted line, e.g. "Source: Student Senate agenda, 30 Jul 2026".
- **Constitution line.** Facts confirmed by the Rensselaer Union Constitution (as amended 6 Feb 2026) get no badge. Instead they get a muted line from `{% include 'lab/front-door/_cite.html' with art="Art. VII §1" %}`, which renders `<p class="text-sm text-muted">Source: Union Constitution, Art. VII §1</p>`. In `data.py`, every constitution-backed entry carries a `cite` string (e.g. `"Art. VII §1"`); templates render the line whenever `cite` is set. Numbers marked "derived" in this spec are our arithmetic; render them with "(derived)" after the number. Derived Senate thresholds (e.g. "20 of 29") assume "total voting membership" means all 29 seats; the Constitution doesn't say whether vacant seats count, so the `title` of "(derived)" reads "Our arithmetic, assuming all 29 seats count".
- **Draft badge.** Only for things the Constitution leaves to someone else: bylaws, Senate rules, or Union staff processes. Never name "RUGP" in page text or badge titles. `{% include 'lab/front-door/_draft.html' with why="Senate election rules" %}` renders a pill reading "Draft: confirm" with `title="Not set by the Union Constitution. Confirm with: {{ why }}"`. Allowed `why` values: "Senate bylaws or rules", "Senate election rules", "E-Board bylaws", "Judicial Board bylaws", "Union staff process", "Site owner". In `data.py`, such entries carry `draft="<why>"`.
- **Naming.** Use "Fraternity and Sorority Life (FSL)" for what the agendas call "Greek". The Constitution renamed the seats in Feb 2026 (Amendment VI). Never show a combined "Greek & Independent" group (see `SEATS`).

**Forms:** the only form here is the topic filter, which is a GET request. The officer-view toggle (section 0A) is a plain GET link. There are no POST forms in this prototype.

## 0A. Single source of truth (read before building)

The real site will be mostly a read-only view of other systems, and this prototype has to show that. Testers and officers should be able to see where every fact lives and who would fix it. The background is in `docs/redesign/data-architecture.md`, but you don't need to read it to build this.

**Who owns what**
- **Box** owns files. Agendas, minutes and motions are **written in Word** and published as PDFs in each body's public Box folder. **There is no Box API and there never will be.** The site only shows Box shared links that officers paste, plus Box file and folder embeds (`/embed/s/<id>`). Box's preview renders PDF and Word files. The site never lists, scrapes, syncs or parses Box files.
- **Each body keeps its own meeting records, in the tool it chooses** (revised 21 Oct 2026; see section 0B):
  - **Student Senate:** the Senate's Notion. Meetings, motion status and Public issues sync one way into the site every 15 minutes.
  - **Executive Board:** a minimal meeting entry on this site (number, date, time, place, two pasted Box links). This is shown as an *example* choice; the E-Board hasn't chosen.
  - **Graduate Council, Undergraduate Council, Judicial Board:** their Box folder only. The site shows the folder and says so.
- **The content of a Word document stays in the Word document.** Agenda items, motion text and outcomes as minuted are never retyped into Notion or this site. Item-by-item agendas appear only on Senate pages, as a labelled option ("if the Senate drafts agendas in Notion").
- **Wagtail (this site)** owns the public **roster for every body** (seats, people, term assignments, profile consent). The Senate's Notion gets a read-only copy for attendance. Wagtail also owns start pages, the glossary, "How the Union works", the topic router, process pages (funding, take part) and site notices.
- **Discord** owns announcements. The site links to the server and never copies posts.

Nothing in this prototype connects to Box or Notion. Every sync time and link-check result is seed data, and the banner says so.

**Rules for this prototype**
- No page asks an officer to type anything that lives in Box or the Senate's Notion, or the contents of a Word document.
- Nothing implies that the Executive Board, the Councils or the Judicial Board use Notion.
- No figure that someone would have to retype from an agenda is shown as if the site maintained it. Quoted figures say what they were quoted from and that they won't update.
- Every projected item (meeting, agenda item, decision, seat or person card, quoted budget figure) shows a muted **source line** from `_source.html`.
- Every Wagtail-owned page (home, issue_index, issue_topic, funding, take_part, about) ends `<main>` with the Wagtail source line: "Written on this site · reviewed 21 Oct 2026".
- The Constitution `_cite.html` line and the "Source: … agenda" line stay as they are. They tell testers where *we* got a fact. The new source line says which *system* would own it in production.

**Seed in `data.py`**
```python
SYNC = {
    "notion_minutes_ago": 12,                  # renders "synced 12 min ago"
    "box_links_checked": date(2026, 10, 19),   # weekly status check of pasted links
    "wagtail_reviewed": date(2026, 10, 21),
}
MOCK_NOTION = "https://www.notion.so/"   # every "Edit in Notion" link points here
MOCK_BOX = "https://rpi.box.com/"        # every "Edit in Box" / "Open in Box" link points here
```

`SOURCES` is a dict keyed by source key. Each value is `{key, line, edit_label, edit_url}`. Build `line` from `SYNC` with a helper, never by hard-coding "12".

| key | `line` as rendered | `edit_label` → `edit_url` |
|---|---|---|
| `meeting_senate` | "Meeting record: Senate's Notion · synced 12 min ago" | "Edit in Notion" → MOCK_NOTION |
| `meeting_eboard` | "Meeting record: entered on this site by the E-Board Secretary · updated 24 Aug 2026" | "Edit on this site" → `/admin/` |
| `folder_only` | "Records: files in this body's Box folder. It doesn't list meetings on this site." | "Open in Box" → MOCK_BOX |
| `file` | "Document: Word file in Box, published as PDF · link checked 19 Oct 2026" | "Edit in Box" → MOCK_BOX |
| `file_missing_senate` | "Document: Box · no link added to the meeting record yet" | "Add the link in Notion" → MOCK_NOTION |
| `file_missing_eboard` | "Document: Box · no link added to the meeting record yet" | "Add the link on this site" → `/admin/` |
| `folder_missing` | "Folder: Box · shared link not added yet" | "Share it in Box" → MOCK_BOX |
| `agenda_items_option` | "Agenda items: Senate's Notion agenda page · only if the Senate drafts agendas in Notion (an option, not current practice) · synced 12 min ago" | "Edit in Notion" → MOCK_NOTION |
| `motions` | "Motion status: Senate's Notion Motions table · the motion's text is in the linked Word file · synced 12 min ago" | "Edit in Notion" → MOCK_NOTION |
| `in_minutes` | "Decisions: recorded in the minutes (a Word file in Box). This site doesn't retype them." | "Open in Box" → MOCK_BOX |
| `roster` | "Roster: entered on this site by each body's roster officer · last change 25 Aug 2026" | "Edit on this site" → `/admin/` |
| `quoted_budget` | "Quoted from Executive Board Agenda 01, 25 Aug 2026 (a PDF in Box). This site does not update these figures." | "Open in Box" → MOCK_BOX |
| `wagtail` | "Written on this site · reviewed 21 Oct 2026" | "Edit in Wagtail" → `/admin/` |

A meeting's record and missing-file source lines are picked from its body's adapter (`BODY_RECORDS`, section 0B), never hard-coded per template.

**`_source.html`**, called as `{% include 'lab/front-door/_source.html' with s=sources.meeting %}`, renders:
`<p class="text-sm text-muted" data-source="{{ s.key }}">{{ s.line }}{% if officer %} · <a href="{{ s.edit_url }}" rel="nofollow">{{ s.edit_label }}</a> <span class="text-xs">(mock link)</span>{% endif %}</p>`

**Officer view (mock, no login)**
- Write one helper, `page(request, template, ctx)`, in `views.py` and have every view call it. It adds `sources`, `sync` and `officer` to the context.
- `officer` is True when the URL has `?officer=1`, or when the cookie `lab_officer=1` is set and the URL doesn't have `?officer=0`.
- `?officer=1` sets the cookie `lab_officer=1` (path `/lab/`, session cookie, SameSite Lax). `?officer=0` deletes it.
- The prototype banner gets a toggle. In student mode it reads "Viewing as a student · Show officer links" and links to `?officer=1`. In officer mode it reads "Viewing as an officer (mock) · Hide officer links" and links to `?officer=0`. In officer mode, add the muted line: "On the real site these links appear only to signed-in officers."
- Officer mode only reveals the "Edit in …" links on source lines. It reveals no extra data.

**Banner text** gains a second sentence: "Lines like 'synced 12 min ago' are simulated. Nothing here is connected to Notion or Box. Only the Senate's items would come from Notion."

**Box folders**
```python
BOX_FOLDERS = {
    "senate": {"label": "Student Senate, 57th Senate", "path": "Public Records/Senate/2026-27 Senate 57/", "shared_url": None},
    "eboard": {"label": "Executive Board, FY27", "path": "Public Records/Executive Board/2026-27 EBoard FY27/", "shared_url": None},
}
```
`_box_folder.html` works like this:
- If `shared_url` contains `/s/`, show the link "Open the folder in Box" first. Then, at `sm` and up only, show `<iframe title="Box folder: {{ path }}" src="{{ embed_url }}" class="hidden sm:block w-full h-[28rem] border">`, where `embed_url` is the shared URL with `/s/` replaced by `/embed/s/`. On phones only the link shows: Box says its embed isn't built for mobile browsers.
- Otherwise, show a dashed placeholder box: "Box folder embed goes here: {{ path }}. The shared link hasn't been added yet." The seed has no shared links, so expect the placeholder.
- Don't build an embed from `SiteSettings.box_archive_url`. It is a `/v/` vanity link, and the embed conversion only handles `/s/` links. If it's set, show it only as a plain "Whole Box archive" link.

**`OWNERSHIP_BY_BODY`** is used by about#how-this-site-works. It is a list of `{body, example, meetings, files, decisions, roster, issues}`. `example=True` renders a muted "Example choice: this body hasn't decided" after the body name.
| body | meetings | files | decisions | roster | issues |
|---|---|---|---|---|---|
| Student Senate | Senate's Notion "Meetings" (synced every 15 min, Public rows) | Word files in its Box folder, published as PDF; link pasted into the Notion row | Status in the Senate's Notion "Motions"; the motion's text is in the linked Word file | This site (VGMIA); the Senate's Notion gets a read-only copy for attendance | Senate's Notion "Issues", Public rows only (not built) |
| Executive Board (example) | Entered on this site by its Secretary: number, date, time, place, two Box links | Word files in its Box folder, published as PDF; link pasted on this site | In its minutes (a file) | This site (VP for Rules and Special Projects) | Not tracked publicly |
| Graduate Council (example) | None: files in its Box folder only | Its Box folder | In its minutes (a file) | This site, once a roster officer is named | Not tracked publicly |
| Undergraduate Council and Class Councils (example) | None: files in its Box folder only | Its Box folder | In its minutes (a file) | This site, once a roster officer is named | Not tracked publicly |
| Judicial Board (example) | None: files in its Box folder only | Public rulings in its Box folder; cases are confidential | In its rulings (files) | This site, once a roster officer is named | Not applicable |

**`OWNERSHIP_SHARED`** (the old `OWNERSHIP` minus the meeting and roster rows), a list of `{what, lives_in, who_edits, how_site_gets_it, native}`:
| what | lives_in | who_edits | how_site_gets_it |
|---|---|---|---|
| Photo, bio, pronouns, office hours | This site, only if the member ticks "Public profile" | Each member, or their roster officer | Native; removed at once if consent is withdrawn |
| Contact routes | This site (a role inbox per seat) | Each body's roster officer | Native; never a personal address |
| Budget figures | Business Operations and Union finance; printed on E-Board agendas | E-Board Business Operations | Link to the agenda in Box. Never retyped. |
| Start pages, funding steps, "Run for office or start a petition" | This site | WTG chair, with a named page owner and a review date | Native (Wagtail) |
| Glossary, "How the Union works", topic router | This site | WTG chair | Native (Wagtail) |
| Site notices | This site, with a required expiry date | WTG chair | Native (Wagtail) |
| Non-meeting events | This site (`EventPage`) | Event organiser | Native (Wagtail). Meetings never get EventPages. |
| Announcements | Discord | Anyone with posting rights | Link only |
| Senate attendance, contacts (CRM), internal notes | The Senate's Notion | Senate officers | Never shown on the site |

Under the per-body table, add: "Each body chooses how it keeps its own records. The choices marked as examples are placeholders until each body decides. Whatever it chooses, a body's meetings live in one place, never two, and every body meets the Public Records Standard below."

**`RECORDS_STANDARD`** (about#how-this-site-works, a `<ul>`; `draft="Site owner"` on its heading "The Public Records Standard"):
- "Every body publishes its agendas, draft and approved minutes, motion texts and bylaws in its public Box folder. The Executive Board also publishes its budget and allocation records, which the Constitution makes public." (cite "Art. VII §2" on the last clause)
- "Agendas are in the folder 24 hours before the meeting. Minutes (draft or approved) are there within 14 days."
- "Files are PDFs exported from Word with accessibility tags (File, Save As, PDF), never printed to PDF or scanned. Headings use Word's heading styles, and images have alt text."
- "Files are named `YYYY-MM-DD <Body> <Term> #<nn> <Agenda|Minutes|Motion - Title>.pdf`, and corrections use Upload New Version so links never break."
- "Each body names a records officer (normally its Secretary) who answers for these deadlines. This site's officer health page shows every body's standing."
- "The Judicial Board publishes its rulings on what the Constitution means. Its conduct and rights cases are confidential." (`draft="Judicial Board bylaws"`)

## 0B. Per-body records (revision, 21 Oct 2026)

The site owner told us that agendas, minutes and motions are written in Word, and that only the Senate is adopting Notion. This section describes how the built prototype changes. Where it conflicts with later sections, this section wins. The page count stays at 10.

**`BODY_RECORDS`** in `data.py`, ordered:
```python
BODY_RECORDS = {
    "senate": {"name": "Student Senate", "adapter": "notion", "adapter_label": "Senate's Notion", "records_officer": "Senate Secretary", "folder": "senate", "example": False},
    "eboard": {"name": "Executive Board", "adapter": "site", "adapter_label": "Entered on this site", "records_officer": "E-Board Secretary", "folder": "eboard", "example": True},
    "gc": {"name": "Graduate Council", "adapter": "folder", "adapter_label": "Box folder only", "records_officer": None, "folder": "gc", "example": True},
    "uc": {"name": "Undergraduate Council", "adapter": "folder", "adapter_label": "Box folder only", "records_officer": None, "folder": "uc", "example": True},
    "jboard": {"name": "Judicial Board", "adapter": "folder", "adapter_label": "Box folder only", "records_officer": None, "folder": "jboard", "example": True},
}
```
`BOX_FOLDERS` gains `gc` ("Graduate Council, 2026–27", `Public Records/Graduate Council/2026-27 GC 2026-27/`), `uc` ("Undergraduate Council, 2026–27", `Public Records/Undergraduate Council/2026-27 UC 2026-27/`) and `jboard` ("Judicial Board, 2026–27", `Public Records/Judicial Board/2026-27 JBoard 2026-27/`), all with `shared_url` None.

**Meetings**
- Senate meetings render with the `meeting_senate` source line, and E-Board meetings with `meeting_eboard`. Each meeting dict gains `document_name`: `2026-07-30 Senate 57 #12 Agenda.pdf` and `2026-08-25 EBoard FY27 #01 Agenda.pdf`.
- The meetings page gains `<h2 id="files-only">Bodies that publish records as files</h2>`. For each folder-adapter body there's an h3, then: "The {name} publishes its records as files. It doesn't list meetings on this site. Files are named by date, so the newest sort last." Then its `_box_folder.html` and the `folder_only` source line. The Judicial Board adds: "Its rulings on what the Constitution means are public. Its conduct and rights cases are confidential." (`draft="Judicial Board bylaws"`).
- "All files" lists only the Senate and E-Board folders.
- The 7-day empty state adds: "The Graduate Council, Undergraduate Council and Judicial Board don't list meetings here; see their folders." It links to `#files-only`.
- The past-meetings table gains a "Record" column ("Senate's Notion" / "Entered on this site").

**Meeting page agenda: the document first**
- The Agenda section shows the **document**. If `agenda_url` is set: "Open agenda (PDF)" first, then a Box preview iframe at `sm` and up. Otherwise a dashed box: "Box preview of {document_name} goes here. The link hasn't been added to the meeting record yet." Then the `file` or `file_missing_<body>` source line.
- Under it: `<details><summary>Prototype only: what this document says</summary>`. Inside, a muted line: "Typed from the PDF so testers can try tasks. The real site shows the Box preview instead and never retypes a Word document." Then the sections and items as plain text: no chips and no links.
- **Senate only:** `<h3 id="agenda-option">Option for the Senate: the agenda item by item</h3>`, then: "Shown only if the Senate chooses to draft its agendas in Notion and export them to Word or PDF. The Senate hasn't chosen this; today its agendas are written in Word." (`draft="Site owner"`). Then a `<details><summary>Preview the item-by-item agenda</summary>` holding the existing numbered `<ol>` with glosses and the `agenda_items_option` source line.
- **E-Board:** one muted line instead: "Item-by-item agendas aren't shown for the Executive Board. It writes its agendas in Word, and this site never retypes them."

**Decisions**
- `DECISIONS` are Senate motions only (the projection of the Senate's Notion Motions table). Stop deriving decisions from E-Board agenda items.
- Rewrite the three samples as Senate motions, each with a `motion_file` link (Sample):
  - "Asks the Institute to extend library hours during finals" (passed, 8 Oct 2026)
  - "Asks RPI Dining to publish weekend hours a semester ahead" (waiting, 14 Oct 2026)
  - "Adds the Webex link and full date to every Senate meeting notice" (done, 23 Sep 2026)
- Render motions with the `motions` source line.
- Under the decisions list (meetings#decided): "The Executive Board, Graduate Council, Undergraduate Council and Judicial Board record decisions in their minutes and rulings, published as files." Then the `in_minutes` source line.
- Meeting page "Decisions at this meeting":
  - Senate: the motions for that meeting, or "No motions recorded for this meeting in the Senate's Notion."
  - E-Board: "The Executive Board records its decisions in its minutes. Minutes link not added yet ({n} days since meeting)." Then the `in_minutes` source line. No ballroom outcome rows.

**About: How this site works**
- Lead: "This site keeps one copy of each fact. Files live in Box. Each body keeps its meeting records its own way: the Senate in its Notion, the Executive Board on this site, and the other bodies in their Box folders. This site keeps the roster for every body and its own explanations."
- Then the per-body table, the shared table, `RECORDS_STANDARD`, and "To publish a meeting" as three short lists (`PUBLISH_STEPS_BY_ADAPTER`):
  - **Senate (Notion):** export a tagged PDF and save it in the term folder with the convention name → set the link to "People with the link" → duplicate the last Notion meeting row, paste the link, tick Public → it appears within 15 minutes.
  - **Entered on this site:** the same first two steps → "Post the next meeting" on this site (prefilled from the last one), paste the link → it appears immediately.
  - **Folder only:** the same first two steps → once a month, confirm on this site that the folder is complete.
- Rules for officers: replace "Never type into this site anything that is already in Box or Notion" with "Never retype what's in a Word document (agenda items, motion text, outcomes): link the file." Add "Export with accessibility tags; never Print to PDF."
- The term rollover is "done on this site". Its last step reads: "Audit who can edit the site admin and the Senate's Notion workspace (at least two owners, on a shared role account). The Senate's Notion copy of the roster updates itself."

**Other copy**
- issue_topic, "What happens to it": "Your email goes to the committee's inbox. Senate committees may log issues in the Senate's Notion 'Issues' database; only items they mark Public would ever appear on this site, read-only. The Executive Board, the Councils and the Judicial Board don't publish an issue tracker; what they decide appears in their minutes. Your message itself is never published."
- Home verb "Find out what was decided": "Senate motions, and every body's agendas and minutes."

## 1. Seed facts for `data.py` (real, from the two agenda PDFs and the Union Constitution)

**`CONSTITUTION`** = `{"name": "Rensselaer Union Constitution", "amended": date(2026, 2, 6)}`. Its text is not hosted on this site yet. Wherever the Constitution is named, show "Rensselaer Union Constitution, last amended 6 Feb 2026" with no link (`draft="Site owner"`: where the official copy is published).

**`MEETINGS`** is a list of dicts with these keys: `body` (senate|eboard), `body_name`, `term_slug`, `term_label`, `number`, `starts` (aware datetime, America/New_York), `location`, `remote` (bool), `agenda_status` ("posted"|"not_posted"), `agenda_url` (None; there is no Box link yet, so show "Agenda posted in Box · link not added to the meeting record yet"), `minutes_status` ("not_posted"|"draft"|"approved"), `minutes_url` (None), `public` (True: the Notion row's Public box), `voting_listed` (the agenda header's voting count), `quorum` (agenda header), `nonvoting` (agenda header), `seats_constitution`, `seats_cite`, `sections`.

**Senate meeting:** body senate, "Student Senate", term_slug "57", term_label "57th Student Senate", number 12.
- Starts 2026-07-30 20:00. Location "Webex", remote True.
- Agenda header: voting_listed 19, quorum 13, nonvoting 10.
- seats_constitution 29, seats_cite "Art. VII §1". The Constitution does not set the Senate's quorum, so the 13 is shown only with the agenda source line.
- `sections`, in order. Each is `{title, plain, items:[{title, who, type}]}`:
  1. Bookkeeping. Plain: "Opening business, including a statement that the meeting is recorded by The Polytechnic."
  2. Invitation to Speak and Press & Visitor Q/A. Plain: "Anyone can speak or ask questions here." (`draft="Senate bylaws or rules"`: the Constitution doesn't cover who may speak.)
  3. Grand Marshal Report. Plain: "An update from the Grand Marshal, the Union's chief spokesperson, who runs Senate meetings." (cite "Art. IV §1")
  4. Committee Reports. Items:
     - Academic Affairs (Zach Nobles '27)
     - Community Relations (Mia Stryhalaleck '28)
     - Elections Commission (Lauren Antao '28)
     - Facilities and Services (Charlie Fowle '29)
     - Residential Living and Dining (Shruthi Anandraman '28)
     - Rules and Administration (Griffin Oliver '27)
     - Student Life (Stanley Goodwin '30G)
     - Senate Communications and Engagement (Emily Lin '29)
     - Web Technologies Group (Aaron Niyazov '28)
     - Union Annual Report (Samson Kempiak '28)
  5. Peer Body & Officer Reports. Items:
     - VGM External Affairs (Ryan Kilgore '27)
     - VGM Internal Affairs (Griffin Oliver '27)
     - Executive Board (Cee Ray '27)
     - Graduate Council (Melissa Flores 'G)
     - Undergraduate Council (Nick Castiglione '28)
     - Interfraternity Council (Vacant)
     - Panhellenic Council (Vacant)
     - Multicultural Sorority and Fraternity Council (Vacant)
     - Treasurer (Cee Ray '27). Display as "Senate Treasurer" (see GLOSSARY: not the Treasurer named in the Constitution).
     - Secretary (Selena Tang '29)
     - Parliamentarian (Sasha Notkin '28)
  6. Special Orders. Items: none.
  7. Old Business. Items: none.
  8. New Business. Items: none.
  9. Invitation to Speak and Press & Visitor Q/A.

For this meeting, agenda_status is "posted" and minutes_status is "not_posted".

**E-Board meeting:** body eboard, "Executive Board", term_slug "fy27", term_label "2026–27 Executive Board (FY27)", number 1.
- Starts 2026-08-25 19:00. Location "RU 3202", remote False.
- Agenda header: voting_listed 12, quorum 8, nonvoting 7.
- seats_constitution "15 to 20", seats_cite "Art. VII §2". The Constitution does not set the E-Board's quorum either.
- Sections:
  1. Approval of Minutes
  2. Reports. Items:
     - President (Kate Goldstein '26 '27G)
     - VP Board Operations (Gavin Finn '28)
     - VP Club Relations (Jesse Kim '26 '27G)
     - VP Rules and Special Projects (Blaine Rosenberg '28)
     - Director's Report (Dr. Charlie Potts, Union Director, professional staff)
     - Student Senate (Cee Ray '27)
     - Undergraduate Council (Vacant)
     - Graduate Council (Joydip Paul '29G)
     - Committees: Business Operations (Grey Smith '27), Club Operations (Elijah Pulga '29), Marketing & Strategy (Vacant), Executive Communication (Vacant), Multicultural Leadership Council (Mariam Toure '28), Union Annual Report (Ava Cintula '29), Union Programming and Activities Committee (Lilu Kaufman '26)
  3. Proposals. Items:
     - "Special Ballroom Request – Society of Women Engineers", type proposal, plain "Request to book the Union Ballroom"
     - "Special Ballroom Request – RPI Admissions", same type and plain text
  4. Business. Items: "Rally Week Discussion"
  5. Invitation to Speak
  6. Press & Visitor Q/A

For this meeting, agenda_status is "posted" and minutes_status is "not_posted".

**`DECISIONS`** (revised, see 0B) are Senate motions only: the projection of the Senate's Notion Motions table, where the secretary records each motion's status once, at the vote, and pastes a link to the motion's Word or PDF file. They are never derived from agenda items, and E-Board decisions stay in the E-Board's minutes. The real E-Board ballroom requests therefore appear only inside the E-Board agenda document, not as decision rows.

Add 3 clearly SAMPLE Senate motions with `sample=True` and a `motion_file` link. Each has a date in Sep/Oct 2026, a plain summary, and a status from {"passed", "failed", "waiting", "done"}. Status labels: "Passed", "Didn't pass", "Waiting on a vote", "Done: here's what changed". The three are listed in 0B. Render them with the `motions` source line.

**`BUDGET`**, as of 2026-08-25, source "Executive Board Agenda 01, 25 Aug 2026". These figures are a **quotation from one agenda, not a maintained figure**. The site never keeps its own copy of budget numbers, because someone would have to retype them from each agenda. Render them only with the `quoted_budget` source line and a link to the E-Board Box folder ("Latest figures: the newest E-Board agenda in Box").
- Club Contingencies: initial 100000, current 100000. Plain: "Extra money clubs can request during the year." (`draft="E-Board bylaws"`: what each pool is for is not in the Constitution)
- Travel Contingencies: 60000 / 60000. Plain: "Money clubs can request for travel." (same draft)
- Facilities: 166150 / 166150. Plain: "Money for Union facilities."
- Facilities Reserves: current 126635.47, no initial value. Plain: "Savings held for facilities."
- `BUDGET_RULES` (constitution, each with cite): "The Executive Board prepares and approves the Union budget, and hands out Union money." (Art. VII §2) · "The budget and the records of all extra spending and allocations are public documents." (Art. VII §2) · "No Union money can be spent without a requisition from the Executive Board or its authorised agent." (Art. XIV)

**`SEATS`** is a list of `{body, seat, constituency, holder or None, also, status, fill_rule, inbox}`. `status` is "filled", "vacant", or "elect_fall". `holder=None` with status "vacant" renders as **Vacant**. Status "elect_fall" renders as **To be elected this fall**. `fill_rule` is a key into `FILL_RULES` below. `inbox` is the seat's role inbox; it is None for every seat, because no role inboxes exist yet. Never invent one.

In production, `SEATS` is computed on this site from its own seats plus current-term assignments, for every body (the roster is Wagtail-owned; the Senate's Notion only receives a read-only copy). A seat with no assignment for the current term renders Vacant automatically. So when a body sets a new term as current, every seat shows Vacant until new assignments are entered, and last year's names never carry over. Name, seat and term are always public, because they are printed on public agendas. Photos and bios appear only if the member ticks "Public profile". Nobody has, so every card uses initials.

Student Senate. The Constitution sets 29 voting seats: 7 Graduate, 4 for each of the four undergraduate classes, 3 Independent, 3 Fraternity and Sorority Life (cite "Art. VII §1"). The Grand Marshal presides and votes only to break a tie (cite "Art. IV §1"), so is not one of the 29.
- Grand Marshal: Jordan Krishnayah '28 (constituency "everyone", fill_rule "gm")
- Graduate Senators (graduate, fill_rule "elected_appointed"): Batuhan Yalcin; Alexander Neimeth; Paul Lea; Stanley Goodwin '30G (also SLC chair); Vacant ×3
- Class of 2027 Senators (2027, fill_rule "class_senator"): Ghea Chaw; Griffin Oliver (also VGMIA, RAC chair); Rachel Schneider; Adam Choi
- Class of 2028 Senators (2028, "class_senator"): Aaron Nam; Nick Castiglione; Vacant ×2
- Class of 2029 Senators (2029, "class_senator"): Jaewon Yoon; Melissa DeLuise; Aarushi Kumar; Riley Sanders
- Class of 2030 Senators (2030, "class_senator"): 4 seats, holder None, status "elect_fall". First-year senators are elected in the fall semester (cite "Art. VIII §3"); the 30 Jul 2026 roster predates that election.
- Independent Senators (independent, "elected_appointed"): Shruthi Anandraman '28 (also RLDC chair); Ryan Kilgore '27 (also VGMEA); Ashley Wong '27
- Fraternity and Sorority Life (FSL) Senators (fsl, "elected_appointed"): Mischa Fedak; Andrew Donilon; Radhika Manvar
- **Reconciliation note** (render under the Independent and FSL groups wherever both appear, with cite "Art. VII §1; Art. VIII §5"): "The Senate agenda lists these six under one heading, 'Greek & Independent Senators'. Under the Union Constitution they are two separate groups of three seats: Independent Senators must not be in a fraternity or sorority, and FSL Senators must be. The Constitution is authoritative, so this site shows them as two groups. All six seats are filled." Do not show any "unaccounted seat" note: the earlier workshop note came from our misreading of the agenda, which gives no seat count for that heading.
- Non-voting officers (from the agenda; these titles are set by Senate bylaws, not the Constitution): Senate Treasurer and Senate–E-Board Liaison Cee Ray '27; Parliamentarian Sasha Notkin '28; Secretary Selena Tang '29.
- Count check (render on the meeting page and about page): "29 voting seats (Constitution) · 20 filled on the 30 Jul 2026 roster · 5 vacant · 4 first-year seats to be elected this fall". Compute every number from `SEATS`. The agenda header says 19 voting members; show that only with its source line, and do not try to reconcile it in the UI (it is an open question for the site owner).

Executive Board. The Constitution sets 15 to 20 voting members (cite "Art. VII §2"). Required: 5 club and organization reps; 1 rep each from the Freshman, Sophomore, Junior, Senior and Graduate classes; a Graduate Council rep; an Undergraduate Council rep; a Senate–E-Board Liaison; 2 members-at-large. Optional, at the President's discretion: 2 more club and organization reps and 3 more members-at-large. The President of the Union presides and votes only to break a tie (cite "Art. IV §2").
- President of the Union: Kate Goldstein '26 '27G (everyone, fill_rule "pu")
- Officers (titles from E-Board bylaws; `draft="E-Board bylaws"`; the Constitution has no VP seats and the agenda doesn't say which voting seat each VP holds): Gavin Finn '28 (VP for Board Operations); Jesse Kim '26 '27G (VP for Club Relations); Blaine Rosenberg '28 (VP for Rules and Special Projects)
- Class Representatives (fill_rule "eb_appointed"): Graduate Vacant; 2027 Jacob Bloecher; 2028 Mariam Toure (also MLC chair); 2029 Ava Cintula (also UAR chair); 2030 Vacant (the first-year member is appointed within three weeks after the fall elections, cite "Art. VIII §12")
- Club & Organization Representatives (clubs, "eb_appointed"): Grey Smith '27 (Business Ops chair); Elijah Pulga '29 (Club Ops chair); Samson Kempiak '28; Valerie Rosa-Sanclemente '28; Vacant ×3. Seven seats = 5 required + 2 optional.
- Members-at-Large (everyone, "eb_appointed"): Ahmed Shoaib '29; Aaron Brown '29; Sumaya Moumita '28; William Liu '29; Vacant. Five seats = 2 required + 3 optional.
- Council and Senate seats (voting under the Constitution, although the agenda prints them under "Peer Body Representatives"): Senate–E-Board Liaison Cee Ray '27 (fill_rule "eb_peer", chosen by the Senate); Graduate Council rep Joydip Paul '29G ("eb_peer", chosen by the Graduate Council); Undergraduate Council rep Vacant ("eb_peer", chosen by the Undergraduate Council).
- Note: the E-Board membership block is headed "2025-2026" although the agenda is for 2026–27. Show "Roster may be out of date" with source.

**`FILL_RULES`**: how each kind of seat gets filled, in plain words. Each is `{key, text, cite, draft?}`. Render it on vacant cards ("How this seat gets filled") and on about#get-involved.
- gm: "Elected by all students in the spring. Needs at least 40% of the vote. If the post falls vacant, the Senate appoints a replacement by a 2/3 vote within two weeks." cite "Art. VIII §1, §10; Art. XI §1"
- pu: "Elected by all students in the spring. Needs at least 40% of the vote. If the post falls vacant, the Executive Board appoints a replacement within two weeks and the Senate confirms by 2/3." cite "Art. VIII §1, §10; Art. XI §2"
- class_senator: "Elected by the class (first-years in the fall, other classes in the spring). If a seat falls vacant, the Class Council appoints someone. If 20% of the class signs a petition within two weeks of the announcement, there must be a special election instead." cite "Art. VIII §1, §3; Art. XI §5, §6"
- elected_appointed: "Elected in the spring. A vacant seat can be filled by appointment. If 20% of the constituency signs a petition within two weeks of the announcement, there must be a special election instead." cite "Art. VIII §1, §9; Art. XI §5". Plus `draft="Senate bylaws or rules"`: who makes the appointment.
- eb_appointed: "Appointed by the President of the Union and approved by 2/3 of the Senate. Required seats are filled within three weeks after the spring elections; the first-year seat within three weeks after the fall elections; optional seats by the end of the fourth week of the fall semester." cite "Art. VII §2; Art. VIII §12". Plus `draft="E-Board bylaws"`: how to apply.
- eb_peer: "Chosen by the body it represents (the Senate, Graduate Council or Undergraduate Council) within three weeks after that body's elections." cite "Art. VII §2; Art. VIII §12"

**`COMMITTEES`** (Senate):
- AAC Academic Affairs: Zach Nobles
- CRC Community Relations: Mia Stryhalaleck
- Elections Commission: Lauren Antao (acting)
- FSC Facilities and Services: Charlie Fowle
- RLDC Residential Living and Dining: Shruthi Anandraman
- RAC Rules and Administration: Griffin Oliver
- SLC Student Life: Stanley Goodwin
- SCEC Senate Communications and Engagement: Emily Lin
- WTG Web Technologies Group: Aaron Niyazov
- UAR Union Annual Report: Samson Kempiak (acting)

E-Board committees: Business Operations, Club Operations, Marketing & Strategy (vacant chair), Executive Communication (vacant chair), MLC, UAR, UPAC.

The Constitution does not list any committees; they come from the agendas and are set by each body's bylaws. Committee one-liners therefore carry `draft="Senate bylaws or rules"` (or "E-Board bylaws"). One constitutional fact to show under the Senate committee table: "The Grand Marshal is an automatic (ex-officio) member of every Senate committee." (cite "Art. IV §1")

**`TOPICS`** (topic router). The router is Wagtail-owned content: it rarely changes, so it lives on this site. Each topic points to a *seat* (the committee chair's seat), and the seat resolves to its current holder and role inbox through the roster projection. Each has `slug, question, examples, owner_label, owner_body, owner_seat, outside_sg, sample_contact=False`:
- dining: "Problem with dining or meal plans?" Owner: RLDC (Senate). outside_sg: "RPI's dining service runs meal plans and dining halls; RLDC raises student concerns with them."
- housing: "Problem with your residence hall or housing?" Owner: RLDC. outside_sg: "Residence Life runs housing day to day."
- buildings: "Broken, inaccessible, or unsafe building or space?" Owner: FSC. outside_sg: "For urgent repairs contact RPI Facilities directly."
- academics: "Concern about classes, advising, or academic policy?" Owner: AAC.
- student-life: "Wellbeing, campus life, or student services?" Owner: SLC.
- troy: "Off-campus or Troy community issue?" Owner: CRC.
- clubs: "Club rules, registration, or club money?" Owner: Executive Board. Body fact: "The Executive Board decides how clubs are classified and hands out Union money." (cite "Art. VII §2"). Routing to the VP for Club Relations / Club Operations Committee carries `draft="E-Board bylaws"`.
- grad: "Grad-specific: stipends, grad housing, TA workload?" Owner: Graduate Council and Graduate Senators. Body fact: "The Graduate Council is the Union's advocacy body for graduate students. Its voting members are the 7 Graduate Senators plus at least 5 at-large members." (cite "Art. VII §4")
- class: "About your class: class events or class dues?" Owner: your Class Council (undergraduates) or the Graduate Council (graduate class dues). Body fact: "Each class elects a Class Council. It recommends how class dues are spent, and the Undergraduate Council must approve that spending by majority." (cite "Art. VII §5"). Chair: "Roster not listed yet".
- rights: "Think a Union body broke the Constitution, or your student rights were violated?" Owner: Judicial Board. Body fact: "The Judicial Board is the Union's student court. It hears charges that the Union Constitution, the Rensselaer Student Bill of Rights, or student conduct rules were violated, and it can rule Senate, Executive Board or council decisions unconstitutional." (cite "Art. VII §3"). This topic's "How to raise it" is replaced by a link to take_part#judicial-board (see 5.7).
- elections: "Question about elections?" Owner: Elections Commission. (`draft="Senate election rules"`: the Constitution leaves election procedure to the Senate, Art. VIII §6.)
- website: "Problem with this website?" Owner: Web Technologies Group.
- other: "Something else". Owner: Student Senate (Grand Marshal's office). Body fact: "The Grand Marshal is the leader and chief spokesperson for the whole Union." (cite "Art. IV §1")

Every topic page also shows the line: "If anyone is in danger, contact RPI Public Safety now." (`draft="Site owner"`: add the number once confirmed). Do NOT invent phone numbers or email addresses anywhere.

**`GLOSSARY`**: each entry is `{term, text, cite?, draft?}`. Entries with `cite` get the constitution line; entries with `draft` get the badge; plain dictionary words get neither. Render in this order:
- Rensselaer Union: "Every enrolled RPI student, graduate or undergraduate, who has paid the Union Activity Fee, and the organisation they form." cite "Art. I; Art. II"
- Union Activity Fee: "The fee that makes you a Union member. The Senate sets the amount by a 2/3 vote of all its voting seats." cite "Art. II; Art. VII §1"
- Student Senate: "The Union's main lawmaking body. It has 29 voting seats, passes its own rules, sets the Activity Fee, and approves many appointments." cite "Art. VII §1"
- Executive Board (E-Board): "The Union's budgeting body. It prepares and approves the budget, hands out Union money, and decides how clubs are classified." cite "Art. VII §2"
- Judicial Board: "The Union's student court. It decides cases about student rights and conduct, and it is the only body that can say what the Constitution means." cite "Art. VII §3"
- Graduate Council: "The advocacy body for graduate students: the 7 Graduate Senators plus at least 5 at-large members." cite "Art. VII §4"
- Undergraduate Council: "The advocacy body for undergraduates. Its voting members are the President and Vice President of each of the four Class Councils, and it oversees those councils." cite "Art. VII §5"
- Class Council: "The elected council for one undergraduate class: the Class President, the Vice President, at least 8 Representatives and the class's 4 Senators. It recommends how class dues are spent." cite "Art. VII §5"
- Grand Marshal: "The Union's leader and chief spokesperson, elected by all students. Runs Senate meetings and votes only to break a tie. An RPI-specific title." cite "Art. IV §1"
- President of the Union: "Runs the Executive Board and appoints most of its members, with 2/3 Senate approval. Votes only to break a tie." cite "Art. IV §2; Art. VII §2"
- Director of the Union: "A paid staff member who runs Union activities and funds day to day. Advises the Executive Board but cannot veto it." cite "Art. V"
- Senate Treasurer: "A Senate officer listed on the agendas. Not the same as the 'Treasurer' in the Constitution, which is RPI's own Treasurer, who holds the Union's money." cite "Art. VI" (the Senate Treasurer role itself carries `draft="Senate bylaws or rules"`)
- Class dues: "Money collected from the members of a class and spent through that class's council." cite "Art. VII §4, §5"
- Referendum: "A vote of all affected students on a question. It is binding if a majority votes yes and at least 20% of those students vote." cite "Art. XII §1, §3, §4"
- Petition: "A signed request from students. Depending on the goal it needs 10%, 20% or 50% of the students concerned." cite "Art. X; Art. XI §5; Art. XII §1"
- Recall (removal election): "A student vote to remove an elected officer or senator before the term ends." cite "Art. X §1, §2"
- Ex-officio: "Holding a seat automatically because of another office you hold."
- Plurality: "The most votes, even if that is less than half."
- Quorum: "The minimum number of voting members who must be present for a meeting to act. The Constitution leaves this to each body's own rules; the latest Senate agenda lists 13." Source line: Student Senate agenda, 30 Jul 2026. `draft="Senate bylaws or rules"`.
- Bylaws: "A body's own detailed rules, passed under the Constitution. The Senate, Executive Board, Judicial Board, Graduate Council and Undergraduate Council each have them." cite "Art. VII"
- Robert's Rules of Order: "The standard meeting rulebook the Union uses wherever the Constitution and a body's own rules are silent." cite "Art. VII §6"
- Parliamentarian: "The officer who advises a meeting on its rules." `draft="Senate bylaws or rules"`
- Contingency: "A pool of money clubs can ask the Executive Board for during the year." `draft="E-Board bylaws"`
- Invitation to Speak: "Time at the start and end of every meeting when anyone may speak." `draft="Senate bylaws or rules"`
- Minutes: "The official written record of a meeting."

Do NOT include an entry for "RUGP". The Constitution never mentions it, so the site cannot describe it from this source.

**`PROCESSES`** (for the take_part page, 5.7). An ordered list of dicts: `{id, title, lead, who, needs, timing, then, not_set, not_set_why, cite}`. `not_set` is a list of plain strings rendered under "Not set by the Constitution" with the Draft badge using `not_set_why`. Contents:

1. `run`, "Run for office"
   - lead: "Most Union seats are elected by students. You can run if you're a Union member when the election is held."
   - who: "Any Union member, as long as you meet RPI's eligibility rules and any extra rules the Senate sets. Grand Marshal, President of the Union and Judicial Board Chairperson need at least one full semester at RPI. Independent Senators must not be in a fraternity or sorority; FSL Senators must be."
   - needs: "Grand Marshal and President of the Union need at least 40% of the vote. Most other seats go to whoever gets the most votes. A tie means a new election between the tied candidates."
   - timing: "General elections are in the spring. First-year Senators and the first-year Class Council are elected in the fall. Winners take office within one week of the results."
   - then: "You serve until the next general election for your seat. Nobody may serve more than two full terms combined as Grand Marshal and/or President of the Union. You can't run for both of those at once, or for two seats on the same council."
   - not_set: ["How to get your name on the ballot, including any signatures", "Election dates and campaign rules"], not_set_why "Senate election rules"
   - Extra line: "Ask the Elections Commission (Lauren Antao, acting)." Source line: Student Senate agenda, 30 Jul 2026. Link: "See open seats" → about#get-involved.
   - cite "Art. IV §6; Art. VIII §1, §3, §4, §5, §8, §10–§13; Art. IX"
2. `appointed`, "Get appointed instead"
   - lead: "Some seats are appointed rather than elected."
   - who: "Executive Board class, club and at-large seats: appointed by the President of the Union and approved by 2/3 of the Senate. Judicial Board members: proposed by its Chairperson, then approved by 2/3 of the Judicial Board and 2/3 of the Senate."
   - timing: "Optional Executive Board seats are filled by the end of the fourth week of the fall semester."
   - not_set: ["How to apply, and who to send it to"], not_set_why "E-Board bylaws"
   - cite "Art. VII §2, §3; Art. VIII §12"
3. `referendum`, "Make students vote on something (referendum)"
   - lead: "If enough students sign a petition, the Senate must hold a student vote on almost any question."
   - who: "Any Union member can start one. It can be about anything except changing the Constitution."
   - needs: "Signatures from at least 10% of all Union members. The Senate can only refuse by a 2/3 vote of all its voting seats (20 of 29, derived). The Senate can also put a question on the ballot itself by a 2/3 vote."
   - timing: "The vote is held within 45 days (not counting vacations) or at the next regular election, whichever is sooner, but never less than 14 days after approval and never during exams."
   - then: "It passes with a majority of votes, but only counts if at least 20% of the affected students vote. Once passed it is binding: the Senate must pass whatever is needed to carry it out, and only another referendum can undo it."
   - not_set: ["Petition format and where to hand it in", "How signatures are checked", "How many students 10% is right now"], not_set_why "Senate bylaws or rules"
   - cite "Art. XII §1–§4"
4. `challenge`, "Challenge an appointment to an elected seat"
   - lead: "When an elected seat is filled by appointment instead of election, students can force an election."
   - who: "Students in the constituency for that seat."
   - needs: "A petition signed by 20% of that constituency."
   - timing: "The Senate must receive it within two weeks of the appointment being announced. If students are away from campus, the two weeks start when it is announced to the full campus."
   - then: "A special election is held for the seat."
   - Example line (computed from SEATS): "Right now the Class of 2028 has 2 vacant Senate seats. If its Class Council appoints people to them, 20% of the class can force an election."
   - not_set: ["Petition format and where to hand it in"], not_set_why "Senate bylaws or rules"
   - cite "Art. XI §5, §6"
5. `recall`, "Remove an elected officer or senator"
   - lead: "Students can remove the people they elected before their term ends."
   - Rendered as a table with caption "How removal works", columns Who | How it starts | What removes them:
     - Grand Marshal, President of the Union, Graduate or Undergraduate Council President | A 2/3 Senate vote, or a petition from 20% of their constituents followed by a Senate majority | A petition signed by 50% of their constituents, or 2/3 of those voting in a removal election where at least 20% vote
     - An elected senator | A petition from 20% of their constituents, or a Senate majority | 2/3 of those voting in a removal election where at least 20% vote
     - Any voting senator, for good cause | The Senate | 2/3 of all Senate voting seats (20 of 29, derived)
     - A Graduate or Class Council member, for good cause | A majority "impeachment" vote at a council meeting; the removal vote is at the next meeting | 2/3 of that council; the member can't vote
   - not_set: ["What counts as 'good cause'", "How removal elections are run"], not_set_why "Senate bylaws or rules"
   - cite "Art. X §1, §2, §5"
6. `judicial-board`, "Bring a case to the Judicial Board"
   - lead: "The Judicial Board is the Union's student court."
   - who: "The Constitution says any charge can be referred to it. It does not say who may file."
   - needs: "A charge that names a violation of the Union Constitution, the Rensselaer Student Bill of Rights, or RPI's rules on student conduct."
   - then: "The Board decides the case. It can rule that a decision of the Senate, Executive Board, Graduate Council, Undergraduate Council or a Class Council is unconstitutional. It is the only body that can interpret the Constitution."
   - not_set: ["Who may file and how", "Deadlines, hearings and appeals", "Who currently chairs the Board"], not_set_why "Judicial Board bylaws"
   - No start button. Show "How to file: not published yet" in the summary box.
   - cite "Art. VII §3"
7. `amend`, "Change the Constitution"
   - lead: "Students vote on every change to the Constitution, but the Senate has to propose it first. A petition alone can't amend it."
   - who: "Ask a senator to propose it (link reps_index), or raise it at a meeting (link meetings)."
   - needs: "2/3 of the Senate, then a majority of students voting in a campus election where at least 20% of eligible students vote."
   - timing: "The proposal goes to RPI's President one month before the vote; RPI's President may refer it to the Board of Trustees. The exact wording must be published campus-wide at least two weeks before the vote. No votes during exams."
   - cite "Art. XII §1; Art. XIII §1–§4"

## 2. Optional real-DB reads (each wrapped, each falls back)

- **Settings:** `from home.models import SiteSettings; s = SiteSettings.load(request_or_site=request)`. Use `contact_email`, `office_location`, `office_hours`, `discord_url`, `instagram_url`, `box_archive_url`. If an attribute is blank or missing, omit the element. Never print an empty label.
- **Upcoming events:** `from events.models import EventPage; from home.models import _upcoming_by_next_occurrence; upcoming = _upcoming_by_next_occurrence(list(EventPage.objects.live()), today, limit=5)`, where `today = timezone.localdate()`.
  - If the result is empty or the query errors, the 'This week' section uses the fallback below.
  - Only show events whose next occurrence is within 7 days.
  - Skip any event with `event_type == "meeting"`. Meetings come only from `MEETINGS` (the Senate's Notion projection and the E-Board's site entries) and never from hand-made EventPages. Only non-meeting events are Wagtail-owned.
- **People:** `from branches.models import MemberRoleAssignment`. If `.exists()`, use the DB rows. Otherwise use `SEATS`. The current local DB has 0 rows, so expect the fallback. In production these models are the roster's owner for every body, so either way they render with the `roster` source line.

## 3. Pages and URLs

| name | URL | template |
|---|---|---|
| home | `/lab/front-door/` | `home.html` |
| issue_index | `/lab/front-door/raise-an-issue/` | `issue_index.html` |
| issue_topic | `/lab/front-door/raise-an-issue/<slug:topic>/` | `issue_topic.html` |
| reps_index | `/lab/front-door/your-reps/` | `reps.html` |
| reps | `/lab/front-door/your-reps/<slug:key>/` | `reps.html` |
| meetings | `/lab/front-door/meetings/` | `meetings.html` |
| meeting | `/lab/front-door/meetings/<slug:body>/<slug:term>/<int:number>/` | `meeting.html` |
| funding | `/lab/front-door/funding/` | `funding.html` |
| take_part | `/lab/front-door/take-part/` | `take_part.html` |
| about | `/lab/front-door/about/` | `about.html` |

- Unknown slugs or keys return a 404.
- Reps keys: 2027, 2028, 2029, 2030, graduate, independent, fsl, clubs.

## 4. Global layout (`base.html`)

**Head:**
- `<html lang="en">`, viewport meta.
- `<title>{% block title %}{% endblock %} · RPI Student Government (prototype)</title>`.
- `<meta name="description">` per page.
- Open Graph title and description for link previews.

**Styles:**
- Load `<script src="https://cdn.tailwindcss.com/3.4.17"></script>` with an inline config extending these colors: ink #0b0c0c, muted #505a5f, line #b1b4b6, brand #a50015 (rpi-red-dark; 8.1:1 on white), brand-bright #d6001c (for large or bold only, 5.4:1), focus #ffdd00, panel #f3f2f1.
- Inline `<style>` for focus: `:focus-visible{outline:3px solid #0b0c0c;box-shadow:0 0 0 6px #ffdd00}`.
- `@media (prefers-reduced-motion: reduce){*{transition:none!important}}`.
- Font: system stack (`ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Arial`). No webfont, for speed.

**Body structure, in order:**
1. Skip link "Skip to main content", visible on focus.
2. Prototype banner.
3. `<header>` with the wordmark "RPI Student Government" and the subline "Rensselaer Union" (link to home).
4. A search input. GET to `/search/` with `name="query"`, using the real site search, with label "Search".
5. `<nav aria-label="Main">` with 5 real `<a>` links: **Raise an issue** · **Funding** · **Meetings & decisions** · **Your reps** · **How the Union works**.
   - On screens under 768px the nav is wrapped in `<details><summary>Menu</summary>…</details>`, so there is no JS. At md and up it shows as an inline row.
   - The current page gets `aria-current="page"`.
6. `<main id="main">`.
7. `<footer>`, an identifier block:
   - "Part of the Rensselaer Union · 110 8th Street, Troy, NY 12180".
   - SiteSettings office hours, location and email, if present.
   - Discord and Instagram links if present.
   - "Report a problem with this page": a link to `issue_topic` website.
   - "Maintained by the Web Technologies Group · Page last reviewed: 21 Oct 2026".

**Typography and spacing:**
- Body text 1.125rem / line-height 1.6 on mobile, 1.1875rem at md.
- h1 2rem (mobile) / 2.5rem (md), bold. h2 1.5rem. h3 1.25rem.
- Content max-width 40rem for prose, with the layout container at max-w-5xl.
- Side padding: 16px on mobile, 24px at md.
- Links: brand color, underlined, thicker underline on hover.
- Every tap target is at least 44px high.

**Breakpoints:** mobile-first single column. At md (768px), the homepage verb list becomes a 2-column grid. At lg (1024px), the meeting page gets a sticky in-page nav on the left.

## 5. Page specs

### 5.1 Home (`home`)

1. **Alert slot.** Render only if `data.NOTICE` is set and `NOTICE['expires'] >= today`.
   - Seed: `NOTICE = None` by default.
   - Add a commented example with `expires` 14 days out.
   - Style: full-width yellow left border, black text.
2. **Heading.** h1 "What do you need to do?"
3. **Verb list.** `<ul>` of 6 large link rows. Each row is a bold link, a one-line description, and a chevron (aria-hidden):
   - **Raise an issue**: "Tell the right people about a problem: dining, housing, classes, clubs and more." → issue_index
   - **Get money for your club**: "How clubs request extra funding and travel money, and where to find the latest figures." → funding
   - **Find out what was decided**: "Recent votes and meeting records from the Senate and Executive Board." → meetings#decided
   - **See who represents you**: "Your senators and class representative, and how to reach them." → reps_index
   - **Go to a meeting**: "When and where the next meetings are. Anyone can speak." → meetings
   - **Run for office or start a petition**: "{N} seats are open right now. Students can also force a vote, challenge an appointment, or remove an officer." → take_part
   - N is computed as the count of `SEATS` with holder None and body in (senate, eboard), including "elect_fall" seats. Never hard-code it.
4. **This week.** h2.
   - Show cards for each MEETINGS or DB event whose start is between today and today+7.
   - Each card shows: body name, full date with weekday and year (`D j M Y`), time, location, an agenda status line ("Agenda posted" link, or "Agenda not posted yet"), the line "Anyone can speak at the start and end.", and the meeting's own record source line (`meeting_senate` or `meeting_eboard`). Agenda status is derived from the record: a Box link present means "Agenda posted".
   - **If none:** do not show empty cards. Render one line: "No Senate or Executive Board meetings are listed for the next 7 days." and a link to "See past meetings and records". Today, 21 Oct 2026, this is the expected state with seed data.
5. **Your representatives.** h2.
   - A row of pill links: '27, '28, '29, '30, Grad, Independent, Fraternity & Sorority Life, Clubs (each → reps/<key>/).
   - The text: "Pick your group to see your senators and class rep."
   - Progressive enhancement: a tiny inline script stores the last-picked key in localStorage (wrapped in try/catch) and, on return, shows a "Your group: Class of 2028, change" link first.
6. **Recently decided.** h2. The newest 3 from DECISIONS (sample ones badged).
   - Each row: status word in a bordered chip with text (never colour alone), plain summary, body, date with year.
   - One `decision` source line under the list (not per row).
   - "All meetings and decisions" link.
   - Production rule (add as an HTML comment in the template): this section collapses entirely when there are no Senate motions with a recorded status. Other bodies' decisions are in their minutes and never appear here. Sections never render empty.
7. **Your Union in one sentence each.** A `<dl>` of the 5 governing bodies named in the Constitution (Student Senate, Executive Board, Judicial Board, Graduate Council, Undergraduate Council) with their GLOSSARY sentences, linking to about#<body>. One constitution line under the list: "Source: Union Constitution, Art. VII".

No hero image, no carousel, no counters.

### 5.2 Raise an issue (`issue_index`, `issue_topic`)

**Index page:**
- h1 "Raise an issue".
- Intro: "Pick what it's about. We'll show you who handles it and what student government can and can't change."
- A list of the TOPICS questions as large link rows.
- A muted line: "Not sure? Choose Something else."

**Topic page:**
- h1 is the topic question.
- **"Who handles this" summary box** (panel background, left border): owner label, its body, the chair's name from COMMITTEES if known (or "Chair: Vacant"), and the one-sentence body description.
- **"What student government can do"**: the topic's body fact with its constitution line, when the topic has one (clubs, grad, class, rights, other). Otherwise 2–3 sentences of plain text with `draft="Senate bylaws or rules"`, because the Senate committees' remits come from bylaws, not the Constitution.
- **"If nothing changes"** (every topic except website): "Students can make the Senate hold a binding student vote on almost any question with a petition signed by 10% of Union members." Link "How petitions work" → take_part#referendum. cite "Art. XII §1".
- **"Outside student government"**: `outside_sg`, shown if present.
- **"How to raise it"**: an ordered process list:
  1. Email the committee. Use the owner seat's role `inbox` as a mailto. Every inbox is None in the seed, so fall back to the SiteSettings contact_email with the subject prefilled "For: <owner_seat>: [Topic] issue", and add the muted note "This committee doesn't have its own role inbox yet." If there is no contact_email either, show "Contact address to be confirmed" + `_draft.html` with `why="Site owner"`. Never show a personal address.
  2. Or speak at the next Senate meeting. Link to meetings, with the sentence about the Invitation to Speak.
  3. Or post in the Union Discord, if `discord_url` is set.
- **"What happens to it"** (muted, `draft="Site owner"`): the 0B copy (Senate committees may track issues in the Senate's Notion; other bodies don't publish a tracker).
- A safety line.
- "Back to all topics".
- The `wagtail` source line at the end of `<main>`.

There is no form, so nothing is collected.

### 5.3 Your reps (`reps_index`, `reps`)

**Index page:** h1 "Who represents you". The same pills as on home, as large buttons in a 2-col grid on mobile and 4-col at md.

**Key page:** h1 such as "Class of 2028: your representatives". Sections:
1. **Your Student Senate seats.** Cards from SEATS where body is senate and the constituency matches.
   - **Filled seat card:** initials avatar (48px circle, brand bg, white text, aria-hidden), name, seat label, "also" roles, and a contact line. The contact line uses the seat's role `inbox` if set. Otherwise it reads "Contact: Union office (this seat has no role inbox yet)", as a mailto to contact_email with the subject "For: <seat>", if contact_email is set. Office hours: "Not listed (shown only if the member opts in)".
   - **Vacant seat card:** dashed border, "Vacant seat", then "How this seat gets filled:" with the seat's `FILL_RULES` text and constitution line (plus its Draft badge if the rule has one). Link "Run for office" → take_part#run.
   - Above the cards, one line: "Your class has 4 Senate seats under the Union Constitution." (graduate: "Graduate students have 7 Senate seats"; independent / fsl: "There are 3 Independent / 3 Fraternity and Sorority Life Senate seats") with cite "Art. VII §1".
2. **Your Executive Board class representative.** Same card style. Under it: "Appointed by the President of the Union and approved by 2/3 of the Senate, not elected." cite "Art. VII §2".
3. **Your Class Council** (class keys 2027–2030 only). A summary box: "Your class also elects a Class Council: a Class President, a Vice President, at least 8 Representatives and your 4 Class Senators. It recommends how your class dues are spent and appoints replacements when a Class Senator seat falls vacant." cite "Art. VII §5; Art. XI §6". Then "Roster not listed yet."
4. **Also representing everyone.** Grand Marshal, President of the Union, Members-at-Large.
5. **Fallback rule.** If a key's Senate seats are all status "elect_fall" (2030):
   - Instead of the seat cards in section 1, show a summary box: "Your class has 4 Senate seats. First-year senators and the first-year Class Council are elected in the fall semester. The latest roster we have (30 Jul 2026) is from before that election." cite "Art. VII §1; Art. VIII §3". Link "How to run" → take_part#run.
   - Then: "Until then, these people represent everyone:" followed by section 4, moved first.
   - The E-Board card shows "Vacant: appointed within three weeks after the fall elections" (cite "Art. VIII §12").
   - Never render an empty page.
6. **Graduate page.** Also shows a Graduate Council box: "The Graduate Council is the advocacy body for graduate students. Its voting members are the 7 Graduate Senators plus at least 5 at-large members, and it elects its own President from among its members. It controls graduate class dues." cite "Art. VII §4; Amendment V". Then: "Graduate Council report at Senate #12: Melissa Flores 'G. E-Board Graduate Council rep: Joydip Paul '29G." with the agenda source line. Do not call anyone the Graduate Council President; the roster doesn't say. Link to issue_topic grad.
7. **Clubs page.** Shows the Club & Organization Reps plus VP for Club Relations and links to funding. Under the reps: "Club and organisation reps are appointed by the President of the Union with 2/3 Senate approval. Clubs don't elect them." cite "Art. VII §2".
8. **Independent and FSL pages.** Show the reconciliation note from `SEATS`.
9. **Your say over these seats** (every key, last section). A short list built from the seat types on the page:
   - If the page has elected senators: "Recall a senator: a petition from 20% of the constituency, or a Senate majority, starts a removal election. 2/3 of those voting removes them, if at least 20% vote." cite "Art. X §2"
   - If the page has a vacant elected seat: "If it's filled by appointment, 20% of the constituency can force an election by petition within two weeks of the announcement." cite "Art. XI §5"
   - Always: "Grand Marshal or President of the Union: removable by a petition from 50% of all students, or by 2/3 in a removal election where at least 20% vote." cite "Art. X §1"
   - Link "All the ways students can act" → take_part.
   - For independent / fsl add `draft="Senate election rules"` to the recall line: the Constitution doesn't define who counts as these seats' constituents.

Footer line on each card group: the `roster` source line, then "Prototype data: Senate agenda 30 Jul 2026 / E-Board agenda 25 Aug 2026."

### 5.4 Meetings & decisions (`meetings`, `meeting`)

**Meetings index:**
- h1 "Meetings and decisions".
- **Upcoming:** same logic and empty state as home.
- **Past meetings:** a table with caption "Past meetings".
  - Columns: Body | Meeting | Date | Agenda | Minutes.
  - Rows link to `meeting`.
  - The Minutes cell says "Not posted ({days} days since meeting)", computed. It is never blank.
  - A "Record" column says "Senate's Notion" or "Entered on this site". Under the table: the `meeting_senate` and `meeting_eboard` source lines.
- **Decisions:** `<h2 id="decided">Decisions</h2>`, a list of Senate motions from DECISIONS with status chips, then the `motions` source line, the "in their minutes" line and the `in_minutes` source line (0B).
- **Bodies that publish records as files** (`<h2 id="files-only">`): see 0B.
- **All files** (`<h2 id="files">`): one `_box_folder.html` per entry in `BOX_FOLDERS`, each with an h3 label. Lead line: "Every agenda, set of minutes and attachment is a PDF in the Union's Box. Files are named like `2026-07-30 Senate 57 #12 Agenda.pdf`, so the newest sort last."
- **How meetings work:** a `<details>` explaining the fixed agenda order in plain words.

**Meeting page** (`/meetings/senate/57/12/`, `/meetings/eboard/fy27/1/`):
- h1 "Student Senate meeting #12". Subline: "57th Student Senate · Thursday 30 July 2026, 8:00 PM ET · Webex".
- **Summary box:**
  - Agenda: "Posted in Box · link not added to the meeting record yet". When a link exists, the row shows "Open agenda (PDF in Box)" as the first, full-width link on phones.
  - Minutes: not posted (N days).
  - Source lines at the bottom of the box: the meeting's record source (`meeting_senate` or `meeting_eboard`), then `file` or its `file_missing_<body>` variant.
  - Quorum: "13 needed (agenda lists 19 voting members)", with the agenda source line. Muted note: "The Union Constitution doesn't set quorum; each body's own rules do."
  - Seats: Senate "29 voting seats under the Constitution · 5 vacant · 4 first-year seats to be elected this fall" (computed from SEATS, cite "Art. VII §1"). E-Board "15 to 20 voting seats under the Constitution · {n} vacant" (cite "Art. VII §2").
  - Who chairs: Senate "The Grand Marshal chairs and votes only to break a tie." (cite "Art. IV §1"). E-Board "The President of the Union chairs and votes only to break a tie; the Director of the Union advises." (cite "Art. IV §2; Art. VII §2").
- **Want to speak?** "Anyone can speak during the Invitation to Speak at the start and end of the meeting. Just attend and wait to be recognised." (`draft="Senate bylaws or rules"`)
- **Agenda:** an `<ol>` of sections with numbers, each followed by its plain gloss in muted text and nested items.
  - Vacant reporters show "Vacant".
  - Empty sections show "Nothing listed".
  - Revised (0B): the agenda is shown as the document first. The numbered list above appears only on Senate pages, inside the labelled "Option for the Senate: the agenda item by item" block, with the `agenda_items_option` source line. E-Board pages never itemise the agenda; the E-Board's contents appear only in the "Prototype only: what this document says" stand-in. The plain glosses are Wagtail-owned explanations, not part of the record.
- **Decisions at this meeting:** Senate: its motions from the Senate's Notion, or "No motions recorded for this meeting in the Senate's Notion." E-Board: "The Executive Board records its decisions in its minutes", with the minutes status and the `in_minutes` source line.
- **Who was on the Senate at this meeting:** a collapsed `<details>` with the membership snapshot (voting, non-voting, vacant), grouped by the constitutional seat groups (Graduate, each class, Independent, FSL), with the reconciliation note under Independent/FSL. For the E-Board, group as in `SEATS` and show the Council and Senate seats as voting. End with the `roster` source line.
- **Files for this term:** the body's `_box_folder.html`.
- **At lg:** a left sticky in-page nav (Summary, Speak, Agenda, Decisions, Members, Files).

### 5.5 Funding (`funding`): start-page pattern

The very top shows a red-bordered warning box: "Draft for testing. The Union Constitution confirms that the Executive Board decides how Union money is handed out, but it doesn't say how a club applies. We have not yet confirmed the steps or who handles requests day to day. Do not use this page to apply."

- h1 "Get money for your club".
- Lead sentence: "The Executive Board hands out Union money, including extra money clubs can ask for during the year." The first clause carries cite "Art. VII §2"; the words "extra money clubs can ask for" carry `draft="E-Board bylaws"`.
- **"What the Constitution says"** (short list, each with its cite, from `BUDGET_RULES`): the E-Board prepares and approves the budget and hands out Union money; the budget and records of extra spending are public; no Union money is spent without an E-Board requisition. Add: "Five to seven Executive Board seats are reserved for club and organisation representatives." (cite "Art. VII §2")
- **"What the last agenda said" table.** Caption "Contingency funds as printed on Executive Board Agenda 01, 25 Aug 2026".
  - Columns: Fund | What it's for | Started with | Left (as printed).
  - No progress bars and no "% left": they would make a quoted figure look live.
  - Reserves row shows "Not applicable" for Started with.
  - Underneath: the `quoted_budget` source line, then the link "Latest figures: the newest E-Board agenda in Box" (the eboard `BOX_FOLDERS` link, or the folder placeholder text if it has no shared link), then: "Allocations from these funds are public records under the Union Constitution. This site will link to them where finance publishes them; it won't retype them." cite "Art. VII §2".
- **"Before you start"** bullet list (each `draft="E-Board bylaws"`): who can apply; what you'll need; when the board meets (link to meetings); how long a decision takes: "to be confirmed". The Constitution says only that club classification follows the Executive Board's bylaws (cite "Art. VII §2").
- **"Steps"** process list (each step `draft="Union staff process"`): talk to your club's Club Financial Advisor → submit a request (owner to confirm) → the E-Board considers it as a Proposal at a meeting → decision recorded in minutes.
- **Start button.** Large and disabled-looking, but still a real link to about#funding-owner, labeled "Start request (link to be confirmed)".
- **"Book the Union Ballroom"** subsection: "Requests to use the Ballroom for special events go to the Executive Board as a 'Special Ballroom Request'" (agenda source line). Add: "The Executive Board manages the business of the facilities the Union runs." (cite "Art. VII §2"). Link to the E-Board meeting page to see examples.
- **"Other ways"**: "Ask the VP for Club Relations" (name from SEATS), Union office hours from SiteSettings.
- The `wagtail` source line at the end of `<main>`: the funding start page is Wagtail-owned. Only the quoted table carries `quoted_budget`.

### 5.6 How the Union works (`about`)

- h1 "How the Union works".
- Intro line: "Everything on this page about who sits where and who decides what comes from the Rensselaer Union Constitution, last amended 6 Feb 2026, unless marked otherwise."
- In-page nav: Bodies · Officers · Committees · Glossary · Get involved · How this site works.
- **Bodies:** the five governing bodies (Art. VII), then Class Councils under the Undergraduate Council. Each body is `<h2 id=…>` (ids: senate, eboard, judicial-board, graduate-council, undergraduate-council, class-councils) with:
  - its GLOSSARY sentence;
  - a "Who sits on it" line: Senate "29 voting seats: 7 Graduate, 4 per undergraduate class, 3 Independent, 3 Fraternity and Sorority Life"; E-Board "15 to 20 voting members: 5 class reps, 5–7 club and organisation reps, 2–5 members-at-large, and one seat each for the Senate, Graduate Council and Undergraduate Council"; Judicial Board "6 voting members and 5 alternates"; Graduate Council "the 7 Graduate Senators and at least 5 at-large members (at least 12, derived)"; Undergraduate Council "the President and Vice President of each Class Council (8, derived)"; Class Councils "Class President, Vice President, at least 8 Representatives and the class's 4 Senators";
  - "Chaired by" line (Grand Marshal; President of the Union; Judicial Board Chairperson; Graduate Council President; Undergraduate Council President; Class President), each noted "votes only to break a tie" except the Graduate Council President ("voting rights set by the Graduate Council's bylaws");
  - the cite (Senate "Art. VII §1", E-Board "Art. VII §2", Judicial Board "Art. VII §3", Graduate Council "Art. VII §4", Undergraduate Council and Class Councils "Art. VII §5");
  - "What you can do here" links (e.g. Senate → Raise an issue, Go to a meeting; Judicial Board → take_part#judicial-board) + leader name where the agendas give one + link to its reps or meeting page. Graduate Council, Undergraduate Council, Class Councils and Judicial Board say "Roster not listed yet".
- **Officers** (`id=officers`): "The Union has five officers: the Grand Marshal, the President of the Union, the Judicial Board Chairperson, the Graduate Council President and the Undergraduate Council President. They must meet regularly to coordinate." cite "Art. IV". Then one line each from GLOSSARY for Grand Marshal, President of the Union, Director of the Union (staff, not an officer) and Senate Treasurer.
- **Committees:** a table with Committee | What it handles (one line, `draft="Senate bylaws or rules"`) | Chair (or Vacant). Under it, the Grand Marshal ex-officio line from `COMMITTEES`.
- **Glossary:** a `<dl>` from GLOSSARY.
- **Get involved** (`id=get-involved`): open seats grouped by body, counted from SEATS (first-year Senate seats listed as "To be elected this fall"). Under each group, that seat type's `FILL_RULES` text and cite. Then "How to run: contact the Elections Commission (Lauren Antao, acting)" (agenda source line; `draft="Senate election rules"`) and a link "Every way to take part" → take_part.
- **Who runs club funding** (`id=funding-owner`): "The Union Constitution gives the Executive Board the power to hand out Union money (Art. VII §2), but not the application steps. We are confirming whether requests go through the Club Financial Advisors, Union staff, or another system." `draft="Union staff process"`.
- **How this site works** (`id=how-this-site-works`, handoff):
  - Lead: as in 0B.
  - **"Each body's records"** table from `OWNERSHIP_BY_BODY`, caption "Each body's records, and where they live" (`draft="Site owner"` on the caption). Columns: Body | Meeting records | Agendas and minutes | Decisions | Roster | Issues. Then the "Each body chooses" line.
  - **"What lives where"** table from `OWNERSHIP_SHARED`, caption "What lives where, and who edits it". Columns: What | Lives in | Who edits | How this site gets it. Rows with `native=True` get a bordered "Written on this site" tag in the first cell.
  - **"The Public Records Standard"**: `RECORDS_STANDARD`.
  - **"Written on this site"** list: name the Wagtail-owned pages in this prototype, linked: the homepage verbs, Raise an issue (topic router), Get money for your club (start page; its quoted table excepted), Run for office or start a petition, How the Union works (bodies, officers, committees, glossary), and site notices.
  - **"To publish a meeting"**: three short lists, one per adapter (`PUBLISH_STEPS_BY_ADAPTER`, see 0B). The example file name is `2026-10-26 Senate 57 #16 Agenda.pdf`. Then the rule: "A meeting record with a Box agenda link, or a correctly named PDF in the folder, is a complete publish."
  - **Rules for officers** (bullets): "To fix a file, use Upload New Version in Box. Don't upload a second copy: the link stays the same and this site follows automatically." · "Never retype what's in a Word document (agenda items, motion text, outcomes): link the file." · "Export Word documents to PDF with accessibility tags; never Print to PDF." · "Budget figures are linked, never retyped." · "If something here looks wrong, use the Edit link shown to officers and fix it at the source."
  - A 6-step term rollover checklist, done on this site (each body on its own schedule): set end dates on last term's assignments; set the new term as current (every seat on this site then shows Vacant automatically); make sure the four first-year Senate seats show "To be elected this fall"; enter new assignments as results come in; check the seat groups still match the Constitution (29 Senate seats, 15–20 E-Board seats; re-check after any amendment); audit who can edit the site admin and the Senate's Notion workspace (at least two owners, on a shared role account); the Senate's Notion copy of the roster updates itself.
  - The `wagtail` source line at the end of `<main>`.

### 5.7 Run for office or start a petition (`take_part`)

This is the one page added after the constitution review. Every process on it is created by the Union Constitution, so it satisfies "no door without a process". Where the Constitution leaves the mechanics to someone else, the page says so plainly and does not offer a button.

- h1 "Run for office or start a petition".
- Lead: "As a Union member you can do more than vote. These are the things the Rensselaer Union Constitution lets any student start." Muted line: "Rensselaer Union Constitution, last amended 6 Feb 2026."
- Jump list (`<ul>` of in-page links) to each `PROCESSES` entry, using its title.
- Each process is a `<section id="{id}">` with `<h2>` title, the lead, then a summary box (panel background, left border) as a `<dl>`: **Who can** (`who`), **What it takes** (`needs`), **When** (`timing`), **What happens next** (`then`). Omit any row whose field is empty; never print an empty label.
- Under the box: "Not set by the Constitution" followed by the `not_set` list and one Draft badge with `why=not_set_why`. Then the constitution line with `cite`.
- `recall` renders its table instead of the summary box. Table has a caption and `th scope`.
- `challenge` renders its example line, computed from SEATS.
- `run` ends with the Elections Commission line and the "See open seats" link.
- `judicial-board` shows "How to file: not published yet" as the first row of its box and has no button.
- No start buttons anywhere on this page: none of these processes has a confirmed submission route yet. The bottom of the page says: "When the Senate publishes petition and ballot rules, each section gets a start button."
- Linked from: home verb 6, about#get-involved, issue_topic pages ("If nothing changes"), issue_topic rights, and the reps "Your say" section. Add a footer link "Your rights as a Union member" → take_part.

## 6. Accessibility checklist (WCAG 2.2 AA)

- One h1 per page. No skipped heading levels. Landmarks: header, nav, main, footer.
- All text contrast at least 4.5:1. Use brand #a50015 for text and links, never #d6001c for small text.
- Status is never conveyed by colour alone: a chip always contains the word.
- Every date rendered with the year in `<time datetime="YYYY-MM-DD">`.
- Tables have a `<caption>` and `<th scope>`.
- Focus is always visible (yellow/black). Tap targets at least 44×44.
- Works with JS off: the only JS is the localStorage reps shortcut.
- Decorative icons get `aria-hidden="true"`.
- The `<details>` menu is keyboard operable by default.
- Zoom to 200% and a 320px width cause no horizontal scroll.

## 7. Tests (`tests.py`)

Use `django.test.TestCase` with the client. Assert status 200 for:
- home, issue_index, issue_topic dining, issue_topic rights, reps 2028, reps 2030, reps fsl, meetings, meeting senate/57/12, meeting eboard/fy27/1, funding, take_part, about.

Also assert:
- 404 for reps/1999, and for meeting senate/57/99.
- The reps 2030 page contains "represent everyone" and "elected in the fall semester".
- The reps fsl page contains "Fraternity and Sorority Life" and "two separate groups".
- No page response contains "Greek & Independent" outside the reconciliation note (assert the home and about pages don't contain it), and no page contains "RUGP".
- The take_part page contains "10%", "Judicial Board" and "Union Constitution, Art. XII".
- The meeting senate/57/12 page contains "29 voting seats".
- The home page contains "Prototype".
- `data.py` sanity: Senate seats in `SEATS` (excluding Grand Marshal) number exactly 29, and Executive Board voting seats (excluding President and the three VP officer titles) number between 15 and 20.
- Single source of truth, per body (revised):
  - meeting senate/57/12 contains "Meeting record: Senate's Notion · synced 12 min ago", "Document: Box", "Prototype only: what this document says" and "Option for the Senate".
  - meeting eboard/fy27/1 contains "entered on this site by the E-Board Secretary" and "records its decisions in its minutes", and does not contain "Option for the Senate". With `?officer=1` it does not contain "Edit in Notion".
  - meetings contains "Bodies that publish records as files", "Graduate Council", "Undergraduate Council" and "Judicial Board", and "publishes its records as files" at least 3 times.
  - Every entry in `logic.decisions()` has body "Student Senate". No row of `OWNERSHIP_BY_BODY` other than the Senate's contains "Notion".
  - about contains "Each body's records", "The Public Records Standard" and "accessibility tags".
  - Without `?officer=1`, meeting senate/57/12 does not contain "Edit in Notion". With `?officer=1` it does, and the response sets the `lab_officer` cookie. A later request with `?officer=0` doesn't contain it.
  - funding contains "Quoted from Executive Board Agenda 01" and does not contain "% left".
  - about contains "What lives where", "Upload New Version" and "Written on this site".
  - meetings contains "Box folder embed goes here".
  - No `SEATS` entry has a non-None `inbox`. With the empty test DB there is no contact_email, so assert that the reps 2028 and issue_topic dining pages contain no "mailto:".

Run with `DATA_DIR=<scratch dir> env/bin/python manage.py test lab`. The test DB is created fresh, so the fallbacks get exercised. Also run `env/bin/python manage.py check`.