# Prototype spec: Public Record + Desk

**Slug:** `the-record`  
**Recommended:** False  
**Thesis:** Transparency first, for repeat users: the press, officers, and students checking what passed. Dense, fast listings of meetings, decisions and money, with plain status words. Every listing is a read-only view of where each body keeps its records: the Senate's Notion, the E-Board's entries on this site, or a body's Box folder. An officer Desk and a health page check every body against one Public Records Standard, and show what's missing and where to fix it. The two-minute test times each body's real workflow.

# Prototype: Public Record + Desk (`the-record`)

## 0. Ground rules

This builds one self-contained prototype in the existing `lab` app at `/Users/aaron/src/stugov-site`. Wagtail 7.3 / Django 6.0. Use `env/bin/python`.

**Do not edit** `lab/urls.py`, `lab/views.py`, `lab/prototypes/__init__.py`, anything under `stugov/`, or any model. Create no migrations and add no dependencies.

**Create these files:**
```
lab/prototypes/the_record/{__init__.py,urls.py,views.py,data.py,tests.py}
lab/templates/lab/the-record/*.html   # includes _sample.html, _draft.html, _cite.html, _source.html, _box_folder.html
```

**`META` in `__init__.py`:**
```python
META = {"name": "Public Record + Desk", "thesis": "Transparency first: meetings, decisions and money as dense, searchable records, read from wherever each body keeps them (the Senate's Notion, entries on this site, Box folders); plus an officer Desk and health page that check every body against one Public Records Standard.", "recommended": False}
```

**Wiring:** mounted at `/lab/the-record/`. Namespace `lab:the_record`.

**Database:** the default dev DB is EMPTY (no tables). Wrap every DB read in `try/except DatabaseError` and fall back to `data.py`. Reads only; never save or send email.

**Content labelling:**
- Every page has a top banner: "Prototype layout for testing. Not the official site. Items marked Sample are made up." plus a link to `/lab/`.
- Fabricated values carry a `Sample` pill (`_sample.html`).
- Real values from the agendas carry a source line, e.g. "Source: Executive Board Agenda 01, 25 Aug 2026".
- Facts confirmed by the Rensselaer Union Constitution (last amended 6 Feb 2026) carry no badge. They get a muted constitution line via `{% include 'lab/the-record/_cite.html' with art="Art. VII §2" %}`, rendering "Source: Union Constitution, Art. VII §2". In `data.py` such entries carry `cite`.
- The `Draft: confirm` pill (`_draft.html`, called `with why="..."`) is only for things the Constitution leaves to someone else. Its `title` reads "Not set by the Union Constitution. Confirm with: {{ why }}". Allowed `why`: "Senate bylaws or rules", "Senate election rules", "E-Board bylaws", "Judicial Board bylaws", "Union staff process", "Site owner". In `data.py` such entries carry `draft="<why>"`. Never name "RUGP" on any page: the Constitution doesn't mention it.
- Numbers marked "derived" are our arithmetic and render with "(derived)", whose `title` reads "Our arithmetic, assuming all 29 Senate seats count". The Constitution doesn't say whether vacant seats count toward "total voting membership".
- Naming: say "Fraternity and Sorority Life (FSL)", not "Greek" (renamed by Amendment VI, Feb 2026). The agendas' combined "Greek & Independent Senators" heading is shown only inside the reconciliation note (see Membership snapshots).

## 0A. Single source of truth (read before building)

This prototype's job is to show a public record that **nobody types into the website**. Every listing is a read-only view of the system that owns the fact. The officer pages show what that view currently contains, what is missing, and where to fix it. The background is in `docs/redesign/data-architecture.md`, but you don't need to read it to build this.

**Who owns what**
- **Box** owns files. Agendas, minutes and motions are **written in Word** and published as PDFs in each body's public Box folder. **There is no Box API and there never will be.** The site can't list, sync, scrape or parse Box, and it can't detect filenames. It only uses Box shared links that a secretary pastes, Box file and folder embeds (`/embed/s/<id>`; Box's preview renders PDF and Word), and a weekly status check on pasted links (404, or an RPI login page).
- **Each body keeps its own meeting records** (revised, see 0B):
  - **Senate:** the Senate's Notion. "Meetings" holds term, number, date and time, place, `Agenda` (URL), `Minutes` (URL), `Minutes approved` (date) and `Public`. "Motions" holds a short label, meeting, status, `Motion file` (URL) and `Public`. A one-way sync copies Public rows and whitelisted fields every 15 minutes. Attendance and contacts stay in Notion and are never synced.
  - **Executive Board:** a minimal meeting entry on this site. This is shown as an example choice.
  - **Graduate Council, Undergraduate Council, Judicial Board:** their Box folder only.
- **The content of a Word document stays in the Word document.** Agenda items, motion text and outcomes as minuted are never retyped. Senate motion *status* is a new fact the secretary records once in Notion. Every other body's decisions are in its minutes.
- **The roster** (seats, people, term assignments) is owned by this site for every body. The Senate's Notion gets a read-only copy for attendance.
- **Budget figures** belong to Business Operations and Union finance and are printed on E-Board agendas. The site quotes one agenda, links to the source, and never keeps its own copy.
- **Wagtail (this site)** also owns the explanations: the rules page, body descriptions, the "What is this?" glosses, the vote-threshold and petition tables, site notices, and the Desk's handoff text.

Nothing in this prototype connects to Box or Notion. Every sync time, link-check result and health flag is seed data, and the banner says so.

**Rules for this prototype**
- No page has a form that asks an officer to type something that lives in Box or the Senate's Notion, or the contents of a Word document. The Desk's Senate panel is a clearly labelled *stand-in for Notion* (section 5.8). The site-entry form exists only for bodies that chose "entered on this site".
- Nothing implies that the Executive Board, the Councils or the Judicial Board use Notion.
- Every projected item (meeting, agenda item, decision, membership snapshot, quoted budget figure) shows a muted **source line** from `_source.html`.
- Wagtail-owned pages (rules, and the explanatory blocks on home) end with the Wagtail source line: "Written on this site · reviewed 21 Oct 2026".
- The Constitution `_cite.html` line and the "Source: … agenda" line stay as they are. They tell testers where *we* got a fact. The new source line says which *system* would own it in production.

**Seed in `data.py`**
```python
SYNC = {
    "notion_minutes_ago": 12,                  # renders "synced 12 min ago"
    "notion_last_success": datetime(2026, 10, 21, 13, 48, tzinfo=NY),
    "notion_next_run_minutes": 3,
    "notion_last_error": None,
    "webhook_last": "2 hours ago",             # webhooks only trigger an early sync
    "box_links_checked": date(2026, 10, 19),   # weekly status check of pasted links
    "wagtail_reviewed": date(2026, 10, 21),
}
MOCK_NOTION = "https://www.notion.so/"   # every "Edit in Notion" / "Fix in Notion" link points here
MOCK_BOX = "https://rpi.box.com/"        # every "Edit in Box" / "Fix in Box" link points here
```
`NY = ZoneInfo("America/New_York")`.

`SOURCES` is a dict keyed by source key. Each value is `{key, line, edit_label, edit_url}`. Build `line` from `SYNC` with a helper, never by hard-coding "12".

| key | `line` as rendered | `edit_label` → `edit_url` |
|---|---|---|
| `meeting_senate` | "Meeting record: Senate's Notion · synced 12 min ago" | "Edit in Notion" → MOCK_NOTION |
| `meeting_eboard` | "Meeting record: entered on this site by the E-Board Secretary · updated 24 Aug 2026" | "Edit on this site" → `/admin/` |
| `folder_only` | "Records: files in this body's Box folder. It doesn't list meetings on this site." | "Open in Box" → MOCK_BOX |
| `agenda_items_option` | "Agenda items: Senate's Notion agenda page · only if the Senate drafts agendas in Notion (an option, not current practice) · synced 12 min ago" | "Edit in Notion" → MOCK_NOTION |
| `file` | "Documents: Word files in Box, published as PDF · links checked 19 Oct 2026" | "Edit in Box" → MOCK_BOX |
| `motions` | "Motion status: Senate's Notion Motions table · the motion's text is in the linked Word file · synced 12 min ago" | "Edit in Notion" → MOCK_NOTION |
| `in_minutes` | "Decisions: recorded in the minutes (a Word file in Box). This site doesn't retype them." | "Open in Box" → MOCK_BOX |
| `roster` | "Roster: entered on this site by each body's roster officer · last change 25 Aug 2026" | "Edit on this site" → `/admin/` |
| `quoted_budget` | "Quoted from Executive Board Agenda 01, 25 Aug 2026 (a PDF in Box). This site does not update these figures." | "Open in Box" → MOCK_BOX |
| `wagtail` | "Written on this site · reviewed 21 Oct 2026" | "Edit in Wagtail" → `/admin/` |

**`_source.html`**, called as `{% include 'lab/the-record/_source.html' with s=sources.meeting %}`, renders:
`<p class="text-sm text-muted" data-source="{{ s.key }}">{{ s.line }}{% if officer %} · <a href="{{ s.edit_url }}" rel="nofollow">{{ s.edit_label }}</a> <span class="text-xs">(mock link)</span>{% endif %}</p>`

**Officer view (mock, no login)**
- Write one helper, `page(request, template, ctx)`, in `views.py` and have every view call it. It adds `sources`, `sync` and `officer` to the context.
- `officer` is True when the URL has `?officer=1`, or when the cookie `lab_officer=1` is set and the URL doesn't have `?officer=0`. The Desk and health pages always render with `officer=True`.
- `?officer=1` sets the cookie `lab_officer=1` (path `/lab/`, session cookie, SameSite Lax). `?officer=0` deletes it.
- The prototype banner gets a toggle. In student mode it reads "Viewing as a student · Show officer links" and links to `?officer=1`. In officer mode it reads "Viewing as an officer (mock) · Hide officer links" and links to `?officer=0`, with the muted line "On the real site these links appear only to signed-in officers."
- Officer mode only reveals the "Edit in …" links. It reveals no extra data.

