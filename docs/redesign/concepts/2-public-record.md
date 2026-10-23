# Concept 2: The Public Record (transparency & legislation)

# The Public Record: a concept proposal

## 1. Thesis

**Purpose:** sg.rpi.edu is the official, searchable record of what the Rensselaer Union decides, who made each decision, and what the Union spends. Every other page on the site is built from that record.

A student government's real product is its decisions. Today the Senate's page says the Senate meets on Mondays, but it lists no agendas, minutes or legislation. `/the-record/` sends people off the site to a Box folder. A student can't find out what passed, and a new officer can't find out what last year's Senate already tried. This concept makes the decision record the core of the site.

**Principles**

1. **One record per thing, and every list is generated from records.** Motions, meetings, people, budget lines and terms are each a single record. The homepage, the trackers, body pages and profiles are queries over those records. Nobody edits the same fact in two places, so it can't drift. Cornell's meeting table missing resolutions is the failure this prevents.
2. **No status is ever blank.** Every empty state says what it means: "Not yet voted", "Minutes not posted (meeting was 18 days ago)", "Budget as of Aug 25, 2026". UT's empty Passed/Signed cells are the failure this prevents.
3. **Plain-language stages, not procedure.** The tracker says "Senate voted: passed 15–2–1", not "motion carried on division". Each body gets one sentence explaining what it does.
4. **Everything links both ways.** A motion links to the meetings where it was discussed, a meeting links to its motions, and a person links to what they sponsored. Each record links to its source document in Box, which stays the source of truth for files.
5. **Every record is dated and owned.** Each record shows when it was entered, who keeps it up to date, and which document it came from.

## 2. Primary users and top tasks

I could not read the constitution (the read was blocked), so these tasks rest on the two agendas and the Digital Infrastructure Plan. The bodies, quorums, agenda order and budget lines below are real. Bill numbering, the formal stages and the signing authority still need to be checked against the constitution and the RUGP.

| # | Task | Persona | Evidence |
|---|---|---|---|
| 1 | "What did the Union decide about X?" Search decisions by keyword, body, term or status | Student, press | No legislation exists anywhere on the site today |
| 2 | "When is the next meeting, what's on the agenda, and can I speak?" | Student | Both agendas have a standing *Invitation to Speak* item and *Press & Visitor Q/A* |
| 3 | "Where is my club's contingency or ballroom request?" | Club leader | The E-Board agenda has *Proposals* such as Special Ballroom Requests, and funds Club and Travel Contingencies |
| 4 | "How much money is left, and where did it go?" | Student, club leader | The E-Board agenda already prints Club Contingencies $100,000, Travel $60,000, Facilities $166,150 and Reserves $126,635.47 |
| 5 | "Who represents me, and what have they done?" | Student | 19 voting senators, organized by class, Graduate and Greek/Independent seats |
| 6 | Publish the agenda before a meeting and the outcomes after minutes are approved | Secretary, Parliamentarian | The agendas follow a fixed order, which can be entered as structured data |
| 7 | "Has this been tried before?" | Incoming officer | 57th Senate and FY27 numbering, plus high turnover |
| 8 | Prove the Union keeps its records | WTG chair, Union Annual Report committee | The plan lists permanent, historical, procedural and meeting record tiers |

## 3. Information architecture

**Top-level nav (6 items):** Decisions · Meetings · Money · People · Documents · Have your say

```
Decisions        /decisions/
  ├─ All decisions (search + filters: body, term, type, status)
  ├─ In progress / Passed / Implemented ("You said, we did" = Implemented filter)
  └─ How a decision is made (process list, plain language)
Meetings         /meetings/
  ├─ Upcoming (generated)
  ├─ Past meetings by body and term
  └─ How to speak at a meeting
Money            /money/
  ├─ Budget right now (budget lines, as-of date)
  ├─ Allocations (each one linked to the decision that approved it)
  └─ How to request funding (process list → E-Board proposal)
People           /people/
  ├─ Who represents me (choose class year / Grad / Greek / Independent)
  ├─ Bodies: Student Senate, Executive Board, Undergraduate Council
  │    (→ class councils), Graduate Council, Judicial Board
  │    each body → its committees, roster, meetings and decisions
  └─ Past terms (57th Senate, 56th …; FY27, FY26 …)
Documents        /documents/
  ├─ Governing documents (Constitution, RUGP, bylaws, policies with version history)
  └─ Archive (indexed Box files, searchable)
Have your say    /have-your-say/
  ├─ Speak at a meeting · Contact your representative · Report an issue
```

