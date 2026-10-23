# Agendas and Digital Infrastructure Plan digest

> Produced without access to the constitution; see constitution.md for the constitution digest.

The constitution could not be read, so sections 1, 2, 3 and 5 are mostly empty below. The Read tool refused `/Users/aaron/Documents/areas/stugov/union-constitution/main.tex` because `permissions.blockReadsOutsideWorkingDirectories` blocks reads outside `/Users/aaron/src/stugov-site`. I did not work around that with `cat`, and the repo has no copy of the text. **To unblock:** run `/add-dir /Users/aaron/Documents/areas/stugov/union-constitution`, or copy `main.tex` into the repo, then rerun this step. The thresholds and election timing the task asks for are not in the agendas or the plan, so I have not guessed them.

The sections below come from the two agenda PDFs and the Digital Infrastructure Plan, which I read in full.

# Digest (partial)

## 1. Bodies and officers (agenda evidence only)

The constitutional wording, who elects or appoints each body, and the full roster are missing. This is what the agendas show.

**Student Senate (57th Senate, Jul 30, 2026 agenda)**
- 19 voting members, quorum 13, 10 non-voting members, 29 total.
- It is led by the Grand Marshal, who is also listed first in the membership.
- Voting seats by constituency:
  - Graduate Senators: 7 seats, 3 filled.
  - Class of 2027: 4 seats.
  - Class of 2028: 4 seats, 2 vacant.
  - Class of 2029: 4 seats.
  - "Greek & Independent" Senators: 7 seats, both Independent and FSL (Fraternity & Sorority Life).
