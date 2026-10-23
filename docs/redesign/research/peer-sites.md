# Reference and peer site research

# Reference research: student-government website redesign (Rensselaer Union)

Verified 2026-10-21. "Verified" means seen on the live site through fetch or search today. "From knowledge" means I could not confirm it on the live site. Fetch failures are listed in the current-state notes below.

## A. Gold standards

### GOV.UK (verified)
- **Current state:** Live and active. The homepage has a cookie banner, a search box, and a "Popular on GOV.UK" list of tasks.
- **Borrow:**
  - Task-first topic list. "Services and information" is 16 topic cards, each with a one-line description of what it covers. This is not an org chart.
  - A "Popular" quick-links strip above the topics. Ours would be "Contact a senator," "Request funding," "Find a meeting," "Report an issue."
  - The Start page pattern. It names the service by the problem it solves. It gives cost and time up front, says what you will need, lists other ways to do it (phone, email), and has one clear start button. It keeps eligibility questions off the page.
  - "Is this page useful?" and "Report a problem" on every page. This is the cheapest feedback loop available.
- **Design principles worth quoting to future officers:**
  - "Start with user needs."
  - "Do less" (do only what only you can do).
  - "Do the hard work to make it simple."
  - "Be consistent, not uniform."
  - "Make things open."
  - The principles page does not mention plain language explicitly. It is implied by "do the hard work to make it simple."
- **Don't copy:** The scale machinery (content designers, a service-assessment regime) and the 16-topic breadth. We need 6-8 tasks. The pattern catalogue's forms for NI numbers, bank details and so on are irrelevant.

### USWDS and Digital.gov (verified, v3.14.0)
- **Components confirmed on the overview page:**
  - Banner: identifies an official site.
  - Identifier: parent-body links at the footer.
  - Step indicator: shows progress through a multi-step process.
  - Process list: the steps of a process.
  - Summary box: key points or next steps from a longer page.
  - Alert and Site alert: urgent, site-wide notices.
  - In-page navigation: jump links for long pages.
- **Borrow:**
  - Process list for "How a bill becomes a resolution" and "How funding requests work," rendered as plain numbered HTML.
  - Summary box at the top of each long document, such as a budget policy: "Here's what you need to know."
  - Site alert for one slot of urgent news (election week, meeting cancelled).
  - Identifier-style footer. It would say "Part of the Rensselaer Union," and it is where the "who maintains this / last reviewed / handoff doc" line can live permanently.
  - In-page navigation for the governing-documents pages.
- **Don't copy:** The "official .gov" banner semantics, which don't apply. Don't adopt USWDS wholesale. It is a heavy dependency, and the site already uses Tailwind. Borrow the patterns and write them as Django includes.

### Boston.gov (verified)
- **Current state:** Active.
- **Borrow:**
  - "Today's status" cards on the homepage: City Hall hours, trash, street cleaning. This is the template for a **"This week" strip**: next Senate meeting, committee meetings today, office hours open now, and open elections.
  - A Featured resources grid of verbs: pay a ticket, apply for a permit. Use it for tasks.
  - Feedback and the 311 "Report an issue" link in the header and footer, so the way to complain is always visible.
  - Councilor profiles with contact links on the homepage.
  - Popular searches and popular questions in the search box.
  - A published pattern library (Fleet, github.com/CityOfBoston/patterns). I could not confirm its license from search results, so verify before reuse. The idea to borrow is a documented pattern library as the handoff mechanism.
- **Don't copy:**
  - The AI-summary search. It adds risk and cost, and Boston itself warns it can be wrong.
  - The 10-item mega menu. That is the scale of a city.
  - Whether it is "mobile-first" was not stated on the page, so don't cite Boston for that.

### Canada.ca (verified)
- **Current state:** Active.
- **Borrow:**
  - "Most requested" as a short list of 8 high-traffic tasks, separate from the full topic list.
  - A website-outages banner slot that sits below the primary content.
  - A topic card pattern: heading link plus one sentence.
  - A "Your government" block listing contacts, news, departments, laws and open data. For us this would be a "Your Union" block with senators, committees, governing documents and records.
  - A page-details date on every page.
- **Don't copy:** The 16-theme main menu and the bilingual machinery. The fetch did not show a "Report a problem" link on the homepage. The pattern exists on inner pages from knowledge, so don't cite it from this fetch.

## B. One-thing-well

