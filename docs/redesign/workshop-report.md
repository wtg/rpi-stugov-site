# Site redesign workshop: what the Rensselaer Union site should be for

*Lead designer synthesis, 21 Oct 2026. Branch: `redesign/explore`. Prototypes are served at `/lab/`.*

## 1. The problem

You said the site isn't very useful to students or to student government people, and the audit agrees.

**What a student finds today**
- The homepage is a hero banner and five branch cards.
- The navigation follows the org chart: E-Board, Senate, Councils, Events, Records. A student has to understand the Union before they can use the site.
- The two things a student is most likely to click are both broken:
  - "File a complaint" (`/complaint-form/`) returns a 404.
  - "The Record" (`/the-record/`) redirects off the site to a Box folder.
- Every event on the calendar is from February. In October the homepage says "No upcoming events."
- The dropdown menu only opens on mouse hover, so keyboard users can't reach it.
- The site has no legislation, no votes, no "who represents me", and no explanation of what any body does.

**What an officer finds today**
- No easy way to publish an agenda or minutes.
- The roster CSVs don't match the import commands.
- Every committee page is empty.
- No handoff documentation exists.
- The live state lives in a gitignored SQLite file that is behind the code.

The site fails both audiences for the same reason: its structure is the Union's internal structure, and keeping it current depends on one person remembering to.

The peer sites we checked fail the same way:
- Berkeley's tracker is labeled with the wrong year.
- UT Austin and Houston have empty 2026-27 tables.
- MIT's announcements have no dates.
- KU's legislation-tracker link returns a 404.

Stale content is the default outcome for a volunteer-run site. Preventing it has to be built into the design, not left to good intentions.

**A gap in the research.** I couldn't read the Union constitution. Reads outside the repo are blocked by `permissions.blockReadsOutsideWorkingDirectories`. Everything about bodies, seats, quorum and meeting order comes from the two agenda PDFs (Senate #12 on 30 Jul 2026, E-Board Agenda 01 on 25 Aug 2026) and the Digital Infrastructure Plan. Anything in the prototypes that depends on constitutional text is marked "Draft: confirm against constitution/RUGP". Unblocking that read is the most important next step (see section 8).

## 2. What the research found

- **The task-first pattern is well proven.** GOV.UK, Canada.ca and Boston.gov all lead with verbs ("Most requested", "Popular"), not departments.
- **Students come for money.** MIT's UA gives funding the most prominent spot on its homepage. KU's homepage cards are "Apply for funding" and "Track or file legislation."
- **Cornell does legislation transparency best among peers.** Each meeting has its own page with agenda, minutes, tallies and associated resolutions. Statuses separate what the Assembly did from how the President responded.
- **Nobody does "you said, we did."** UT Austin's "Implemented" column is the closest. That could mean RPI has an opening, or it could mean nobody can keep it running. Treat it with caution.
- **The agendas already contain structured data.**
  - Fixed meeting orders: 9 sections for the Senate, 6 for the E-Board.
  - Membership snapshots: Senate 19 voting seats with quorum 13; E-Board 12 voting with quorum 8.
  - Vacancies: 3 Graduate and 2 Class-of-2028 Senate seats; the Class of 2030 and Graduate E-Board reps.
  - A four-line contingency budget printed on every E-Board agenda.
  - The prototypes use this real data.
- **The schedule is irregular.**
  - The live site says the Senate meets "Mondays 7pm."
  - Meeting #12 was a Thursday at 8 PM on Webex.
  - The E-Board met on a Tuesday at 7 PM in RU 3202.
  - Meetings must be created by a person, not generated from a recurrence rule.
- **The existing code is worth keeping.**
  - `Role`, `MemberProfile` and `MemberRoleAssignment` (with `Role.constituency`) are the right model for "who represents me."
  - `EventPage` recurrence, `SiteSettings`, the Box cache and the `ComplaintFormPage` form engine can all be reused.

## 3. The four concepts