- Some senators also hold a role, shown in parentheses: VGMIA, VGMEA, SLC, RLDC.
- Non-voting officers are the Treasurer, the Parliamentarian, the Senate-EBoard liaison, and the committee chairs.
- The Senate's committees, each with a chair named in the agenda:
  - AAC: Academic Affairs.
  - CRC: Community Relations.
  - Elections Commission.
  - FSC: Facilities and Services.
  - RLDC: Residential Living and Dining.
  - RAC: Rules and Administration.
  - SLC: Student Life.
  - SCEC: Senate Communications and Engagement.
  - WTG: Web Technologies Group (the website's owner).
  - UAR: Union Annual Report.
- Other agenda roles:
  - Vice Grand Marshal for External Affairs (VGMEA).
  - Vice Grand Marshal for Internal Affairs (VGMIA).
  - Secretary.
  - Peer bodies: Graduate Council, Undergraduate Council, Interfraternity Council, Panhellenic Council, Multicultural Sorority and Fraternity Council.
  - Some of these are marked "Vacant", so vacancy handling matters.

**Executive Board (FY27 Agenda 01, Aug 25, 2026)**
- 12 voting members, quorum 8, 7 non-voting, 22 total.
- Voting members:
  - President of the Union.
  - 3 Vice Presidents: Board Operations, Club Relations, Rules and Special Projects.
  - Class Representatives for Graduate and 2027 through 2030.
  - Club and Organization Representatives (8 seats).
  - Member-At-Large Representatives (5 seats).
- Non-voting members: Club Financial Advisors, Peer Body Liaisons (Senate, Undergraduate Council, Graduate Council), Secretary, Parliamentarian, and the committee chairs.
- Committees:
  - Business Operations.
  - Club Operations.
  - Marketing & Strategy.
  - Executive Communication.
  - Multicultural Leadership Council (MLC).
  - Union Annual Report (a second UAR body, separate from the Senate's UAR committee).
  - UPAC: Union Programming and Activities Committee.
- The Director (Dr. Charlie Potts) reports to the board, so a professional staff director exists.

Note an inconsistency: the Aug 2026 agenda's membership block says "2025-2026 Rensselaer Union Executive Board" while its title says "2026–2027". Treat the roster as possibly stale and design for it to be edited.

## 2. Student-facing processes
Not available without the constitution. The agendas hint at only these:
- The standing "Invitation to Speak" and "Press & Visitor Q/A" items on both agendas are the only visible public-participation hooks.
- The Executive Board handles "Special Ballroom Request" proposals, so room and space requests go through it.
- The Executive Board funds Club Contingencies, Travel Contingencies and Facilities.

## 3. Transparency obligations and records
The constitution's obligations are missing. The agendas and plan show these records:
- Agendas with a membership roster attached.
- Minutes (the EBoard agenda opens with "Approval of Minutes").
- Motions and resolutions.
- A live budget snapshot printed on the EBoard agenda:
  - Club Contingencies: $100,000 initial and current, 100%.
  - Travel Contingencies: $60,000 initial and current, 100%.
  - Facilities: $166,150 initial and current, 100%.
  - Facilities Reserves: $126,635.47 current.
  - These four lines are a ready-made dashboard widget.
- The plan lists these permanent records:
  - Union Constitution.
  - Rensselaer Union Guidelines and Procedures (RUGP).
  - The Rensselaer Handbook of Student Rights & Responsibilities, maintained by RPI.
  - Bylaws and Union Policies, plus a history of policy changes.
  - Historical archives.
- Both agendas give the Union's address (110 8th Street, Troy, NY 12180) and the URL sg.rpi.edu.

## 4. What the agendas reveal

**Senate meeting structure (fixed order):**
1. Bookkeeping, including the Polytechnic Statement of Recording.
2. Invitation to Speak and Press & Visitor Q/A.
3. Grand Marshal Report.
4. Committee Reports.
5. Peer Body & Officer Reports.
6. Special Orders.
7. Old Business.
8. New Business.
9. Invitation to Speak and Press & Visitor Q/A again.

**Executive Board meeting structure:**
1. Approval of Minutes.
2. Reports: officers, Director, liaisons, committees.
3. Proposals, such as Special Ballroom Requests.
4. Business, such as the Rally Week Discussion.
5. Invitation to Speak.
6. Press & Visitor Q/A.

**Naming and numbering conventions:**
- Senate: "57th Student Senate", meeting number "#12", date in the filename as `07_30_26`.
- Executive Board: "FY27", "Agenda 01", the board year "2026–2027".
- Academic years are written on names as class years like `'27`, `'28`, or `'30G` for graduate.
- Locations vary between Webex and a physical room (RU 3202), and the page needs a location field.
- Time zone is written as "EST".

**What a legislation and motion tracker would need to model:**
- Body (Senate or EBoard), session number, meeting number and date.
- Item type, from this set: Report, Proposal, Special Order, Old Business, New Business, Motion, Resolution, Appointment.
- Sponsor and requesting organisation.
- Status, such as submitted, on agenda, passed, failed or tabled. The vote status values and vote counts are not in the agendas; they would come from minutes.
- Links to the agenda, the minutes and the supporting document in Box.
- Whether a meeting had quorum, and the membership snapshot for that date (voting, non-voting, vacant seats).
- Neither agenda contains a numbered bill, so numbering for motions and resolutions has to come from the constitution, bylaws or minutes.

## 5. Recurring calendar
From the agendas only:
- The Senate met Jul 30, 2026 at 8:00 PM as its 12th meeting of the 57th Senate.
- The Executive Board met Aug 25, 2026 at 7:00 PM, its first meeting of FY27.
- Both are summer or early-fall dates, so a fiscal year likely starts July 1 (FY27 meetings in August fit that). That is inferred, not stated.
- Cadence for either body, and election and budget timing, need the constitution.

## 6. Constraints from the Digital Infrastructure Plan
- **Purpose:** a reliable central platform that survives student government turnover. The plan's stated reasons for a new site are centralized access, ease of use and resilience to turnover.
- **Four components:**
  - Discord for real-time chat: a public server for students, and private role-based channels for members.
  - The website, as a hub for information and documents.
  - Box for file storage and version history.
  - An Admin role for maintenance and access.
- **Box is the source of truth for documents.** The plan describes:
  - Public docs (constitutions, minutes, flyers).
  - Private docs (budgets).
  - Team folders per council and committee.
  - The site embeds files with Box's Embed Widget, with inline previews and direct links.
  - This matches the current Wagtail design, where `RecordPage.box_url` is primary and Wagtail docs are the fallback.
- **Records tiers the site should show:** permanent records, historical archives, procedural records (bylaws, policy history), and embedded meeting records (minutes, motions, resolutions).
- **File maintenance:**
  - Users submit changes through a form with a description and rationale.
  - Important updates are reviewed before publishing.
  - Files use a naming standard like `YYYY-MM-DD-DocumentTitle`.
  - Backups are automatic.
  - Update alerts go out when documents change.
- **Site architecture in the plan:**
  - Sections for the Graduate Council, the Undergraduate Council, committees, and an Events & Activities hub.
  - Hierarchical navigation, modular design, mobile optimization, and future API integration with Box, Google Drive or the RPI portal.
  - The plan assumes WordPress, but the current site is Wagtail.
- **Admin role:** one named Primary Administrator (and designated sub-admins) who verifies content, assigns roles, runs periodic access audits, and trains successors. This is probably the Web Technologies Group chair. Role and access changes at each turnover must be a documented procedure.
- **Other constraints:**
  - Documents are Word or Excel from standard templates and are converted to PDF for the public.
  - Webex is used for live meetings.
  - Shared calendars, standard email lists and social links are part of the plan.
  - There is a plan for an annual system review.
  - Usage analytics and storage management are in scope.

## Files

- `/Users/aaron/src/stugov-site/#12 07_30_26 57th Student Senate Meeting Agenda-1.pdf`
- `/Users/aaron/src/stugov-site/FY27 Agenda 1 - August 25, 2026.pdf`
- `/Users/aaron/src/stugov-site/Union-Digital-Infrastructure-Plan-1360e6813c44807fa1c5fece505d6344.html`
- `/private/tmp/claude-501/-Users-aaron-src-stugov-site/814b13ec-3ac9-47e7-96e9-c31ad2c067e7/scratchpad/plan.txt`, `senate.txt` and `fy27.txt` are my text extractions of the three files above.