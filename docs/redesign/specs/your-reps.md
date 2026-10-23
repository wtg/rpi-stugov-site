# Prototype spec: Your Representatives

**Slug:** `your-reps`  
**Recommended:** False  
**Thesis:** Constituency first. The site starts by asking who you are, then shows the real people and vacant seats that represent you. A topic router answers 'who do I tell?'. A sample 'You said, we did' board shows what closing the loop would look like and what it would demand of whoever owns it. The roster is kept on this site for every body. The board is a read-only view of the Senate committees' issues in the Senate's Notion, the only body using Notion. Profiles show only what each member consents to, and contacts go to seats, never to personal addresses.

# Prototype: Your Representatives (`your-reps`)

## 0. Ground rules

This builds one self-contained prototype in the existing `lab` app at `/Users/aaron/src/stugov-site`. Wagtail 7.3 / Django 6.0. Use `env/bin/python`.

**Do not edit** `lab/urls.py`, `lab/views.py`, `lab/prototypes/__init__.py`, `stugov/`, or any model. Create no migrations and add no new dependencies.

**Create these files:**
```
lab/prototypes/your_reps/{__init__.py,urls.py,views.py,data.py,tests.py}
lab/templates/lab/your-reps/*.html   # includes _sample.html, _draft.html, _cite.html, _source.html
```

**`META` in `__init__.py`:**
```python
META = {"name": "Your Representatives", "thesis": "Constituency first: pick who you are, see the people and vacant seats that represent you, and route your issue to the right seat.", "recommended": False}
```

**Wiring:** mounted at `/lab/your-reps/`. Namespace `lab:your_reps`.

**Database:** the default dev DB is EMPTY. Wrap every DB read in `try/except DatabaseError` and fall back to `data.py`. Read only.

**Content labelling:**
- Every page has a top banner: "Prototype layout for testing. Not the official site. Items marked Sample are made up." plus a link to `/lab/`.
- `Sample` pill (`_sample.html`) for fabricated content. Source lines for agenda-derived facts, e.g. "Source: Student Senate agenda, 30 Jul 2026".
- **Constitution line.** Facts confirmed by the Rensselaer Union Constitution (last amended 6 Feb 2026) carry no badge. They get a muted line via `{% include 'lab/your-reps/_cite.html' with art="Art. X §2" %}`, rendering "Source: Union Constitution, Art. X §2". In `data.py` such entries carry `cite`.
- **Draft badge.** `{% include 'lab/your-reps/_draft.html' with why="..." %}` renders a "Draft: confirm" pill with `title="Not set by the Union Constitution. Confirm with: {{ why }}"`. Use it only for things the Constitution leaves to bylaws, Senate rules or staff. Allowed `why`: "Senate bylaws or rules", "Senate election rules", "E-Board bylaws", "Judicial Board bylaws", "Union staff process", "Site owner". In `data.py` such entries carry `draft="<why>"`. Never name "RUGP" on any page: the Constitution doesn't mention it.
- **Derived numbers** (our arithmetic) render with "(derived)", whose `title` reads "Our arithmetic, assuming all 29 Senate seats count".
- **Naming.** Say "Fraternity and Sorority Life (FSL)", never "Greek" (renamed by Amendment VI, Feb 2026). The agendas' combined "Greek & Independent Senators" heading appears only inside the reconciliation note below.
- **Never invent emails, phone numbers, office hours, pronouns or bios for real people.** Unknown fields render "Not listed".

## 0A. Single source of truth (read before building)

The prototype has to show where each fact lives, who edits it, and what a member has agreed to publish, body by body (revised, see 0B). The background is in `docs/redesign/data-architecture.md`, but you don't need to read it to build this.

**Who owns what**
- **This site (Wagtail)** owns the roster for **every** body: seats (body, label, constituency, voting, role inbox), people (name, class, `Public profile` consent, photo, bio, pronouns, major, office hours) and term assignments. Each body's roster officer edits its seats. Nobody keeps a second roster (CSV, spreadsheet, or the Senate's Notion) alongside it. The Senate's Notion receives an automatic read-only copy for attendance.
- **The Senate's Notion** would own the "You said, we did" issues for Senate committees, in an "Issues" database with a `Public` box. Only rows with Public ticked, and only these fields, would sync: title, topic, constituencies, owner seat, source, raised date, status, dated updates, outcome. A student's original message is never synced. Other bodies don't publish an issue tracker. This board is not built for real: it needs a committee to own it.
- **Meeting records** are kept per body. The Senate's are in its Notion; the E-Board's are entered on this site (an example choice); the Graduate Council, Undergraduate Council and Judicial Board publish files in their Box folders only. Agendas and minutes are Word files in **Box**, published as PDFs, and never itemised here.
- **This site** also owns the explanations: the chooser, constituency descriptions, the topic router, fill rules, powers, the glossary and "How it works".

Nothing in this prototype connects to Notion or Box. Every sync time is seed data, and the banner says so. Nothing implies that the Executive Board, the Councils or the Judicial Board use Notion.

**Rules for this prototype**
- No page asks an officer to type a roster, issue or meeting fact into the website.
- Every projected item (person or seat card, person page, issue card, meeting line) shows a muted **source line** from `_source.html`.
- Wagtail-owned pages (home, raise, how) end `<main>` with the Wagtail source line: "Written on this site · reviewed 21 Oct 2026".
- **Public fields.** Name, seat and term are always public, because they're printed on public agendas. Photo, bio, pronouns, major and office hours appear only when that person's `public_profile` is True. Personal email is never synced. Every Contact button goes to the seat's role inbox.
- The Constitution `_cite.html` line and the "Source: … agenda" line stay as they are. They tell testers where *we* got a fact. The new source line says which *system* would own it in production.

**Seed in `data.py`**
```python
SYNC = {"notion_minutes_ago": 12, "wagtail_reviewed": date(2026, 10, 21)}
MOCK_NOTION = "https://www.notion.so/"   # every "Edit in Notion" link points here
```
`SOURCES` is a dict keyed by source key. Each value is `{key, line, edit_label, edit_url}`. Build `line` from `SYNC` with a helper.
| key | `line` as rendered | `edit_label` → `edit_url` |
|---|---|---|
| `roster` | "Roster: entered on this site by each body's roster officer · last change 25 Aug 2026" | "Edit on this site" → `/admin/` |
| `issues` | "Issues: Senate's Notion, items marked Public · synced 12 min ago" | "Edit in Notion" → MOCK_NOTION |
| `meeting_senate` | "Meeting record: Senate's Notion · synced 12 min ago" | "Edit in Notion" → MOCK_NOTION |
| `meeting_eboard` | "Meeting record: entered on this site by the E-Board Secretary · updated 24 Aug 2026" | "Edit on this site" → `/admin/` |
| `folder_only` | "Records: files in this body's Box folder. It doesn't list meetings on this site." | "Open in Box" → MOCK_BOX |
| `document` | "Agenda: Word file in Box, published as PDF" | "Edit in Box" → MOCK_BOX |
| `quoted_budget` | "Quoted from Executive Board Agenda 01, 25 Aug 2026 (a PDF in Box). This site does not update these figures." | "Open in Box" → "https://rpi.box.com/" |
| `wagtail` | "Written on this site · reviewed 21 Oct 2026" | "Edit in Wagtail" → `/admin/` |