1. **The Front Door (task-first services).** The homepage asks "What do you need to do?" and offers six verbs. Each real process gets a GOV.UK-style start page saying who it's for, what you need, how long it takes, and one button. Bodies move under "About the Union." Every page is owned by a role and shows when it was last reviewed.
2. **The Public Record (transparency and legislation).** The site is the searchable record of decisions, meetings, money and people, and every list is generated from those records. Key features: a Congress.gov-style stage tracker, budget lines with as-of dates, allocations linked to the votes that approved them, and terms as institutional memory. Its rule is "no status is ever blank."
3. **Your Representatives (representation and feedback loop).** The front page asks "I'm a…" and shows your senators and class rep at a shareable `/your-reps/2028/` URL. It adds a "Who handles what" topic router (dining goes to RLDC, buildings to FSC) and a "You said, we did" issue board. Issues are owned by seats, not people.
4. **The Operator's Console (built for the people who run it).** It treats staleness as the main design problem.
   - **Two-minute rule:** any routine publishing task should take a secretary two minutes or less, from a phone.
   - **Meetings as records:** a meeting is a record, and an agenda PDF alone counts as a valid publish.
   - **Rollover:** at the start of a term, seats become Vacant instead of keeping last year's names.
   - **Expiring notices:** homepage notices must expire.
   - **The Desk:** an admin to-do list that doubles as the handoff document.

## 4. Judge scoreboard

Each judge read the concepts through a different lens: student usefulness, maintainability and build cost, and a skeptical feasibility review.

| Concept | Student lens | Maintainer lens | Skeptic lens | Mean |
|---|---|---|---|---|
| 1 Front Door | **8** | 5 | **6** | **6.3** |
| 2 Public Record | 6 | 4 | 4 | 4.7 |
| 3 Your Representatives | 6.5 | 6 | 5 | 5.8 |
| 4 Operator's Console | 5 | **8** | **6** | **6.3** |

### Key critiques

- **The Front Door** is the only concept where a first-year who has never heard of the Executive Board can finish a task in under a minute. All three judges flagged the same risk: **fake doors**. If club funding is really run by Union staff or Club Financial Advisors through another system, "Request club funding" becomes a polished page that ends in a guessed email address. That would lose student trust faster than today's 404. Other critiques:
  - Public "may be out of date" banners on a 120-day cycle would cover the whole site by spring.
  - Six or more page types is a lot for the next maintainer to learn.
  - "Get help" sounds like counselling.
- **The Public Record** was the best answer to "I heard the Senate passed something." But as a homepage it reads like C-SPAN.
  - It has the highest data-entry burden: Decision as a Wagtail Page, separate action logs, roll-call votes.
  - It has the most guessed schema. Neither agenda has a numbered bill.
  - It would launch with zero decisions.
  - The "Money" framing is misleading. The four lines are contingency pools, not "where your fee goes", and the plan classifies budgets as private.
- **Your Representatives** has the single most student-useful idea across all four concepts: the **topic router**. It is static data that rarely changes and needs no moderation. Its weaknesses:
  - Most students don't want to meet their senator; they want dining fixed.
  - A first-year who picks "Class of 2030" in September would see no Senate seats at all.
  - The issue board creates a new weekly moderation job with no committed owner.
- **The Operator's Console** is the right engine and should never be the visible personality. Its weaknesses:
  - Recurrence-generated meetings would publish phantom "Agenda not posted" badges for meetings that never happened.
  - The custom Desk views and management commands are bespoke code that a volunteer team would inherit untested.

### Where the judges converged

The skeptic made the sharpest observation. Concepts 2 and 4 share one data model, and Concepts 1 and 3 share one feedback engine. All four arrived at the same navigation: meetings, decisions, people and bodies, get help, documents. **The real decision is not which concept to pick. It is how much structured data secretaries will actually enter, and whether anyone will own the feedback loop.**

## 5. Recommended design philosophy: "A front door over an honest record"

