# Current site audit

# RPI Student Government site audit

Nothing in the repo or in `db.sqlite3` was modified. The ORM checks ran against a copy of the DB at `/private/tmp/claude-501/-Users-aaron-src-stugov-site/814b13ec-3ac9-47e7-96e9-c31ad2c067e7/scratchpad/dbcopy/db.sqlite3`, which I migrated to current. The real DB was only read with `sqlite3 -readonly`.

Two things appeared on disk while I was auditing, and I did not create them. A `lab` app was added (`lab/`, `"lab"` in `INSTALLED_APPS`, and `path("lab/", include("lab.urls"))` in `stugov/urls.py`). It auto-discovers prototype subpackages under `lab/prototypes/`. Details are in section 6.

## 1. Current information architecture

**The database situation is not obvious.** `stugov/settings/base.py` sets `DATA_DIR` to `./data`, so the default DB is `data/db.sqlite3`. That file is 0 bytes. The populated DB is the gitignored `./db.sqlite3` (1.5 MB, last modified May 3). It is behind the code: `showmigrations` reports `branches.0010` to `0013`, `home.0006` and `0007`, `sso.0001`, and all allauth `account` and `socialaccount` migrations unapplied. Running `DATA_DIR=$PWD python manage.py ...` points at it, and the existing `./media` folder holds its images.

Page tree in `db.sqlite3` (24 pages, all live unless noted):

```
Root
└─ Home (HomePage)                       site: localhost:80, root_page=Home, site_name blank
   ├─ E-Board (BranchPage)               in menu; no children
   ├─ Student Senate (BranchPage)        in menu
   │   ├─ Meet the Senate (MemberListingPage)    in menu, 5 hand-placed members
   │   └─ Senate Committees (CommitteeIndexPage) not in menu
   │        └─ 6 CommitteePages (Engagement & Comms, Web Tech, Academic Affairs, Student Life, Community Relations, Res Life & Dining)
   │           all empty descriptions; only 3 have a chair; Academic Affairs is the only one with show_in_menus
   ├─ Undergraduate Council (BranchPage) in menu; empty (no class councils)
   ├─ Graduate Council (BranchPage)      not in menu; empty
   ├─ Judicial Board (BranchPage)        not in menu; empty
   ├─ Events (EventIndexPage)            in menu
   │   └─ 4 EventPages: Senate (Feb 17 2026), Academic Affairs (Feb 19), Student Life (Feb 17), WMP Vision Board (unpublished)
   └─ Records (RecordIndexPage, slug the-record)  in menu
       └─ 2 RecordPages: Senate Minutes #29, Rensselaer Union Constitution (both with Box links)
Alt Home (AltHomePage, depth 2)         leftover; the model is deleted in code (home.0006)
```

**Nav output.** `{% main_navigation %}` lists the Home children with "Show in menus" set. In order of `path`, that is E-Board, Student Senate, Undergraduate Council, Events, Records. Each gets a hover-only dropdown that repeats the parent as its first entry. Only Student Senate has a dropdown child ("Meet the Senate"). Graduate Council, Judicial Board and the committees are unreachable from the nav. The top-level items are `<div href=...>`, not links, and the dropdown opens on `group-hover` only, so keyboard users cannot open it. The mobile menu is a flat list.

**Hard-coded links to pages that do not exist.** `/complaint-form/` and `/get-involved/` are linked from the footer, and `/complaint-form/` also from the homepage sidebar. There is no ComplaintFormPage or "Get Involved" page in the DB, so both return 404. I confirmed this with the test client. `/the-record/` returns a 302 to the Box URL, because `RecordIndexPage.serve()` redirects whenever `SiteSettings.box_archive_url` is set (it is: `https://rpi.box.com/v/rpisg`). The `RecordPage` pages are therefore unreachable from the index.

**Homepage content.**
- The hero title is "WELCOME TO THE RPI STUDENT GOVERNMENT WEBSITE!".
- All five `HomePageQuickLink` rows have empty URLs and empty `link_page`. The one with a URL is the Instagram link.
- The events block shows "No upcoming events" today (2026-10-21), because every event is from February.

## 2. Content model inventory

