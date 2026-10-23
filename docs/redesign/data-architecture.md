# ADR: Data architecture and single source of truth

*Status: proposed, 21 Oct 2026; revised the same day after new facts from the site owner. Branch `redesign/explore`. Answers the site owner's question: "is this something that will have to be reconciled with a single source of truth?"*

**What the revision changed.** The first version assumed the whole Union would pick one structured system, Notion or Wagtail, for meeting records, the roster and issues. The owner has since told us three things:
- Agendas, minutes and motions are written in **Word**.
- **Only the Senate** is looking at Notion, as its knowledge base, CRM and relational data. The E-Board, the Councils and the Judicial Board are not.
- How the E-Board, the Undergraduate and Graduate Councils and the Judicial Board organise themselves is their own business, "just as long as their public records are strong."

So this version replaces "the Union picks Notion or Wagtail" with a **per-body model**. Every body meets one tool-agnostic **Public Records Standard** (§3.2). Each body keeps its records however it likes, and the website reads them through a per-body **adapter** (§3.3).

**Hard constraints**
- **There will be no Box API.** That means no CCG or JWT service account, no webhooks and no programmatic folder listing. Without the API, three things still work:
  - Box shared links.
  - Box embed widgets for files and shared folders (`/embed/s/<id>`). Box's preview renders PDF and Word (`.docx`) files, so an embedded Word file is readable in the page.
  - People pasting links.
- **Notion's API is available** through self-serve internal integrations.
- **Single source of truth, no double entry** (§2).

## 1. Decision in one paragraph

- **Every fact has exactly one owner.**
  - Box owns files, and every public record is a file in a body's public Box folder.
  - **The content of a Word document lives in the Word document.** Agenda items, motion text and outcomes as minuted are never retyped into Notion or Wagtail.
  - Each body owns its own meeting facts, in the tool it chooses. Today that means the Senate in Notion, and every other body either on this site (a minimal meeting entry) or nowhere but its Box folder.
  - **Wagtail owns the public roster for every body**, the Senate included (§6.4). The Senate's Notion gets an automatic read-only copy for attendance.
  - Wagtail owns public explanatory content.
- **Every body meets the same Public Records Standard:** what must be public, how soon, where, in what format, and who answers for it. The Standard doesn't care which tools a body uses.
- **The website renders every body the same way**, whatever its adapter. Where an adapter gives it less structure, the site says so plainly ("This body publishes its records as files. See the folder.") instead of showing empty tables.
- **Officers type each fact once.** The only cross-system step is pasting a Box shared link next to the meeting or motion it belongs to. §5 argues why that is a reference and not double entry.
- **The site makes decay visible to operators.** It shows each item's source and checks every body against the Standard, so neglect can't hide.

## 2. Two different promises

| | Single source of truth (SSOT) | Single point of entry (SPOE) |
|---|---|---|
| Promise | Each fact has one authoritative owner. Every other appearance of it is derived from that owner. | An officer types each fact once, in one place. |
| Violated by | Two editable copies that can disagree, e.g. a meeting date in Notion and in Wagtail. | Retyping, e.g. uploading a PDF to Box *and* to Wagtail, or typing a Word agenda's items into Notion. |
| Not violated by | Automated, one-way mirrors and caches (a Notion-to-Wagtail sync, a downloaded photo thumbnail) that are read-only downstream and can be rebuilt from the owner. | Pasting a *pointer* (URL or ID) to where the owner keeps a fact. |

**The rule.** Mirrors are fine if they are automated, one-way, read-only downstream and rebuildable. Double entry is not fine.

**The test for any new feature:** "If an officer changes this in the owner system, does the site change with no human action, or flag that it hasn't?"

## 3. Per-body records

### 3.1 Bodies choose their tools; the site adapts

| Body | Internal tools (their business) | Website adapter (proposed starting point) |
|---|---|---|
| **Student Senate** | Word for agendas, minutes and motions. Notion as knowledge base, CRM and relational data (being adopted). | **Notion projection** (§3.3). Meetings, motion status and Public issues sync from the Senate's Notion. Files are in Box. |
| **Executive Board** | Word, plus whatever it uses internally | **(B) Minimal meeting entry on this site**, *if it wants* per-meeting pages. Otherwise **(A)**. |
| **Graduate Council** | Its own choice | **(A) Box folder only**, until it asks for more |
| **Undergraduate Council** (and the four Class Councils under it) | Its own choice | **(A) Box folder only**, until it asks for more |
| **Judicial Board** | Its own choice | **(A) Box folder only**. What is public needs its own rule (§3.2). |

These are defaults to offer, not decisions to impose. A body can move from A to B, or to C, at any time without the site changing shape, because the site renders every body the same way (§3.4).

### 3.2 The Public Records Standard

The floor every body meets, whatever its tools. It's written so a secretary with Word and a Box login can meet it with nothing else. Each number below is a proposal for the site owner and the bodies to confirm. The Union Constitution requires only that the budget and the records of all extra spending and appropriations be public (Art. VII §2). Publishing agendas and minutes is Union practice, so the Standard needs adopting (see §11 of the workshop report).