1. **Lead with what students came to do.** The homepage offers four to six verbs, and each must have a real process behind it. The org chart stays fully available, one level down, under "How the Union works."
2. **Plain language, with no unexplained term.**
   - "Contingency" becomes "extra money clubs can request during the year."
   - "Invitation to Speak" becomes "Anyone can speak at the start and end of every meeting."
   - "Grand Marshal" gets a one-line explanation wherever it appears.
   - Use one name for the organisation everywhere.
3. **The meeting is the unit of record.** A meeting needs only body, term, number, date and time with the year, place, and a Box agenda link. Minutes links, agenda items and decisions are optional additions. A PDF link alone is a complete publish.
4. **Never blank, never false.**
   - Every date has a year.
   - Every empty state says what it means: "Agenda not posted yet", "Minutes not posted (meeting was 18 days ago)", "Vacant".
   - Homepage sections with nothing fresh to show collapse instead of saying "No upcoming events."
5. **Seats, not people.** Contact routes and accountability belong to roles. A new term starts with seats Vacant, never with last year's names.
6. **No door without a process.** Don't publish a start page until the constitution or RUGP confirms the process and who owns it. Until then, the funding verb points to the existing E-Board process and is clearly labeled as such.
7. **A thin engine with few page types.**
   - Show staleness to officers in the admin, not to students.
   - The exception is genuinely time-sensitive content, such as deadlines and elections.
   - Homepage notices must have an expiry date.
8. **Design for arrival from Discord.** Every meeting, decision and reps view gets a stable, readable URL, because a shared link in Discord is how most students will actually arrive.

## 6. What we'll prototype

There are three prototypes, all at `/lab/`. Each has its own base template and visual style, and each renders entirely from the real agenda data plus clearly badged sample data, even with an empty database.

1. **`front-door`: Front Door (recommended).** This is the synthesis.
   - Homepage, top to bottom: six verbs, an honest "This week" section, a reps lookup with the Class of 2030 fallback, and recently decided items.
   - "Raise an issue" is the topic router from Concept 3, including grad-specific topics.
   - "Find out what was decided" leads to a Cornell-style meeting page for Senate 57 #12, built from the real agenda.
   - Funding is a start page with a visible "process owner unconfirmed" banner and the real budget snapshot.
   - A "How the Union works" page holds the glossary and a "How this site works" handoff section.
   - Visual style: GOV.UK-like, large type, single column.
2. **`the-record`: Public Record and Desk.** This is the transparency-first alternative for repeat users: press, officers and the curious.
   - Dense meeting and decision listings in a Weather.gov / Congress.gov style.
   - A decision tracker with plain-language status words.
   - A money table with a CSV download.
   - A **mock secretary "Desk"** page with a timed "Post the next meeting" form, prefilled from the previous meeting. It saves nothing and exists to run the two-minute test with a real secretary before we build any models. This is the prototype for the "student government people" half of your complaint.
3. **`your-reps`: Your Representatives.** This is the representation-first alternative.
   - An "I'm a…" chooser on the front page.
   - Constituency pages built from the real agenda rosters, with honest Vacant cards.
   - Person pages that show every role someone holds. For example, Griffin Oliver appears as a Class of 2027 Senator, VGMIA and RAC chair.
   - The topic router, plus a sample "You said, we did" board that includes "Not possible" outcomes. The point is to show what owning that loop would involve.

The three prototypes are genuinely different information architectures: verb-first, record-first and constituency-first. Students can therefore compare them on the same tasks.

### Not built in this round

The judges agreed these should wait:
- Recurrence-generated meetings.
- Custom admin views or new models.
- Decision-as-Page.
- Roll-call votes and attendance, which need a Senate rules decision.
- A live, moderated issue tracker, which needs an owner.
- Allocation-to-decision links, which need Business Ops buy-in.
- More than one start page for an unconfirmed process.

## 7. How to evaluate the prototypes