| Model | Fields | Good for |
|---|---|---|
| `HomePage` | hero title/subtitle/image/credit; StreamField `body` (heading, paragraph, image, info_cards, CTA); `quick_links` inline (max 6). `get_context` adds `upcoming_events` (5) and `branch_pages` | A generic landing page. Nothing is tied to student tasks. |
| `SiteSettings` (generic setting) | discord/instagram/facebook/twitter URLs; contact_email; office_location; office_hours; footer_text; `box_archive_url` | Global contact and social links. Keep. |
| `BranchPage` | branch_type (senate, eboard, uc, gc, jboard); tagline; image plus credit; StreamField body (standard blocks); contact_email; meeting_schedule | One branch landing page. |
| `MemberListingPage` | intro; `role_configs` inline (`BranchRoleConfig`: role, role_display, tier 0 to 4) | "Meet the X". Pulls people from the global role assignments. |
| `Role` (snippet) | name; positions (for vacancy counts); constituency (a class year, "graduate", "associated", "independent", or "none") | The part that supports "who represents me". Names like `[tag] Name` have the tag stripped for display. |
| `MemberProfile` (snippet) | first/last name; email; photo; class_year; major; bio | People. Not a page, so no URL. |
| `MemberRoleAssignment` (snippet) | member and role | Who holds which role, once, globally. |
| `CommitteeIndexPage` / `CommitteePage` | description; meeting_time/location; chair via `CommitteeRoleConfig`; `CommitteeMemberPlacement` (member plus free-text role) | Committee directory. All six committees are empty. |
| `ClassCouncilIndexPage` / `ClassCouncilPage` | class_year; description; role configs (tiers 0 to 3) | UC class councils. None exist in the DB. |
| `FlexiblePage` | subtitle; StreamField body | The "everything else" page. None exist in the DB. |
| `EventIndexPage` | intro. Uses `RoutablePageMixin` with JSON at `api/events/?month=&year=&branch=` | Calendar page plus API. |
| `EventPage` | start/end date; start/end time; location; description; branch; event_type; recurrence (none, daily, weekly, biweekly, monthly) with end date and note; external_link. Has `next_occurrence()` and `occurrences()` | Meetings and events. Recurrence is already modelled, but the DB doesn't use it. |
| `RecordIndexPage` | intro. `get_context` queries `BoxFileCache` with `type`, `folder` and `q` filters | Meant as a filterable Box file list, but a redirect hides it. |
| `BoxFileCache` | box_file_id; name; record_type (inferred from filename); folder path; shared_link; size; modified_at | Cache for Box files, filled by `python manage.py sync_box_records`. It needs `BOX_CLIENT_ID`, `BOX_CLIENT_SECRET` and `BOX_ENTERPRISE_ID`, and the DB has 0 rows. |
| `RecordPage` / `RecordDocument` | record_type; date_published; academic_year; summary; body; branch; `is_public` (login redirect in `serve()`); box_url (embed URL derived); inline Wagtail docs | Per-document pages. Effectively dead code. |
| `ComplaintFormPage` / `FormField` | Wagtail form builder; intro; thank_you_text; privacy_notice; email on submission; `parent_page_types = [HomePage]` | A working generic form engine, but no instance exists. |
| `BlogIndexPage` / `BlogPage` | author (default "John Doe"); date; intro; body. No `parent_page_types` | Unfinished. Not in `HomePage.subpage_types` as a real child and has no instances. |
| `search` view | `Page.objects.live().search()`, paginated, 10 per page | The template is the unstyled Wagtail starter. |
| `sso` | `OIDCGroupMapping`, `OIDCManagedGroupMembership` | Admin login only (see section 5). |

## 3. Honest assessment

**(a) Student who wants to get something done.**
- **Find my senator:** The only per-person view is the "Meet the Senate" page, and the DB has 5 people on it. `Role.constituency` exists but nothing uses it. No search by class, no "I'm a class of 2028 student, who represents me?". Cards have no email, office hours or contact method.
- **Get funding / request money:** Nothing. There is no funding model, process or page. The only forms are the (nonexistent) complaint form.
- **Report a problem:** The complaint form is linked in two places and returns 404.
- **See what passed:** There is no legislation, vote or resolution model. The records are Box files, and `/the-record/` bounces the student off the site to Box.
- **Find meetings:** The calendar works, but the content is eight months old. There is no "next Senate meeting" shortcut.
- **General issues:** The nav is organised by branch (the org chart), and the homepage is a hero plus five branch cards. A student has to know the structure to use it. Social links and the contact section are the most reliable parts. Search is unstyled, and the dropdown is inaccessible by keyboard.