**1. What must be public**

| Body | Records |
|---|---|
| Every body | Agenda for every meeting, including attachments the body will consider. Minutes of every meeting, as draft and then as approved. The text of every motion, resolution or bylaw change it votes on. Its bylaws. |
| Executive Board | Also the budget, and records of all extra spending, appropriations and allocations (constitutional, Art. VII §2). |
| Judicial Board | Its rulings on what the Constitution means, and any ruling that a body's decision is unconstitutional. Conduct and rights cases name students and are not public. Anonymised summaries are the Judicial Board's decision, to confirm against its bylaws. |
| Never public | Anything under `Internal/`: drafts that aren't ready, CRM exports, personal contact details, attendance until the Senate's rules say otherwise. |

**2. How soon**

| Record | Deadline (proposed) | What the site can check |
|---|---|---|
| Agenda | In the folder **24 hours before the meeting** (48 is the target) | Adapters B and C: the agenda link on the meeting record. Adapter A: nothing automatically. |
| Draft minutes | In the folder **within 7 days**, with "Draft" in the filename | Same as above, via the minutes link |
| Minutes, overall ceiling | Draft or approved minutes in the folder **within 14 days** of the meeting | Same. This drives the "Minutes link missing" flag. |
| Approved minutes | **Within 3 days** of the approval vote, as a new version of the draft (rule 5) | B and C: the "Minutes approved" date |
| Motion text | In the folder **before the vote**, as an attachment or inside the agenda | Senate only: the file link on the Motions row |
| E-Board budget and allocation records | As soon as they exist, and **at least once a semester** | No automatic check. The health page asks the E-Board to confirm each semester. |

**3. Where**
- One public Box folder per body per term: `Public Records/<Body>/<YYYY-YY> <Body code> <Term>/`.
- The shared link is set to **"People with the link"**, never "People in your company". Otherwise visitors hit an RPI login.
- Filenames follow the convention in §5: `YYYY-MM-DD <Body> <Term> #<nn> <Agenda|Minutes|Minutes (Draft)|Motion - Title|Attachment - Title>.pdf`.
- The `Public Records` tree is owned by a Union role account. Each body's records officer has Editor rights on that body's folder only.

**4. Format: Word in, accessible PDF out**
- The public copy of a Word document is a **PDF exported from Word**. Put the `.docx` alongside it only if the body wants people to be able to reuse the text.
- A `.docx` alone also renders in Box's preview, so it is a degraded pass rather than a failure. But a Word file can carry tracked changes, comments and author names. Before publishing a `.docx`, run Inspect Document (Windows) or turn on "Remove personal information" (Mac).
- **Accessibility of the export.** This is part of the Standard, not a nicety:
  - Use Word's built-in styles. Heading 1 for the agenda's sections (Old Business, New Business), Heading 2 for items, real numbered lists, and a header row on tables. Don't fake headings with bold text.
  - Add alt text to logos and images, or mark them decorative.
  - Set the document title (File, Properties) and the language.
  - Use link text that makes sense out of context.
  - Run Word's Accessibility Checker (Review, Check Accessibility) and fix what it finds.
  - Export a **tagged PDF**. On Windows: File, Save As, PDF, Options, with "Document structure tags for accessibility" ticked. On Mac: File, Save As, PDF, "Best for electronic distribution and accessibility". **Never use Print to PDF**, which strips the tags.
  - Never publish a scan of a printed document.
- The site's Web Technologies Group (WTG) provides one Word template per body with these styles already set. That template does most of the work: a secretary who types into it gets an accessible PDF for free.

