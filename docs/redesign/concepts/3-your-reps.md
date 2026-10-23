# Concept 3: Your Representatives (representation & feedback loop)

# Concept: "Your Representatives"

## 1. Thesis

**Purpose:** The site connects each RPI student to the specific people who represent them, and shows publicly what happened after students spoke up.

Today the site is organized like the org chart: E-Board, Senate, councils. A student has to understand the Union before they can use it. This concept organizes the site around the student instead. You say who you are, and the site shows your senators, your class representative, the chairs who handle your issue, and a record of what those people have done with student input.

**Principles**

1. **Start from the constituent.** Every page should answer "what does this mean for me?" The first question on the site is "Who are you?", not "Which branch?"
2. **Accountability belongs to the seat.** Issues and promises attach to a Role (for example, "Class of 2028 Senator" or "RLDC Chair"), not to a person. When officers turn over, the open items pass to whoever holds the seat next.
3. **Close the loop in public.** Every piece of student input that the government takes on gets a public entry, a status, and a dated outcome, including "we couldn't, and here's why."
4. **Personal, with no login.** Your choice is stored in the URL and in local storage, nothing more. `/your-reps/2028/` is a page you can share and bookmark, and it works with JavaScript turned off.
5. **Be honest about gaps.** Vacant seats, out-of-date profiles, and issues with no recent update are labeled as such. The site never shows a blank where an answer should be.

**Caveat:** I could not read the constitution. The constituency and seat facts below come from the Jul 30 Senate and Aug 25 Executive Board agendas, not from the governing text. They need to be checked against it.

## 2. Primary users and top tasks

| # | Task | Persona | Grounding |
|---|------|---------|-----------|
| 1 | **Find who represents me and contact them** | Student | The Senate's voting seats are split by constituency: Graduate (7), Classes of '27, '28, '29 (4 each), and Greek & Independent (7). The Executive Board has Class Representatives for Graduate and '27 to '30, plus 8 club and 5 at-large seats. Most students can't name any of these people. |
| 2 | **Raise an issue with my reps** | Student | Today the only public hook is the "Invitation to Speak" item on both agendas, which requires showing up at 8pm. The complaint form returns a 404. |
| 3 | **See what happened to things students raised** ("You said, we did") | Student, and gov members as their accountability record | No peer site I checked does this. UT Austin's "Implemented" column comes closest. |
| 4 | **Find the right person by topic** ("Dining is bad. Who do I tell?") | Student | The Senate committees map neatly onto complaints: RLDC (dining and housing), FSC (facilities), AAC (academics), SLC (student life), CRC (Troy community). Clubs go to the Executive Board's VP Club Relations and club representatives. |
| 5 | **Show up and speak** (next meeting, location, how Invitation to Speak works) | Student | Senate and Executive Board meeting times, with Webex or RU 3202 as the location. |
| 6 | **Keep my profile and office hours current; log progress on issues I own** | Gov member | — |
| 7 | **Roll the roster over after elections** | WTG chair / Primary Administrator | Required by the Digital Infrastructure Plan's admin role. |

Funding requests and the legislation tracker matter, but they are secondary in this concept. They show up as destinations reached through people and issues (see section 8).

## 3. Information architecture

**Top nav (5 items plus search):** Your reps · Raise an issue · You said, we did · Meetings · How the Union works · [Search]

```
Your reps
├─ Choose who you are       (/your-reps/)
├─ Class of 2027 … 2030      (/your-reps/2028/)  generated
├─ Graduate students         (/your-reps/graduate/)
├─ Greek-affiliated / Independent (/your-reps/fsl/, /your-reps/independent/)
├─ Clubs & organizations     (/your-reps/clubs/)   EBoard club reps, VP Club Relations
└─ Everyone                  (/people/)  A–Z directory → /people/<slug>/ profiles

Raise an issue
├─ Tell your reps (form, routed by constituency + topic)
└─ Who handles what (topic router: dining, housing, facilities, academics, clubs, safety…)

You said, we did
├─ All issues (filter: status, topic, constituency, term)
└─ Issue detail (/issues/<id>/)

Meetings
├─ Upcoming (Senate, Executive Board, committees, office hours)
├─ How to speak at a meeting
└─ Agendas & minutes (Box-backed list)

How the Union works
├─ Student Senate   → roster, committees (AAC, CRC, FSC, RLDC, RAC, SLC, SCEC, WTG, UAR, Elections)
├─ Executive Board  → roster, committees (UPAC, MLC, Club Ops, Business Ops…)
├─ Undergraduate Council → class councils
├─ Graduate Council
├─ Judicial Board
├─ Governing documents (Constitution, RUGP, bylaws; Box)
└─ Glossary & "how a decision gets made"
```