- **Student test.** Show each prototype to three or four students on their phones, including at least one first-year, one grad student and one club treasurer. Give them these tasks:
  - "Dining closes too early on weekends: who do you tell?"
  - "Your club needs money for a trip."
  - "Did the Senate do anything about X?"
  - "Who are your senators?"

  Time each task, and note where people hesitate over wording.
- **Secretary test.** Ask the Senate or E-Board secretary to post meeting #13 on `the-record` Desk page, which has a built-in stopwatch.
  - **PDF-only path:** if it takes more than about two minutes, the structured-record idea is dead, and the site should remain a well-explained front door over Box.
  - **Agenda items:** time the structured agenda-item path separately.
- **Keyboard and screen-reader test.** Tab through each homepage, and run VoiceOver on one meeting page.

## 8. Open questions for you

1. **Constitution and RUGP.** Can you run `/add-dir /Users/aaron/Documents/areas/stugov/union-constitution`, or copy `main.tex` into the repo? We need to confirm:
   - Who owns club funding, travel funding and ballroom requests.
   - Bill and resolution numbering.
   - Whether the Grand Marshal or President formally responds to Senate legislation.
   - How the 7 "Greek & Independent" seats are split. The agenda lists only 6 names.
   - When the Class of 2030 elects senators.
2. **Name.** Should the site call itself "Rensselaer Union", "RPI Student Government" or "Student Senate"? Pick one for the site header.
3. **Schedule.** The live site says the Senate meets Mondays at 7 PM in Shelnutt Gallery, but #12 was Thursday at 8 PM on Webex. Which is current?
4. **Budget.** The Digital Infrastructure Plan classifies budgets as private, but the contingency lines are printed on public agendas. Can the site show them? Does a broader "where the activity fee goes" breakdown exist?
5. **Ownership.** Would SCEC, or anyone, commit in writing to answering routed issues within about three weeks? If not, "You said, we did" stays out of the real build.
6. **Contacts.** Do role-based shared inboxes exist, such as a Senate secretary address or an RLDC chair address? `members.csv` has no emails, and the prototypes won't invent any.
7. **Photos.** Will representatives opt in to public photos? The prototypes use initials.
8. **Testers.** Can you recruit the student testers and one secretary for the timed test?
9. **Data.** Is the production database newer than the local `db.sqlite3`? The local copy has 0 roles and 0 assignments, so the prototypes use the agenda rosters.
10. **Survey.** Does the annual Senate survey still run? Its past outcomes would be the most credible seed for "You said, we did."

## 9. Constitution update (post-workshop)

After the workshop the constitution became readable (`docs/redesign/reference/union-constitution.tex`, last amended 6 Feb 2026). It is digested in `docs/redesign/research/constitution.md`, and all three specs have been updated against it. This closes the research gap described in section 1.

**What it confirmed**
- There are five governing bodies: Senate, Executive Board, Judicial Board, Graduate Council and Undergraduate Council. Class Councils sit under the Undergraduate Council.
- The Grand Marshal chairs the Senate and the President of the Union chairs the E-Board. Both vote only to break a tie (Art. IV).
- The E-Board prepares and approves the budget, hands out Union money and classifies clubs (Art. VII §2). So the funding verb points at the right body.
- First-year senators are elected in the fall (Art. VIII §3). The Class of 2030 fallback stays.
- **The budget and records of all extra spending are public documents** (Art. VII §2). This answers open question 4 for the budget itself: the contingency lines can be shown, whatever the Digital Infrastructure Plan says.

**What it changed**
- **Senate seats.** The Senate has 29 voting seats: 7 Graduate, 4 per undergraduate class, 3 Independent and 3 Fraternity and Sorority Life. The agenda's "Greek & Independent" heading covers two separate groups of three. "Greek" is now "Fraternity and Sorority Life (FSL)" (Amendment VI). The "seventh seat unaccounted for" note was our misreading of the agenda and is gone. The roster gives 20 filled, 5 vacant and 4 to be elected this fall. The agenda header says 19 voting members; we show that with its source and don't reconcile it.
- **E-Board seats.** The E-Board has 15 to 20 voting members.
  - The Senate, Graduate Council and Undergraduate Council representatives are voting members, even though the agenda prints them as "Peer Body Representatives".
  - The constitution has no VP seats. VP titles come from the bylaws.
  - Class, club and at-large seats are appointed by the President with 2/3 Senate approval. They are not elected.