**5. Corrections keep links stable**
- To fix or replace a file, use **Upload New Version** in Box. Never delete and re-upload, and never upload a second copy (the `-1` suffix in today's filenames is that mistake). The shared link, and every page that points to it, then shows the new version with nothing to reconcile.
- Draft minutes become approved minutes the same way: upload the approved file as a new version of the draft, then rename it to drop "(Draft)".

**6. Who is accountable**
- Each body names a **records officer** (default: its Secretary) in the site's body settings. They answer for the deadlines above.
- The body's chair answers for the records officer.
- WTG answers for the site, the templates, the link checks and the health page. **WTG never fixes another body's records.** It flags them.
- The health page (§7) shows every body's standing against the Standard to officers. What happens after repeated misses is for the bodies to agree when they adopt the Standard.

### 3.3 The adapter menu

| | (A) Box folder only | (B) Minimal meeting entry on this site | (C) Adopt the Senate's Notion setup | Senate: Notion projection |
|---|---|---|---|---|
| Body enters | Nothing beyond the files | Per meeting: number, date, time, place, and two pasted Box links (agenda, minutes), plus the minutes-approved date. About a minute, prefilled from the last meeting. | The same facts in its own copy of the Senate's Notion databases | Meeting rows, Motions rows (status and a pasted file link) and Public issues, in Notion |
| Site gets | The folder embed and an "Open in Box" link | Per-meeting pages, "next meeting", the calendar, the Standard's deadline checks | The same as the Senate | Everything in B, plus motion status and Public issues |
| Structure | Weakest | Meetings only | Same as the Senate | Meetings, motions, issues. Agenda items only if the Senate drafts agendas in Notion (§3.5). |
| Valid when | Always. This is the floor. | The body doesn't also keep the same meeting facts in another structured system | The body has its own Notion members, and someone to keep its schema in line with the sync | Senate officers use Notion for a full semester (§6.3) |
| Source line on the site | "Records: files in the <Body> Box folder" | "Meeting record: entered on this site by the <Body> Secretary · updated <date>" | "Meeting record: <Body>'s Notion · synced <n> min ago" | "Meeting record: Senate's Notion · synced <n> min ago" |

**Senate Notion projection: the whitelist.** The sync reads only databases shared with the integration, only rows with `Public` ticked, and only these properties, by property ID:
- **Meetings:** term, number, date and time, location, `Agenda` (URL), `Minutes` (URL), `Minutes status` (draft or approved), `Minutes approved` (date), `Public`. Also a remote-join link, published only if "Publish join link" is ticked.
- **Motions:** a short label (a name for the row, like a filename, not the motion's text), meeting (relation), type (motion, resolution, bylaw, appointment, fee), `Status`, `Motion file` (URL to the Word or PDF file in Box), `Public`. A vote tally stays private until the Senate decides to publish tallies.
- **Issues:** title, topic, constituencies, owner seat, source, raised date, status, dated updates, outcome, `Public`. A student's original message is never synced.
- **Agenda items (only under the §3.5 option):** meeting (relation), section, order, title, presenter seat, type.
- **Never synced:** attendance, CRM contacts, internal notes, personal contact details.
- **Pushed the other way:** the roster, from this site into a read-only "Senators (from website)" database (§6.4).

**(B) is a pointer pattern too.** The Word agenda already says the date, number and place in its header, and the meeting entry says them again. That duplication sits between Word and *any* structured record, Notion included, and it's the price of having per-meeting pages at all. It's detectable: a human sees a mismatch in the preview, and the health page can flag an entry whose date doesn't match the date in the pasted filename. Only the Senate's §3.5 option removes it entirely.

### 3.4 One way to render every body, and honest degradation

The site has one meeting and records interface. Each body declares its adapter, and pages switch on what that adapter can supply, never on which body it is.

| What a page wants | Senate (Notion) | (B) or (C) | (A) folder only |
|---|---|---|---|
| Next meeting card | Yes | Yes | "The <Body> doesn't list meetings on this site. Its agendas are in its folder." |
| Per-meeting page | Yes | Yes | None. The body page shows the folder. |
| Agenda | The document: Box file preview on desktop, "Open agenda (PDF)" first on phones | The same | Inside the folder embed |
| Agenda item by item | Only under the §3.5 option | Never | Never |
| Decisions | Motions rows: label, status, link to the motion text | "Decisions are recorded in the minutes." Plus the minutes link. | "Decisions are recorded in the minutes, in the folder." |
| Roster | This site | This site | This site, or "Roster not listed yet" |
| Standard checks | Automatic (links, dates) | Automatic | "Can't check automatically. Records last confirmed complete by the <Body> records officer on <date>." |

**Degradation rules**
- Never show an empty table for a body that can't fill it.
- Never imply that a folder-only body is inactive. Say what kind of publishing it does, then link the folder.
- Lead with "Open in Box" on phones. Box says Box Embed "isn't optimized for mobile browsers" ([Box Embed guide](https://developer.box.com/guides/embed/box-embed/)).
- Every projected item carries a source line naming its adapter (the table in §3.3).

**Data model sketch (Wagtail)**
- `Body`: name, code, adapter (`notion` | `site` | `folder`), current term, folder shared link, records officer (a `Role`), and "records last confirmed complete" (a date the records officer sets for adapter A).
- `Meeting`: body, term, number, starts, location, agenda URL, minutes URL, minutes status, approved date, and `source` (`notion` | `site`) with `source_id` and `synced_at`.
  - Notion-sourced rows are read-only in the admin, with an "Edit in Notion" link.
  - Site-sourced rows are edited in a short form, the Desk's "Post the next meeting".
- `Motion`: Notion-sourced only.
- Folder-only bodies have no `Meeting` rows at all.

### 3.5 Word documents: what can be structured without retyping

Agendas, minutes and motions are written in Word, so their content lives in the Word file. The site shows the document. It never shows a hand-made copy, and it never parses the document.

| Fact | Where it lives | Structured on the site? | Why |
|---|---|---|---|
| Meeting number, date, time, place | The meeting record (B, C or Senate Notion). Folder-only bodies: the filename. | Yes, for B, C and the Senate | Typed once in the record. It repeats the Word header (§3.3). |
| Agenda link, minutes link | Pasted into the record | Yes | Pointers |
| Minutes draft or approved, and the approval date | The record | Yes | A new fact about the file, recorded when it happens |
| Agenda items, presenters, sections | **The Word agenda** | **No.** Show the document. | Retyping the items into Notion or Wagtail is double entry. Parsing Word or PDF files is fragile and would need the Box API to fetch them. |
| Motion text | **The Word motion file** (or the agenda) | No. Link it from the motion's row. | The text is the content. |
| Senate motion status and outcome | **A Notion Motions row** | Yes, Senate only | See below |
| Outcomes as minuted, and vote tallies | **The Word minutes** | No | Content |
| E-Board, Council and Judicial Board decisions | Their minutes and rulings (files) | No. "Decisions are recorded in the minutes." | Content |

**Why a Senate Motions row is not double entry.** The secretary records a motion's status once, at the meeting, when the vote happens and before the minutes exist. That status is a new fact, and the row is its owner. The motion's text stays in the Word file the row links to. To keep it one-way, the secretary builds the minutes' list of motions from the Notion Motions view (copy and paste, or a filtered export) rather than typing the outcomes twice. If the Senate approves minutes with a corrected outcome, the secretary updates the row. That's the one place where a human has to reconcile, and it's visible: the row's "last edited" date moves.

**Option, the Senate's choice and not a requirement: draft agendas in Notion.** If the Senate's secretary writes the agenda as a Notion page, its items become structured data and the site can show the agenda item by item, link items to motions, and search them. Then the Word or PDF file is an export, not the source. The trade-offs:

| For | Against |
|---|---|
| Item-by-item agendas, items linked to motions, searchable decisions, no Word header to retype | It changes how the secretary works, and it has to hold up for a full term to be worth building. |
| The site's HTML agenda is itself an accessible version | Notion doesn't export `.docx`. Getting a Word file means copy and paste or a converter, and Notion's PDF export isn't reliably tagged, so the export needs an accessibility check every time. |
| | The exported PDF is a manual copy. If someone edits the Notion page after export, the PDF in Box is stale until they re-export and upload a new version. A Notion "Exported" date, checked against the page's last-edited time, can flag that. |
| | It only works if every agenda goes through Notion. A half-and-half term gives a site where some meetings have items and some don't. That's acceptable (it degrades to the document), but it reads as inconsistent. |

The prototypes show this option behind an explicit label on Senate meeting pages, next to the default view of the document.

## 4. Data ownership map

Key to "how the site gets it": **E** = Box embed or link. **S** = Notion sync (one-way, cron, Senate only). **N** = native Wagtail. **M** = mirror pushed from Wagtail into the Senate's Notion. **L** = link-out.

| Data | Senate | E-Board, Graduate Council, Undergraduate Council, Judicial Board | How the site gets it | Public / private |
|---|---|---|---|---|
| Agenda, minutes, motion and attachment *files* (written in Word, published as PDF) | Box | Box | E. Per-file links on meeting records, plus the per-body term folder embed. | Files in `Public Records` are public. `Internal` is never linked. |
| Meeting record (number, date, time, place, agenda and minutes links, minutes status, approved date) | Senate's Notion "Meetings" | (B) Wagtail `Meeting` · (C) the body's own Notion · (A) none, only the filename in the folder | S / N / none | Public, except remote-join links unless ticked |
| Agenda items | Only under the §3.5 option, in the Senate's Notion | Never structured. The document is shown. | S (option) / E | Public |
| Motion status and outcome | Senate's Notion "Motions" (label, status, link to the motion file) | In the minutes (file) | S / E | Public |
| Motion text, outcomes as minuted, tallies | The Word files in Box | The Word files in Box | E | Public. Tallies are private in Notion until the Senate decides. |
| Attendance | Senate's Notion, linked to the mirrored roster | The body's business. Never on the site. | Never synced | Private |
| Seats, people, assignments, profile consent | **Wagtail** (§6.4) | **Wagtail** | N. M into the Senate's Notion. | Name, seat and term are public. Profile fields only with consent. |
| Issues ("You said, we did") | Senate's Notion "Issues", Public rows | Not tracked publicly, unless a body asks | S | Public rows only |
| Records officer and "records last confirmed" | Wagtail `Body` | Wagtail `Body` | N | Officer-only |
| Contact routes and topic router | Wagtail | Wagtail | N. Routes point to seats. | Public |
| Non-meeting events | Wagtail `EventPage`, or link out | Same | N / L. Meetings come only from meeting records, never from EventPages. | Public |
| Budget figures | n/a | Business Operations and Union finance, printed on E-Board agendas | L to the newest E-Board agenda. Never retyped. | Public (Art. VII §2) |
| Governing documents | Source text, with the PDF in Box | Same | E / L, plus a Wagtail summary | Public |
| Evergreen pages, glossary, start pages, notices | Wagtail | Wagtail | N | Public |
| Announcements | Discord | Discord | L | Public server |
| CRM, knowledge base, meeting prep | Senate's Notion | The body's business | Never | Private |

## 5. Meeting publishing without the Box API

There are two kinds of fact here:
- **The file's content** (what the agenda says) belongs to the Word file in Box.
- **The meeting record** (that Senate 57 #12 happened on Thursday 30 Jul 2026 at 8 PM on Webex, with this agenda and those minutes) belongs to the body's adapter: the Senate's Notion, a Wagtail entry, or, for a folder-only body, nobody but the filename.

Box can't hold a structured meeting record without an API, because the only structure it has is a filename the site can't read.

| Mechanism | Officer steps | Facts typed for the site | Pointers pasted | Site gets structure? | Use for |
|---|---|---|---|---|---|
| Folder only | Save the PDF into the body's term folder using the naming convention | 0 | 0 | No | Adapter (A). Also the floor for everyone. |
| Notion row | Duplicate the last meeting row, paste the Box links | 0 extra: the Senate keeps the row anyway | 2 | Yes | The Senate |
| Site entry | The same, in the Wagtail form, prefilled from the last meeting | About 6 | 2 | Yes | Adapter (B) |
| Scrape Box folder pages | Upload only | 0 | 0 | Fragile | Never |
| Upload-notification inbox | Upload only, then one "confirm match" click per file | 0 | 0 | Partial | Later, as a nudge |

**Folder only: what the site loses.** It's true zero entry, and it works today: the site already converts `/s/` links to `/embed/s/`. But a folder-only body gets:
- no per-meeting URLs to share in Discord;
- no "next meeting" and no meetings on the calendar;
- no on-site search;
- no automatic check against the Standard. A body that stops uploading looks the same as one that never met. That's why adapter (A) asks the records officer to confirm "records complete" each month, and the health page shows how long it's been.

**Is pasting a link double entry?** No.
- A fact is a claim about the world ("the meeting was on 30 Jul"). A pointer is the address where the owner keeps a fact.
- Copying a fact creates a second version that can drift silently. A pointer has no second version. Upload a corrected agenda as a new Box version and the same link shows the new content.
- A pointer fails in only two ways, and both are detectable:
  - It breaks (the file is deleted or unshared). An automated link check catches this.
  - It's wrong (the wrong file was pasted). A human sees this in the preview.
- In database terms, a pointer is a foreign key, not a denormalised copy.

It is still one extra *step*, and steps get forgotten. That is why the health page flags meetings with a missing agenda or minutes link.

How to keep the pointers to a minimum:
1. Paste exactly two links per meeting, agenda and minutes. Attachments live in the term folder embed, which needs no pasting. A Senate motion gets one more link, to its file, on its Motions row.
2. Never attach a file to a Notion `files` property. That would make Notion a second file host, and Notion-hosted file URLs expire after one hour ([Notion file object](https://developers.notion.com/reference/file-object)). Use a URL property, which doesn't expire.

**Don't scrape public Box shared-folder pages.**
- They are rendered by JavaScript, so a scraper needs a headless browser, and any front-end change at Box breaks it silently.
- Box's Acceptable Use Policy forbids "any automated process or service (such as a bot, a spider, or periodic caching of information stored by Box)" ([Box Terms of Service §10(d)](https://www.box.com/legal/termsofservice)).
- Breakage would show up as a quietly empty list, which is the failure mode this design exists to prevent.

A plain HTTP status check on links a human pasted is a different matter: low volume, what a browser does, and it reads no content. Run it weekly. An unshared link may come back as a 200 login page rather than a 404, so the check looks for a login-wall marker, not just the status code.

**Other API-free mechanisms**

| Mechanism | Assessment |
|---|---|
| **Upload notifications to a site mailbox.** A mailbox owned by the WTG role collaborates on the public folders with notifications on. The site reads it over IMAP and turns "X uploaded *file* to *folder*" into an "unmatched file" queue. | **Worth prototyping.** For folder-only bodies, it would let the health page see "last upload to the Graduate Council folder: 12 days ago" without the API. It processes email Box sends us; it doesn't access Box. Collaborators each have to enable notifications ([UIUC Box notifications](https://answers.uillinois.edu/74329)). It breaks if Box changes the email format, so it's a nudge, never an owner. |
| **Box email-upload addresses** ([UMN](https://it.umn.edu/services-technologies/how-tos/box-upload-files-box-email)) | Inbound only. Helps secretaries upload from a phone. Gives the site nothing. |
| **Power Automate / Zapier Box connectors** ([MS connector](https://learn.microsoft.com/connectors/box)) | This *is* API access through a third-party app. Expect no. |
| **User-OAuth custom app** | Also API access. Expect no. |
| **Box Drive on an always-on machine** | Don't count on it. |
| **Box RSS feeds** | Not offered. |

### Box folder and filename convention

Names start with the date, so Box's sort-by-name order is chronological. It follows the Digital Infrastructure Plan's `YYYY-MM-DD-DocumentTitle`.

```
Public Records/
  Senate/2026-27 Senate 57/2026-07-30 Senate 57 #12 Agenda.pdf
  Senate/2026-27 Senate 57/2026-07-30 Senate 57 #12 Minutes.pdf
  Senate/2026-27 Senate 57/2026-10-14 Senate 57 #15 Motion - Committee reporting bylaws.pdf
  Executive Board/2026-27 EBoard FY27/2026-08-25 EBoard FY27 #01 Agenda.pdf
  Executive Board/2026-27 EBoard FY27/2026-08-25 EBoard FY27 #01 Attachment - Special Ballroom Request (UPAC).pdf
  Graduate Council/2026-27 GC 2026-27/...
  Undergraduate Council/2026-27 UC 2026-27/...
  Judicial Board/2026-27 JBoard 2026-27/2026-11-03 JBoard 2026-27 Ruling - Interpretation of Art. VII §2.pdf
  Governing Documents/Union Constitution (amended 2026-02-06).pdf
Internal/            (never shared publicly; budgets in progress, drafts, CRM exports)
```

Pattern: `YYYY-MM-DD <Body> <Term> #<nn> <Agenda|Minutes|Minutes (Draft)|Motion - Title|Attachment - Title>.pdf`. Judicial Board rulings use `Ruling - Title` and may omit the meeting number.

Body codes are `Senate`, `EBoard`, `JBoard`, `GC` and `UC`. As a regex: `^(\d{4}-\d{2}-\d{2}) (Senate|EBoard|JBoard|GC|UC) (\S+)(?: #(\d+))? (Agenda|Minutes(?: \(Draft\))?|Motion - .+|Attachment - .+|Ruling - .+)\.(pdf|docx)$`.

| Today | Convention |
|---|---|
| `#12 07_30_26 57th Student Senate Meeting Agenda-1.pdf` | `2026-07-30 Senate 57 #12 Agenda.pdf` |
| `FY27 Agenda 1 - August 25, 2026.pdf` | `2026-08-25 EBoard FY27 #01 Agenda.pdf` |

The `-1` suffix is Box's duplicate-upload marker. Upload New Version replaces it and keeps the shared link valid.

### What to do with the dead Box API code

1. Tag the current commit (`archive/box-api-sync`).
2. Delete `records/management/commands/sync_box_records.py`, remove `boxsdk` from `requirements.txt`, and drop the `BOX_*` settings.
3. Remove `BoxFileCache` with a migration. Without the API it can never hold rows.
4. Keep `infer_record_type`'s regexes as the seed for a filename-convention linter that runs over pasted links.
5. Replace `RecordIndexPage`'s redirect-or-cache logic with per-body folder embeds, one per `Body`.
6. Retire `RecordDocument` uploads from the editor. Uploading files to Wagtail creates a second file host.
7. `RecordPage` becomes a governing-document page: a Box link plus a Wagtail-owned summary.

`SiteSettings.box_archive_url` is a `/v/` vanity link, and `box_embed_url` only converts `/s/` links. Verify that the vanity link embeds, or switch to an `/s/` link.

## 6. Notion for the Senate, and the roster

### 6.1 Verified Notion API facts

- **Rate limits.** 180 requests per minute (about 3 per second) per connection on non-Business plans, with a separate ~3/s limit on data-source queries. Over-limit requests get a 429 with `Retry-After` ([request limits](https://developers.notion.com/reference/request-limits)). A full Senate sync is trivially within that.
- **Data-source API.** Since API version 2025-09-03, a database is a container of *data sources*, queried at `POST /v1/data_sources/{id}/query`, filterable on `last_edited_time` ([upgrade guide](https://developers.notion.com/docs/upgrade-guide-2025-09-03), [query reference](https://developers.notion.com/reference/query-a-data-source)). Pin the API version.
- **Webhooks** exist per connection, including `page.properties_updated` and `data_source.schema_updated`. Payloads carry IDs, not values, and delivery is at-most-once, possibly out of order, within about 5 minutes ([event delivery](https://developers.notion.com/reference/webhooks-events-delivery)). Use them only as a "sync now" trigger; cron is the guarantee.
- **Permissions.** An internal connection sees nothing until pages are shared with it ([internal integrations](https://developers.notion.com/guides/get-started/internal-integrations)). Share *only* the public-facing Senate databases, plus the roster mirror it writes to.
- **Schema fragility, mitigated.** "A property's `id` stays the same when its name changes" ([property object](https://developers.notion.com/reference/property-object)). Sync by property ID. Renames are harmless, and deletions or type changes show up as health errors.
- **Writes.** Updating a page sets only the properties sent, so the roster mirror can own its columns while the Senate adds private columns to the same rows.
- **Cost.** Plus is $10 and Business $20 per member per month ([pricing](https://www.notion.com/pricing)). Notion's student organization program gives volunteer student orgs at "select verified" institutions free org-wide access ([Notion for students](https://www.notion.com/students)). Confirm RPI is eligible. Only Senate officers need seats.
- **SSO** (SAML) requires Business. Otherwise offboarding means removing members by hand.
- **Export.** Markdown, CSV, HTML and PDF page exports exist, plus a whole-workspace export ([export](https://www.notion.com/help/export-your-content)). There's no `.docx` export.

### 6.2 What the Senate's Notion owns

- Knowledge base, CRM and meeting prep: private, never synced.
- Meetings and Motions: public rows synced (the whitelist in §3.3).
- Issues: public rows synced.
- Attendance: private, related to the mirrored roster.
- Optionally, agenda pages (§3.5).
- **Not the roster** (§6.4).

**Volunteer burden.** One sync command (~400 lines) for three data sources, one push command (~150 lines) for the roster mirror, a health check and a locked-schema document. Don't build a CRM in Wagtail for anyone.

**Turnover.** The workspace is owned by a **role account** (e.g. a `sg-web@` mailbox, if RPI provides one), never a person. Keep at least two workspace owners at all times, and run an export each term.

### 6.3 When the Senate falls back to (B)

The Senate switches to the site entry (B), with no data to migrate except a one-time import of meeting rows, if any of these happen:
- The secretaries don't actually use Notion for a full semester.
- The workspace can't be held by a role account with two owners.
- RPI policy bars student data in Notion.
- No developer can own the sync for at least a year.

Because the roster already lives on the site (§6.4), a fallback never strands seats or people.

### 6.4 Roster ownership: Wagtail for every body

**Decision.** Wagtail owns the public roster for **all** bodies, the Senate included: `Role` (seats), `MemberProfile` (people, consent and profile fields) and `MemberRoleAssignment` (person, seat, term, start and end). The Senate's Notion references it through an automatic, read-only mirror.

**Why not split the roster by body (Senate in Notion, everyone else in Wagtail)?**
- **People cross bodies.** Cee Ray '27 is Senate Treasurer and also the E-Board's Senate–E-Board Liaison. Griffin Oliver '27 is a Class of 2027 Senator, VGMIA and RAC chair. Samson Kempiak '28 chairs a Senate committee and holds an E-Board club seat. Stanley Goodwin '30G is a Graduate Senator and SLC chair. A split would give these people two records, one per system, so their name, class year and photo consent would each have two owners. Consent is the worst case: withdrawing it in one place and not the other is a privacy failure.
- **Every body can reach Wagtail.** Only the Senate uses Notion. A Notion roster would leave four bodies needing a second system anyway.
- **It survives a Senate fallback** (§6.3) with nothing to migrate.
- **The models already exist** (`Role.constituency` included), and the site reads its own database for the most-visited pages.

**Why not "whoever tracks attendance owns the roster"** (the first version's rule)? Attendance only needs to *reference* people. A one-way mirror gives the Senate's Notion the rows it needs for relations, without a second owner.

**How the mirror works**
- A cron job pushes name, seat, constituency, term, voting and current/ended from Wagtail into a Senate Notion database named "Senators (from website: edit on the site)". Those properties are suffixed "(from website)" and are overwritten on every push.
- Rows are never deleted. An ended assignment is marked "Ended", so past attendance relations stay valid.
- The Senate may add its own private columns to these rows, such as notes or personal contact. Those are Notion-owned facts. The push never touches them.
- If someone edits a mirrored column in Notion, the next push overwrites it, and the health page reports the overwrite so the edit can be made on the site instead.
- Until the mirror ships, the Senate's Notion must not keep its own editable list of senators that the public site reads. The site reads only Wagtail.

**Who edits**
- Senate seats and assignments: the VGMIA.
- E-Board: the VP for Rules and Special Projects.
- Graduate Council, Undergraduate Council and Judicial Board: their records officers, once named. Until then their pages say "Roster not listed yet".
- Profile consent and fields: the member, through a signed-in profile form on the site. Their roster officer can record it on their behalf. How members sign in is an open question (RPI single sign-on?).
- Fix the CSV importers and use them only to bootstrap and at term rollover, never as a parallel source.

**Public fields.** Name, seat and term are always public, because they're printed on public agendas. Photo, bio, pronouns, major and office hours require a per-person `Public profile` consent (default off) and show a `Profile reviewed` date. Personal email is never published; contact goes to the seat's role inbox. Without consent, show initials.

**Term rollover.** Assignments carry a `Term`. When a body sets a new term as current, no assignments exist for it, so every seat shows Vacant until new ones are entered. Last year's names never carry over. First-year Senate seats show "To be elected this fall." Each body rolls over on its own schedule.

## 7. What the website must never do, and what it must do

**Never:**
- Offer an upload form that stores files. Box is the only file host.
- Retype or parse the content of a Word document: agenda items, motion text, outcomes as minuted.
- Show item-by-item agendas for a body that writes its agendas in Word.
- Allow editing in Wagtail of anything the Senate's Notion owns (Senate meetings, motions, issues).
- Keep a second editable roster anywhere, including in the Senate's Notion.
- Retype budget numbers that are on an agenda.
- Hand-create EventPages for meetings.
- Host public documents as Notion attachments, or mirror Box PDFs into `/media/`.
- Imply that the E-Board, the Councils or the Judicial Board use Notion, or require them to.
- Show a "Box files" list it can't populate.

**Always:**
- Show a **source line** on every projected item, naming its adapter: "Meeting record: Senate's Notion · synced 12 min ago", "Meeting record: entered on this site by the E-Board Secretary", "Records: files in the Graduate Council Box folder".
- Show logged-in officers deep links to where each item is fixed: "Edit in Box", "Edit in Notion" (Senate only) or "Edit on this site".
- Show the document, not a copy of it: a Box file preview on desktop, "Open (PDF)" first on phones.
- Provide an operator-facing **health page** in the Wagtail admin, organised **by body against the Public Records Standard**. It flags:
  - Adapters B, C and Senate: past meetings with no minutes link after 14 days; meetings within 24 hours with no agenda link (flag from 2 days out); approved minutes not linked 3 days after the approval date.
  - Adapter A: "records last confirmed complete" older than 31 days; no folder shared link.
  - Every body: no records officer named; Box links that fail the weekly status or login-wall check; links that don't match the filename convention; a `.docx` linked with no PDF (warning).
  - Senate: the last successful Notion sync, its last error, missing property IDs (schema drift), and roster-mirror overwrites.
  - Site: expired notices, an overdue term rollover, seats vacant for more than 60 days.
- Say what it can't see: "files in a folder-only body's folder", "whether a PDF is tagged", "whether a file's contents match its record".

## 8. Phased plan

| Phase | Ships | Needs |
|---|---|---|
| **0: Standard and cleanup** | Draft the Public Records Standard with each body's chair. Each body names a records officer and picks an adapter (default A). Create the `Public Records/<Body>/<Term>/` tree on a role account. Rename current-term files and set links to "People with the link". WTG publishes one accessible Word template per body and a one-page "Export a tagged PDF" guide. Remove the Box API code (§5). | Officer buy-in from five bodies. One afternoon of WTG time. |
| **1: every body at the floor** | A `Body` model with an adapter field, and folder embeds for all five bodies (A everywhere, immediately). The roster in Wagtail for all bodies, bootstrapped with the fixed importers. Governing-document pages, start pages, glossary, topic router. Events in Wagtail. A `Meeting` model with a `source` field and the (B) entry form for any body that wants it (likely the E-Board). Health page v1: per-body Standard checks, link checks, "records last confirmed", notices, rollover. | No Notion |
| **2: the Senate's Notion projection** | Locked Senate schema (Meetings, Motions, Issues) synced by property ID. Cron every 15 minutes, with webhooks for an early run. Roster mirror pushed into the Senate's Notion. Admin read-only for Notion-sourced rows. Health page v2: sync status, schema drift, mirror overwrites. A one-time import of any Senate meetings entered under (B), then switch the Senate's `source`. | Senate workspace on a role account. One developer. |
| **2+: Senate options** | If the Senate chooses: agenda items drafted in Notion (§3.5), synced and linked to motions. Public attendance, once the Senate's rules say so. | A Senate decision |
| **Later** | (C) for any other body that asks for it, by copying the Senate's template with a `Body` property. The upload-notification nudge, which gives folder-only bodies a freshness signal. A budget projection, only if finance keeps the figures somewhere structured. | Owners and requests |
| **If the Box API ever appears** | Restore the listing code from the tag. Auto-match files to meetings by the filename regex, so officers paste zero links. Folder-only bodies get automatic Standard checks. `BoxFileCache` returns as a pure cache. Nothing else changes. That is the payoff of adopting the convention now. | IT approval |

## 9. Implications for the three prototypes

**All three**
- **Adapters per body.** Seed a per-body adapter map: the Senate is `notion`, the E-Board is `site` (labelled as an example choice), and the Graduate Council, Undergraduate Council and Judicial Board are `folder`.
- **Source lines by adapter.** Senate items say "Senate's Notion". E-Board items say "entered on this site". Folder-only bodies say "Box folder". The roster says "entered on this site" for every body.
- **Remove anything implying the E-Board, Councils or Judicial Board use Notion.** Their "Edit in Notion" links become "Edit on this site" or "Edit in Box".
- **Agendas as documents.** Agendas and minutes are shown as documents: a Box preview stand-in plus an "Open (PDF)" link. Item-by-item agendas appear only on Senate meeting pages, behind an explicit "Option: if the Senate drafts agendas in Notion" label. The E-Board's agenda is never itemised.
- **Decisions.** Decisions are Senate Motions rows (status from Notion, text in a linked file). Every other body shows "Decisions are recorded in the minutes."
- **Handoff tables per body.** The "How this site works" tables become a per-body table (meeting records, files, decisions, roster, issues), followed by the site-wide rows and a summary of the Public Records Standard.
- **Page counts stay the same:** front-door 10, the-record 9, your-reps 7.

**front-door**
- The meetings page gains "Bodies that publish records as files" (the Graduate Council, Undergraduate Council and Judicial Board), each with its folder and the honest line.
- "Recently decided" shows only Senate motions.
- The funding page's budget stays a quotation.

**the-record**
- **Desk path switch.** The switch has three options: Senate (Notion), Entered on this site (the E-Board's example) and Folder only. The site-entry form loses its "agenda items" extra.
- **Health page.** It gains a "Public Records Standard, by body" table. E-Board rows read like "Minutes for meeting 01 not linked 57 days after (limit 14)". Folder-only rows read "Can't check automatically. Records last confirmed complete: never".
- **Decisions tracker.** It lists only Senate motions, plus a per-body "in the minutes" panel.

**your-reps**
- The roster source becomes "entered on this site" for every body.
- "You said, we did" shows Senate committee issues from the Senate's Notion. Issues owned by E-Board seats are re-owned to Senate seats or dropped.
- The router says which bodies track issues publicly.
- The person page's officer table says that attendance lives in the Senate's Notion for senators only, and that the Senate's Notion keeps a read-only copy of name, seat and term.