The five branches are **bodies under People**, and they are not top-level nav items. Each body page is a dashboard of its own records: one plain sentence, the next meeting, recent decisions, the roster and its committees. Committees sit under their parent body (Senate: AAC, CRC, FSC, RLDC, RAC, SLC, SCEC, WTG, UAR, Elections Commission; E-Board: Business Ops, Club Ops, Marketing & Strategy, MLC, UPAC, UAR). Class councils sit under the Undergraduate Council.

## 4. Homepage (mobile-first)

**Above the fold on a phone (about 640px):**
1. **Site alert slot**, shown only when set (for example "Election week" or "Meeting cancelled").
2. **Search:** "Search decisions, meetings, people…". This is the Weather.gov idea of a single entry point.
3. **Next meeting card:** "Student Senate, Meeting #13 · Mon Nov 2, 8:00 PM · RU 3202 + Webex". It has three links: *Agenda*, *Speak at this meeting*, *Add to calendar*. If both bodies meet this week, the cards stack.

**Below the fold:**
4. **Latest decisions:** five rows, each with a status chip, an identifier, a plain-language summary and a date. Example: `PASSED · S57-014 · Extends library hours during finals · Oct 19`. Then a "See all decisions" link.
5. **Money right now:** the four budget lines as horizontal bars showing amount remaining, with "As of Aug 25, 2026 · source: E-Board Agenda 01", a link to Allocations, and a *Request funding* button.
6. **You said, we did:** the three most recently implemented items, each linking the original request, the decision and the outcome.
7. **Your Union in one sentence each:** the five bodies, each with a link.
8. **Footer:** "Part of the Rensselaer Union" identifier, 110 8th Street, contact, Discord, the *Report a problem with this page* link, and "Records maintained by the Web Technologies Group, last reviewed …".

There is no hero image and no carousel. All content is server-rendered HTML.

## 5. Signature page types

**A. Decision (Motion)**, a Wagtail Page, so it gets URLs, revisions and search indexing:
- `identifier` (for example S57-014; the format is still to be confirmed against the bylaws)
- `title` and `plain_summary` (one sentence, required)
- `body` (Senate, E-Board, UC, GC, J-Board), `session` (FK to Term), `item_type` (Motion, Resolution, Proposal, Appointment, Special Order)
- `sponsors` (MemberProfile, many-to-many), `requesting_org` (text), `amount_requested` and `amount_approved` (for funding)
- `stage` (Submitted, In committee, On agenda, Voted, Response, Implemented, Withdrawn)
- `outcome` (Passed, Failed, Tabled, Pending)
- **Actions** (inline Orderable): date, meeting FK, action text, `yes`/`no`/`abstain`, optional roll-call
- `source_documents` (Box URLs), `related` (self, many-to-many)
- `implementation_note`, `implemented_on`
- The tracker bar, the "Latest action" line and the "You said, we did" entries are all generated from these fields.

**B. Meeting**, a Page:
- `body`, `term`, `meeting_number`, `start` (datetime), `location`, `webex_url`
- `quorum_required` and `voting_seats` (snapshot at the time, for example 13 of 19), `members_present`
- **Agenda items** (Orderable): the section is a fixed enum that mirrors the real order (Bookkeeping, Invitation to Speak, Reports, Special Orders, Old Business, New Business…), plus a title and an optional Decision FK
- `agenda_box_url`, `minutes_box_url`, `minutes_status` (Not yet posted, Draft, Approved), `recording_url`
- The past-meeting badge "Minutes overdue" is computed from these fields.

**C. Budget line and Allocation**, both snippets:
- BudgetLine: `fiscal_year`, `account` (Club Contingencies…), `plain_description`, `initial`, `current`, `as_of`, `source_document`
- Allocation: `budget_line`, `recipient_org`, `amount`, `date`, `decision` FK
- The Money page is a sorted table with CSS bars and a CSV download, and every allocation traces back to the vote that approved it.

**D. Term (Session)**, a snippet:
- `body`, `label` (57th Senate / FY27), `start`, `end`, `roster_snapshot` (frozen JSON taken at rollover)
- This is how institutional memory works: old terms stay browsable, and each decision belongs to exactly one term.

**E. Person record**, a routed view on MemberProfile:
- roles with term dates, constituency, contact, office hours
- sponsored decisions and attendance
- a "last confirmed" date