- **"Treasurer"** in the constitution means RPI's Treasurer. The agendas' officer is shown as "Senate Treasurer".
- **Labelling.** The blanket "Draft: confirm against constitution/RUGP" badge is retired. Labels now work like this:
  - A confirmed fact carries no badge, only a muted "Source: Union Constitution, Art. VII §1" line.
  - "Draft: confirm" now marks only what the constitution leaves to bylaws, Senate rules or staff, and it names who to confirm with.
  - Our own arithmetic is marked "(derived)", for example "20 of 29".
- **New content in each prototype.** Each process below comes straight from the constitution, so each passes "no door without a process".
  - front-door gained a "Run for office or start a petition" page: run, get appointed, referendum, challenge an appointment, recall, Judicial Board, amend.
  - the-record gained a "How decisions are made" page: vote thresholds, petitions, named records, transparency rules. It also gained a "Ruled unconstitutional" status.
  - your-reps gained per-seat "How this seat is filled / Answers to" lines and a "Your powers" section, with no new page.
  - All three routers gained a rights topic that goes to the Judicial Board.

**What it killed**
- Every mention of "RUGP". The constitution never mentions it.
- Invented bill numbers. References are now meeting-based, for example "E-Board FY27 #1, item 3a".
- A Cornell-style "President's response" stage on decisions. The constitution has no sign-off or veto after a Senate or E-Board vote; only the Judicial Board can overturn a decision. This answers question 1c.
- Any claim that agendas and minutes *must* be public. Publishing them is Union practice, not a constitutional duty, and the-record says so.
- Treating quorum as constitutional. No body's quorum is set there; agenda figures appear only with their source.

**Still open.** The constitution leaves these to bylaws or staff:
- How a club actually applies for money, and who handles it day to day (question 1a, partly answered).
- Quorum.
- Petition format and signature checks.
- How to file with the Judicial Board.
- Ballot access and election dates.
- How the Graduate Council's at-large members are chosen. The text contradicts itself.
- Where the official copy of the constitution is published.

## 10. Single source of truth

The owner asked whether the design has to be reconciled with a single source of truth, given Box for files and a possible move to Notion. The answer is yes, and it can be done without the Box API, which we assume we'll never have. The decision is in `docs/redesign/data-architecture.md`. In short:
- **Box owns files.**
- **One structured system owns the meeting record and roster:** Notion if officers adopt it for meetings and attendance, Wagtail if they don't. Never both.
- **Wagtail owns only explanations:** start pages, the glossary, "How the Union works", the topic router, notices.
- **The site is mostly a read-only projection,** synced one way and labelled with its source.
- **Pasting a Box shared link into the meeting record is a pointer, not double entry.** There are two per meeting (agenda and minutes), and a health page flags any that are missing or broken.

**How each prototype changed**
- **All three**
  - Every projected item carries a muted source line, such as "Meeting record: Notion · synced 12 min ago".
  - An officer toggle (`?officer=1`) reveals mock "Edit in Notion / Box" links.
  - The banner says the sync is simulated.
  - The handoff section now has a "What lives where, and who edits it" table, and Wagtail-owned pages are labelled "Written on this site".
  - Contacts go to a seat's role inbox, never a personal address.
  - Meetings never come from hand-made calendar entries.
  - No page asks an officer to type a fact that lives in Box or Notion.
- **front-door** (still 10 pages)
  - The budget is now a quotation ("as printed on E-Board Agenda 01", no bars, linked to the latest agenda in Box), not a maintained figure.
  - The meetings page gains Box folder embeds.
  - Item-by-item agendas are labelled "only if written in Notion".
  - Issue routing explains that tracked issues would live in a Notion database, shown read-only.
