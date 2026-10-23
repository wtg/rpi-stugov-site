# Concept 4: The Operator's Console (built for the people who run it)

# The Operator's Console: a concept for the Rensselaer Union site

## 1. Thesis

**Purpose:** The site is the Union's public record, and it gets published as a side effect of officers doing their normal jobs.

Peer sites mostly fail in the same way, and it isn't bad design. Berkeley's tracker still says 2025-26. UT's and Houston's tables are blank. RPI's events have no year and its homepage quick links are empty. In each case one student's memory was the only thing keeping the site current. This concept treats freshness as the main design problem. Students get a useful site because the secretaries' workflow keeps it accurate.

**Principles**

1. **Records, not pages.** Everything public is a structured record: Meeting, Decision, Seat assignment, Process, or Notice. Public pages are generated views of those records. Nobody hand-writes a list.
2. **The two-minute rule.** Any routine publishing task must take two minutes or less from a phone. That covers posting an agenda, recording an outcome and swapping a senator. If a task takes longer, the model is wrong.
3. **Freshness is visible and enforced.** Every record has an owner role and a review-by date. Content that goes stale is labelled as stale and drops off the homepage. It is never silently wrong.
4. **Terms come first.** Everything is keyed to a term ("57th Senate", "FY27 Executive Board"). Moving to a new term is one command. It does not mean rebuilding the site.
5. **Box holds the files; the site holds the facts.** PDFs stay in Box. The site stores dates, status, relationships and a plain-language summary.

## 2. Primary users and top tasks

The constitution was not readable, so the processes below come from the two agendas and the Digital Infrastructure Plan. Section numbers, deadlines and thresholds must be checked against the constitution and the Rensselaer Union Guidelines and Procedures before they are built.

| Rank | Task | Persona | Grounding |
|---|---|---|---|
| 1 | Post an agenda for the next meeting | Gov (Senate and EBoard secretaries) | Both agendas follow a fixed section order |
| 2 | Find the next meeting: when, where, and what's on it | Student | Senate meets Mondays at 7pm; locations switch between Webex and RU 3202 |
| 3 | See what passed and what happened afterwards | Student | EBoard approves minutes; motions and resolutions appear in New and Old Business |
| 4 | Record outcomes after a meeting (pass/fail/tabled, tally, minutes link) | Gov (secretaries) | Minutes are approved at the following meeting |
| 5 | Find who represents me (class year, grad, FSL or Independent) | Student | Senate seats are set by constituency; `Role.constituency` already exists |
| 6 | Get money or space for my club | Student (club officers) | Club and Travel Contingencies, Special Ballroom Requests (EBoard) |
| 7 | Speak at a meeting or raise an issue | Student | Standing "Invitation to Speak" and "Press & Visitor Q/A" items |
| 8 | Change roster members at turnover or mid-term | Gov (Web Technologies Group chair and body leads) | Vacant seats appear on both agendas |

The console exists for tasks 1, 4 and 8. Tasks 2, 3 and 5 are what students get as a result.

## 3. Information architecture

**Top-level nav (5 items plus search):** Meetings · Decisions · People · Get help · Documents · [Search]

```
Meetings
  ├─ Upcoming (all bodies, filter by body)
  ├─ Past meetings (by term; agenda, minutes, recording)
  └─ Subscribe (calendar feed per body)
Decisions
  ├─ Tracker (filter: term, body, stage, type)
  └─ You said, we did (decisions with an implementation outcome)
People
  ├─ Who represents me (class / grad / FSL / Independent picker)
  ├─ Student Senate         → committees (AAC, CRC, FSC, RLDC, RAC, SLC, SCEC, WTG, UAR, Elections)
  ├─ Executive Board        → committees (Business Ops, Club Ops, UPAC, MLC, ...)
  ├─ Undergraduate Council  → class councils (2027–2030)
  ├─ Graduate Council
  └─ Judicial Board
Get help
  ├─ Request club funding / Travel funding / Book the Ballroom
  ├─ Speak at a meeting
  └─ Report a problem
Documents
  ├─ Governing documents (Constitution, RUGP, Bylaws, policy history)
  └─ Archive (Box-backed, searchable via BoxFileCache)
```

The five branches, the class councils and the committees all live under **People**. Each body page is generated. It shows a one-sentence description, the next meeting, the last five decisions, the current roster with vacancies, and the body's committees. The org chart is still there, but it sits one level down instead of driving the nav.

## 4. Homepage (mobile-first)

Every section is a query. The homepage has no StreamField. The only hand-entered content is a Notice, and Notices expire.

**Above the fold on a phone:**