The five branches, the class councils and the committees all still exist. They sit one level down under "How the Union works," for students who want to understand the structure. Their rosters are generated from the same role assignments that drive "Your reps."

## 4. Homepage (mobile first, 375px wide)

**Above the fold on a phone:**
1. **One-line purpose:** "Your student government: who represents you, and what they're doing about it."
2. **"I'm a…" chooser:** large tap targets for '27, '28, '29, '30 and Grad, plus an optional second row for Greek-affiliated or Independent. Choosing one shows that constituency's rep cards on the page. The progressive-enhancement fallback is a plain link to `/your-reps/<key>/`. A returning visitor goes straight to their cards, with a "Not you? Change" link.
3. **This-week line:** "Senate meets Mon 8:00 PM · RU 3202 / Webex · Anyone can speak →"

**Below the fold:**
4. **Your rep cards** (after a choice): photo, name, seat, office hours, one contact button. Vacant seats appear as "Seat open: here's how it gets filled."
5. **Raise an issue:** a single CTA with three topic shortcuts.
6. **You said, we did:** the three most recently updated issues, each with its status chip and a one-line outcome.
7. **Who handles what:** six topic links (Dining → RLDC, Buildings → FSC, and so on).
8. **Footer:** "Part of the Rensselaer Union" identifier, contact details, Discord, a page-reviewed date and its owner.

## 5. Signature page types

**A. Constituency page (`YourRepsPage`, routable, generated)**
- `constituency_key` (route parameter: a year, `graduate`, `fsl`, `independent`, `clubs`)
- `intro` (one plain sentence per constituency, stored in a small snippet)
- Generated sections:
  - Senate seats for this constituency
  - Executive Board representative
  - Class council officers
  - "Also represents you": Grand Marshal, President, the 5 at-large members
  - Vacancies, with how each is filled
- `not_yet_elected_note`: shown for '30 if first-year seats aren't filled yet. The Jul 30 agenda lists Senate seats for '27 to '29 only.
- Open issues tagged to this constituency

**B. Representative profile (`MemberProfile` gains a URL through a view)**
- `slug`, `preferred_name`, `pronouns`, `photo`, `class_year`
- Roles: drawn from `MemberRoleAssignment`, showing seat, body and term end
- `office_hours` (structured: day, start, end, location or Webex)
- `preferred_contact` (choice: email, Discord, office hours) and `public_email` (opt-in)
- `working_on`: generated from the issues the person's roles own
- `last_confirmed` (date)
- `statement` (≤280 characters, optional)