- **the-record** (still 9 pages)
  - **Desk.** The timed "Post the next meeting" form is gone from the Desk's default view. The Desk now lists jobs from the health checks with "Fix in Notion/Box" links. It also runs a new two-minute test of the real workflow: upload to Box, set the link, fill a clearly labelled *stand-in for a Notion row*, see it appear. The old form survives only behind `?path=wagtail`, fenced as the homegrown alternative for a body that doesn't use Notion.
  - **Outcomes.** Outcomes are never typed in: they come from minutes written in Notion, or not at all.
  - **Health page.** A new mock health page (it replaces the money CSV export) shows:
    - sync status;
    - what is currently projected;
    - minutes overdue after 14 days and agenda links missing 2 days out;
    - failed link checks;
    - vacant seats;
    - what it can't see without the Box API.
  - **Seed data.** A sample Senate #11 shows the links-present and PDF-only states.
  - **Removed.** The Recording column, the BoxFileCache read and the CSV are gone.
- **your-reps** (still 7 pages)
  - Profiles show photo, bio and office hours only with a Notion "Public profile" consent box, which nobody has ticked.
  - Officers see a "what the sync publishes" field table.
  - "Profile confirmed" becomes a synced "Profile reviewed" date.
  - `?term=next` previews term rollover, with every seat open automatically.
  - "You said, we did" is labelled as a read-only view of a Notion Issues database, Public rows only.
  - "How it works" gains a "This site" section.

