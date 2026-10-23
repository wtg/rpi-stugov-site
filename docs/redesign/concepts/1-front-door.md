# Concept 1: The Front Door (task-first services)

# The Front Door: a task-first Rensselaer Union site

## 1. Thesis

**Purpose:** The site is the one place an RPI student goes to get something done with their student government: get money, get heard, get represented, or get a seat at the table. The org chart is reference material behind that.

**Principles**

1. **Start from the verb.** Every top-level entry point is something a student wants to do. "Student Senate" is not an entry point; "Raise an issue with the Senate" is. Bodies show up on a page only when they are the answer to a task.
2. **One start page per service.** Each service gets a start page that names the problem it solves. It says who the service is for, what you need, how long it takes and what happens next, followed by one button. If no real process sits behind it, it doesn't get a page.
3. **Roles own pages, people don't.** Each service, guide and explainer belongs to a `Role` (for example "Vice President for Club Relations"), not to a named student. When officers change, the page stays owned.
4. **Every page admits its age.** Each page shows its last-reviewed date and its owner. When a page goes stale it says so and gives a fallback contact.
5. **Close the loop in public.** Anything a student submits gets one visible outcome, even if the outcome is "we couldn't do this, here's why."

A caveat: I could not read the constitution. The tasks below are grounded in the two agendas, the Digital Infrastructure Plan and the current models. Anything marked *(confirm)* depends on constitutional or RUGP text that I have not seen.

## 2. Primary users and top tasks

Personas: **S** = student (undergrad, grad, club leader, FSL member), **G** = government member (officer, senator, committee chair, WTG admin).

| # | Task (plain language) | Persona | Grounding |
|---|---|---|---|
| 1 | **Find the next meeting and what's on it** | S, G | Senate (57th, mtg #12, Jul 30) and EBoard (FY27 Agenda 01, Aug 25) agendas. Location varies (Webex or RU 3202). |
| 2 | **Find who represents me and contact them** | S | Senate seats by constituency: Class of 2027/28/29, Graduate, Greek and Independent. EBoard Class Reps for Graduate and 2027 to 2030. `Role.constituency` already models this. |
| 3 | **Get money for my club or a trip** | S (club leaders) | EBoard controls Club Contingencies ($100k) and Travel Contingencies ($60k). The steps, deadlines and the role that owns the process need confirming *(confirm, likely RUGP)*. |
| 4 | **Speak at a meeting** | S | "Invitation to Speak" and "Press & Visitor Q/A" are standing items on both agendas. Today they are the only public participation route, and nobody explains them. |
| 5 | **Raise an issue or report a problem** | S | The Senate committees map to topics: FSC (facilities), RLDC (housing and dining), AAC (academics), SLC (student life), CRC (Troy community). The complaint form currently returns 404. |
| 6 | **Request a space (e.g. the Ballroom)** | S (club leaders) | "Special Ballroom Request" is an EBoard proposal type. |
| 7 | **See what was decided** | S, G | Minutes, motions and resolutions. Approval of minutes is item 1 on the EBoard agenda. |
| 8 | **Run for office or join a committee** | S | There is an Elections Commission. Class of 2028 has 2 vacant Senate seats and Graduate has 4 vacant. Election dates are unknown *(confirm)*. |
| 9 | **Publish an agenda or minutes; update who holds a seat** | G | The plan names Box as the source of truth. The role/assignment snippets exist. |
| 10 | **Answer a submitted issue and record the outcome** | G | Not modelled anywhere today. This is the "you said, we did" engine. |
| 11 | **Hand the site over at turnover** | G | The plan's Admin role, access audits and successor training. |

The ranking is deliberate. Tasks 1, 2 and 5 are frequent and serve every student. Task 3 matters most to club leaders: MIT's UA, KU and the RPI EBoard's own budget block all show that money is what brings people back.

## 3. Information architecture

**Top nav (5 items plus search):**

1. **Get help**: raise an issue, report a problem, speak at a meeting
2. **Get funding and space**: club funding, travel funding, room requests, where the money goes
3. **Meetings and decisions**: upcoming meetings, agendas, minutes, what passed
4. **Your representatives**: find yours, contact, vacancies, run for office
5. **About the Union**: what each body does, governing documents, how this site works

Search sits in the header on every page, with popular searches listed under the box.

**Sitemap (two levels):**

```
Home
├─ Get help
│   ├─ Raise an issue (topic router → committee)
│   ├─ Speak at a meeting
│   ├─ Report a problem with this site
│   └─ You said, we did
├─ Get funding and space
│   ├─ Request club contingency funding   (ServicePage)
│   ├─ Request travel funding             (ServicePage)
│   ├─ Request a special room booking     (ServicePage)
│   ├─ Start or register a club           (StepByStep, confirm owner)
│   └─ Where the money goes               (budget lines)
├─ Meetings and decisions
│   ├─ Upcoming meetings                  (EventIndexPage)
│   ├─ Meeting pages                      (one per meeting)
│   └─ Decisions archive                  (searchable; Box-backed)
├─ Your representatives
│   ├─ Find your representatives          (constituency picker)
│   ├─ Open seats and how to run          (StepByStep)
│   └─ Join a committee
└─ About the Union
    ├─ Student Senate          → Senate committees (10)
    ├─ Executive Board         → EBoard committees (7)
    ├─ Undergraduate Council   → Class councils
    ├─ Graduate Council
    ├─ Judicial Board
    ├─ Governing documents     (Constitution, RUGP, bylaws, policy history)
    └─ How this site works     (handoff, design patterns, owners)
```