## 6. Maintenance story

| Who | What | When |
|---|---|---|
| Body Secretary | Create the Meeting, attach the agenda Box link, add agenda items, linking or creating Decisions (only identifier, title and summary are required) | When the agenda goes out |
| Secretary / Parliamentarian | Record tallies and outcomes, set `minutes_status` to Approved | After minutes are approved |
| Treasurer / VP Business Ops | Update the four BudgetLine `current` values, which are the same numbers already printed on every E-Board agenda | Each E-Board meeting |
| Sponsor or committee chair | Set Implemented and write a one-line outcome | When the outcome happens |
| WTG chair (Primary Admin) | Term rollover: snapshot rosters, open a new Term, run an audit of overdue records | Each term (FY start, and when a new Senate is seated) |

**Graceful decay.** Every gap is shown openly, and nothing silently goes wrong:
- If nobody enters motions, meeting pages still show the Box agenda and minutes links. The site falls back to a dated document index, which is still better than a bare Box folder.
- An overdue badge such as "Minutes not posted, 21 days" creates gentle public pressure without anyone policing it.
- The budget always shows its as-of date, so a stale figure is visibly stale rather than wrong.
- A Wagtail admin panel lists overdue records.
- *Stretch goal:* a "paste agenda" admin form. The agenda order is fixed, so pasted text could be parsed into agenda items.

## 7. Mapping to the existing codebase

- **Keep:**
  - `MemberProfile`, `Role` and `MemberRoleAssignment` (add `term_start`/`term_end` so history is kept)
  - `Role.constituency`, which powers "Who represents me"
  - `EventPage` recurrence (non-meeting events, plus the "next meeting" calculation)
  - `BoxFileCache` and `sync_box_records`, as the Documents archive index
  - `SiteSettings`, `stugov/blocks.py` and the OIDC admin login
  - `ComplaintFormPage`, as the engine for "Speak at a meeting" and "Report an issue"
- **Repurpose:**
  - `RecordIndexPage` becomes the Documents index, with the Box redirect removed.
  - `RecordPage` becomes the governing-document page (Constitution, RUGP, bylaws) with a version history.
  - `BranchPage` becomes the body dashboard.
  - `CommitteePage` gains a list of the decisions it handled.
  - The search template gets faceted results by type.
- **Add:**
  - `Term`
  - `MeetingPage` with an `AgendaItem` Orderable
  - `DecisionPage` with a `DecisionAction` Orderable
  - `BudgetLine` and `Allocation` snippets
  - a routed person view
  - `DecisionIndexPage` and `MeetingIndexPage` with filters
  - a loader that fixes the mismatch between `members.csv`/`roles.csv` and the importers
- **Drop:** `BlogPage`/`BlogIndexPage`, the leftover Alt Home row, `HomePageQuickLink` (replaced by generated content), `RecordDocument`, and the hard-coded `/get-involved/` and `/complaint-form/` links.

## 8. Weaknesses, and what I'd take from the other angles

- **Most students don't come for accountability.** MIT's site shows that students come for money and events. A record-first homepage could feel like C-SPAN. I'd take the **task-first strip** ("Request funding · Contact your senator · Speak at a meeting · Report an issue") from the services angle and put it right under search.
- **An empty tracker looks worse than none at all.** UT and Houston show this. On launch day there are zero decisions. Mitigation: backfill the 57th Senate and FY27 from existing minutes before launch, and hide the tracker sections until there are at least 10 records.
- **Data entry is the main risk.** This concept asks Secretaries to type what is already in Word documents. If the required fields grow beyond the minimum, the site will decay. Tallies depend on careful minute-taking, which I haven't been able to check.
- **The constitution hasn't been read.** The stage names, bill numbering, who signs, veto or response powers, and J-Board rulings are all guesses until someone reads it.
- **Political sensitivity.** Public roll-call votes and attendance could create tension inside the Senate. They should be opt-in by body, and that needs a Senate rules decision.
- **Representation feels thin here.** I'd take the representation angle's **constituency lookup and rich profiles** (photo, office hours, preferred contact).
- **Sustainability needs more than graceful decay.** From the sustainability angle I'd take the **last-reviewed stamp, the handoff page and the rollover checklist** as first-class features.
- **This concept is a database, not an explainer.** I'd also take the **plain-language explainers** and a "This week" strip from the GOV.UK and Boston-style concepts.