**What this changes elsewhere in this report**
- The secretary test in section 7 now times the Box upload plus the Notion row, not a website form. If that takes well over two minutes, fall back to folder embeds only. That is option (a) in the decision.
- New open questions for you:
  - Will each body use Notion for meetings and attendance?
  - Can the workspace sit on a shared role account with two owners?
  - Does RPI policy allow student data in Notion?
  - Who owns the sync for a year?
  - Does the `/v/` Box archive link embed?
  - Will RPI IT allow Power Automate or a user-authorised Box app? (If yes, see the decision's "If the Box API ever appears".)
  - Question 6 (role inboxes) now matters more, since every contact route depends on it.

## 11. Per-body autonomy and Word documents

After section 10 was written, you told us three things:
- Agendas, minutes and motions are written in Word.
- Only the Senate is looking at Notion. The E-Board and the other bodies are not.
- How the E-Board, the Councils and the Judicial Board organise themselves is their own business, as long as their public records are strong.

That changes the decision in `docs/redesign/data-architecture.md`, and it partly replaces section 10. "One system owns the meeting record for the whole Union" is gone.

**What changed**
- **A Public Records Standard replaces a Union-wide tool choice.** It's a tool-agnostic floor every body meets:
  - **What:** agendas, draft and approved minutes, motion texts and bylaws. The E-Board also publishes budget and allocation records, which the Constitution makes public. The Judicial Board publishes rulings, not cases.
  - **When:** agendas 24 hours before the meeting; minutes within 14 days.
  - **Where:** one public Box folder per body per term, using the filename convention.
  - **Format:** tagged PDFs exported from Word, from a per-body template WTG provides. Not Print to PDF, not scans.
  - **Corrections:** Upload New Version, so links never break.
  - **Who answers:** a named records officer per body.
- **Each body picks how the site reads its records.** The options are:
  - **(A) Box folder only:** zero entry, weakest structure.
  - **(B) A minimal meeting entry on this site:** number, date, place and two pasted Box links.
  - **(C) Copy the Senate's Notion setup,** if a body ever wants to.
  - **The Senate** gets a Notion projection: meetings, motion status and Public issues.

  The site renders every body the same way and degrades honestly. A folder-only body's page says "This body publishes its records as files. See the folder." It doesn't show empty tables.
- **Word content stays in Word.** The site shows agendas and minutes as documents: a Box preview, which renders PDF and `.docx`, with "Open (PDF)" first on phones. It never shows a retyped or parsed list.
  - A Senate motion's *status* is a new fact the secretary records once in Notion, with a link to the motion's Word file.
  - Item-by-item agendas exist only if the Senate chooses to draft agendas in Notion and export them. The prototypes show that as a labelled option, with its trade-offs: no `.docx` export, untagged Notion PDFs, and the PDF in Box going stale if the page is edited after export.
- **The roster moves to Wagtail for every body, the Senate included.** People hold seats across bodies (Cee Ray '27, Griffin Oliver '27, Samson Kempiak '28, Stanley Goodwin '30G). A per-body split would give them two records, and their photo consent would have two owners. The Senate's Notion gets an automatic read-only copy for attendance, and the Senate can add private columns to it.
- **The health page checks every body against the Standard.** For example: "E-Board: minutes for meeting 01 not linked 57 days after (Standard: 14)". Folder-only bodies get "Can't check automatically. Records last confirmed complete: never", because without the Box API the site can't see inside their folders.
- **The prototypes** keep their page counts.
  - Senate items carry Notion source lines. E-Board items say "entered on this site". The Graduate Council, Undergraduate Council and Judicial Board show folder-only views.
  - E-Board decisions are no longer rows. They're "recorded in the minutes".
  - The ownership tables are per body. Nothing implies that a body other than the Senate uses Notion.

**What this changes elsewhere in this report**
- **Secretary test (section 7).** It now runs three ways:
  - The Senate secretary times the Word-to-tagged-PDF export, the Box upload and the Notion row.
  - The E-Board secretary times the same export and upload plus the site's meeting form.
  - A Council secretary times the export and upload alone.

  If even the export-and-upload step takes well over two minutes, fix the template and the instructions before anything else.
- **Section 10's "Notion if officers adopt it" questions** now apply to the Senate only.

**Questions this raises for you**
1. **Adopting the Standard.** The Constitution doesn't require agendas or minutes to be public, so the Standard needs adopting.
   - Who adopts it, and how? A Senate resolution, each body's bylaws, or an agreement among the five officers (who must meet regularly anyway, Art. IV)?
   - What happens when a body misses deadlines repeatedly?
2. **Deadlines.** Are 24 hours for agendas and 14 days for minutes (7 for drafts, 3 after approval) right? Should drafts be public at all, or only approved minutes?
3. **Adapter per body.** Will the E-Board want per-meeting pages (B), or a folder only (A)? We've shown it as B, labelled as an example. Do the Graduate Council, Undergraduate Council and Judicial Board even have public Box folders today?
4. **Judicial Board records.** What is public: rulings on constitutional questions only, anonymised case summaries, or nothing? Who decides, under its bylaws?
5. **Class Councils.** Do they publish separately, or through the Undergraduate Council's folder?
6. **Records officers.** Who is the records officer for each body this term? Will the bodies accept a role account owning the `Public Records` tree, with each body holding Editor rights on its own folder only?
7. **PDF and accessibility.** Is a tagged PDF required, or is a `.docx` in Box acceptable? Do secretaries mostly use Word on Windows, on Mac, or on the web? The export steps differ, and we'd write the guide for what they actually use. Can WTG own a Word template per body?
8. **Roster on this site.** Will the Senate accept the VGMIA editing seats on the website, with Notion receiving a read-only copy, instead of the Senate keeping its roster in Notion? If the Senate insists on Notion, we need a per-fact split (person facts on the site, Senate assignments in Notion), which costs more and is easier to get wrong.
9. **Member sign-in.** For members to manage their own photo and bio consent on the site, they need to sign in. Is RPI single sign-on available to the site? If not, roster officers record consent on members' behalf.
10. **Senate options.** Does the Senate want to try drafting agendas in Notion for a term? Will its secretary record motion status in a Notion Motions table at the vote, and build the minutes' motion list from it?
11. **Issues outside the Senate.** Is it acceptable that only Senate committees show "You said, we did" items, while E-Board and Council responses appear only in their minutes?