1. **Alert slot.** Shown only while a Notice is active, for example "Election voting closes Fri Oct 24, 2026".
2. **Next meeting card.**
   - Shows body, full date with the year, time, and room or Webex link.
   - Shows "Agenda posted" with a link, or, honestly: "Agenda not posted yet".
   - Has a "See all meetings" link.
3. **Four task buttons:** Find my rep · Request funding · Speak at a meeting · Report a problem.

**Below the fold:**

4. **Recently decided.** The last five Decisions, each with a stage chip and a one-line summary.
5. **This week.** Committee meetings, office hours and deadlines, built from Meetings, Process deadlines and Notices.
6. **Who represents you.** A class-year dropdown that shows matching Seat assignments, each with photo, role and contact.
7. **Where the contingency money stands.** The four budget lines (Club, Travel, Facilities, Facilities Reserves), each with an "as of" date.
8. **Footer freshness strip.** For example: "Senate roster confirmed Oct 3, 2026 · Records synced from Box 2 hours ago · Site maintained by the Web Technologies Group."

**Empty states:** if a section has no fresh data, it collapses instead of showing "No upcoming events".

## 5. Signature page types

**A. Meeting** (snippet with drafts and revisions, served through a routable index at `/meetings/senate/57/12/`)
- **Identity:** `body`, `term`, `number`, `starts_at`, `location`, `remote_url`.
- **Status:** `status` (scheduled / agenda posted / held / minutes posted / cancelled).
- **Files and records:** `agenda_file` (Box URL or upload), `minutes_file`, `recording_url`, `quorum_present`.
- **Agenda items:** inline `AgendaItem` rows with:
  - `section`, pre-filled from the body's template. The Senate template has 9 sections and the EBoard template has 6.
  - `title`, `item_type` (report / proposal / special order / motion / resolution / appointment).
  - `sponsor`, `document_url`.
  - `outcome` and `tally` (for example 15-2-1).
- **Generation:** meetings are auto-created from the body's recurrence rule (reusing the EventPage recurrence code), so the secretary never creates one, only fills it in.
- **The two-minute "Post agenda" view:**
  1. Pick the meeting. The next one is already selected.
  2. Paste the Box link.
  3. Optionally tick which items are decisions.
  4. Publish.

**B. Decision** (the tracker record)
- **Fields:** `term`, `body`, `number`, `title`, `summary` (required, 280 characters max, plain language), `type`, `sponsor` (Role or Person).
- **Stage:** `stage`, with plain labels: Introduced → In committee → Voted → Response → Implemented / Closed.
- **History:** `events` are derived from the AgendaItems that reference the decision, so its history writes itself from meetings.
- **"You said, we did" fields:** `origin` (petition, survey or student request), `implemented_on`, `outcome_note`.
- **Numbering:** the numbering scheme is left open until the bylaws are checked.

**C. Term, Seat and Assignment**
- **Term:** `body`, `name`, `starts_on`, `ends_on`.
- **Seat:** today's `Role`, with `positions` and `constituency`.
- **Assignment:** `person`, `seat`, `term`, `start`, `end`, `confirmed_on`.
- **Rollover:** `rollover_term` copies the seats into a new term and leaves them empty. Unfilled seats then show as **Vacant**, not as last year's names.
- **Person pages:** generated from assignments, each with a "Served on" history.

**D. Process** (a start page, in the GOV.UK pattern)
- **Fields:**
  - `verb_title` ("Request travel funding"), `who_its_for`, `owner_role`.
  - `steps` (process list), `what_you_need`, `deadline_rule`.
  - `action` (form, email or external link), `featured`, `review_by`.
- **Form engine:** where there's a form, it reuses the ComplaintFormPage engine.

**E. Notice**
- **Fields:** `text`, `link`, `starts`, `expires`. The expiry date is required and capped at 14 days.
- **Uses:** feeds the alert slot and the "This week" strip.

**The Desk** (admin homepage panels, private)
- A "Your jobs" list driven by the operator's role, with items like:
  - "Senate #13 is in 3 days; agenda not posted."
  - "Minutes for #12 are 9 days overdue."
  - "6 Processes past review date."
  - "FY27 ends Jun 30; rollover not scheduled."
- This is the console the concept is named after.

## 6. Maintenance story

| Who | What | When |
|---|---|---|
| Senate and EBoard secretaries | Post agenda link; mark decisions; add minutes link and outcomes | Each meeting (~2 min before, ~5 min after) |
| Committee chairs | Confirm meeting time and room | Once per term |
| Grand Marshal / President's office (or delegate) | Assignment changes, appointments, vacancies | When they happen |
| EBoard Treasurer / VP Board Operations | Update budget snapshot | Monthly or per agenda |
| Web Technologies Group chair (Primary Administrator) | Rollover, review queue, access audit, Process review | Each term, plus a monthly 15-minute review |

