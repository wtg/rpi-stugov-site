# Site redesign exploration

Branch `redesign/explore`. Three alternate site structures, built as clickable prototypes so they can be compared before committing to one. Nothing here touches the live page tree, models or migrations.

## Try the prototypes

```bash
env/bin/python manage.py runserver
```

Open <http://localhost:8000/lab/>. Each prototype has a "What's real?" disclosure in its top banner, and `?officer=1` reveals the officer-only "Edit in Box / Notion / this site" links.

| Prototype | Thesis | Start at |
|---|---|---|
| **Front Door** (recommended) | Task-first: six plain-language verbs, then "this week", then your reps. The org chart sits one level down. | `/lab/front-door/` |
| **Public Record + Desk** | Transparency first: dense meeting, motion and money listings, plus an officer desk and a health page that checks every body against the Public Records Standard. | `/lab/the-record/` |
| **Your Representatives** | Constituency first: pick who you are, see the seats that represent you (vacancies included), and route an issue to the right seat. | `/lab/your-reps/` |

Code lives in `lab/prototypes/<name>/` and `lab/templates/lab/<slug>/`. Tests: `env/bin/python manage.py test lab`.

## Read in this order

1. [workshop-report.md](workshop-report.md): the problem, four concepts, judge scores, the recommended philosophy, how to test with students and secretaries, and open questions (§8, §11).
2. [data-architecture.md](data-architecture.md): single source of truth with no Box API, Word-authored documents, and per-body tooling. Covers the Public Records Standard, the adapter menu, the Box filename convention, the Senate's Notion projection and roster ownership.
3. [specs/](specs/): the build spec for each prototype. Section 0B overrides later sections.
4. Background: [concepts/](concepts/) (four competing proposals), [judges.md](judges.md), [research/](research/) (constitution digest, site audit, peer sites, agendas and the infrastructure plan).

`reference/union-constitution.tex` is a copy of the Union constitution, so tooling can read it from inside the repo.