**Banner text** gains a second sentence: "Lines like 'synced 12 min ago' are simulated. Nothing here is connected to Notion or Box. Only the Senate's items would come from Notion."

**Box folders**
```python
BOX_FOLDERS = {
    "senate": {"label": "Student Senate, 57th Senate", "path": "Public Records/Senate/2026-27 Senate 57/", "shared_url": None},
    "eboard": {"label": "Executive Board, FY27", "path": "Public Records/Executive Board/2026-27 EBoard FY27/", "shared_url": None},
}
```
`_box_folder.html` works like this:
- If `shared_url` contains `/s/`, show the link "Open the folder in Box" first. Then, at `sm` and up only, show `<iframe title="Box folder: {{ path }}" src="{{ embed_url }}" class="hidden sm:block w-full h-[28rem] border">`, where `embed_url` is the shared URL with `/s/` replaced by `/embed/s/`. On phones only the link shows.
- Otherwise, show a dashed placeholder box: "Box folder embed goes here: {{ path }}. The shared link hasn't been added yet."
- Don't build an embed from `SiteSettings.box_archive_url`. It is a `/v/` vanity link, and the embed conversion only handles `/s/` links. If it's set, show it only as a plain "Whole Box archive" link.

**Box naming convention** (shown on the Desk). Pattern: `YYYY-MM-DD <Body> <Term> #<nn> <Agenda|Minutes|Attachment - Title>.pdf`, inside `Public Records/<Body>/<YYYY-YY Body Term>/`. Body codes: `Senate`, `EBoard`, `JBoard`, `GC`, `UC`. `RENAMES` (today's name → convention):
- `#12 07_30_26 57th Student Senate Meeting Agenda-1.pdf` → `2026-07-30 Senate 57 #12 Agenda.pdf`
- `FY27 Agenda 1 - August 25, 2026.pdf` → `2026-08-25 EBoard FY27 #01 Agenda.pdf`

The site can't check filenames, because it has no Box API. The convention helps people browsing the folder embed.

## 0B. Per-body records (revision, 21 Oct 2026)

The site owner told us that agendas, minutes and motions are written in Word, and that only the Senate is adopting Notion. How the E-Board, the Councils and the Judicial Board organise themselves is their business, as long as their public records are strong. This section describes how the built prototype changes. Where it conflicts with later sections, this section wins. The page count stays at 9.

**Bodies and adapters**
- `BODIES` entries gain `adapter`, `adapter_label` and `records_officer`:
  - senate: `notion`, "Senate's Notion", "Senate Secretary".
  - eboard: `site`, "Entered on this site", "E-Board Secretary". This is an *example* choice, rendered with "Example choice: the E-Board hasn't decided" and `draft="Site owner"`.
- A new `FOLDER_BODIES` dict holds the bodies with no meeting records, in this order: `gc` "Graduate Council", `uc` "Undergraduate Council" (note: "including the four Class Councils"), `jboard` "Judicial Board". Each has `adapter="folder"`, `records_officer=None` and `records_confirmed=None`.
- `BOX_FOLDERS` gains `gc`, `uc` and `jboard`, paths `Public Records/<Graduate Council|Undergraduate Council|Judicial Board>/2026-27 <GC|UC|JBoard> 2026-27/`, with `shared_url` None.
- Meeting dicts rename `notion_edited` to `record_edited`. A meeting's source line, its "Last edited" label and its fix link (Senate "Fix in Notion" → MOCK_NOTION; E-Board "Fix on this site" → `/admin/`) all come from its body's adapter.

**`RECORDS_STANDARD`** (shown on the Desk and the health page, heading "The Public Records Standard", `draft="Site owner"`). A list of `{rule, check}`:
- "Agenda in the body's public Box folder 24 hours before the meeting" · "From the agenda link on the meeting record; flagged from 2 days out"
- "Draft or approved minutes in the folder within 14 days" · "From the minutes link"
- "Approved minutes within 3 days of approval, uploaded as a new version of the draft" · "From the Minutes approved date"
- "Motion text in the folder before the vote" · "Senate only: the file link on the Motions row"
- "PDFs exported from Word with accessibility tags; never printed to PDF or scanned" · "Not checked automatically"
- "Files named `YYYY-MM-DD <Body> <Term> #<nn> <Agenda|Minutes|Motion - Title>.pdf`; corrections use Upload New Version" · "Pasted links are checked against the pattern"
- "Each body names a records officer" · "From the body settings on this site"
- "Folder-only bodies confirm once a month that their folder is complete" · "From the 'records last confirmed' date"
- Under the list: "The Judicial Board publishes its rulings on what the Constitution means. Its conduct and rights cases are confidential." (`draft="Judicial Board bylaws"`)

**Agendas are documents**
- The meeting page's Agenda section first shows the **document**. If linked: "Open agenda (PDF)" first, then a Box preview iframe at `sm` and up. If not linked: a dashed box, "Box preview of `<document_name>` goes here. The link hasn't been added to the meeting record yet." Each meeting gets a `document_name`, e.g. `2026-08-25 EBoard FY27 #01 Agenda.pdf`.
- Under it, a `<details>` titled "Prototype only: what this document says". It holds the sections as plain document text, with no links or chips, and the note: "Typed from the PDF so testers can try tasks. The real site shows the Box preview and never retypes a Word document."
- **Senate meetings only** get a view switch, `<nav aria-label="How this agenda is shown">`, with two links:
  - "As the document (today)": the default.
  - "Item by item (option: only if the Senate drafts agendas in Notion)": `?agenda=items`. This renders the existing numbered agenda with glosses, under the heading "Option for the Senate: the agenda item by item", with the `agenda_items_option` source line and the note: "The Senate hasn't chosen this. Today its agendas are written in Word."
- E-Board pages never itemise. Instead they show: "Item-by-item agendas aren't shown for the Executive Board. It writes its agendas in Word, and this site never retypes them."

**Decisions are Senate motions**
- `DECISIONS` = the sample Senate motions only. Remove `_real_decisions()` and the `decision_id`s on the E-Board ballroom items; those items survive only in the E-Board document stand-in.
- Rewrite the two E-Board samples as Senate motions:
  - `sample-senate-failed`: "Senate 57 #13, item 8a", "Moves regular Senate meetings to Monday evenings", motion, Rules and Administration Committee, failed.
  - `sample-senate-done`: "Senate 57 #14, item 8b", "Puts the Webex link and the full date on every Senate meeting notice", resolution, Senate Communications and Engagement Committee, done, with the 3-step history and outcome note.
- Every decision gains `motion_file` (Sample link) and `motion_file_name`, e.g. `2026-09-23 Senate 57 #14 Motion - Webex link on notices.pdf`. The decision page's Sources show "Motion text: <file name> (Word file in Box, as PDF)".
- The decisions tracker explainer: "Decisions here are Senate motions. The Senate's secretary records each motion's status once, at the vote, in the Senate's Notion Motions table, with a link to the motion's text in Box. The Executive Board, Graduate Council, Undergraduate Council and Judicial Board record decisions in their minutes and rulings, published as files." Link to meetings#files.
- Filtering by `body=eboard` shows "The Executive Board records its decisions in its minutes", with its folder link, instead of "No decisions match".

**Meetings and home**
- The meetings page body filter adds Graduate Council, Undergraduate Council and Judicial Board. Choosing one shows that body's folder panel: "The {name} publishes its records as files. It doesn't list meetings on this site.", with `_box_folder.html` and the `folder_only` source line.
- With no filter, the meetings page adds `<h2 id="files-only">Bodies that publish records as files</h2>`, with the three panels.
- Home's "Next meeting per body" keeps the Senate and E-Board cards. Under them, one line per folder body: "{name}: publishes records as files · Open folder".
- The tables gain a "Record" column: "Senate's Notion" / "Entered on this site".

**Desk path switch (three paths)**
- `?path=notion` "Senate (Notion)": the default. The stand-in panel's Body select offers only Senate.
- `?path=site` "Entered on this site (E-Board, example)": the old `path=wagtail` form, which `wagtail` still aliases. The Body select offers only E-Board. **Remove** the "Add agenda items now" checkbox and the item inputs: retyping a Word agenda's items is double entry.
- `?path=folder` "Folder only (Graduate Council, Undergraduate Council, Judicial Board)": no form, no POST.
- Under the switch: "Each body chooses. A body's meetings live in one place, never two."

**Desk section C "Recording outcomes"**
- Senate: "Each motion is a row in the Senate's Notion Motions table: a short label, the meeting, its status, and a link to the motion's Word or PDF file in Box. The secretary sets the status once, at the vote. The motion's text stays in the file. Build the minutes' list of motions from the Notion view rather than typing outcomes twice."
- Every other body: "Outcomes are in the body's minutes. This site links the minutes and never retypes them."
- `MOTIONS_MOCK` becomes two Senate rows, Motion | Meeting | Status | Motion text | Public:
  - "Committee reporting bylaws" · Senate 57 #15 · Waiting on a vote · `2026-10-14 Senate 57 #15 Motion - Committee reporting bylaws.pdf` · ☑
  - "Webex link on meeting notices" · Senate 57 #14 · Passed · `2026-09-23 Senate 57 #14 Motion - Webex link on notices.pdf` · ☑
  - Caption: "What the Senate's Motions table in Notion would look like (Sample)".

**Health checks by body**
- Every check row gains `body`.
- Agenda timing follows the Standard. 1 day or less before the meeting is `overdue` ("Agenda due 24 hours before the meeting"). 2 days out is `soon`. Further out is `waiting` ("flagged from <meeting − 2 days>").
- "Public is unticked in Notion" applies to Senate meetings only.
- Minutes rows keep the check text "Minutes link missing" and add "(Standard: 14 days)" to the item, e.g. "E-Board FY27 #1 · 25 Aug 2026 · 57 days (Standard: 14 days)".
- New `standard_checks(today)`:
  - For each folder body, a `check` row: "Folder only: can't check deadlines automatically · records last confirmed complete: never · no records officer named". Owner "<Body> (records officer not named)". "Fix on this site".
  - For every body whose folder `shared_url` is None, a `check` row: "Box folder shared link not added". "Fix in Box".
- Roster rows say "Fix on this site" / "Record on this site when filled" (→ `/admin/`), because the roster is Wagtail-owned for every body.
- The Sample schema row becomes: "Schema change: Senate Motions property 'Status' (id `qT%3Fb`) not found…", item "Senate's Notion · Motions".
- Add an `ok` row: "Roster copy in the Senate's Notion: up to date (pushed 12 min ago)".
- `NOT_CHECKED` adds: "What's inside the Graduate Council, Undergraduate Council and Judicial Board folders: without the Box API the site can't see their files, so it relies on each records officer confirming." · "Whether a PDF is tagged for accessibility, or whether a file's contents match its record." Attendance becomes: "Attendance: private in the Senate's Notion, never synced."
- The health page gains section **"2. Public Records Standard, by body"**, and later sections renumber. It's a table with caption "Each body against the Public Records Standard". Columns: Body | How the site gets its records | Records officer | Agendas (24 h before) | Minutes (within 14 days) | Folder link | Overall (severity chip). Every value is computed from the checks:
  - Senate: "Senate's Notion" · "Senate Secretary" · "Next: Senate 57 #16, link not added · flagged from 24 Oct" · "3 meetings past 14 days with no minutes link (oldest: #12, 83 days) · #15 due by 28 Oct 2026" · "Not added" · Overdue.
  - E-Board: "Entered on this site (example)" · "E-Board Secretary" · "No upcoming meeting listed" · "4 meetings past 14 days with no minutes link (oldest: #1, 57 days)" · "Not added" · Overdue.
  - (Counts are computed from `meeting_checks`; the values above are what the seed gives on 21 Oct 2026.)
  - Graduate Council, Undergraduate Council, Judicial Board: "Box folder only" · "Not named" · "Can't check: folder only" · "Can't check: folder only; records last confirmed: never" · "Not added" · Check.
- The sync panel says: "Senate's Notion: Meetings, Motions, Issues synced in", "Roster copy pushed out to the Senate's Notion: Senators (from website)". The counts are computed from the seed.

**Desk "How this site works"**
- `WHAT_LIVES_WHERE` splits into `RECORDS_BY_BODY`, a table with caption "Each body's records". Columns: Body | Meeting records | Agendas and minutes | Decisions | Roster | Issues. Rows:
  - Senate: Senate's Notion · Word in Box as PDF, link in the Notion row · Notion Motions status plus the file · this site (VGMIA), copied to Notion · Senate's Notion Issues.
  - E-Board (example): entered on this site · Word in Box as PDF, link on this site · in its minutes · this site (VP Rules and Special Projects) · not tracked publicly.
  - Graduate Council / Undergraduate Council / Judicial Board (examples): none, Box folder only · their folder · in their minutes or rulings · this site once named · not tracked publicly.
- Then the shared rows: the budget, Wagtail-owned explanations, notices, and "Senate attendance, contacts, internal notes · Senate's Notion · never shown".
- Then `RECORDS_STANDARD`. The "voting members and quorum" proposal row becomes a Senate-only Notion property proposal.
- `NEVER_LIST`:
  - "a 'post a meeting' form for the Senate: its meetings come from its Notion"
  - "retyping or parsing a Word agenda, motion or minutes"
  - "editing in this site anything the Senate's Notion owns"
  - "requiring any body other than the Senate to use Notion"
  - "retyped budget numbers"
  - "calendar entries made by hand for meetings"
  - "a second file host: no PDFs uploaded to this site"
- `OFFICER_RULES` adds "Export Word documents to PDF with accessibility tags (File, Save As, PDF); never Print to PDF."
- The rollover section heading becomes "Term rollover, done on this site". Its last step reads: "…audit who can edit the site admin and the Senate's Notion workspace. The Senate's Notion copy of the roster updates itself."
- The footer reads: "Files live in Box. The Senate's meeting records come from its Notion; the E-Board's are entered on this site; other bodies publish files only. The roster is kept on this site."

## 1. Seed data (`data.py`): real facts from the two agendas and the Union Constitution

**Meetings.** Store both meetings as dicts. Keys: `body`, `body_name`, `term_slug`, `term_label`, `number`, `starts` (aware datetime America/New_York), `location`, `remote`, `agenda_status`, `agenda_url` (None), `minutes_status`, `minutes_url` (None), `minutes_approved` (date or None), `public` (True: the Notion row's Public box), `notion_edited` (aware datetime: when the row was last edited in Notion), `voting_listed`, `quorum`, `nonvoting` (these three are the agenda header's figures), `seats_constitution`, `seats_cite`, `sections` (each `{title, plain, items:[{title, who, type, decision_id?}]}`).

These dicts stand in for synced rows from the Notion Meetings database. Each meeting's agenda and minutes status is derived from its links: a link present means "posted". The two real agendas exist as PDFs but have no Box shared link yet. So the seed keeps `agenda_status="posted"` with `agenda_url=None`, and pages say "Agenda posted in Box · link not added to the meeting record yet". The health page flags it. There is no recording field: recordings have no owner yet.

**Senate meeting.** 57th Student Senate #12, term_slug "57", notion_edited 2026-07-28 21:10.
- 2026-07-30 20:00, Webex. Agenda header: voting_listed 19, quorum 13, nonvoting 10. seats_constitution 29, seats_cite "Art. VII §1". The Constitution doesn't set quorum.
- Agenda posted. Minutes not posted.
- Sections in order:
  1. Bookkeeping (a. Polytechnic Statement of Recording)
  2. Invitation to Speak and Press & Visitor Q/A
  3. Grand Marshal Report
  4. Committee Reports
     - Academic Affairs, Zach Nobles '27
     - Community Relations, Mia Stryhalaleck '28
     - Elections Commission, Lauren Antao '28
     - Facilities and Services, Charlie Fowle '29
     - Residential Living and Dining, Shruthi Anandraman '28
     - Rules and Administration, Griffin Oliver '27
     - Student Life, Stanley Goodwin '30G
     - Senate Communications and Engagement, Emily Lin '29
     - Web Technologies Group, Aaron Niyazov '28
     - Union Annual Report, Samson Kempiak '28
  5. Peer Body & Officer Reports
     - VGMEA, Ryan Kilgore '27
     - VGMIA, Griffin Oliver '27
     - Executive Board, Cee Ray '27
     - Graduate Council, Melissa Flores 'G
     - Undergraduate Council, Nick Castiglione '28
     - Interfraternity Council, Vacant
     - Panhellenic Council, Vacant
     - Multicultural Sorority and Fraternity Council, Vacant
     - Treasurer, Cee Ray '27 (display "Senate Treasurer"; the Constitution's "Treasurer" is RPI's own Treasurer, Art. VI)
     - Secretary, Selena Tang '29
     - Parliamentarian, Sasha Notkin '28
  6. Special Orders
  7. Old Business
  8. New Business
  9. Invitation to Speak and Press & Visitor Q/A

**E-Board meeting.** 2026–27 Executive Board (FY27) Agenda 01, term_slug "fy27", notion_edited 2026-08-24 16:02.
- 2026-08-25 19:00, RU 3202. Agenda header: voting_listed 12, quorum 8, nonvoting 7. seats_constitution "15 to 20", seats_cite "Art. VII §2".
- Agenda posted. Minutes not posted.
- Sections:
  1. Approval of Minutes
  2. Reports
     - President Kate Goldstein '26 '27G
     - VP Board Operations Gavin Finn '28
     - VP Club Relations Jesse Kim '26 '27G
     - VP Rules and Special Projects Blaine Rosenberg '28
     - Director's Report Dr. Charlie Potts
     - Student Senate Cee Ray '27
     - Undergraduate Council Vacant
     - Graduate Council Joydip Paul '29G
     - Committee reports: Business Operations (Grey Smith '27), Club Operations (Elijah Pulga '29), Marketing & Strategy (Vacant), Executive Communication (Vacant), Multicultural Leadership Council (Mariam Toure '28), Union Annual Report (Ava Cintula '29), Union Programming and Activities Committee (Lilu Kaufman '26)
  3. Proposals
     - Special Ballroom Request, Society of Women Engineers (decision_id "eb-fy27-01-a")
     - Special Ballroom Request, RPI Admissions (decision_id "eb-fy27-01-b")
  4. Business: Rally Week Discussion
  5. Invitation to Speak
  6. Press & Visitor Q/A

**Add one SAMPLE upcoming meeting** (`sample=True`):
- Student Senate #13, 57th Senate, Monday 26 Oct 2026, 7:00 PM, "Location to be confirmed".
- agenda_status "not_posted". notion_edited 2026-10-19 18:30.
- This demonstrates the honest "Agenda not posted yet" state.

**Add one SAMPLE past meeting** (`sample=True`) to show both the "links present" state and the PDF-only path:
- Student Senate #11, 57th Senate, Thursday 16 Jul 2026, 8:00 PM, Webex. notion_edited 2026-07-31 10:05.
- `agenda_url = MOCK_BOX + "s/sample-senate-57-11-agenda"`, `minutes_url = MOCK_BOX + "s/sample-senate-57-11-minutes"`, `minutes_approved` date(2026, 7, 30). Both links carry the Sample pill wherever they render.
- `seats_constitution` and `seats_cite` as for #12. `voting_listed`, `quorum` and `nonvoting` are None and render "Not recorded".
- `sections = []`. The meeting page then shows: "This agenda was written in Word, so its items aren't in Notion. Open the agenda PDF in Box." This is the PDF-only path, and it is a complete publish.
- Its minutes link fails the sample link check (see `LINK_CHECKS`).

**Decisions and the record** (revised, see 0B). Decisions are Senate motions from the Senate's Notion Motions table: status recorded once at the vote, text in a linked Word file. They are never derived from agenda items. The real E-Board ballroom requests stay inside the E-Board agenda document, and E-Board outcomes stay in its minutes. Render every decision with the `motions` source line.

**Decisions.** Each decision is a dict. Keys: `id` (slug), `ref` (display reference; use the meeting-based reference "E-Board FY27 #1, item 3a" instead of an invented bill number; the Constitution sets no numbering scheme), `title`, `plain_summary` (required, ≤200 chars), `body`, `term_label`, `type` (proposal|motion|resolution|appointment|bylaw|fee|referendum), `requested_by`, `status`, `threshold` (a key into `THRESHOLDS`, or None), `history:[{date, meeting_ref, text}]`, `outcome_note`, `sample`.

Status vocabulary, in plain words:
- `on_agenda`: "On the agenda"
- `waiting`: "Waiting on a vote"
- `passed`: "Passed"
- `failed`: "Didn't pass"
- `tabled`: "Postponed"
- `done`: "Done: here's what changed"
- `not_recorded`: "Outcome not recorded yet"
- `overturned`: "Ruled unconstitutional" (the Judicial Board can declare any Senate, E-Board or council legislation unconstitutional, cite "Art. VII §3"). No seed decision uses it; it exists so the filter and chip styles cover it. Chip: gray-900 on white with a solid 2px border.

Real decisions:
- **eb-fy27-01-a.** Ballroom request from Society of Women Engineers. Plain summary: "Asks to book the Union Ballroom for a Society of Women Engineers event." Status `not_recorded`. threshold None (renders "Votes needed: not set by the Constitution" with `draft="E-Board bylaws"`). History: 25 Aug 2026, "On E-Board Agenda 01 as a proposal".
- **eb-fy27-01-b.** Same, for RPI Admissions.

Add 5 SAMPLE decisions across both bodies, dated Sep to Oct 2026, covering each of passed / failed / tabled / done / waiting. Requested_by is a committee name, never a real person's name. Give the `done` one a 3-step history and an outcome_note. At least two samples must use constitutional thresholds so the "Votes needed" line can be tested:
- a Senate `appointment`: "Approves the President of the Union's appointment of two Members-at-Large to the Executive Board" (no names), threshold `eb_appointment`, status passed.
- a Senate `bylaw`: "Changes the Senate's bylaws on committee reporting", threshold `senate_bylaws`, status waiting.
The other samples use threshold None ("Votes needed: not set by the Constitution", `draft="Senate bylaws or rules"`).

**`THRESHOLDS`** (votes the Constitution requires). Dict keyed by slug; each `{action, body, needs, derived, cite}`. `derived` is the arithmetic for a full 29-seat Senate, or None.
- `senate_bylaws`: "Pass or change Senate bylaws" · Senate · "2/3 of all voting seats" · "20 of 29" · "Art. VII §1"
- `activity_fee`: "Set the Union Activity Fee" · Senate · "2/3 of all voting seats" · "20 of 29" · "Art. VII §1"
- `eb_appointment`: "Approve the President's Executive Board appointments" · Senate · "2/3 of the Senate" · None · "Art. VII §2"
- `eb_replacement`: "Replace an Executive Board member mid-year" · E-Board then Senate · "President appoints; majority of the E-Board, then 2/3 of the Senate" · None · "Art. VII §2"
- `eb_bylaws`: "Pass Executive Board bylaws" · E-Board then Senate · "2/3 of all E-Board voting seats, then a Senate majority" · None · "Art. VII §2"
- `pu_other_appointment`: "Ratify the President's appointments other than E-Board members" · E-Board · "2/3 of the E-Board" · None · "Art. IV §2"
- `gm_nullify`: "Cancel an appointment made by the Grand Marshal" · Senate · "Majority of all voting seats" · "15 of 29" · "Art. IV §1"
- `jb_appointment`: "Approve a new Judicial Board member" · Judicial Board then Senate · "2/3 of the Judicial Board, then 2/3 of the Senate" · None · "Art. VII §3"
- `referendum_ballot`: "Put a question to a student vote" · Senate · "2/3 vote" · None · "Art. XII §1"
- `referendum_reject`: "Refuse a referendum petition signed by 10% of students" · Senate · "2/3 of all voting seats" · "20 of 29" · "Art. XII §1"
- `removal_call`: "Call a removal election for the Grand Marshal, President of the Union, or a Council President" · Senate · "2/3 vote, or a Senate majority after a 20% petition" · None · "Art. X §1"
- `senator_remove`: "Remove a senator for good cause" · Senate · "2/3 of all voting seats" · "20 of 29" · "Art. X §2"
- `class_dues`: "Change class dues" · Council then Senate · "Undergraduate Council majority (or 2/3 of the Graduate Council for graduate dues), then 2/3 of all Senate voting seats" · "20 of 29" · "Art. VII §4, §5"
- `gm_vacancy`: "Appoint a new Grand Marshal if the post falls vacant" · Senate · "2/3 of the Senate, within two weeks" · None · "Art. XI §1"
- `pu_vacancy`: "Appoint a new President of the Union if the post falls vacant" · E-Board then Senate · "E-Board appoints within two weeks; 2/3 of the Senate confirms" · None · "Art. XI §2"
- `amendment`: "Amend the Constitution" · Senate then all students · "2/3 of the Senate, then a majority of students voting, with at least 20% turnout" · None · "Art. XIII §1"
- `ordinary`: "Everything else" · any body · "Not set by the Constitution. Robert's Rules of Order apply wherever a body's own rules are silent." · None · "Art. VII §6", plus `draft="Senate bylaws or rules"`.

**`PETITIONS`** (what students can force). List of `{goal, signatures, deadline, result, cite}`:
- "Force a student vote (referendum) on anything except the Constitution" · "10% of all Union members" · "Vote held within 45 days (excluding vacations) or at the next regular election, whichever is sooner; at least 14 days after approval; not during exams" · "Binding if a majority votes yes and at least 20% of affected students vote; the Senate must enact it" · "Art. XII §1–§4"
- "Force an election for a seat that was filled by appointment" · "20% of that seat's constituency" · "Received by the Senate within two weeks of the announcement" · "Special election" · "Art. XI §5"
- "Start a removal election for the Grand Marshal, President of the Union, or a Council President" · "20% of their constituents, then a Senate majority" · "None set" · "Removed by 2/3 of voters if at least 20% vote" · "Art. X §1"
- "Remove the Grand Marshal, President of the Union, or a Council President outright" · "50% of their constituents" · "None set" · "Removed" · "Art. X §1"
- "Recall an elected senator" · "20% of their constituents" · "None set" · "Removed by 2/3 of voters if at least 20% vote" · "Art. X §2"

**`NAMED_RECORDS`** (records the Constitution names). List of `{name, what, published_here, cite}`; `published_here` is "Not linked yet" for all of them today, rendered with `draft="Site owner"`:
- Rensselaer Union Constitution (last amended 6 Feb 2026) · "The Union's founding rules" · Art. XIII §5 (amendments must be appended to it)
- Student Senate bylaws · Art. VII §1
- Executive Board bylaws · Art. VII §2
- Judicial Board bylaws · Art. VII §3
- Graduate Council bylaws · Art. VII §4
- Undergraduate Council bylaws · Art. VII §5
- Rensselaer Student Bill of Rights · "Rights the Judicial Board enforces" · Art. VII §3
- Senate election procedure and rules · "Ballot access, groupings for FSL seats, extra eligibility rules" · Art. VIII §5, §6, §13
- Union budget and records of extra spending and allocations · "Public documents under the Constitution" · Art. VII §2

**`TRANSPARENCY_RULES`** (each with cite): "The budget and records of all extra spending and allocations are public documents." (Art. VII §2) · "RPI's Treasurer holds the Union's money and gets a copy of every financial transaction." (Art. VI) · "No Union money may be spent without an Executive Board requisition." (Art. XIV) · "The exact wording of a constitutional amendment must be published campus-wide at least two weeks before the vote." (Art. XIII §3) · "The Senate must give adequate notice of all elections." (Art. VIII §6) · "Senators must report regularly to their councils." (Art. VII §1). Plus one honest line with no cite: "The Constitution does not require meeting agendas or minutes to be public. Publishing them here is a Union practice, not a constitutional duty."

**Budget.** As of 2026-08-25, source "Executive Board Agenda 01, 25 Aug 2026". This is a **quotation from one agenda, not a maintained figure**. Render it only with the `quoted_budget` source line. Nobody updates it on the site, so there is no CSV export and no "last updated" job.
- Club Contingencies: 100000 / 100000
- Travel Contingencies: 60000 / 60000
- Facilities: 166150 / 166150
- Facilities Reserves: current 126635.47, no initial

Plain descriptions (the Constitution doesn't define the pools, so the two contingency lines carry `draft="E-Board bylaws"`):
- "Extra money clubs can request during the year"
- "Money clubs can request for travel"
- "Money for Union facilities"
- "Savings held for facilities"

**Membership snapshots.** Each body's snapshot is `{seats_constitution, groups:[{label, seats, filled, vacant, elect_fall, cite}], note}`, rendered as a table.

Senate (cite "Art. VII §1"; 29 voting seats; the Grand Marshal presides and votes only on ties, Art. IV §1):
| Group | Seats | Filled | Vacant | To be elected this fall |
|---|---|---|---|---|
| Graduate | 7 | 4 | 3 | 0 |
| Class of 2027 | 4 | 4 | 0 | 0 |
| Class of 2028 | 4 | 2 | 2 | 0 |
| Class of 2029 | 4 | 4 | 0 | 0 |
| Class of 2030 (first-years) | 4 | 0 | 0 | 4 |
| Independent | 3 | 3 | 0 | 0 |
| Fraternity and Sorority Life | 3 | 3 | 0 | 0 |
| **Total** | **29** | **20** | **5** | **4** |
- First-year senators are elected in the fall (cite "Art. VIII §3"); the 30 Jul 2026 roster predates that election.
- Reconciliation note (render under the table, with cite "Art. VII §1; Art. VIII §5"): "The agenda lists the Independent and FSL senators under one heading, 'Greek & Independent Senators'. The Union Constitution, as amended in 2023 and Feb 2026, makes them two separate groups of three seats. The Constitution is authoritative, so this record shows them separately."
- Agenda-header line with its source: "Agenda header: 19 voting members, quorum 13." Muted note: "The roster lists 20 filled voting seats; the difference is unexplained in the source. The Constitution does not set quorum." (`draft="Senate bylaws or rules"`)
- Non-voting officers (titles set by Senate bylaws): Senate Treasurer and Senate–E-Board Liaison Cee Ray '27, Parliamentarian Sasha Notkin '28, Secretary Selena Tang '29, and the committee chairs.

Executive Board (cite "Art. VII §2"; 15 to 20 voting seats; the President presides and votes only on ties, Art. IV §2):
| Group | Seats | Filled | Vacant |
|---|---|---|---|
| Class representatives (Graduate, 2027–2030) | 5 | 3 | 2 (Graduate, 2030) |
| Club and organisation representatives (5 required + 2 optional) | 7 | 4 | 3 |
| Members-at-large (2 required + 3 optional) | 5 | 4 | 1 |
| Senate–E-Board Liaison (chosen by the Senate) | 1 | 1 (Cee Ray '27) | 0 |
| Graduate Council representative (chosen by the Graduate Council) | 1 | 1 (Joydip Paul '29G) | 0 |
| Undergraduate Council representative (chosen by the Undergraduate Council) | 1 | 0 | 1 |
| **Total** | **20** | **13** | **7** |
- Note under the table: "The agenda prints the three Council and Senate representatives as 'Peer Body Representatives' and lists three Vice Presidents separately. Under the Constitution the three representatives are voting members, and there are no separate VP seats. The agenda header says 12 voting members." The VP titles (Gavin Finn '28, Board Operations; Jesse Kim '26 '27G, Club Relations; Blaine Rosenberg '28, Rules and Special Projects) render under "Officers" with `draft="E-Board bylaws"`.
- Other non-voting roles from the agenda: Club Financial Advisors, Secretary, Parliamentarian (Vacant), committee chairs. Advisers under the Constitution: the Director of the Union and assistants (cite "Art. VII §2").

**Health checks (for the Desk and the health page).** These replace the old hand-kept freshness list. Each check is a dict: `{area, check, item, since, days, owner_role, severity, fix_label, fix_url, sample, cite?, draft?}`.
- `area` is one of "Meetings", "Links", "Sync", "Roster" or "Site".
- `severity` is one of `overdue` ("Overdue"), `soon` ("Due soon"), `check` ("Check"), `waiting` ("Waiting") or `ok` ("OK").
- `fix_label` is "Fix in Notion", "Fix in Box" or "Fix in Wagtail", and `fix_url` is MOCK_NOTION, MOCK_BOX or `/admin/` to match.
- Compute `days` from `timezone.localdate()`.

*Computed from `MEETINGS`* by `meeting_checks(today)`. Never hard-code these rows:
- A past meeting with no `minutes_url`:
  - more than 14 days after the meeting: `overdue`, "Minutes link missing", for example "Senate 57 #12 · 30 Jul 2026 · 83 days";
  - otherwise: `soon`, "Minutes due by <meeting + 14 days>".
  - Owner: "<Body> Secretary". Fix in Notion.
- A past meeting with no `agenda_url`: `check`, "No agenda link on the meeting record". Fix in Notion.
- An upcoming meeting with no `agenda_url`:
  - 2 days away or less: `overdue`, "Agenda link missing: meeting in N days";
  - otherwise: `waiting`, "Agenda link not added yet · flagged from <meeting − 2 days>". On 21 Oct 2026, Senate #13 (26 Oct) shows "flagged from 24 Oct".
- A meeting with `public=False`: `check`, "Not shown on the site: Public is unticked in Notion". No seed meeting triggers this.

*Computed from the membership snapshots:*
- Each group with `vacant > 0`: `check`, "Seats vacant more than 60 days". Item example: "Senate · Graduate: 3 seats". `since` is the roster date (30 Jul 2026 for the Senate, 25 Aug 2026 for the E-Board), labelled "vacant on every roster since at least …". Owner: VGMIA (Senate) or President of the Union (E-Board). `fix_label` "Record in Notion when filled".

*Seeded* (`sample` as marked):
- Sync: `SYNC` drives a status panel, not a table row. Add one `check` row, Sample: "Schema change: Assignments property 'End date' (id `qT%3Fb`) not found. Renamed columns are fine, but this one was deleted or its type changed. End dates are ignored until it's fixed." Owner: WTG chair. Fix in Notion.
- Links: `LINK_CHECKS` is a list of `{item, kind, url, result, checked}`, where `result` is "ok", "404" or "login" and `checked` is date(2026, 10, 19). All rows are Sample:
  - "Senate 57 #11 · Agenda" · ok
  - "Senate 57 #11 · Minutes" · login. This becomes an `overdue` row: "Opens an RPI login page. Set the shared link to 'People with the link'." Owner: Senate Secretary. Fix in Box.
  - Summary line: "2 pasted links checked on 19 Oct 2026 · 1 opens a login page · 0 return 404."
- Roster:
  - "Class of 2030 Senate seats: fall election results not entered" · `check` · since 1 Sep 2026 (`draft="Senate election rules"`: the actual election date) · Elections Commission · Fix in Notion.
  - "E-Board first-year member: due within three weeks of the fall elections" · `waiting` · "Waiting on fall election" · President of the Union · cite "Art. VIII §12".
  - "Seats: the three E-Board Council and Senate seats are marked non-voting, but the Constitution counts them as voting" · `check` · VP Rules and Special Projects · Fix in Notion ("tick Voting on those Seats rows") · cite "Art. VII §2".
  - "Term rollover: not due. Senate 57 and EBoard FY27 are the current terms." · `ok`.
- Site (Wagtail-owned):
  - "Union Constitution and bylaws: no Box link on the governing-documents block" · `check` · WTG chair · Fix in Wagtail.
  - "Expired site notices: none" · `ok`.
  - "Pages past their review date: none" · `ok`.

`NOT_CHECKED` (an honest list on the health page): "File names, and whether every file in Box has a meeting record: these need the Box API, which the Union doesn't have." · "Attachments: they show in the folder embed and aren't linked one by one." · "Attendance: private, never synced."

## 2. Optional DB reads (wrapped)

- `SiteSettings.load(request_or_site=request)`, for the footer email, office and Discord, and `box_archive_url` (shown only as a plain link; see `_box_folder.html`).
- Don't read `EventPage` meetings. Meetings come only from the meeting records (`MEETINGS`), never from hand-made calendar entries.
- Don't read `records.BoxFileCache`. It needs the Box API and can never hold rows. The meetings page uses Box folder embeds instead.

## 3. Pages

| name | URL | template |
|---|---|---|
| home | `/lab/the-record/` | `home.html` |
| meetings | `/lab/the-record/meetings/` | `meetings.html` |
| meeting | `/lab/the-record/meetings/<slug:body>/<slug:term>/<int:number>/` | `meeting.html` |
| decisions | `/lab/the-record/decisions/` | `decisions.html` |
| decision | `/lab/the-record/decisions/<slug:id>/` | `decision.html` |
| money | `/lab/the-record/money/` | `money.html` |
| rules | `/lab/the-record/rules/` | `rules.html` (added after the constitution review) |
| desk | `/lab/the-record/desk/` | `desk.html` (GET and POST; `?path=notion` (Senate, default), `?path=site` (alias `wagtail`), or `?path=folder` (GET only)) |
| health | `/lab/the-record/desk/health/` | `health.html` (replaces the old money CSV export, so the page count stays at 9) |

## 4. Visual direction: dense, like Weather.gov or Congress.gov

**Styles and type:**
- Tailwind Play CDN `<script src="https://cdn.tailwindcss.com/3.4.17"></script>`.
- System UI font. Base 1rem (16px) on mobile and 0.9375rem tables at md. Line-height 1.5.
- References like "Senate 57 #12" in `font-mono`.

**Colour tokens:**
- head #1a1a2e (stugov-dark; white text 16:1)
- ink #111827
- muted #4b5563 (7:1)
- line #d1d5db
- link #a50015
- rowalt #f9fafb
- focus ring 3px #2563eb outline plus 2px white offset

**Status chips.** Bordered, with the word always present:
- passed: green-800 text on green-50
- failed: red-800 on red-50
- waiting/on_agenda: amber-900 on amber-50
- not_recorded/tabled: gray-800 on gray-100 with a dashed border
- done: blue-900 on blue-50

All of these exceed 7:1.

**Header:**
- A dark bar with the wordmark "Rensselaer Union · Public Record".
- Nav: **Meetings** · **Decisions** · **Money** · **Rules** · **Have your say** (`/lab/the-record/meetings/#speak`) · **Desk** (labeled "For officers"; the health page is linked from the Desk).
- On mobile the nav is a horizontally wrapping row of text links (no hamburger, since there are only 6 short items). It must wrap, not scroll.
- A search field "Search decisions" submits GET to the decisions page with `?q=`.

**Layout:**
- Max width max-w-6xl, padding 16px.
- Tables become stacked definition lists under 640px: each row renders as a bordered block with label/value pairs. Use two markup variants with `sm:hidden` / `hidden sm:table`, or a CSS grid.

**Footer:** "Site maintained by the Web Technologies Group · Files live in Box; each body keeps its meeting records its own way (see 0B); the roster is kept on this site · Rules from the Rensselaer Union Constitution, last amended 6 Feb 2026 · Last reviewed 21 Oct 2026 · How this site works (desk#how-this-site-works) · Report a problem" (mailto contact_email if set).

## 5. Page specs

### 5.1 Home

1. **Alert slot.** Only if a NOTICE is set and not expired. Seed None.
2. **Next meeting per body.**
   - Two cards side by side at md, stacked on mobile.
   - Each card: body, `font-mono` ref, full date with weekday and year, time ET, location.
   - Status line: either "Agenda posted" (link) or "Agenda not posted yet".
   - Links: "Speak at this meeting" (to meeting#speak) and "Add to calendar" (a `data:text/calendar` link generated in the view, or omit it).
   - If a body has no upcoming meeting: "No upcoming E-Board meeting listed. Last met 25 Aug 2026 →". Never blank.
   - Each card ends with the `meeting` source line.
3. **Latest decisions.**
   - A table with caption "Latest decisions".
   - Columns: Status | Decision (plain summary, linked) | Body | Date.
   - 6 rows, followed by the `decision` source line and "All decisions →".
4. **Records status strip.** One line per past meeting: "Senate 57 #12 · 30 Jul 2026 · Agenda ✓ · Minutes: not posted (83 days)". Use the words "posted" and "not posted" alongside any glyph, and mark glyphs `aria-hidden`. Statuses are derived from the links on each meeting record. End with the `meeting` and `file` source lines.
5. **Contingency funds, as printed.** The four lines as a compact table headed "As printed on Executive Board Agenda 01, 25 Aug 2026". No bars and no "% left": a quoted figure must not look live. Then the `quoted_budget` source line and "Details →".
6. **What each body does.** A 5-row `<dl>`, one sentence each, each with its constitution line. No Draft badges:
   - Student Senate: "The Union's main lawmaking body: 29 voting seats, chaired by the Grand Marshal. Passes its own rules, sets the Activity Fee, and approves many appointments." (Art. VII §1)
   - Executive Board: "The budgeting body: prepares and approves the budget, hands out Union money, and classifies clubs. Chaired by the President of the Union." (Art. VII §2)
   - Judicial Board: "The student court for rights and conduct cases, and the only body that interprets the Constitution. It can rule other bodies' decisions unconstitutional." (Art. VII §3)
   - Graduate Council: "The advocacy body for graduate students: the 7 Graduate Senators plus at least 5 at-large members. Controls graduate class dues." (Art. VII §4)
   - Undergraduate Council: "The advocacy body for undergraduates: the President and Vice President of each Class Council. Oversees the four Class Councils and approves their class-dues spending." (Art. VII §5)
   - Link under the list: "Votes needed and what students can force →" (rules).
   - Then the `wagtail` source line: these descriptions are written on this site.

### 5.2 Meetings

- **Filters** (GET, no JS):
  - body: all / senate / eboard
  - term: all / 57 / fy27
  - A Submit button. Filtering happens in Python.
- **Upcoming:** table.
- **Past:** table.
  - Columns: Ref | Body | Date | Location | Agenda | Minutes. There is no Recording column until recordings have an owner.
  - Every cell has a value, e.g. "Posted (PDF in Box)", "Link not added yet", "Not posted (83 days)".
- Under both tables: the `meeting` and `file` source lines.
- **Speak at a meeting** (`<section id="speak">`): "Both the Senate and the Executive Board set aside time at the start and end of every meeting when anyone may speak or ask questions (Invitation to Speak, Press & Visitor Q/A). Attend in person or on Webex." (`draft="Senate bylaws or rules"`: the Constitution doesn't cover speaking rights.) Then: "Want more than a hearing? A petition signed by 10% of Union members makes the Senate hold a binding student vote." (cite "Art. XII §1") with a link "What students can force →" (rules#petitions).
- **All files** (`<h2 id="files">`): one `_box_folder.html` per entry in `BOX_FOLDERS`, each under an h3. Lead: "Every agenda, set of minutes and attachment is a PDF in the Union's Box. Names start with the date, so they sort in order." If `box_archive_url` is set, add a plain "Whole Box archive" link.

### 5.3 Meeting detail (Cornell-style)

- h1 "Student Senate · Meeting #12".
- **Metadata `<dl>`:** term, date and time with year, location, remote link ("Webex link not published"; in production it shows only if the Notion row's "Publish join link" box is ticked), agenda ("Open agenda (PDF in Box)" when linked, shown first and full-width on phones; otherwise "Posted in Box · link not added to the meeting record yet"), minutes status with days (plus "Approved <date>" when `minutes_approved` is set). End the `<dl>` with the `meeting` and `file` source lines.
- **Quorum and membership box:** Senate: "29 voting seats (Constitution) · 20 filled · 5 vacant · 4 first-year seats to be elected this fall" with cite "Art. VII §1", then "Agenda header: 19 voting members, 13 needed for quorum" with the agenda source line. E-Board: "15 to 20 voting seats (Constitution) · 13 filled · 7 vacant" with cite "Art. VII §2", then "Agenda header: 12 voting members, 8 needed for quorum". All counts are computed from the membership snapshot. A "Full membership" `<details>` renders the snapshot table and its notes. The box ends with the `roster` source line. In production, filled and vacant counts are computed from Notion Seats minus current-term Assignments, so nobody keeps the counts by hand.
- **Who chairs:** Senate "Chaired by the Grand Marshal, who votes only to break a tie." (Art. IV §1). E-Board "Chaired by the President of the Union, who votes only to break a tie. The Director of the Union advises but cannot veto." (Art. IV §2; Art. V).
- **Agenda:** an `<ol>` with section numbers matching the PDF, items with reporter names, "Vacant" in italics, and empty sections showing "Nothing listed".
  - Each section has a `<details>` "What is this?" with a plain gloss. Glosses that rest on the Constitution carry its line (e.g. Grand Marshal Report: "An update from the Grand Marshal, the Union's chief spokesperson." Art. IV §1; Director's Report: "An update from the Director of the Union, a paid staff adviser who runs Union activities and funds." Art. V). Glosses about meeting order (Bookkeeping, Invitation to Speak, Special Orders, Old/New Business) carry `draft="Senate bylaws or rules"`; the Constitution only says Robert's Rules apply where a body's own rules are silent (Art. VII §6).
  - Items with a decision_id link to the decision page.
  - Revised (0B): this numbered list appears only on Senate meetings under `?agenda=items`, labelled "Option for the Senate: the agenda item by item", with the `agenda_items_option` source line. The default for every meeting is the document view. The "What is this?" glosses are written on this site; they are explanations, not part of the record.
  - If `sections` is empty (Senate #11) and `?agenda=items` is requested: "This agenda was written in Word, so it has no items in Notion. It's shown as the document." The document view is a complete publish, not an error.
- **Associated decisions:** Senate: the motions whose history cites this meeting, then the `motions` source line. E-Board: "The Executive Board records its decisions in its minutes", with the minutes status and the `in_minutes` source line.
- **Files for this term:** the body's `_box_folder.html`.
- **Prev/next meeting links** within the same body.

### 5.4 Decisions tracker

- **Filters** (GET): q (substring over title and plain_summary), body, status, term. Show the result count: "7 decisions".
- **Table.** Columns: Status | Ref | Decision | Body | Last action.
  - Rows link to the detail page.
  - Sample rows show the Sample pill.
- **Empty result:** "No decisions match. Clear filters."
- **Explainer at the top:** the 0B copy (decisions here are Senate motions; other bodies' decisions are in their minutes). Then the `motions` source line and the `in_minutes` source line.

### 5.5 Decision detail

- h1 is the plain summary. Below it, the title and `font-mono` ref.
- **Stage tracker.** A horizontal `<ol>` of 4 steps: "On the agenda" → "Voted" → "Outcome recorded" → "Done".
  - The current step is bold with `aria-current="step"`. Earlier steps show a check plus the visually hidden text "completed".
  - It wraps to vertical under 640px.
  - No Draft badge. Under the tracker, a muted note: "These steps describe what the public record shows. The Union Constitution has no sign-off or veto step after a Senate or Executive Board vote. The Judicial Board can later rule a decision unconstitutional." (cite "Art. VII §3"). A decision with status `overturned` shows a fifth, final step "Ruled unconstitutional".
- **"Votes needed"** line from `THRESHOLDS[threshold]`: e.g. "Votes needed: 2/3 of all Senate voting seats (20 of 29, derived)" plus its constitution line. If threshold is None: "Votes needed: not set by the Constitution" with the decision's Draft badge. Link "All vote thresholds →" (rules#votes).
- **"Latest action"** line.
- **History:** a table with Date | Meeting (link) | What happened.
- **Outcome note**, if present.
- **Sources:** agenda and minutes links (PDFs in Box), or "Not posted". Then the `decision` source line.
- **Share line:** shows the absolute URL in a readonly input, for pasting into Discord.

### 5.6 Money

- h1 "Contingency funds".
- Summary box, three lines:
  1. "Under the Union Constitution, the Executive Board prepares and approves the Union budget and hands out Union money. The budget and the records of all extra spending and allocations are public documents." (cite "Art. VII §2")
  2. "No Union money may be spent without an Executive Board requisition, and RPI's Treasurer gets a copy of every transaction." (cite "Art. XIV; Art. VI")
  3. "These four lines are pools printed on each E-Board agenda. They are not the full Union budget." (`draft="E-Board bylaws"`: what the pools cover)
- **Full budget status** line: "FY27 Union budget: not posted on this site. It is a public document under the Constitution." (cite "Art. VII §2"; `draft="Site owner"`: where to get it.)
- **Table**, caption "As printed on Executive Board Agenda 01, 25 Aug 2026": Fund | What it's for | Started with | Left (as printed). There are no bars, no "% left" and no CSV download. They would turn a one-off quotation into something that looks maintained, and someone would have to retype every new agenda's figures to keep it true.
- Under the table: the `quoted_budget` source line, then "Latest figures: the newest E-Board agenda in Box" (the eboard `_box_folder.html` link or placeholder).
- **"Allocations this year":** "Allocations are public records under the Union Constitution (Art. VII §2). This site will link to them wherever finance publishes them. It won't retype them." (an honest empty state).
- The summary box and explanations are Wagtail-owned: end `<main>` with the `wagtail` source line.

### 5.7 Rules (`rules`): how decisions are made

The one page added after the constitution review. In this record-first site, the rules are part of the record: a reader checking a decision needs to know what vote it needed and what students could do about it.

- h1 "How decisions are made". Lead: "From the Rensselaer Union Constitution, last amended 6 Feb 2026. Where the Constitution leaves something to a body's own rules, we say so."
- In-page nav: Votes needed · What students can force · Records the Constitution names · Transparency rules.
- **Votes needed** (`id=votes`): table, caption "Votes the Constitution requires". Columns: Action | Who votes | Votes needed | For a full Senate (derived) | Source. Rows from `THRESHOLDS` in the order listed. Empty derived cells show "Not applicable". The Source column shows the article text, e.g. "Art. VII §1". The `ordinary` row shows its Draft badge. Under the table: "'All voting seats' is the Constitution's 'total voting membership'. Our derived numbers assume all 29 seats count, including vacant ones; the Constitution doesn't say." Stacked on mobile like other tables.
- **What students can force** (`id=petitions`): table, caption "Petitions in the Constitution". Columns: Goal | Signatures needed | Deadline | Result | Source, from `PETITIONS`. Under it, a Draft line (`why="Senate bylaws or rules"`): "Not set by the Constitution: petition format, where to hand it in, and how signatures are checked." And: "A petition alone can't amend the Constitution. Amendments need 2/3 of the Senate first, then a campus vote with at least 20% turnout." (cite "Art. XII §1; Art. XIII §1")
- **Bring a case** (`id=judicial-board`), a short paragraph: "Any charge that the Union Constitution, the Rensselaer Student Bill of Rights, or student conduct rules were violated can be referred to the Judicial Board, which can rule legislation unconstitutional." (cite "Art. VII §3"). Then "How to file: not published" with `draft="Judicial Board bylaws"`.
- **Records the Constitution names** (`id=records`): table with Record | What it is | On this site | Source, from `NAMED_RECORDS`. The "On this site" cell is never blank: "Not linked yet" plus the Draft badge.
- **Transparency rules** (`id=transparency`): a list from `TRANSPARENCY_RULES`, each with its constitution line, ending with the honest no-cite line about agendas and minutes.
- The whole page is Wagtail-owned: end `<main>` with the `wagtail` source line.

### 5.8 Desk (mock officer console)

The Desk serves every body, each through its own adapter (0B). The Senate's view has no "Post the next meeting" form, because its meeting facts already live in its Notion. The form (Section B′) is the real entry point for a body that chose "entered on this site", shown for the E-Board as an example. A folder-only body gets steps and no form (Section B″). The Desk does three things. It shows what is missing against the Public Records Standard, it says where to fix it, and it times each body's real workflow.

- Banner: "Mock for testing only. Nothing you enter is saved, published, or emailed. Nothing here is connected to Notion or Box."
- h1 "Officer desk". It renders with `officer=True`.
- **Path switch**, a `<nav aria-label="Where this body keeps meeting records">` with three links: "Senate (Notion)" → `?path=notion` (default); "Entered on this site (E-Board, example)" → `?path=site`; "Folder only (Graduate Council, Undergraduate Council, Judicial Board)" → `?path=folder`. The current one gets `aria-current="page"`. Under it: "Each body chooses. A body's meetings live in one place, never two."

**Section A, "Your jobs".** Lead: "What the site can't show students correctly until someone fixes it at the source." List every health check whose severity isn't `ok`, sorted overdue → soon → check → waiting, then by `days` descending. Show at most 8. Each row shows the severity chip (word always visible), the check and item, the age ("83 days", or its waiting text), the owner role, and its `fix_label` link with "(mock link)". Below: "Full health page →" (health), and the Notion sync status in one line: "Notion sync: last success 12 min ago · next run in 3 min · no errors".

**Section B (`path=notion`, default), "Publish a meeting: the two-minute test".**
- Lead: "Publishing a meeting is two pasted links and one Notion row. Time it with the real agenda PDF, starting before you open Box."
- A "Start the timer" button (`type="button"`). If nobody clicks it, the timer starts on the first `focusin` inside the stand-in panel. It writes elapsed seconds into a hidden input `elapsed`. The `aria-live="polite"` region updates only on submit, not every second.
- **The steps**, an `<ol>`:
  1. "Export the Word agenda as a tagged PDF (File, Save As, PDF, with accessibility tags on; never Print to PDF). In Box, save it in `Public Records/Senate/2026-27 Senate 57/` as `2026-10-26 Senate 57 #16 Agenda.pdf`." (Show the pattern and the two `RENAMES` examples in a `<details>` "Naming rule".) "Replacing a file? Use Upload New Version, not a second upload: the link stays the same."
  2. "Share → set the link to 'People with the link' → copy it. If it's set to 'People in your company', students hit an RPI login."
  3. "In Notion's Meetings database, duplicate the last meeting. Change the number, date and place, paste the link into Agenda, and tick Public."
  4. "It appears on this site within 15 minutes, or sooner, because Notion pings the site when a row changes."
  - Two buttons beside the steps: "Open the Senate Box folder" (MOCK_BOX) and "Open Notion Meetings" (MOCK_NOTION), each with "(mock link)".
- **Stand-in for step 3.** A panel styled like one Notion database row: a light gray `#f7f6f3` background, a property-name column on the left, a monospace "Meetings" breadcrumb, and a thick dashed border. Its heading reads "Stand-in for Notion". Above it, a bold label: "This is not a website form. On the real site this panel doesn't exist: you'd do this in Notion. It's here so the test can run without a Notion workspace." Properties, each with a visible label and a hint:
  - Body: select, Senate or E-Board, default Senate.
  - Term: select, "57" or "FY27", following the body.
  - Number: integer, prefilled with the latest *past* meeting of that body + 1, so 13 for the Senate. The hint reads "Prefilled because you duplicated the last meeting."
  - Date: type=date, empty.
  - Time: prefilled 20:00.
  - Location: prefilled "Webex".
  - Agenda: type=url, optional, placeholder "https://rpi.box.com/s/…". The hint reads "Paste the Box shared link."
  - Public: checkbox, unticked. The hint reads "Only rows with Public ticked appear on the site."
  - Required: body, term, number, date, time, location.
- A submit button: "Sync now (simulated)".
- Always add the muted note: "If the Union already has a Notion workspace, do step 3 there with a stopwatch, and use this panel only to see what the site would show."

**On POST (`path=notion`):**
- Validate with one Django `forms.Form`, `MeetingRowForm` (no model). On errors, re-render with an error summary at the top (`role="alert"`, links to fields) plus inline errors.
- On success, render "What the site shows after the next sync (simulated)":
  - If Public is unticked: "Not shown on the site: Public is unticked in Notion. Tick it and sync again." Show no card.
  - Otherwise: the meeting card exactly as on home, with the source line "Meeting record: Notion · synced just now (simulated)". If an agenda link was given, the status reads "Agenda posted (link to <host of the URL>)". Never render the pasted URL as a clickable link.
  - "Checks the health page would run on this row", a list:
    - No agenda link, meeting 2 days away or less: "Overdue: agenda link missing, meeting in N days".
    - No agenda link, meeting later: "Waiting: flagged from <date − 2 days> if still missing".
    - Agenda link doesn't match `^https://([a-z0-9-]+\.)*box\.com/s/[A-Za-z0-9]+`: "Check: this isn't a Box shared link (…/s/…). Students may hit a login page or a dead link."
    - Agenda link matches: "OK: looks like a Box shared link. The weekly check will confirm it opens without an RPI login."
    - The date has passed: "The minutes link will be flagged 14 days after the meeting."
  - "Time taken: 1 min 42 s · Target: under 2 minutes, Box upload included." Without JS: "Time not measured".
- Never persist. Never log field values.

**Section B′ (`path=site`), "Post the next meeting (entered on this site)".**
- An amber box: "For a body that chose to list its meetings on this site, shown here for the Executive Board as an example. The Senate never uses this form: its meetings come from its Notion. This site is where this body's meeting record lives, so it is typed here once."
- The same `MeetingRowForm`, styled as a normal site form, with Body limited to E-Board and without the Public box (everything entered here is public). No agenda-item inputs: a Word agenda's items are never retyped.

**Section B″ (`path=folder`), "Publish as files only".** No form. Steps: (1) export the Word document as a tagged PDF; (2) save it in the body's folder with the convention name; (3) set the link to "People with the link"; (4) once a month, confirm on this site that the folder is complete (a disabled, Sample-badged checkbox "Records are complete up to today"). Then "What students see": the body's `_box_folder.html` with the honest folder-only line. Then "What you give up": no meeting pages, no "next meeting", no calendar, no automatic deadline checks.
- The same "Start the timer" button and the same steps 1–2 (Box). Step 3 reads "Fill in this form and paste the link." Step 4 reads "It appears immediately."
- On POST: the same preview and checks, with the source line "Meeting record: entered on this site by the E-Board Secretary · just now". Never persist.

**Section C, "Recording outcomes".** No inputs. Text: "Outcomes come from the minutes, so this site never asks you to type them. If minutes are written in the Notion meeting page, each motion is a row in its Motions table (Item, Outcome, Votes, Public), and it syncs here. If minutes are a Word or PDF file in Box, the site shows the minutes link and decisions stay 'Outcome not recorded yet'. Typing outcomes into this site as well would be double entry." Then a static, Sample-badged mock of a Notion Motions table: two rows for the E-Board ballroom items (Society of Women Engineers, RPI Admissions), with Outcome "(blank)", Votes "(blank)" and Public "☐". It has the caption "What a Motions table in Notion would look like (Sample)".

**Section D, "Term rollover", done in Notion.** An ordered list of 6 steps: set end dates on last term's assignments; set the new term as current (every seat on the site then shows Vacant automatically, and last year's names never carry over); make sure the four first-year Senate seats show "To be elected this fall"; enter new assignments as results come in; check the seat groups still match the Constitution's current Art. VII (29 Senate seats, 15–20 E-Board seats) and re-check `THRESHOLDS` after any amendment; audit who can edit the Notion workspace and the site admin (at least two owners, on a shared role account). Owner: WTG chair (`draft="Site owner"`).

**Section E, "How this site works"** (`id=how-this-site-works`, the handoff).
- Lead: "This site keeps one copy of each fact. Files live in Box, meeting records and the roster live in Notion, and this site owns only its own explanations. Everything else is a read-only view that updates itself, and the health page shows when it hasn't."
- **"What lives where"** table, caption "What lives where, and who edits it" (`draft="Site owner"`). Columns: What | Lives in | Who edits | How this site gets it. Rows that this site owns get a bordered "Written on this site" tag in the first cell.
  | What | Lives in | Who edits | How this site gets it |
  |---|---|---|---|
  | Meeting records: date, time, place, agenda and minutes links | Notion "Meetings" | Each body's Secretary | Synced every 15 min (Public rows only) |
  | Agenda, minutes and attachment PDFs | Box, `Public Records/<Body>/<Term>/` | Each body's Secretary | Link pasted into the Notion row; folder embed |
  | Agenda items and motions | The Notion meeting page, only if the agenda and minutes are written there | Secretary | Synced; otherwise the PDF only |
  | Seats, people, term assignments | Notion "Seats", "People", "Assignments" | VGMIA (Senate), VP Rules and Special Projects (E-Board) | Synced; read-only in the site admin |
  | Budget figures | Business Operations and Union finance; printed on E-Board agendas | E-Board Business Operations | Quoted with a link. Never retyped. |
  | Rules page, body descriptions, glosses, vote and petition tables | This site (Written on this site) | WTG chair | Native (Wagtail) |
  | Site notices | This site (Written on this site), with an expiry date | WTG chair | Native (Wagtail) |
  | Attendance, contacts, internal notes | Notion | Officers | Never shown |
- **"Never"** list: "a 'post a meeting' or upload form on this site (unless the body chose the homegrown path)" · "editing in this site anything Notion owns" · "retyped budget numbers" · "calendar entries made by hand for meetings" · "a second file host: no PDFs uploaded to this site".
- **Rules for officers**: "Fix files with Upload New Version in Box." · "Set shared links to 'People with the link'." · "Name files `YYYY-MM-DD <Body> <Term> #<nn> <Agenda|Minutes|Attachment - Title>.pdf`." · "If something here looks wrong, use the Edit link and fix it at the source."

### 5.9 Health (`health`): what the site projects, and what's missing

An operator page. It isn't linked from the public nav, and it renders with `officer=True`. Banner: "Mock health page. Every value is seed data." It has the Sample pill next to the h1.

- h1 "Site health". Lead: "Every body checked against the Public Records Standard, plus what this site shows from the Senate's Notion, the E-Board's entries and each Box folder. Each problem links to where it's fixed. The site never fixes another body's records."
- Revised (0B): a new section "2. Public Records Standard, by body" follows the sync status, and the sections below renumber.
- **1. Sync status** (a panel of `<dl>` rows, from `SYNC`):
  - Notion: "Last successful sync 12 min ago (21 Oct 2026, 1:48 PM ET) · next run in 3 min · last error: none".
  - Databases synced: Meetings, Seats, People, Assignments. Show row counts computed from the seed: meetings = `len(MEETINGS)`; seats = Senate 29 + E-Board 20; people = number of distinct names in the snapshots.
  - Webhook: "Last early-sync trigger 2 hours ago. Webhooks only speed things up; the 15-minute schedule is the guarantee."
  - Box: "No Box connection (the Union has no Box API). Pasted links checked weekly; last check 19 Oct 2026."
  - The Sample schema-change row, shown as a `check` item with "Fix in Notion".
- **2. What the site is showing**, table caption "Meeting records as synced from Notion". Columns: Ref | Date | Public | Agenda link | Minutes link | Last edited in Notion | On the site. Rows from `MEETINGS`, newest first. Link cells say "Linked", "Missing" or "Login page (failed check)". "On the site" says "Shown" or "Hidden (Public unticked)". Then the `meeting` source line.
- **3. Problems**, table caption "Problems to fix". Columns: Status | Area | Check | Item | Age | Owner | Fix. Rows are all health checks whose severity isn't `ok`, in the Desk's sort order. Sample rows show the Sample pill. The Fix cell holds the `fix_label` link and "(mock link)". Cited rows show their constitution line, and drafted rows show their Draft badge.
- **4. All clear**: the `ok` rows as a short list ("Term rollover: not due…", "Expired site notices: none", "Pages past their review date: none", "Box links returning 404: none").
- **5. Not checked**: the `NOT_CHECKED` list, under the heading "What this page can't see".
- Tables stack on mobile like the others.

## 6. Accessibility (WCAG 2.2 AA)

- Skip link and landmarks. One h1 per page.
- Table captions and `th scope`. Stacked mobile variants keep the label text.
- Chips are never colour-only. Every date includes the year with `<time>`.
- Focus is visible. Tap targets at least 24px (WCAG 2.5.8 minimum); aim for 44px on primary actions.
- Forms: labels, `aria-describedby` hints, an error summary with `role="alert"`, and `autocomplete="off"` on mock fields.
- Works without JS, except the stopwatch, which degrades to "Time not measured".
- 320px width causes no horizontal scroll.

## 7. Tests

GET 200 for home, meetings, `meetings?body=senate`, `meetings?body=gc` (contains "publishes its records as files"), meeting senate/57/12 (contains "29 voting seats", "Fraternity and Sorority Life", "Prototype only: what this document says" and "As the document (today)"), `meeting senate/57/12?agenda=items` (contains "Option for the Senate"), meeting senate/57/11 (contains "written in Word"), meeting eboard/fy27/1 (contains "entered on this site" and "records its decisions in its minutes"; not "Option for the Senate"), decisions, `decisions?body=eboard` (contains "records its decisions in its minutes"), a sample Senate decision with threshold None (contains "not set by the Constitution"), the sample `eb_appointment` decision (contains "2/3 of the Senate"), money (contains "public documents" and "Quoted from Executive Board Agenda 01"), rules (contains "20 of 29", "10% of all Union members" and "Union Constitution, Art. XII"), desk (contains "Stand-in for Notion" and "Your jobs"), `desk?path=site` and `desk?path=wagtail` (contain "never uses this form" and not "Add agenda items"), `desk?path=folder` (contains "Records are complete up to today"), health (contains "Last successful sync", "Minutes link missing", "Public Records Standard, by body", "Can't check: folder only" and "What this page can't see").

Also assert:
- No page contains "RUGP". The Senate snapshot's group seat counts sum to 29, and its E-Board counts sum to between 15 and 20.
- There is no `money_csv` URL name (reversing it raises `NoReverseMatch`), and money doesn't contain "Download CSV" or "% left".
- Meetings doesn't contain "Recording" and does contain "Box folder embed goes here".
- `meeting_checks(date(2026, 10, 21))` returns an `overdue` "Minutes link missing" row for Senate 57 #12 with `days == 83`, and a `waiting` row for Senate #13 that mentions "24 Oct".
- Without `?officer=1`, meeting senate/57/12 contains "Meeting record: Senate's Notion · synced 12 min ago" but not "Edit in Notion". With `?officer=1` it contains "Edit in Notion" and the response sets the `lab_officer` cookie. With `?officer=1`, meeting eboard/fy27/1 contains "Edit on this site" and not "Edit in Notion".
- Every `DECISIONS` entry has body "senate". `decision eb-fy27-01-a` returns 404.
- `meeting_checks(date(2026, 10, 21))` returns an `overdue` "Minutes link missing" row for E-Board FY27 #1 with `days == 57` whose `fix_label` is "Fix on this site".
- No `RECORDS_BY_BODY` row other than the Senate's contains "Notion".

POST to desk (`path=notion`):
- With valid data and Public ticked, returns 200 and contains "synced just now (simulated)".
- With valid data and Public unticked, contains "Public is unticked".
- With agenda "https://example.com/x", contains "isn't a Box shared link".
- With missing date, returns 200 and contains the error summary.

POST to desk with `path=site` and valid data returns 200 and contains "entered on this site by the E-Board Secretary".

404 for decision nope and for meeting senate/57/99.

Run `env/bin/python manage.py test lab` and `manage.py check`.