**`_source.html`**, called as `{% include 'lab/your-reps/_source.html' with s=sources.roster %}`, renders:
`<p class="text-sm text-muted" data-source="{{ s.key }}">{{ s.line }}{% if officer %} · <a href="{{ s.edit_url }}" rel="nofollow">{{ s.edit_label }}</a> <span class="text-xs">(mock link)</span>{% endif %}</p>`

**Officer view (mock, no login)**
- Write one helper, `page(request, template, ctx)`, in `views.py` and have every view call it. It adds `sources`, `sync` and `officer` to the context.
- `officer` is True when the URL has `?officer=1`, or when the cookie `lab_officer=1` is set and the URL doesn't have `?officer=0`.
- `?officer=1` sets the cookie `lab_officer=1` (path `/lab/`, session cookie, SameSite Lax). `?officer=0` deletes it.
- The prototype banner gets a toggle. In student mode it reads "Viewing as a student · Show officer links" and links to `?officer=1`. In officer mode it reads "Viewing as an officer (mock) · Hide officer links" and links to `?officer=0`, with the muted line "On the real site these appear only to signed-in officers."
- Officer mode reveals the "Edit in …" links on source lines, plus the "Profile fields" table on person pages (5.3). It never reveals a value that isn't public.

**Banner text** gains a second sentence: "Lines like 'synced 12 min ago' are simulated. Nothing here is connected to Notion. Only the Senate's items would come from Notion."

## 0B. Per-body records (revision, 21 Oct 2026)

The site owner told us that only the Senate is adopting Notion, and that agendas, minutes and motions are written in Word. Other bodies organise themselves as they like, as long as their public records are strong. This section describes how the built prototype changes. Where it conflicts with later sections, this section wins. The page count stays at 7.

**Roster: this site, for every body.** People cross bodies: Cee Ray '27 is Senate Treasurer and the E-Board's Senate–E-Board Liaison, and Griffin Oliver '27 is a Senator, VGMIA and RAC chair. If the roster were split by body, those people would have two records, and their photo consent would have two owners. So this site owns seats, people, assignments and profile consent for every body. The Senate's Notion gets an automatic read-only copy (name, seat, term, voting) so it can record attendance.
- The `roster` source line reads: "Roster: entered on this site by each body's roster officer · last change 25 Aug 2026" → "Edit on this site" (`/admin/`).
- The person page's "Profile reviewed" line reads: "Not reviewed by this member yet. Members review their own profile on this site each semester."
- The officer "Profile fields" table rows change:
  - Name, seat, term: "Public". Why: "Printed on public agendas. Entered on this site." For anyone with a Senate role, add "The Senate's Notion keeps a read-only copy for attendance."
  - Photo, bio, pronouns, major, office hours: "Hidden". Why: "'Public profile' is unticked on this site."
  - Personal email: "Never published". Why: "Contact goes to the seat's role inbox."
  - Attendance: shown only for people with a Senate role. "Never synced". Why: "Kept privately in the Senate's Notion."
- The rollover preview banner reads: "Rollover preview (mock): the 2027–28 term is set as current on this site and no assignments have been entered yet, so every seat shows open. Nobody had to clear last year's names."

**Issues: Senate committees only.** "You said, we did" is a read-only view of the Senate's Notion "Issues" database, Public rows only. Other bodies don't publish an issue tracker.
- The `issues` source line reads: "Issues: Senate's Notion, items marked Public · synced 12 min ago".
- Re-own the two sample issues with non-Senate owners:
  - `iss-004` (club funding form): owner_seat "Senate–E-Board Liaison".
  - `iss-005` (grad stipends): owner_seat "Graduate Senators". Its 6 Oct update reads "Raised at a Senate meeting; the Graduate Council was asked for a written answer."
- `ISSUE_TRACKING` maps each owner body to one line, shown in the raise routing panel as "Tracked publicly?":
  - senate: "Yes. Senate committees log issues in the Senate's Notion, and items they mark Public appear on You said, we did."
  - eboard: "No. The Executive Board doesn't publish an issue tracker. What it decides appears in its minutes."
  - gc: "Graduate Senators can log it in the Senate's tracker. The Graduate Council doesn't publish one."
  - uc: "No. Class Councils and the Undergraduate Council don't publish an issue tracker."
  - jboard: "No. Judicial Board cases are confidential."
  - Topic to body: clubs → eboard, grad → gc, class → uc, rights → jboard, every other topic → senate.
- The raise POST confirmation, for a non-Senate topic, replaces the "Notion Issues" sentence with: "The {body} doesn't publish an issue tracker, so nothing would appear on You said, we did. Its response would be in its minutes."
- loop's "Where these come from" reads: "Each item is a row in a Senate committee's Notion Issues database. The committee updates it there, and this page shows rows marked Public, read-only. Nothing on this page is typed into the website. Only the Senate tracks issues publicly; other bodies' decisions appear in their minutes."