**Graceful decay ladder.** The site gets thinner when it's neglected, but it never says anything false.

- A meeting starts without an agenda: it keeps showing "Agenda not posted", and that stays in the public record.
- Minutes are more than 14 days late: the meeting shows a "Minutes pending" badge, and the Desk escalates to the body lead.
- A Decision hasn't changed in 60 days: it shows "Status last confirmed [date]".
- A Process passes its review-by date: it gets a yellow "May be out of date, last confirmed by [role] on [date]" banner. At twice the interval it leaves the homepage task row but stays reachable.
- A term ends with no rollover: the roster shows "Served in the 57th Senate", and current seats show Vacant.
- Notices always expire.

**Worst case: nobody touches the site for a year.** It shows the bodies, empty seats, processes with warnings, and a complete archive up to the last update. That beats today, where the site links to two 404 pages, shows eight-month-old events, and redirects the Records page off-site.

**Handoff:** the Desk doubles as the job description. A new secretary is told "clear your Desk list", not handed a wiki.

## 7. Mapping to the existing codebase

- **Keep:**
  - The Role, MemberProfile and MemberRoleAssignment trio, with `term`, `start`, `end` and `confirmed_on` added to assignments.
  - `Role.positions` and `Role.constituency`.
  - EventPage recurrence logic, which moves into Meeting generation.
  - The events JSON API.
  - `SiteSettings`.
  - `BoxFileCache` and `sync_box_records`. Box files are matched to meetings by the `YYYY-MM-DD-Title` naming standard.
  - The ComplaintFormPage engine.
  - OIDC SSO, with group mapping per role (Secretary, Chair, Admin). This is what the operator login is built on.
  - The `import_*` commands, once the CSV columns are fixed.
- **Repurpose:**
  - `BranchPage` becomes a generated Body page with only a description and contact info as editorial fields.
  - `MemberListingPage` and its hard-coded tier configs give way to the Term roster view.
  - `CommitteePage` gets a generated roster and meetings.
  - `EventIndexPage` becomes Meetings plus non-meeting events.
  - `HomePage` keeps its hero image and drops its StreamField body.
- **Add:**
  - Models: `Term`, `Meeting`, `AgendaItem`, `Decision`, `Process` (page), `Notice` (snippet).
  - A `Freshness` mixin with `owner_role`, `reviewed_on` and `review_interval`.
  - Desk panels through the `construct_homepage_panels` hook.
  - A custom "Post agenda" admin view.
  - Management commands: `rollover_term`, `generate_meetings`, `stale_report`.
  - A `RoutablePageMixin` index for records.
- **Drop:**
  - `RecordPage` and `RecordDocument`, superseded by Meeting attachments and the Box cache.
  - `BlogPage`.
  - `HomePageQuickLink`, replaced by `Process.featured`.
  - The leftover AltHomePage row.
  - The hard-coded `/complaint-form/` and `/get-involved/` links.

## 8. Weaknesses, and what I'd steal

- **Structured entry is friction.** "Paste a link and tick decisions" is more work than "drop a PDF in Box". If the Post agenda view is even slightly clumsy, secretaries will skip it and the whole thesis fails. AgendaItems must stay optional, so the agenda PDF on its own is a valid publish.
- **More custom code for a volunteer team.** The Desk, the custom admin views and the generators are code that a future Web Technologies Group has to understand. That cuts against sustainability. It needs tests (events and records have none today) and a short architecture doc, or the console becomes the next thing to decay.
- **The model is guessed without the constitution.** Decision stages, numbering, who appoints whom, and agenda posting deadlines may all be wrong. A wrong schema is expensive to migrate.
- **It can feel like a database.** Tables of meetings and chips are honest but cold. Students mostly come for money and help, not governance.
- **Data quality depends on the minutes.** Tallies and outcomes only exist if the secretaries record them. "Unknown" has to be an explicit, visible value, never a blank cell, which is UT's mistake.
- **No student login.** "Track my request" and petitions are out of scope for now.

**What I'd steal from the other angles:**
- From task-first: the GOV.UK-style plain-language homepage verbs and an explainer for each body. Get help should get the most care.
- From transparency: a proper "Where your fee goes" table with a CSV download, which goes beyond four contingency lines.
- From representation: richer person cards with office hours and one preferred contact method, so "Who represents me" feels human.

The console should be the engine underneath the site, not its personality.