# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Activate virtualenv (required before all commands)
source env/bin/activate

# Run development server
python manage.py runserver

# Run tests
python manage.py test

# Run tests for a single app
python manage.py test home

# Generate migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Verify no pending migrations exist
python manage.py makemigrations --check

# Run Django system checks
python manage.py check

# Docker build & run
docker build -t stugov .
docker run -p 8000:8000 stugov
```

Default settings module: `stugov.settings.dev` (set in `manage.py`).

## Architecture

Wagtail 7.3rc1 CMS on Django 6.0 for the RPI Student Government website. Wagtail extends Django with a page tree, an admin CMS interface, StreamField (structured content blocks), and snippets (reusable content objects without URLs).

### App layout and responsibilities

| App | What it owns |
|-----|-------------|
| `stugov/` | Project config: settings, root URLs, `blocks.py` (shared StreamField blocks), base templates |
| `home` | `HomePage` (singleton landing page), `HomePageQuickLink`, `SiteSettings` (global social/contact config), navigation template tag |
| `branches` | All 5 government branches: `BranchPage`, `MemberListingPage`, `CommitteeIndexPage`/`CommitteePage`, `ClassCouncilIndexPage`/`ClassCouncilPage`, `FlexiblePage`, and the `MemberProfile` snippet |
| `events` | `EventIndexPage` (with JSON API via `RoutablePageMixin`) and `EventPage` |
| `records` | `RecordIndexPage`, `RecordPage` (Box embed primary, Wagtail docs fallback), `RecordDocument` |
| `forms_ext` | `ComplaintFormPage` (extends Wagtail's `AbstractEmailForm`), `FormField` |
| `blog` | `BlogIndexPage`, `BlogPage` |
| `search` | Search view at `/search/` |

### Key architectural patterns

**Shared blocks in `stugov/blocks.py`:** All StreamField block definitions live here to avoid circular imports between apps. Apps import `STANDARD_STREAMFIELD_BLOCKS` or individual block classes from this module.

**MemberProfile is a Snippet, not a Page:** Members don't have their own URLs. They're referenced from multiple pages via Orderable through-models (`BranchMemberPlacement`, `CommitteeMemberPlacement`, `ClassCouncilMemberPlacement`) that carry context-specific roles.

**Through-models with ParentalKey:** Wagtail requires `ParentalKey` (not `ForeignKey`) for inline-editable related objects. Every `Orderable` attached via `InlinePanel` uses `ParentalKey` to enable Wagtail's draft/publish workflow.

**Page hierarchy enforced at model level:** `parent_page_types` and `subpage_types` on each Page model constrain what can be created where. The valid page tree structure is encoded in the models, not just documentation.

**Box as Single Source of Truth for records:** `RecordPage.box_url` is the primary document source. The `box_embed_url` property converts shared links (`/s/...`) to embed links (`/embed/s/...`). Wagtail file attachments (`RecordDocument`) are the fallback.

**SiteSettings via `BaseGenericSetting`:** Social links, contact info, Discord URL, and Box archive URL are stored in a singleton accessed in templates as `{{ settings.home.SiteSettings.field_name }}`. Requires `wagtail.contrib.settings` in `INSTALLED_APPS` and its context processor in `TEMPLATES`.

**RoutablePageMixin on EventIndexPage:** Serves both the HTML calendar page (default) and a JSON API at `api/events/?month=X&year=Y` for the JavaScript calendar widget.

**Access control via `serve()` override:** `RecordPage.serve()` checks `is_public` and redirects unauthenticated users. This controls the Wagtail page only — Box documents have their own permissions.

### Template structure

- `stugov/templates/base.html` — Tailwind CSS (CDN), nav via `{% main_navigation %}` tag, footer via `{% include %}`
- `stugov/templates/includes/` — Shared partials: `navigation.html`, `footer.html`, `member_card.html`, `event_card.html`, `pagination.html`
- `stugov/templates/blocks/` — StreamField block templates: `cta_block.html`, `info_card_block.html`, `document_list_block.html`, `box_embed_block.html`
- Each app has templates at `{app}/templates/{app}/` following Wagtail's convention of `{app_name}/{model_name_snake_case}.html`

### Navigation

Built by `home/templatetags/navigation_tags.py`. The `{% main_navigation %}` inclusion tag walks the page tree: top-level children of the root page (with "Show in menus" checked) become nav items, their children become dropdown entries.

### Data migration for HomePage body

Migration `home/0004` includes a `RunPython` step that converts the original `RichTextField` body content to `StreamField` JSON format. This was necessary because SQLite's `JSON_VALID` constraint rejects raw HTML during column type changes. The pattern: wrap old HTML in `[{"type": "paragraph", "value": "<old html>", "id": "..."}]` before altering the column.

### URL routes

- `/admin/` — Wagtail admin
- `/django-admin/` — Django admin
- `/documents/` — Wagtail document library
- `/search/` — Search view
- `/` — Wagtail page serving (catch-all, must be last in urlpatterns)