### Congress.gov (partly verified)
- **Current state:** The site returns 403 to automated fetch, so I could not read a live bill page. Search results confirm the following. Each bill page has an overview box at the top. The box shows sponsor, committees, latest action and a **"tracker"** giving a visual of the bill's progress through Congress. Chambers produce the status steps, and the Library of Congress aggregates them.
- **From knowledge, not verified today:** The tracker is a horizontal bar (Introduced, Passed House, Passed Senate, To President, Became Law). The bill page has tabs for Text, Actions, Cosponsors, Committees, and Related bills.
- **Borrow:**
  - A horizontal tracker for every piece of legislation. For us the stages would be Drafted, Committee, Senate vote, Grand Marshal response, Implemented.
  - A "Latest action: date, text" line in the overview box.
  - Tabs: Text, Actions (dated log), Sponsors, Related.
  - A data-first model. One record per bill, with every list generated from it.
- **Don't copy:** The legalese ("referred to the Committee on…"). Keep the stage labels in plain language, and show actual vote tallies where the Senate records them.

### USAspending.gov (partly verified)
- **Current state:** The fetch returned only the site name. Findings come from search (Treasury, CRS and press sources).
- **Borrow:**
  - Spending Explorer has three entry points (budget function, agency, object class). It drills down level by level through a treemap.
  - It has a graphic by default with a toggle to a list view.
  - It shows obligations, not cash spent, and says so (flagged by PBS).
- **For us:** A Where Your Student Activity Fee Goes page. It would be one stacked bar or table, a plain-text list underneath, and a one-sentence definition of each category. Offer a CSV download.
- **Don't copy:** The multi-level treemap. For a budget of about 15 lines, a sorted table with horizontal bars is clearer and accessible. Always include the list view.

### Weather.gov (verified)
- **Current state:** Active.
- **Borrow:**
  - A single location input is the whole entry point: "Local forecast by City, St or ZIP." Our version is "I am a [class year / grad / club leader / FSL]" or "Find my senator." Optional "Remember me."
  - A headline banner above everything for the one thing that matters now.
  - Plain text links, a low-bandwidth radar option, and almost no images. It is fast and degrades well.
- **Don't copy:** The very dense nav, the long alert-link lists, and the "LOADING..." JS-populated sections.

### Gov.sg (verified, with a caveat)
- **Current state:** Active; footer says last updated 19 Oct 2026.
- **Caveat:** The homepage is a policy and explainer hub (Budget, National Day Rally, Explainers). It does not surface services itself. Don't cite it as a "one front door" for services from this fetch.
- **Borrow:**
  - A scam-safety banner explaining how to verify the site. For us, a short "how to tell this is the real Union site" note is unnecessary. The useful idea is explainers: plain-language cards that answer one question each.
  - Footer with a visible last-updated date.
- **Don't copy:** Hero banners tied to campaigns. They age quickly.

## C. Peer student governments

### MIT Undergraduate Association, ua.mit.edu (verified)
- **Current state:** Mostly current. October 2026 events are listed.
- **Borrow:**
  - Funding is the most prominent content (Community & Diversity Fund, Travel Grants, Participatory Budgeting). This shows funding is what students come for.
  - Participatory Budgeting results are published with a contact email.
- **Don't copy:**
  - No upcoming meetings or legislation on the homepage.
  - Undated announcements, with no way to tell what is still open.
  - A placeholder URL (`new-page-2`) behind a live link.
  - An informal nav label, "Free Money."
  - Menus duplicated between the desktop and mobile versions.

### Stanford ASSU (not usable)
- **Current state:** The fetch returned only scaffolding: four service links (including GrantEd and ASSUePay) and an empty slideshow. It was probably rendered by JavaScript. I could not assess content currency. I am not reporting anything else about it.

### Berkeley ASUC, asuc.org (verified)
- **Current state:** Mixed.
- **Borrow:**
  - Nav includes "Our Impact," which holds the resolution tracker.
  - Contact routes by purpose (administration, press, advocacy), each with email, phone and hours.
  - Budget, agendas and financial disclosures are one click away.
- **Don't copy:**
  - The tracker is labeled 2025-2026 while the nav points to the 2026-2027 board.
  - Stale counters ("137 Years").
  - Bills, votes and schedules live in external Google Docs.
  - A link pointing to a `dev.asuc.org` host.
  - Empty links.
  - A carousel with a stale Read More target.