The five branches, class councils and committees all live under **About the Union**. Each body page leads with one plain sentence, for example "The Student Senate is the elected body that represents students to RPI's administration," followed by a "What you can do here" list linking back to services. Committees also feed the issue router. Task pages can reach bodies, but students never have to go through a body to start a task.

## 4. Homepage (mobile-first)

**Above the fold on a phone (about 375×700):**

1. **Header.** Wordmark "Rensselaer Union Student Government", a search icon and a menu button. One name everywhere, which ends the current Union / SG / Senate drift.
2. **Alert slot** (optional, one line). For example: "Senate meeting moved to Webex tonight." It comes from `SiteSettings`, expires automatically, and does not render when empty.
3. **H1 "What do you need to do?"** with a full-width search box.
4. **Six task links** as a plain stacked list, each a verb plus one line of context:
   - Raise an issue
   - Find your representatives
   - Get club or travel funding
   - Go to or speak at a meeting
   - See what was decided
   - Run for office

**Below the fold:**

5. **This week.** Up to three cards in a Boston.gov "today" style, all generated: the next Senate meeting (date, time, room or Webex, agenda link), the next EBoard meeting, and one open deadline (an election filing or funding cycle). An empty week shows "No meetings scheduled this week" with a link to the calendar, never stale cards.
6. **Who represents you.** An inline picker ("I am: Class of 2028 ▾ / Graduate / Greek / Independent") that shows two to four faces with a contact button each. The choice is remembered in localStorage.
7. **You said, we did.** The latest closed issue, showing the request, the committee and the outcome, plus a link to all of them.
8. **Recently decided.** The three most recent decisions, showing body, date, outcome and a link to the meeting.
9. **Your Union.** A Canada.ca-style block with one-line links to each body, the governing documents and the budget.
10. **Footer identifier.** "Part of the Rensselaer Union, 110 8th Street, Troy NY", the office hours and email from `SiteSettings`, the Discord and Instagram links, "Report a problem with this page", and "This site is maintained by the Web Technologies Group. Last reviewed: date."

There is no hero image, carousel or counter. The page should work without JavaScript, apart from the picker.

## 5. Signature page types

**1. `ServicePage` (the start page)** is the core of this concept.
- `verb_title` ("Request travel funding")
- `summary` (one sentence, "Use this to…")
- `who_for` (rich text, short)
- `before_you_start` (list: what you need, deadlines, how long a decision takes)
- `steps` (StreamField of numbered steps, rendered as a USWDS-style process list)
- `start_action` (one of: a Wagtail form page, an external URL, or mailto to `owner_role` email)
- `start_label`
- `other_ways` (in person, office hours)
- `owner_role` (FK `Role`)
- `related_body` (FK `BranchPage`)
- `last_reviewed`, `review_every_days` (default 120)
- `is_seasonal` with `open_from` / `open_until` (for example funding cycles and elections)

**2. `StepByStepPage`** is for journeys that cross services, such as "Run for Senate" or "Start a club". It holds an ordered StreamField of stages. Each stage has a title, a short explanation, and links to ServicePages or external systems. It also has `owner_role` and `last_reviewed`.

**3. `IssueRouterPage`** extends the existing `ComplaintFormPage` engine.
- Step 1 asks "What's it about?" with topic choices. Each topic is an `IssueTopic` snippet: label, description and FK `CommitteePage`.
- Step 2 is the form, which includes "May we publish an anonymised summary?"
- The submission emails the committee chair's role address plus a shared inbox.
- An `Outcome` snippet links the submission to its result: `summary`, `topic`, `committee`, `status` (received, being looked at, raised at meeting, resolved, not possible), `outcome_text`, optional `meeting` link, and `closed_on`. Outcomes with publish consent appear on "You said, we did."

**4. `MeetingPage`** is a front-door take on Cornell's meeting page. It is an `EventPage` subtype or extension with these fields:
- `body`, `session_label` ("57th Senate" or "FY27"), `meeting_number`
- `location` and `webex_url`
- `agenda_box_url` and `minutes_box_url`
- `how_to_speak` (inherited from a body-level default)
- `decisions` (inline Decision rows: title, type from Motion / Resolution / Appointment / Proposal, outcome, tally, document link)

It leads with "Want to speak? Here's how," because public comment is a service too.