**Meetings (how#meetings), per body**
- Senate #12 renders with `meeting_senate`: "Meeting record: Senate's Notion · synced 12 min ago".
- E-Board 01 renders with `meeting_eboard`: "Meeting record: entered on this site by the E-Board Secretary · updated 24 Aug 2026" (an example choice).
- Each agenda is shown as "Agenda: Word file in Box, published as PDF". Never list its items.
- Then a "Bodies that publish records as files" list from `FOLDER_BODIES` (Graduate Council, Undergraduate Council, Judicial Board). Each gets: "Publishes its records as files. It doesn't list meetings on this site." Then the folder path (`Public Records/<Body>/2026-27 …/`) in a dashed "Box folder embed goes here" box, and the `folder_only` source line.

**How it works, "This site" section**
- Lead: "This site keeps one copy of each fact. It keeps the roster for every body and its own explanations. Files live in Box. Each body keeps its meeting records its own way: the Senate in its Notion, the Executive Board on this site, and the other bodies as files in Box."
- `OWNERSHIP` splits in two:
  - **`OWNERSHIP_BY_BODY`**, caption "Each body's records". Columns: Body | Meeting records | Roster | Issues. Rows:
    - Senate: Senate's Notion · this site (VGMIA), copied to the Senate's Notion · Senate's Notion Issues, Public rows.
    - E-Board (example): entered on this site · this site (VP for Rules and Special Projects) · not tracked publicly.
    - Graduate Council, Undergraduate Council, Judicial Board (examples): Box folder only · this site once a roster officer is named ("Roster not listed yet") · not tracked publicly.
  - **`OWNERSHIP_SHARED`**: seats, people and assignments for every body (this site, native); profile fields (this site, only with consent, edited by the member or their roster officer); the chooser and other explanations (native); "Senate attendance, contacts (CRM), internal notes · Senate's Notion · never shown".
- The line under the tables reads: "Each body chooses how it keeps its own records; the choices marked as examples are placeholders. Whatever it chooses, every body publishes agendas and minutes in its public Box folder under the Public Records Standard."
- "What members control" ends: "…decides on this site whether to publish a photo, bio, pronouns, major and office hours."
- "At the start of a new term": "Set the new term as current on this site…"
- The footer reads: "In the real site the roster is kept on this site by each body's roster officer. In this prototype it comes from the Union agendas of 30 Jul and 25 Aug 2026."

**`OWNERSHIP`** (superseded by `OWNERSHIP_BY_BODY` and `OWNERSHIP_SHARED` in 0B; kept here for history) was used by how#site. It is a list of `{what, lives_in, who_edits, how_site_gets_it, native}`:
| what | lives_in | who_edits | how_site_gets_it |
|---|---|---|---|
| Seats: label, constituency, voting, role inbox | Notion "Seats" | VGMIA (Senate), VP Rules and Special Projects (E-Board) | Synced; read-only in the site admin |
| People and term assignments | Notion "People", "Assignments" | VGMIA / VP Rules | Synced; read-only |
| Photo, bio, pronouns, major, office hours | Notion "People", only with "Public profile" ticked | Each member | Synced only with consent. Photos are copied into the site because Notion file links expire, and deleted if consent is withdrawn. |
| "You said, we did" issues (not built) | Notion "Issues", with a Public box | The owning committee (e.g. SCEC) | Would sync Public rows, read-only |
| Meeting records | Notion "Meetings"; agenda PDFs in Box | Each body's Secretary | Synced; links to Box |
| Chooser, constituency descriptions, topic router, fill rules, powers, glossary | This site | WTG chair | Native (Wagtail) |
| Attendance, contacts (CRM), internal notes | Notion | Officers | Never shown on the site |

## 1. Seed data (`data.py`)

**`PEOPLE`.** A dict keyed by slug (`slugify(first last)`). Each value is `{name, class_label (e.g. "'28", "'30G", "'26 '27G", or ""), roles:[{body, seat, constituency, note}], public_profile, profile_reviewed, photo, bio, pronouns, major, office_hours}`. For every real person, `public_profile=False`, `profile_reviewed=None`, and the five profile fields are None. Nobody has opted in, and we never invent profile data. Templates render the profile fields only when `public_profile` is True. Otherwise they show initials and the line "Photo, bio and office hours appear only if this member opts in."

Build it from these real rosters: Senate agenda 30 Jul 2026 and E-Board Agenda 01 of 25 Aug 2026. One person can hold several roles; merge them by name.

**Student Senate.** The Constitution sets 29 voting seats: 7 Graduate, 4 for each undergraduate class, 3 Independent, 3 Fraternity and Sorority Life (cite "Art. VII §1"). The Grand Marshal chairs and votes only to break a tie (cite "Art. IV §1").
- Grand Marshal: Jordan Krishnayah '28 (everyone)
- Graduate Senators (graduate): Batuhan Yalcin, Alexander Neimeth, Paul Lea, Stanley Goodwin '30G (also Student Life Committee chair), plus 3 Vacant
- Class of 2027 Senators (2027): Ghea Chaw, Griffin Oliver (also Vice Grand Marshal for Internal Affairs and Rules and Administration chair), Rachel Schneider, Adam Choi
- Class of 2028 (2028): Aaron Nam, Nick Castiglione (also Undergraduate Council report), plus 2 Vacant
- Class of 2029 (2029): Jaewon Yoon, Melissa DeLuise, Aarushi Kumar, Riley Sanders
- Class of 2030 (2030): 4 seats, status "elect_fall" (first-year senators are elected in the fall semester, cite "Art. VIII §3"; the 30 Jul 2026 roster predates that election)
- Independent (independent): Shruthi Anandraman '28 (also RLDC chair), Ryan Kilgore '27 (also VGM External Affairs), Ashley Wong '27
- Fraternity and Sorority Life (fsl): Mischa Fedak, Andrew Donilon, Radhika Manvar
  - **Reconciliation note** (shown on the independent and fsl constituency pages and in how#bodies, with cite "Art. VII §1; Art. VIII §5"): "The Senate agenda lists these six under one heading, 'Greek & Independent Senators'. Under the Union Constitution they are two separate groups of three seats: Independent Senators must not be in a fraternity or sorority, and FSL Senators must be. The Constitution is authoritative, so this site shows them separately. All six seats are filled." No "missing seat" note: the agenda gives no seat count for that heading.
- Non-voting officers (titles set by Senate bylaws, not the Constitution):
  - Cee Ray '27: Senate Treasurer, Senate–E-Board Liaison (the Constitution's "Treasurer" is RPI's own Treasurer, Art. VI, so always say "Senate Treasurer")
  - Sasha Notkin '28: Parliamentarian
  - Selena Tang '29: Secretary
- Committee chairs:
  - Zach Nobles '27 (Academic Affairs)
  - Mia Stryhalaleck '28 (Community Relations)
  - Lauren Antao '28 (acting Elections Commissioner)
  - Charlie Fowle '29 (Facilities and Services)
  - Emily Lin '29 (Senate Communications and Engagement)
  - Samson Kempiak '28 (acting Union Annual Report chair; also E-Board Club & Org Rep)
  - Aaron Niyazov '28 (Web Technologies Group)
- Peer reports: Melissa Flores 'G (Graduate Council).

**Executive Board.** The Constitution sets 15 to 20 voting members: 5 class reps (Freshman to Senior plus Graduate), 5 club and organisation reps plus up to 2 more, 2 members-at-large plus up to 3 more, and one rep each chosen by the Senate, the Graduate Council and the Undergraduate Council (cite "Art. VII §2"). The President chairs and votes only to break a tie (cite "Art. IV §2").
- President of the Union: Kate Goldstein '26 '27G (everyone)
- Officer titles (from E-Board bylaws, `draft="E-Board bylaws"`; the Constitution has no VP seats): Gavin Finn '28 (VP for Board Operations), Jesse Kim '26 '27G (VP for Club Relations), Blaine Rosenberg '28 (VP for Rules and Special Projects)
- Class Reps: Graduate Vacant; 2027 Jacob Bloecher '27; 2028 Mariam Toure '28 (also MLC chair); 2029 Ava Cintula '29 (also UAR chair); 2030 Vacant
- Club & Org Reps (clubs): Grey Smith '27 (Business Ops chair), Elijah Pulga '29 (Club Ops chair), Samson Kempiak '28, Valerie Rosa-Sanclemente '28, plus 3 Vacant (7 seats = 5 required + 2 optional)
- Members-at-Large (everyone): Ahmed Shoaib '29, Aaron Brown '29, Sumaya Moumita '28, William Liu '29, plus 1 Vacant (5 seats = 2 required + 3 optional)
- Council and Senate seats (voting under the Constitution, although the agenda prints them as "Peer Body Representatives"): Senate–E-Board Liaison Cee Ray '27; Graduate Council rep Joydip Paul '29G; Undergraduate Council rep Vacant
- Non-voting (from the agenda): Club Financial Advisors (clubs) Soloman Liao '29, Axo Ojeda-Ericksen '27; Secretary Eleonora Romani; UPAC chair Lilu Kaufman '26; Vacant: Parliamentarian, Marketing & Strategy chair, Executive Communications chair
- Note: the E-Board membership block is headed "2025-2026". Show "Roster may be out of date" with the source.

**`SEATS`.** A flat list of `{body, seat, constituency, person_slug or None, status, fill_rule, inbox}`, derived from the rosters above. `status` is "filled", "vacant" or "elect_fall"; None with "vacant" renders "Seat open", None with "elect_fall" renders "To be elected this fall". `inbox` is the seat's role inbox. It is None for every seat: no role inboxes exist yet, so never invent one. Sanity: Senate seats (excluding the Grand Marshal) total exactly 29; E-Board voting seats (excluding the President and the VP officer titles) total 20.

In production, `SEATS` is computed on this site from its seats plus current-term assignments, for every body: a seat with no assignment for the current term is Vacant. **Rollover preview:** any reps page accepts `?term=next`. It renders every seat on the page as "Seat open", with no names, under the banner "Rollover preview (mock): the 2027–28 term is set as current on this site and no assignments have been entered yet, so every seat shows open. Nobody had to clear last year's names." Implement this in the view by copying the seats with `person_slug=None, status="vacant"`.

**`FILL_RULES`**: how each seat gets filled and who it answers to. Each is `{key, filled_by, answers_to, cite, draft?}`. Shown on vacant cards, person pages, and how#elections.
- `gm`: filled_by "Elected by all students in the spring; needs at least 40% of the vote. If vacant, the Senate appoints a replacement by 2/3 within two weeks." answers_to "All students: a petition from 50% removes them; or 2/3 in a removal election where at least 20% vote, called by 2/3 of the Senate or by a 20% petition plus a Senate majority." cite "Art. VIII §1, §10; Art. X §1; Art. XI §1"
- `pu`: filled_by "Elected by all students in the spring; needs at least 40% of the vote. If vacant, the Executive Board appoints a replacement within two weeks and 2/3 of the Senate confirms." answers_to same as gm. cite "Art. VIII §1, §10; Art. X §1; Art. XI §2"
- `class_senator`: filled_by "Elected by the class (first-years in the fall, other classes in the spring). If vacant, the Class Council appoints someone; 20% of the class can force a special election by petition within two weeks of the announcement." answers_to "The class: a petition from 20%, or a Senate majority, starts a removal election; 2/3 of voters removes them if at least 20% vote. The Senate can also remove any senator for good cause by 2/3 of all seats (20 of 29, derived)." cite "Art. VIII §1, §3; Art. X §2; Art. XI §5, §6"
- `elected_senator` (Graduate, Independent, FSL): filled_by "Elected in the spring. A vacant seat can be filled by appointment; 20% of the constituency can force a special election by petition within two weeks of the announcement." answers_to as class_senator, with "their constituents" in place of "the class". cite "Art. VIII §1, §9; Art. X §2; Art. XI §5". `draft="Senate election rules"` (who appoints, and who counts as the Independent and FSL constituencies).
- `eb_appointed` (class, club and at-large E-Board seats): filled_by "Appointed by the President of the Union and approved by 2/3 of the Senate, not elected. Required seats within three weeks after spring elections; the first-year seat within three weeks after fall elections; optional seats by the end of the fourth week of fall." answers_to "The Senate: removable by 2/3 of the Senate, or at the President's request with a Senate majority." cite "Art. VII §2; Art. VIII §12; Art. X §3". `draft="E-Board bylaws"` (how to apply).
- `eb_peer`: filled_by "Chosen by the body it represents (Senate, Graduate Council or Undergraduate Council) within three weeks after that body's elections." answers_to "The body that chose them: removable by 2/3 of it, or at the President's request with its majority." cite "Art. VII §2; Art. VIII §12; Art. X §3"
- `officer_title` (VPs, Senate officers, committee chairs): filled_by "Set by the body's own bylaws." answers_to "Set by the body's own bylaws." `draft="Senate bylaws or rules"` or `"E-Board bylaws"`.

**`CONSTITUENCIES`.** Ordered dict. Each is `key: {label, plain, senate_seats, seats_cite, election_note}`:
- 2027: Class of 2027, senate_seats 4
- 2028: Class of 2028, senate_seats 4
- 2029: Class of 2029, senate_seats 4
- 2030: Class of 2030, senate_seats 4. election_note "Your class has 4 Senate seats. First-year senators and the first-year Class Council are elected in the fall semester. The latest roster we have (30 Jul 2026) is from before that election." cite "Art. VII §1; Art. VIII §3". No Draft badge.
- graduate: Graduate students, senate_seats 7
- independent: "Not in a fraternity or sorority (Independent)", senate_seats 3
- fsl: "In a fraternity or sorority (Fraternity and Sorority Life)", senate_seats 3
- clubs: "Club and organisation leaders", senate_seats 0. plain adds: "Clubs aren't a Senate constituency. Clubs have 5 to 7 seats on the Executive Board, but those reps are appointed by the President of the Union with 2/3 Senate approval, not elected by clubs." cite "Art. VII §2"
- seats_cite is "Art. VII §1" for every key except clubs.

Under the chooser, add this helper line: "You can belong to more than one group, for example Class of 2028 and Independent."

**`TOPICS`.** Each is `slug, question, owner_label, owner_role_seat` (used to look up the chair in PEOPLE), `outside_sg`:
- dining: "Problem with dining or meal plans?" → Residential Living and Dining Committee. outside_sg: "RPI's dining service runs meal plans; the committee raises student concerns with them."
- housing: "Problem with your residence hall?" → RLDC. outside_sg: "Residence Life runs housing day to day."
- buildings: "Broken, inaccessible or unsafe building?" → Facilities and Services Committee. outside_sg: "For urgent repairs contact RPI Facilities directly."
- academics: → Academic Affairs Committee
- student-life: → Student Life Committee
- troy: "Off-campus or Troy community issue?" → Community Relations Committee
- clubs: "Club rules, registration or money?" → Executive Board, VP for Club Relations. Body fact: "The Executive Board decides how clubs are classified and hands out Union money." cite "Art. VII §2". The VP routing carries `draft="E-Board bylaws"`.
- grad: "Stipends, grad housing, TA workload?" → Graduate Council and Graduate Senators. Body fact: "The Graduate Council is the Union's advocacy body for graduate students: the 7 Graduate Senators plus at least 5 at-large members." cite "Art. VII §4"
- class: "Class events or class dues?" → your Class Council (graduate students: the Graduate Council). Body fact: "Each class elects a Class Council, which recommends how class dues are spent; the Undergraduate Council approves that spending." cite "Art. VII §5". Chair: "Roster not listed yet".
- rights: "Think a Union body broke the Constitution, or your student rights were violated?" → Judicial Board. Body fact: "The Judicial Board is the Union's student court. It hears charges that the Union Constitution, the Rensselaer Student Bill of Rights, or student conduct rules were violated, and can rule other bodies' decisions unconstitutional." cite "Art. VII §3". outside_sg: none. The routing panel for this topic says "How to file: not published yet" with `draft="Judicial Board bylaws"` and links to how#powers instead of showing the mock form's email preview.
- elections: → Elections Commission (`draft="Senate election rules"`: the Constitution leaves election procedure to the Senate, Art. VIII §6)
- website: → Web Technologies Group
- other: → Grand Marshal's office. Body fact: "The Grand Marshal is the leader and chief spokesperson for the whole Union." cite "Art. IV §1"

The Senate committee owners (RLDC, FSC, AAC, SLC, CRC, Elections Commission, WTG) come from the agendas; the Constitution names no committees. Their remit sentences carry `draft="Senate bylaws or rules"`.

Add a safety line on topic output: "If anyone is in danger, contact RPI Public Safety now." (`draft="Site owner"`). Do not invent a phone number.

**`ISSUES` (all SAMPLE).** These stand in for synced rows from the Senate's Notion "Issues" database (see 0A, 0B). Every owner_seat is a Senate seat. Every row here has `public=True`, the Notion Public box; the sync would drop any row without it. The keys are exactly the whitelisted fields, so there is no field for the student's original message or name. Render every issue list with the `issues` source line. 6 dicts with these keys:
- `id`, `title` (in the student's words, e.g. "Commons dining hall closes too early on weekends")
- `topic`, `constituencies`
- `owner_seat` (a seat label, never a person)
- `source` (Senate survey | Speak at a meeting | Email | Discord)
- `raised_on`
- `status`, one of: heard "Heard", assigned "Owner assigned", working "Working on it", brought "Brought to a meeting", decided "Decided", done "Done", not_possible "Not possible"
- `updates:[{date, text}]`
- `outcome`
- `last_update`

Include at least:
- 1 `done` with 3 updates and an outcome.
- 1 `not_possible` with the reason ("RPI controls this; here's who to contact instead").
- 1 `working` whose last update is more than 60 days before today, so it shows the stale label "No update since 14 Aug 2026".
- 1 `heard`.

All dates are in 2026.

**`GLOSSARY`.** Each entry is `{term, text, cite?, draft?}`; render in this order:
- Rensselaer Union: "Every enrolled RPI student who has paid the Union Activity Fee, and the organisation they form." cite "Art. I; Art. II"
- Student Senate: "The Union's main lawmaking body, with 29 voting seats. Passes its own rules, sets the Activity Fee and approves many appointments." cite "Art. VII §1"
- Executive Board: "The Union's budgeting body: prepares and approves the budget, hands out Union money and classifies clubs." cite "Art. VII §2"
- Judicial Board: "The Union's student court for rights and conduct cases, and the only body that interprets the Constitution." cite "Art. VII §3"
- Graduate Council: "The advocacy body for graduate students: the 7 Graduate Senators plus at least 5 at-large members. Elects its own President." cite "Art. VII §4; Amendment V"
- Undergraduate Council: "The advocacy body for undergraduates: the President and Vice President of each Class Council. Oversees the Class Councils." cite "Art. VII §5"
- Class Council: "Your class's own elected council: Class President, Vice President, at least 8 Representatives and your 4 Class Senators. Recommends how class dues are spent." cite "Art. VII §5"
- Grand Marshal: "The Union's leader and chief spokesperson, elected by all students. Chairs the Senate and votes only to break a tie." cite "Art. IV §1"
- President of the Union: "Chairs the Executive Board and appoints most of its members, with 2/3 Senate approval." cite "Art. IV §2; Art. VII §2"
- Director of the Union: "A paid staff member who runs Union activities and funds. Advises the Executive Board but cannot veto it." cite "Art. V"
- Class Representative (Executive Board): "One E-Board seat per class, appointed by the President of the Union with 2/3 Senate approval. Not the same as a Class Council Representative, who is elected." cite "Art. VII §2, §5"
- Member-at-Large: "An E-Board seat that can represent any Union member; 2 required, up to 3 more." cite "Art. VII §2"
- Recall: "A student vote to remove someone you elected before their term ends." cite "Art. X §1, §2"
- Referendum: "A binding student vote on a question, forced by a 10% petition or put on the ballot by 2/3 of the Senate. It counts if at least 20% vote." cite "Art. XII"
- Ex-officio: "Holding a seat automatically because of another office."
- Quorum: "The minimum number of voting members needed for a meeting to act. The Constitution leaves it to each body's rules; the latest Senate agenda lists 13." Source line: Student Senate agenda, 30 Jul 2026. `draft="Senate bylaws or rules"`
- Invitation to Speak: "Time at the start and end of every meeting when anyone may speak." `draft="Senate bylaws or rules"`
- Senate Treasurer: "A Senate officer from the agendas. Not the Constitution's 'Treasurer', which is RPI's own Treasurer who holds the Union's money." cite "Art. VI"

Do not add an entry for "RUGP".

**`POWERS`** (for how#powers: what you can do if your reps don't act). Ordered list of `{id, title, text, not_set, not_set_why, cite}`:
- `recall`, "Remove someone you elected": "A petition from 20% of a senator's constituents (or a Senate majority) starts a removal election; 2/3 of those voting removes them, if at least 20% vote. For the Grand Marshal, President of the Union, and the Graduate and Undergraduate Council Presidents, a petition from 50% of their constituents removes them outright." not_set "What counts as good cause; how removal elections are run" · "Senate bylaws or rules" · cite "Art. X §1, §2"
- `challenge`, "Force an election for an appointed seat": "If an elected seat is filled by appointment, a petition from 20% of that constituency, received by the Senate within two weeks of the announcement, forces a special election. Example: Class of 2028 has 2 open Senate seats; if its Class Council appoints people to them, 20% of the class can force an election." (compute the example from SEATS) · not_set "Petition format and where to hand it in" · "Senate bylaws or rules" · cite "Art. XI §5, §6"
- `referendum`, "Make students vote on it": "A petition signed by 10% of all Union members makes the Senate hold a binding student vote on anything except the Constitution, unless 2/3 of all Senate seats (20 of 29, derived) reject it. The vote is within 45 days (excluding vacations) or at the next regular election, at least 14 days after approval, never during exams. It passes by majority if at least 20% of affected students vote, and the Senate must then carry it out." not_set "Petition format; how signatures are checked; how many students 10% is" · "Senate bylaws or rules" · cite "Art. XII §1–§4"
- `judicial-board`, "Bring a case to the Judicial Board": "Any charge that the Constitution, the Rensselaer Student Bill of Rights, or student conduct rules were violated can be referred to the Judicial Board. It can rule a Senate, Executive Board or council decision unconstitutional." not_set "Who may file, how, deadlines and appeals" · "Judicial Board bylaws" · cite "Art. VII §3"
- `amend`, "Change the Constitution": "Ask your senators: an amendment needs 2/3 of the Senate, then a majority in a campus vote where at least 20% of students vote. A petition alone can't amend it. The wording must be published campus-wide at least two weeks before the vote." cite "Art. XII §1; Art. XIII §1, §3"
- `run`, "Take the seat yourself": "Any Union member can run, subject to RPI's eligibility rules and the Senate's. General elections are in the spring; first-year seats in the fall." not_set "How to get on the ballot, signatures, dates" · "Senate election rules" · cite "Art. VIII §1, §3, §4, §6, §13"

## 2. Optional DB reads (wrapped)

- `SiteSettings.load(request_or_site=request)`: `contact_email`, plus `office_hours`, `office_location`, `discord_url`.
- **Contact button order** (every card and person page):
  1. If the seat has a role `inbox`: "Email this seat" as a mailto to the inbox. No seat has one in the seed.
  2. Otherwise, if `contact_email` is set: "Email the Union office" as a mailto, with the subject "For: <seat>". Add the muted note "This seat doesn't have its own role inbox yet."
  3. Otherwise: "Contact route not set up yet" + the Draft badge with `why="Site owner"`.
  - Never use a personal address, even if one turns up in the DB (`MemberProfile.email` is not read).
- Don't read `MemberProfile.photo`. Photos would appear only with `public_profile=True` (nobody has it), copied in by the sync. Always render initials.
- `EventPage` upcoming events, via `home.models._upcoming_by_next_occurrence`, for the this-week line. Skip `event_type == "meeting"`: meetings come only from the meeting records (Notion), never from hand-made calendar entries.

## 3. Pages

| name | URL | template |
|---|---|---|
| home | `/lab/your-reps/` | `home.html` |
| reps | `/lab/your-reps/reps/<slug:key>/` | `reps.html` |
| person | `/lab/your-reps/people/<slug:slug>/` | `person.html` |
| people | `/lab/your-reps/people/` | `people.html` (A–Z directory) |
| raise | `/lab/your-reps/raise/` | `raise.html` (GET and POST) |
| loop | `/lab/your-reps/you-said-we-did/` | `loop.html` |
| how | `/lab/your-reps/how-it-works/` | `how.html` |

Unknown keys or slugs return 404.

## 4. Visual direction: warm and people-forward

**Styles and type:**
- Tailwind Play CDN `<script src="https://cdn.tailwindcss.com/3.4.17"></script>`.
- Optional Google Font "Geist" (`https://fonts.googleapis.com/css2?family=Geist:wght@400;600;700&display=swap`), with a system fallback.
- Base 1.0625rem, line-height 1.6. h1 1.875rem → 2.5rem at md.

**Colour tokens:**
- bg #f6f6f8 (page), card #ffffff, ink #1a1a2e, muted #4a4a68 (8.6:1 on white)
- accent #d6001c: only as a button background with white bold text (5.4:1) or for large headings
- link #a50015
- vacant border #8a8aa3 dashed
- focus: 3px #1a1a2e outline with a 2px #ffdd00 inner ring

**Shapes and avatars:**
- Cards: rounded-xl, 1px border #e2e2ea, padding 16px.
- Initials avatars: a 56px circle in #1a1a2e with white text, aria-hidden. The name is shown next to it.

**Header:**
- Wordmark "Your Student Government" with the subline "Rensselaer Union".
- Nav: **Your reps** · **Raise an issue** · **You said, we did** · **How it works** · **Everyone A–Z**.
- Mobile: `<details>` menu.
- The selected constituency shows as a chip in the header ("You: Class of 2028 · change"), read from localStorage via progressive enhancement only.

**Breakpoints:** mobile single column. md: 2-col card grid. lg: 3-col card grid with max-w-6xl.

**Footer:**
- "Part of the Rensselaer Union · 110 8th Street, Troy, NY 12180".
- SiteSettings contact and office hours if present.
- "In the real site the roster is kept on this site by each body's roster officer. In this prototype it comes from the Union agendas of 30 Jul and 25 Aug 2026."
- "Maintained by the Web Technologies Group · How this site works (how#site)".

## 5. Page specs

### 5.1 Home

1. Purpose line (h1): "Your student government: who represents you, and what they're doing about it."
2. **"I'm a…" chooser.**
   - Large 56px-tall link buttons: '27, '28, '29, '30, Grad on row one; Independent, Fraternity & Sorority Life, Club leader on row two. Each links to `reps/<key>/`.
   - Inline script: on click, `try{localStorage.setItem('yr-key',key)}catch(e){}`. On load, if a key is stored, show a "Go to your reps: Class of 2028" link above the chooser.
3. **This-week line.** One sentence from the upcoming meetings. If none in 7 days: "No meetings listed this week. The Senate last met 30 Jul 2026." Link to how#meetings.
4. **"Most requested" strip.** Three link cards so the task-first need isn't lost: "Raise an issue" → raise; "Get money for your club" → reps/clubs/; "Speak at a meeting" → how#speak.
5. **You said, we did.** The 3 most recently updated ISSUES, each with a status chip, title, owner seat and last update. Sample pills. Then the `issues` source line.
6. **Who handles what.** 6 topic links (dining, housing, buildings, academics, clubs, grad), each to `raise?topic=<slug>`.

### 5.2 Constituency page (`reps`)

- h1 "Class of 2028: who represents you". Subline is the constituency's plain description.
- **"Your senators"** grid (the Senate seats for this key). Heading line: "Your group has {senate_seats} Senate seats under the Union Constitution" with the constitution line.
  - **Filled card:** avatar (initials), name (links to person), seat label, other roles ("Also: Chair, RLDC"), "Office hours: Not listed", and the Contact button (see the contact order in section 2).
  - Under each card grid: the `roster` source line.
  - **Vacant card:** dashed border, "Seat open", then the seat's `FILL_RULES.filled_by` text, its constitution line and Draft badge if any. Link "How elections work →" (how#elections).
- **independent / fsl keys:** show the reconciliation note under the grid.
- **"Your Executive Board representative"** (for class and graduate keys). Under the card: "Appointed by the President of the Union with 2/3 Senate approval, not elected." cite "Art. VII §2".
- **"Your Class Council"** (class keys 2027–2030): summary box "Your class elects a Class Council: a Class President, a Vice President, at least 8 Representatives and your 4 Class Senators. It recommends how your class dues are spent and fills vacant Class Senator seats." cite "Art. VII §5; Art. XI §6". Then "Roster not listed yet."
- **"Your Graduate Council"** (graduate key): "The Graduate Council is the advocacy body for graduate students: the 7 Graduate Senators above plus at least 5 at-large members. It elects its own President from among its members and controls graduate class dues." cite "Art. VII §4; Amendment V". Then, with the agenda source line: "Graduate Council report at Senate #12: Melissa Flores 'G. E-Board Graduate Council rep: Joydip Paul '29G." Don't call anyone the Council President.
- **"Represents everyone":** Grand Marshal, President of the Union, Members-at-Large.
- **Empty-constituency rule (2030):**
  - Do not render four empty seat cards.
  - Instead show a summary box with `election_note` (and its constitution line) and "Until then, these people represent everyone:", with the "Represents everyone" section moved directly below it.
  - Also show "Your E-Board Class Representative: Seat open. Appointed within three weeks after the fall elections." cite "Art. VIII §12".
- **clubs key:** Club & Org Reps, VP for Club Relations, Club Financial Advisors, the clubs `plain` note with its cite, plus a "Club money" box: "The Executive Board hands out Union money, and the budget and records of extra spending are public documents." (cite "Art. VII §2") then "As printed on Executive Board Agenda 01 (25 Aug 2026): $100,000 in club contingencies and $60,000 in travel contingencies, none of it spent yet." with the `quoted_budget` source line and `draft="E-Board bylaws"` on "contingencies". Don't present it as a current balance.
- **"Your say over these seats"** (every key, near the bottom): two or three lines built from the seat types on the page, each with its cite: the `answers_to` text of this page's senator fill rule; the challenge line if any seat is vacant ("If it's filled by appointment, 20% of you can force an election within two weeks of the announcement", Art. XI §5); and "If they won't act: 10% of Union members can force a binding student vote" (Art. XII §1). Link "All your powers →" (how#powers).
- **Open issues for this group:** ISSUES filtered by constituency (Sample), then the `issues` source line.
- **Bottom:** "Belong to another group too? Also see Independent / Fraternity and Sorority Life" links.
- **With `?term=next`:** the rollover preview banner above the h1, and every seat card as "Seat open" (see `SEATS`).

### 5.3 Person page

- Avatar 96px, h1 name, class label.
- **"Roles":** a list of every role, with its body and seat, and the term label ("57th Student Senate" / "2026–27 Executive Board"). Under each role, two muted lines from its `FILL_RULES` entry: "How this seat is filled: …" and "Answers to: …", followed by the constitution line (or the Draft badge for `officer_title` roles). Example for Griffin Oliver's Class of 2027 Senator role: "Answers to: The class: a petition from 20%, or a Senate majority, starts a removal election…" Source: Union Constitution, Art. VIII §1, §3; Art. X §2; Art. XI §5, §6.
- **"Represents":** constituency labels, linked.
- **"Office hours":** "Not listed. Shown only if this member opts in."
- **"Contact":** the Contact button for their first seat (section 2 order). It goes to a role inbox or the Union office, never to a personal address.
- **"Working on":** ISSUES whose owner_seat matches one of this person's seats. If none, "No public issues assigned to this seat."
- **"Profile reviewed":** the member's `profile_reviewed` date, kept on this site. It is None for everyone: "Not reviewed by this member yet. Members review their own profile on this site each semester."
- **"Profile fields" table (officer view only)**, caption "What the site publishes for this person" (rows revised in 0B). Columns: Field | On the site | Why.
  - Name, seat, term: Public. "Printed on public agendas."
  - Photo, bio, pronouns, major, office hours: "Hidden". "'Public profile' is unticked on this site."
  - Personal email: "Never synced". "Contact goes to the seat's role inbox."
  - Attendance: "Never synced". "Private."
- The `roster` source line, then the agenda source line.

### 5.4 Everyone A–Z

- An alphabetical list of PEOPLE with role summaries.
- A letter jump-nav: real anchor links, only for letters present.
- A GET text filter `?q=`, applied server side.
- The `roster` source line under the list.

### 5.5 Raise an issue (`raise`)

**Step 1: "What's it about?"** A radio group (fieldset with legend) of TOPICS questions. If `?topic=` is set, preselect it and show its routing.

**Routing panel** for the selected topic:
- "This goes to: Residential Living and Dining Committee (Chair: Shruthi Anandraman '28)".
- The topic's body fact with its constitution line, if it has one; otherwise its remit sentence with the Draft badge.
- The `outside_sg` note.
- For `rights`: "How to file: not published yet" with `draft="Judicial Board bylaws"` and a link to how#powers. Step 2 (the mock form) is not shown for this topic, because there is no route to preview.
- "Also your reps:" with up to 4 rep names from the remembered constituency (via `?for=2028`, which the link from the reps page passes).

**Step 2: mock form.** Fields:
- "Describe the problem" (textarea, required, 20–1000 chars)
- "Which group are you in?" (select of CONSTITUENCIES, optional)
- "May we publish an anonymised summary on You said, we did?" (yes/no radios)

Banner above the form: "Mock for testing. Nothing you type is saved or sent." Do NOT include name or email fields.

**On POST:**
- Validate with a Django `forms.Form`.
- On errors, show an error summary (`role="alert"`, links to fields) plus inline errors.
- On success, render a confirmation preview: "In the real site this would be emailed to: RLDC chair's role inbox (to be set up). The committee would log it as a private row in its Notion Issues database. If you said yes to publishing and the committee ticks Public, an anonymised summary would appear on You said, we did with status 'Heard'. Your own words are never published." Add `draft="Site owner"`: the issue board isn't agreed yet.
- Do not echo the description back verbatim. Show only its character count.
- Never store or log.

The safety line goes at the bottom, then the `wagtail` source line (the topic router is written on this site).

### 5.6 You said, we did (`loop`)

At the top, an explainer box (`draft="Site owner"`: this board is a site practice, not a constitutional duty): "Each item is owned by a seat, not a person, so it passes to the next officeholder. Status is updated after meetings. 'Not possible' outcomes are shown too." Plus a visible note: "Running this for real needs a committee (e.g. Senate Communications and Engagement) to commit to weekly triage. Not yet agreed."

Under it, a "Where these come from" line: "Each item is a row in the owning committee's Notion Issues database. The committee updates it there, and this page shows rows marked Public, read-only. Nothing on this page is typed into the website." Then the `issues` source line.

Under the filters, one line: "Stuck? Students can force a binding student vote with a petition signed by 10% of Union members." cite "Art. XII §1"; link how#powers.

**Filters** (GET): status, topic, constituency.

**Issue cards:**
- Status chip (word plus colour; see tokens), title, topic, owner seat, source, raised date.
- A `<details>` "Updates (3)" with a dated timeline (`<ol>` with `<time>`).
- Outcome.
- Staleness: if `last_update` is more than 60 days before today, add the muted label "No update since <date with year>".

**Chip colours** (each at least 7:1):
- done: green-900 on green-50
- not_possible: gray-900 on gray-100
- working/brought/assigned: amber-900 on amber-50
- heard: blue-900 on blue-50
- decided: purple-900 on purple-50

### 5.7 How it works (`how`)

In-page nav: Bodies · Meetings · Speak · Elections · Your powers · Glossary · This site. Intro line: "Rules on this page come from the Rensselaer Union Constitution, last amended 6 Feb 2026, unless marked Draft."
- **Bodies** (`id=bodies`): the five governing bodies (Senate, Executive Board, Judicial Board, Graduate Council, Undergraduate Council), then Class Councils. Each has its GLOSSARY sentence, a "Who sits on it" line (Senate: 7 Graduate, 4 per class, 3 Independent, 3 FSL = 29; E-Board: 15–20 as listed in `PEOPLE`; Judicial Board: 6 voting members and 5 alternates; Graduate Council: 7 Graduate Senators + at least 5 at-large; Undergraduate Council: each Class Council's President and Vice President, 8 (derived); Class Council: President, VP, at least 8 Representatives, 4 Class Senators), who chairs, its constitution line (Art. VII §1–§5), and links to its rosters ("Roster not listed yet" for the Judicial Board, Graduate Council, Undergraduate Council and Class Councils). Show the reconciliation note under the Senate.
- **The five Union officers** (sub-list under Bodies): Grand Marshal, President of the Union, Judicial Board Chairperson, Graduate Council President, Undergraduate Council President; "they must meet regularly to coordinate." cite "Art. IV".
- **Meetings** (`id=meetings`):
  - Senate #12 was 30 Jul 2026, 8 PM, Webex.
  - E-Board Agenda 01 was 25 Aug 2026, 7 PM, RU 3202.
  - "Minutes not posted" status for both.
  - A note that the live site says Mondays 7 PM; the schedule is to be confirmed.
  - The `meeting` source line.
- **Speak** (`id=speak`): Invitation to Speak / Press & Visitor Q/A, in plain language (`draft="Senate bylaws or rules"`).
- **Elections** (`id=elections`):
  - "When": "General elections are in the spring. First-year Senators and the first-year Class Council are elected in the fall. Results come out by the end of the semester and winners take office within a week." cite "Art. VIII §1–§3, §12"
  - "Who can vote and run": "Any Union member at the time of the election; voting is by secret ballot. Candidates must meet RPI's eligibility rules and any Senate rules. Grand Marshal, President of the Union and Judicial Board Chairperson need one full semester at RPI." cite "Art. IV §6; Art. VIII §4, §13"
  - "How winners are chosen": "Grand Marshal and President of the Union need at least 40% of the vote. Most other seats go to whoever gets the most votes. The three FSL seats are spread across chapter groupings: the top vote-getter wins, and the next two seats go to the top candidates from different groupings (or write-ins). Ties mean a new election between the tied candidates." cite "Art. VIII §5, §8, §10, §11"
  - "How seats get filled": a table, caption "Who fills each kind of seat", columns Seat | Filled by | Answers to | Source, from `FILL_RULES`.
  - Open seats counted from SEATS, grouped by body (first-year Senate seats listed as "To be elected this fall").
  - "Contact the Elections Commission (Lauren Antao, acting)" (agenda source line, `draft="Senate election rules"`: ballot access is set by the Senate, Art. VIII §6).
- **Your powers** (`id=powers`): h2 "If your reps don't act". Lead: "The Constitution gives every Union member these tools." Each `POWERS` entry is an `<h3 id="{id}">` with its text, "Not set by the Constitution: …" plus the Draft badge (when `not_set`), and its constitution line. No buttons: none has a published submission route yet.
- **Glossary:** a `<dl>` from GLOSSARY.
- **How this site works** (`id=site`, the handoff):
  - Lead and tables: as in 0B (per-body table, shared table, and the "Each body chooses" line).
  - **"What lives where"** table from `OWNERSHIP`, caption "What lives where, and who edits it" (`draft="Site owner"`). Columns: What | Lives in | Who edits | How this site gets it. Rows with `native=True` get a bordered "Written on this site" tag in the first cell. Under it: "If a body decides not to use Notion, its roster lives on this site instead. It lives in one place, never both: no parallel spreadsheet or CSV import."
  - **"Written on this site"** list, linked: the "I'm a…" chooser, the constituency descriptions, Raise an issue (topic router), and this How it works page (bodies, elections, fill rules, powers, glossary).
  - **"What members control"**: "Name, seat and term are always public, because they're on public agendas. Each member decides on this site whether to publish a photo, bio, pronouns, major and office hours. Unticking 'Public profile' removes them from this site at once. Contact always goes to the seat's role inbox."
  - **"At the start of a new term"**: "Set the new term as current on this site. Every seat on this site then shows open until new assignments are entered. Nobody clears last year's names by hand." Link: "See what that looks like" → reps/2028/?term=next.
  - The `wagtail` source line.

## 6. Accessibility (WCAG 2.2 AA)

- Skip link, landmarks, one h1 per page, a logical heading order.
- Every card name is a real link. The avatar is aria-hidden and the name is text.
- Chooser buttons are `<a>` elements with at least 44px targets. Radio groups use fieldset/legend.
- Status chips always contain words. Dates include the year in `<time>`.
- Accent red #d6001c only behind white bold text at 1rem or larger, or on large text. Never small red text on the gray bg (#d6001c on #f6f6f8 is about 5.0:1, acceptable but avoid it).
- Works with JS off: localStorage only adds shortcuts.
- Reduced motion is respected. At 320px width there is no horizontal scroll.
- Form errors are announced.

## 7. Tests

GET 200 for:
- home
- reps for 2027, 2028, 2030 (contains "represent everyone" and "elected in the fall semester"), graduate (contains "at least 5 at-large"), fsl (contains "Fraternity and Sorority Life" and "two separate groups"), clubs (contains "not elected by clubs")
- person `griffin-oliver` (contains "Vice Grand Marshal for Internal Affairs", "Class of 2027" and "Answers to")
- person `cee-ray` (contains "Senate Treasurer" and "Senate–E-Board Liaison")
- people, `people?q=kim`
- raise, `raise?topic=dining` (contains "Residential Living and Dining"), `raise?topic=rights` (contains "Judicial Board")
- loop, `loop?status=done`
- how (contains "10% of all Union members", "40%" and "Union Constitution, Art. XII")

Also assert: no page contains "RUGP" or "Greek-affiliated"; Senate seats in `SEATS` (excluding the Grand Marshal) number exactly 29; E-Board voting seats number 20.

Single source of truth:
- reps 2028 contains "Roster: entered on this site" and not "Edit on this site". With `?officer=1` it contains "Edit on this site" and not "Edit in Notion", and the response sets the `lab_officer` cookie.
- loop with `?officer=1` contains "Edit in Notion". `raise?topic=clubs` contains "doesn't publish an issue tracker". No `ISSUES` owner_seat is an E-Board, Council or Judicial Board seat.
- how contains "Each body's records", "Publishes its records as files" and "Judicial Board". No `OWNERSHIP_BY_BODY` row other than the Senate's contains "Notion".
- person `cee-ray` with `?officer=1` contains "read-only copy for attendance".
- `reps/2028/?term=next` contains "Rollover preview" and doesn't contain "Aaron Nam".
- person `griffin-oliver` contains "opts in" and "Not reviewed by this member yet". With `?officer=1` it contains "What the site publishes" and "Never synced".
- Every `PEOPLE` entry has `public_profile` False, and every `SEATS` entry has `inbox` None.
- With the empty test DB there is no contact_email, so reps 2028 contains "Contact route not set up yet" and no "mailto:".
- loop contains "Issues: Senate's Notion, items marked Public", "Nothing on this page is typed into the website" and "Only the Senate tracks issues publicly".
- how contains "What lives where" and "Written on this site".

POST to raise:
- Valid input returns 200 with "would be emailed".
- A too-short description returns 200 with the error summary.

404 for `reps/1999` and `people/nobody`.

Run `env/bin/python manage.py test lab` and `manage.py check`.