**(b) Student-government member who publishes and hands off.**
- **Publish agendas and minutes:** The intended path is "drop it in Box", which is good for handoff. But the sync command needs credentials and has never populated the cache, and the site shows no agenda-to-minutes relationship. The Wagtail document attachment and Box-embed paths are alternative routes.
- **Update rosters:** The CSV importers exist and the three-model structure (profile, role, assignment) is sound. But `members.csv` and `roles.csv` don't match the importers (section 4), the people are the real spring 2026 roster, and the DB roster was dropped by the `branches.0013` migration.
- **Announce things:** There is no news or announcements content type. The blog models are incomplete and `BlogPage.author` defaults to "John Doe".
- **Turnover:** There are real strengths: the role and assignment snippets, `Role.positions` driving vacancies, and Box as the source of truth for documents. The weaknesses are that site state lives in a gitignored SQLite file, every committee and branch page is empty, and there is no handoff documentation. `tailwind.css` is not committed, so a new officer cloning the repo gets an unstyled site until they run npm.

## 4. Reusable assets and dead weight

**Keep:**
- The Role, MemberProfile and MemberRoleAssignment trio. It is the right model for "who represents me", especially with `Role.constituency`.
- `EventPage` and its recurrence logic, plus the JSON API (the recurrence helpers have no tests, but are working).
- `SiteSettings` and `stugov/blocks.py`.
- The Box pieces: `box_embed_url`, `BoxFileCache`, `sync_box_records`, `box_archive_url`.
- `ComplaintFormPage` as the engine for report-a-problem or funding-request forms.
- OIDC SSO for the admin.
- `members.csv` (51 rows: 30 senate, 21 eboard, 49 distinct names; 44 have a class year; none have an email or major), `roles.csv` (40 roles) and the five `import_*` commands.

**Fix before use:**
- `import_members` requires `rcs_id`. `members.csv` has `email` and `branch`, and a semicolon-separated `roles` column. `import_assignments` wants `rcs_id,role`, so it fails on the same file.
- `import_roles` wants `name,positions,constituency`. `roles.csv` has `branch,tier,constituency_class,constituency_fsl`. A dry run succeeds (40 roles) but silently ignores the constituency data.

**Dead or weak:**
- `home_althomepage` and the `Alt Home` page (model gone, row remains).
- `RecordPage`, `RecordDocument` and the record-type taxonomy (shadowed by the Box redirect).
- `BlogPage` as written.
- The `senate_members.csv` format (legacy, gitignored, 32 rows).
- The homepage quick-link rows (all empty).
- Hard-coded `/get-involved/`, `/complaint-form/` and `/the-record/` links.
- `stugov/static/css/stugov.css` and `stugov/static/js/stugov.js` are both 0 bytes.

## 5. Technical constraints

- **Tailwind is built, not CDN.** `base.html` comments say CDN, but it links `static/css/tailwind.css`. The file is gitignored and not built, `node_modules` is absent, and `package.json` pins `tailwindcss ^3` with the typography plugin. Until `npm install && npm run build` runs, existing templates render unstyled. The Dockerfile builds it in a node stage. Node 26 is installed locally.
- **Design tokens** (`tailwind.config.js`): `rpi-red #d6001c`, `rpi-red-dark #a50015`, `stugov-dark #1a1a2e`, `stugov-gray #4a4a68`. Font is Geist via Google Fonts. The typography plugin styles links red.
- **No public authentication.** allauth is used as an OIDC relying party only (`SOCIALACCOUNT_ONLY`), with the provider id `campus` and `OIDC_ENABLED` off by default. Login is routed to Wagtail admin only when it is on. Group claims map to Wagtail groups through the `OIDCGroupMapping` snippet. There is no student-facing login, so anything like "my petitions" needs new work. `RecordPage.is_public=False` redirects to the Wagtail login, which students can't use.
- **Box:** SDK `boxsdk>=3.12`, client-credentials (CCG) auth through environment variables, no webhook, cron needed.
- **Platform:** Wagtail 7.3rc1, Django 6.0, SQLite, Python 3.13 locally and 3.12 in Docker. Production runs gunicorn behind nginx via docker-compose. Search uses the Wagtail database backend. Email goes to the console in dev. The `OIDC_*` env vars are documented in `README.md`.
- **Structural limits:** page types are bound together by `parent_page_types`/`subpage_types`. `MemberProfile` has no URL, so per-person pages need either a view or a new Page type. The `MemberListingPage` tier choices are hard-coded in model classes (`BranchRoleConfig.TierChoices` etc.). `Role.constituency` choices are computed from the current year.
- **Tests:** home 5, branches 2, sso 36 `def test` hits. Nothing for events or records.
- **Venv trap:** `env/bin/activate` hard-codes `/Users/aaron/Documents/dev/stugov-site/env`, so `source env/bin/activate` leaves `python` on a broken pyenv shim. Use `env/bin/python` directly.