**C. Issue (snippet: `Issue` plus an `IssueUpdate` orderable)**
- `title` (written in the student's words, e.g. "Commons closes too early on weekends")
- `source` (survey, Raise-an-issue form, Invitation to Speak, email, Discord), `date_raised`
- `topics`, `constituencies` (many-to-many)
- `owner_role` (FK to **Role**, not to a person)
- `status`: Heard → Owner assigned → Working on it → Brought to Senate/EBoard → Decided → Done, or Not possible (reason required)
- `updates[]`: date, text, and optional links to a meeting, agenda item, motion or Box document
- `outcome` (plain-language summary)
- `last_updated` (auto); `public` (bool, set by moderation)

**D. Topic router (snippet: `Topic`)**
- `name`, `plain_question` ("Problem with dining or housing?")
- `responsible_roles` (Roles or committee pages)
- `outside_sg` (e.g. "RPI Dining runs the meal plan; RLDC advocates to them"), `external_link`

## 6. Maintenance story

| Who | What | How often |
|-----|------|-----------|
| Each rep | Confirms their profile and office hours with one click from the admin | Each semester. After 120 days the profile shows "may be out of date," and the contact button falls back to the body's shared email. |
| Role owner (whoever holds the seat) | Posts an `IssueUpdate` on the issues they own | Prompted after each meeting. An issue with no update for 60 days shows "No update since Sep 3." |
| SCEC (Senate Communications & Engagement) | Triages the Raise-an-issue inbox, publishes issues, assigns `owner_role`, writes the outcomes | Weekly. This is the committee's existing job description, made visible. |
| WTG chair / Primary Administrator | Imports post-election assignments from CSV, ends old assignments, checks vacancies | Twice a year, from a written rollover checklist |

**How the site decays gracefully:** Constituency pages are built from Role records, so they keep working even if nobody touches the site for a year. In that worst case a page shows each seat's name, "Vacant" or "Profile not confirmed," and the body's shared email. Issues stay attached to Roles, so a new senator inherits the queue and nothing is lost. What is out of date is visibly labeled, never silently wrong.

## 7. Mapping to the existing codebase

**Keep as is:** `SiteSettings`, `stugov/blocks.py`, `EventPage` (including recurrence and the JSON API), `BoxFileCache` and `sync_box_records`, OIDC SSO for the admin.

**Keep and extend:**
- `Role`: add `body` (senate, eboard, uc, gc, jboard), `shared_email`, `committee` (FK, optional) and `topics`.
  - `constituency` is single-valued and computed from the current year. It needs explicit values: `fsl`, `independent`, `graduate`, `clubs`, `at_large`. `associated` maps to `fsl`.
- `MemberProfile`: add `slug`, `pronouns`, `office_hours`, `preferred_contact`, `public_email`, `last_confirmed` and `statement`.
- `MemberRoleAssignment`: add `term_start` and `term_end`, so rollover ends assignments instead of deleting them.
- Importers: rewrite `import_roles` and `import_assignments` to read the real `roles.csv` (`constituency_class`, `constituency_fsl`) and `members.csv` (semicolon-separated `roles`).

**Repurpose:**
- `ComplaintFormPage` becomes `RaiseIssuePage`. Add constituency and topic fields, and route the notification email to the matching roles' `shared_email`.
- `MemberListingPage`, `CommitteePage`, `ClassCouncilPage` and `BranchPage` stay as the "How the Union works" pages.
- The `HomePage` body gets the chooser and the rep, issue and topic blocks.

**Add:** the `YourRepsPage` (RoutablePageMixin), a `/people/<slug>/` view, the `Issue` and `IssueUpdate` snippets, the `Topic` snippet, and a `/lab/your-reps/` prototype seeded from the real CSVs.

**Drop:** `RecordPage` and `RecordDocument`, `BlogPage`, the `Alt Home` row, the empty `HomePageQuickLink` rows, the hard-coded `/complaint-form/` and `/get-involved/` links, and the `/the-record/` redirect. Replace the redirect with a Box-backed list.

## 8. Weaknesses, and what I'd steal from the other angles

**Weaknesses:**
- **Most students don't care who their senator is.** They care whether dining gets better. If "Your reps" leads without a strong issues board behind it, it's a vanity directory. This whole concept depends on SCEC actually running the loop.
- **An empty or performative "You said, we did" is worse than none.** Five issues, all marked "Working on it," reads as spin. It needs a minimum: launch with real survey-derived issues and honest "Not possible" outcomes.
- **Constituency is messy.** A student can be both '28 and Greek-affiliated. Co-terms, 5th-years and transfers don't fit neatly. The 7 "Greek & Independent" seats may be elected differently from what I've assumed. **None of this is checked against the constitution.**
- **Without a login there's no "my submissions."** The best I can offer is an emailed reference number, with an issue you can look up only once it's published. Moderation also adds friction and opens the site to accusations of censorship.
- **Privacy.** Reps must opt in to public photos and emails. Some won't, which weakens the cards.
- **Neglected tasks.** Funding, which MIT's prominence suggests is the top reason students visit, is only a destination here. So are the legislation tracker and budgets.

**What I'd steal from the other angles:**
- From **task-first:** a "Most requested" strip on the homepage, with Request funding and Book a space (Executive Board ballroom requests) next to the chooser. GOV.UK-style start pages for funding.
- From **transparency:** the Cornell-style meeting page and a motion/resolution tracker, so that an `IssueUpdate` links to a real agenda item and vote. The Executive Board budget snapshot as a widget.
- From **sustainability:** a "last reviewed + owner" stamp on every page, the written rollover checklist, and a small documented pattern library. I'd also hard-limit the number of page types.
- From **all of them:** plain-language explainers, so the "Your reps" cards can say in one sentence what a Class Representative actually does.