### Cornell Student Assembly, assembly.cornell.edu (verified)
- **Domain note:** `studentassembly.cornell.edu` does not resolve. The real site is `assembly.cornell.edu`.
- **Current state:** Active, and it is the best legislation transparency of the peers checked.
- **Borrow:**
  - A resolutions table: Term, Resolution ("SA R27" plus title), Abstract, Status. Filter by term and by status (14 statuses, from Draft and In Discussion to Adopted by the Assembly and Acknowledged by the President). Page size selector, with about 1,195 entries going back to 2006-07.
  - Separate Assembly action from President's response in the status vocabulary.
  - A meeting page per meeting, containing:
    - metadata (term, body, time, room plus Zoom)
    - a numbered agenda
    - a packet field
    - audio with file sizes
    - minutes with attendance and tallies (for example 19-1-0)
    - an Associated Resolutions table with status
  - Resolution numbers restart each term, and everything is keyed by term.
- **Don't copy:**
  - There are no resolution-to-meeting links in the resolutions listing.
  - The meeting page's table omitted resolutions that its agenda and minutes mention (75 and 80), a data-integrity miss.
  - The packet field is empty.
  - Audio only.
  - No "last updated" stamp.

### Other peers found

**University of Kansas Student Senate, studentsenate.ku.edu (verified)**
- Nav is Branches, Legislation, Funding, Get Involved, Elections.
- Homepage cards: "$24M allocated," "95 senators," "Apply for funding," "Track or file legislation."
- Submit & Track page: filing deadline per cycle (a Sunday, 5pm), two Council reviews, then Assembly final approval, with meeting dates listed per cycle. The tracker itself is a linked spreadsheet.
- It states who to email for extensions.
- `/legislation-tracker` returned 404, so link rot happens even on a good site.
- Borrow the process explanation and the numbers-as-cards pattern.

**UT Austin Student Government, studentgovernment.utexas.edu (verified)**
- Columns: Bill #, Policy Area, Author, Passed, Signed, Implemented, Link.
- The Implemented column is the closest thing to "you said, we did" among the peers. Five of 39 pieces of 2025-26 legislation were marked Implemented.
- Blank cells are undefined (not yet, or unknown?). The 2026-27 section says "will be posted shortly" and is empty.

**University of Houston SGA, uh.edu/sga (verified)**
- Two tables: Senate legislation, and executive initiatives with Lead, Partners, Timeline and Status.
- Both were empty on capture.
- Borrow the separate executive initiatives table, which includes an owner, a partner and a status.

**CU Boulder CUSG (verified, thin)**
- Has Bills and Resolutions headings and invites students to "follow proposed legislation" and "share your voice." No entries or statuses were visible.

**WVU SGA, sga.wvu.edu (blocked)**
- The fetch returned 403. A search snippet says it lists bills, resolutions and proclamations separately, and explains the path from idea to president's approval or veto. I did not read the page.

**"You said, we did"**
- I found no student-government page using that framing. Searches only turned up end-of-year PDF reports (KU, Miami, Troy). Treat this as a genuine gap that RPI could fill, not a pattern to copy.

## D. RPI's current web presence (verified)

- **sg.rpi.edu**
  - Active and current. The site is on its 57th Senate (2026-27) with the 160th Grand Marshal.
  - Nav: E-Board, Student Senate, Undergraduate Council, Graduate Council, Judicial Board, Events, Records. The menu is repeated further down the page, and the pages are organized by org chart.
  - Homepage lists five October events (Oct 22 and 26) with no year, plus "File a Complaint," Get Involved, Discord and Instagram.
  - The Senate page says the Senate meets Mondays 7pm in Shelnutt Gallery, but lists no agendas, minutes or legislation. It names only the Grand Marshal and has no senators list, which is on a separate page.
  - It alternates between "Rensselaer Union," "RPI Student Government" and "Student Senate."
- **Records** (`sg.rpi.edu/the-record/`) 302-redirects to a Box shared folder (`rpi.box.com/v/rpisg`). I did not open it. So there is no searchable archive, only a folder.
- **policy.rpi.edu**
  - Has a Student Government Public Record entry: policy library with portfolio tags and last-reviewed dates, and "View Policy Document" links to Box files.
  - It was not clear whether agendas, minutes or legislation are in there.
  - Governing documents live apart from the main site.
- **Older pages**
  - `sg.rpi.edu/node/6` is the 2021-22 term, and poly.rpi.edu articles date from 2014-15.
  - Search returns these ahead of current content.
- **poll.rpi.edu:** Not found. The search returned The Polytechnic opinion pieces about the annual Senate survey (anonymous, signed in to prove uniqueness, 1,300+ responses historically, past outcomes like Capital District shuttles and prescription delivery). I could not confirm the survey tool is live or at that host. Verify with the Web Technologies Group.
- **union.rpi.edu:** Search did not surface it. The Union's office-holder pages were not found, so I could not check who is currently listed.
- **What this means for students:** They would use the Records Box folder, Discord and Instagram, and probably email. There is no single place to see what the Senate is doing this week.