## 6. Facts a prototype builder needs

**Run it:**
```bash
cd /Users/aaron/src/stugov-site
DATA_DIR=$PWD env/bin/python manage.py migrate   # WRITES to ./db.sqlite3; prefer a copy (below)
DATA_DIR=<dir containing db.sqlite3> env/bin/python manage.py runserver
```
To avoid touching the real DB, copy it first (what I did): `mkdir $S/dbcopy && cp db.sqlite3 $S/dbcopy/ && DATA_DIR=$S/dbcopy env/bin/python manage.py migrate`. After migrating, the copy has 24 pages, 5 members, 0 roles, 0 assignments, and `manage.py check` is clean. A fresh DB needs `createsuperuser` and the importers. Site hostname in the DB is `localhost`, so use `localhost` (not `127.0.0.1`) or add a Site.

**Verified with Django's test client (no server):** `/` 200, `/events/` 200, `/student-senate/` 200, `/student-senate/members-of-senate/` 200, `/search/?query=senate` 200, `/events/api/events/?month=2&year=2026` 200, `/the-record/` 302, `/complaint-form/` 404, `/get-involved/` 404.

**Base template blocks** (`stugov/templates/base.html`): `title`, `title_suffix`, `extra_css`, `body_class`, `content`, `extra_js`. Nav and footer come from `{% main_navigation %}` and `{% include "includes/footer.html" %}`, neither overridable. Loads: `static wagtailcore_tags wagtailuserbar navigation_tags wagtailsettings_tags`. Settings are available as `{{ settings.home.SiteSettings.<field> }}`. Reusable partials: `includes/member_card.html` (`member`, `roles`, `featured`), `event_card.html`, `vacancy_card.html`, `pagination.html`.

**Lab scaffold already on disk:** `lab/prototypes/<name>/` needs `META = {name, thesis, recommended}` in `__init__.py` and `urls.py` with `urlpatterns`. They mount at `/lab/<slug>/` with underscores turned into hyphens, templates go in `lab/templates/lab/<slug>/`, and `/lab/` lists them. The index template is standalone with inline CSS and does not extend `base.html`. Prototype templates can still extend it, but they'd need the built Tailwind CSS.

**Querying real data from a view:**
```python
from django.utils import timezone
from wagtail.models import Page
from branches.models import MemberProfile, Role, MemberRoleAssignment, BranchPage, CommitteePage
from events.models import EventPage
from records.models import BoxFileCache, RecordPage
from home.models import SiteSettings, _upcoming_by_next_occurrence

today = timezone.now().date()
site = SiteSettings.load(request_or_site=request)
people = MemberRoleAssignment.objects.select_related("member", "role")
mine = people.filter(role__constituency="2028")         # who represents a class
events = EventPage.objects.live()                       # next_occurrence(after=today), occurrences(y, m)
upcoming = _upcoming_by_next_occurrence(list(events), today, limit=10)
files = BoxFileCache.objects.filter(record_type="minutes").order_by("-modified_at")
branch = BranchPage.objects.live().get(branch_type="senate")
```
`MembershipDisplay.get_tiered_placements()` on a `MemberListingPage`, `CommitteePage` or `ClassCouncilPage` returns the tiered roster, with a trailing "Vacancies" tier. Role display names come from `Role.get_display_name()`. Event `branch` and `event_type` choices are in `events/models.py`. `Role.constituency` values are year strings, "graduate", "associated", "independent" and "none". `MemberProfile.photo` is a Wagtail image (use the `{% image %}` tag). Images live in `./media/images`, so serve with `DATA_DIR=$PWD` or copy the media dir too.

**Seed data for realistic prototypes:** `members.csv` and `roles.csv` give real names and roles but need a column rename or a small custom loader as noted in section 4. They are untracked, as are the two agenda PDFs in the repo root (`#12 07_30_26 57th Student Senate Meeting Agenda-1.pdf`, `FY27 Agenda 1 - August 25, 2026.pdf`). There is nothing structured for legislation, votes, budgets or "you said, we did", so any prototype of those will need plain Python data or a new model.