**5. `RepresentativeFinder`** is a routable view on a page, not a new data model. It takes `?constituency=2028` and lists `MemberRoleAssignment` rows filtered by `Role.constituency`. Each row shows photo, role, email and office hours (a new `MemberProfile.office_hours` field). Vacant seats render as "Open seat: run for it" and link to the StepByStep.

## 6. Maintenance story

| What | Who (role) | Cadence | When nobody does it |
|---|---|---|---|
| Meetings and agendas | Senate Secretary, EBoard Secretary | Weekly | Past meetings drop off "This week" automatically. The homepage never shows an old meeting as upcoming. |
| Minutes and decisions | Same Secretaries | After approval | The meeting page reads "Minutes not yet posted (usually within 2 weeks)." After 30 days it adds a link to the Box folder. |
| Roster and seats | VGMIA and EBoard VP Rules (confirm) | Each election or appointment | Profiles show "Last confirmed: date". Unfilled seats show as open, which is still true and useful. |
| ServicePages | `owner_role` | Every 120 days, or each cycle | Past `last_reviewed + review_every_days`, the page shows a banner: "This may be out of date. Before relying on it, email [owner role address]." Past twice that period, it drops off the homepage task list, but its URL stays live. |
| Issue outcomes | Committee chairs | Within 3 weeks | After 21 days an open issue shows "Still being looked at" with its age. A Wagtail admin report lists overdue items for the GM and SCEC. |
| Alert | Anyone with editor access | Ad hoc | Expires automatically. |
| The site itself | WTG chair (Primary Admin) | Each turnover and an annual review | The About page "How this site works" holds the rollover checklist: reassign roles, audit Wagtail groups via OIDC mapping, re-review every ServicePage, update session labels. |

Graceful decay is designed in. Generated lists can't go stale, and hand-written pages announce their own age and route to a role address. Role addresses survive turnover in a way personal emails don't.

## 7. Mapping to the existing codebase

**Keep as is:** the `Role` / `MemberProfile` / `MemberRoleAssignment` trio, `SiteSettings`, `stugov/blocks.py`, `BoxFileCache` with `sync_box_records`, OIDC SSO, and the CSV importers (after fixing the column mismatches).

**Repurpose:**
- `HomePage`: replace `quick_links` with an orderable chooser of ServicePages, and add the generated This-week, Finder, Outcome and Decision sections.
- `ComplaintFormPage` becomes the base of `IssueRouterPage`, and is also the engine for any ServicePage whose start action is a form.
- `BranchPage`: keep it as the "About" body page, plus a "What you can do here" field.
- `CommitteePage` gains a reverse relation from `IssueTopic`.
- `EventPage` gains meeting fields, or a `MeetingPage` subclass is added.
- `RecordIndexPage`: remove the Box redirect, so it becomes the searchable Decisions archive with Box as the fallback link.

**Add:** `ServicePage`, `ServiceIndexPage` (one per top-level nav item), `StepByStepPage`, the snippets `IssueTopic`, `Outcome` and `Decision` (inline on meetings), `MemberProfile.office_hours`, `SiteSettings.alert_text` and `alert_expires`, `owner_role` and `last_reviewed` on a shared mixin, and a stale-content admin report.

**Drop:** `RecordPage`/`RecordDocument`, `BlogPage` (replaced by the alert and decisions), the `AltHome` row, the hard-coded `/complaint-form/`, `/get-involved/` and `/the-record/` links, and the hover-only nav. The replacement nav uses real links with a keyboard-operable disclosure.

## 8. Weaknesses and what I'd steal

**Candid weaknesses:**
- **Student government is mostly advocacy and deliberation, not service delivery.** GOV.UK works because government does things to you: taxes, licences. The Union has maybe six real services. Pad the list and you build fake doors that lead to an email address.
- **I can't confirm who owns the processes.** Club funding may really be run by Union staff and Club Financial Advisors, or live in the RUGP and another system. If so, the start page is just a well-written redirect. That is still useful, but less so.
- **Accountability is under-served.** A task-first site can make the Senate look like a help desk and hide whether it is doing its job. Legislation status, attendance and quorum get less weight than "Get help."
- **ServicePages need writing skill.** Plain language takes real effort ("do the hard work to make it simple"), and a new officer every year may not write well. Templates help but don't guarantee it.
- **Outcomes depend on chairs answering.** Without a culture shift, "You said, we did" turns into a "still being looked at" wall. That is honest, but it is embarrassing.

**What I'd steal:**
- **From the Transparency angle:** the full Congress-style decision tracker with stages, separating Senate action from the Grand Marshal or administration response. I'd put it under "Meetings and decisions" and give it equal weight with services.
- **From the Representation angle:** richer member profiles (committee memberships, attendance) and the constituency picker as the persistent personalisation.
- **From the Sustainability angle:** a documented pattern library of Django includes (process list, summary box, alert, identifier), plus a turnover runbook that a cron job or admin report enforces rather than leaving it to memory.
- **From everyone:** read the constitution before building any ServicePage, so that no start page promises a process that doesn't exist.