## E. Ranked list: 12 most valuable patterns for a small, volunteer-run, high-turnover site

1. **Task-first homepage with a "Most requested" strip** (GOV.UK, Canada.ca, Boston.gov). Five or six verbs: contact a senator, request funding, report an issue, find a meeting, see what passed, join a committee.
2. **One data record per thing, generated lists** (Congress.gov, Cornell). Meetings, resolutions, people and funding sources are Wagtail records. All lists, trackers and homepage cards are built from them. This is what survives turnover.
3. **Legislation tracker with plain-language stages** (Congress.gov tracker, Cornell status vocabulary, UT "Implemented"). Add term filter and status filter, with separate Senate action and Grand Marshal response.
4. **Meeting page as the unit of transparency** (Cornell). Date, room and link, agenda, packet, minutes, vote tallies, recording, and an Associated Resolutions table. Link both ways between meetings and resolutions.
5. **"This week" strip** (Boston.gov "today" cards, Weather.gov headline). Next meeting, open elections, deadlines, office hours.
6. **Funding hub with a process list and a "where the money goes" table** (MIT funding prominence, USAspending, USWDS process list). Steps, deadlines, eligibility, and a link to the application. Publish approved amounts.
7. **Your representatives** (Boston.gov councilor profiles, ASUC contact routes). Photo, role, constituency, office hours and one preferred contact method, with a "last confirmed" date on each profile.
8. **"You said, we did"** (the gap; UT Implemented column is the closest). Each entry links the original request, the resolution, and the outcome, with a date.
9. **A "Report a problem / Is this useful?" form on every page** (GOV.UK). It goes to a shared inbox, not one person.
10. **Visible "last reviewed" date plus owner on every page** (Canada.ca page details, USWDS identifier, policy.rpi.edu). Pages older than a set period get an automatic stale banner.
11. **Plain-language explainers** (GOV.UK principles, Gov.sg explainers). One sentence per body (Senate, councils, J-Board, Grand Marshal), a glossary, and the Process list showing how a bill moves.
12. **Documented pattern library and handoff page** (Boston.gov Fleet, GOV.UK "make things open"). A "How to run this site" page: who updates what each term, a rollover checklist (roster, term filters, archive old tracker), and a short template cheat sheet.

Also worth adopting, because it is cheap: skip link, strong contrast, and plain-text fallbacks (Weather.gov low-bandwidth ethos, KU skip link).

## F. Anti-patterns the peers fall into

- **Org-chart navigation.** sg.rpi.edu leads with E-Board and Councils. MIT and Berkeley bury core content in nested menus.
- **Stale rosters and term labels.** Berkeley's tracker says 2025-26 while the nav says 2026-27. UT and Houston have blank 2026-27 tables.
- **Undefined empty cells.** UT's blank Passed/Signed/Implemented cells are ambiguous.
- **Documents scattered across hosts.** Box (RPI Records), Google Docs (Berkeley), and spreadsheets (KU's tracker) are not searchable together.
- **Undated announcements and dates with no year.** MIT's undated Participatory Budgeting text and RPI events with only month and day.
- **Dead and placeholder links.** KU's `/legislation-tracker` 404, MIT's `new-page-2`, Berkeley's `dev.asuc.org` and empty hrefs.
- **Duplicated menus.** RPI and MIT repeat the full nav.
- **Inconsistent naming.** RPI alternates between Union, Student Government and Student Senate. MIT mixes "Free Money" and formal labels.
- **Homepages with no governance content.** No meeting times, agendas or legislation (MIT, Berkeley, RPI Senate page).
- **Stale counters and carousels.** Berkeley's "137 Years" and its carousel link.
- **JS-only content that scrapes and screen readers miss.** Stanford ASSU returned empty placeholders to the scraper; treat that as a warning about JS dependence.
- **Data integrity drift between linked views.** Cornell's meeting table omits resolutions its own agenda lists.
- **Relying on one student's memory.** Every failure above traces to manual upkeep with no owner and no review date.

## Fetch limits to remember

- Blocked with 403: Congress.gov, WVU SGA.
- Returned no usable content: USAspending.gov, Stanford ASSU.
- The `ua.mit.edu/funding` fetch hit a certificate error. The Finboard page I read was a different, unrelated student-government page (it appears to be Finboard policy from a university I did not identify), so I have not used it above.
- Not found: poll.rpi.edu, union.rpi.edu.