from django.test import TestCase
from django.urls import reverse

from . import data as d


def esc(text):
    """Django escapes apostrophes in rendered HTML."""
    return text.replace("'", "&#x27;")


def url(name, *args):
    return reverse(f"lab:your_reps:{name}", args=args)


class PageTests(TestCase):
    def get(self, path, status=200, **kw):
        response = self.client.get(path, **kw)
        self.assertEqual(response.status_code, status, path)
        return response

    def test_url_mount(self):
        self.assertEqual(url("home"), "/lab/your-reps/")
        self.assertEqual(url("reps", "2028"), "/lab/your-reps/reps/2028/")
        self.assertEqual(url("loop"), "/lab/your-reps/you-said-we-did/")
        self.assertEqual(url("how"), "/lab/your-reps/how-it-works/")

    def test_lab_index_lists_prototype(self):
        self.assertContains(self.get("/lab/"), "Your Representatives")

    def test_home(self):
        r = self.get(url("home"))
        self.assertContains(r, "Prototype layout for testing. Not the official site. Items marked Sample are made up.")
        self.assertContains(r, "Nothing here is connected to Notion")
        self.assertContains(r, "Only the Senate's items would come from Notion.")
        self.assertContains(r, "who represents you, and what they")
        self.assertContains(r, "You can belong to more than one group")
        self.assertContains(r, "No meetings listed this week. The Senate last met 30 Jul 2026.")
        self.assertContains(r, "Speak at a meeting")
        self.assertContains(r, "Written on this site · reviewed 21 Oct 2026")
        self.assertContains(r, "Viewing as a student")
        self.assertContains(r, 'href="#main"')
        self.assertContains(r, 'href="' + url("reps", "2030") + '"')

    def test_reps_class_pages(self):
        for key in ("2027", "2028"):
            r = self.get(url("reps", key))
            self.assertContains(r, "Your senators")
            self.assertContains(r, "Your group has 4 Senate seats")
            self.assertContains(r, "Your Class Council")
            self.assertContains(r, "Represents everyone")
        r = self.get(url("reps", "2028"))
        self.assertContains(r, "Aaron Nam")
        self.assertContains(r, "Seat open")
        self.assertContains(r, "Office hours: Not listed")

    def test_reps_2030_empty_constituency(self):
        r = self.get(url("reps", "2030"))
        self.assertContains(r, "represent everyone")
        self.assertContains(r, "elected in the fall semester")
        self.assertContains(r, "Appointed within three weeks after the fall elections")
        # No four empty seat cards
        self.assertNotContains(r, "Class of 2030 Senator")

    def test_reps_graduate(self):
        r = self.get(url("reps", "graduate"))
        self.assertContains(r, "at least 5 at-large")
        self.assertContains(r, "Your Graduate Council")
        self.assertContains(r, "Melissa Flores")
        self.assertNotContains(r, "Council President:")

    def test_reps_fsl_and_independent_reconciliation(self):
        for key in ("fsl", "independent"):
            r = self.get(url("reps", key))
            self.assertContains(r, "two separate groups")
        r = self.get(url("reps", "fsl"))
        self.assertContains(r, "Fraternity and Sorority Life")
        self.assertContains(r, "Mischa Fedak")

    def test_reps_clubs(self):
        r = self.get(url("reps", "clubs"))
        self.assertContains(r, "not elected by clubs")
        self.assertContains(r, "Club money")
        self.assertContains(r, "$100,000")
        self.assertContains(r, "does not update these figures")
        self.assertContains(r, "Executive Board Agenda 01, 25 Aug 2026")

    def test_person_griffin_oliver(self):
        r = self.get(url("person", "griffin-oliver"))
        self.assertContains(r, "Vice Grand Marshal for Internal Affairs")
        self.assertContains(r, "Class of 2027")
        self.assertContains(r, "Answers to")
        self.assertContains(r, "Source: Union Constitution, Art. VIII §1, §3; Art. X §2; Art. XI §5, §6")
        self.assertContains(r, "opts in")
        self.assertContains(r, "Not reviewed by this member yet")

    def test_person_cee_ray(self):
        r = self.get(url("person", "cee-ray"))
        self.assertContains(r, "Senate Treasurer")
        self.assertContains(r, "Senate–E-Board Liaison")

    def test_people_directory(self):
        r = self.get(url("people"))
        self.assertContains(r, "Everyone A–Z")
        self.assertContains(r, 'href="#letter-K"')
        self.assertContains(r, esc("Roster: entered on this site by each body's roster officer · last change 25 Aug 2026"))
        r = self.get(url("people") + "?q=kim")
        self.assertContains(r, "Jesse Kim")
        self.assertNotContains(r, "Aaron Nam")

    def test_raise_pages(self):
        self.assertContains(self.get(url("raise")), "What's it about?")
        r = self.get(url("raise") + "?topic=dining")
        self.assertContains(r, "Residential Living and Dining")
        self.assertContains(r, "Shruthi Anandraman")
        self.assertContains(r, "Mock for testing. Nothing you type is saved or sent.")
        self.assertNotContains(r, 'name="email"')
        r = self.get(url("raise") + "?topic=rights")
        self.assertContains(r, "Judicial Board")
        self.assertContains(r, "not published yet")
        self.assertNotContains(r, 'name="description"')
        r = self.get(url("raise") + "?topic=dining&for=2028")
        self.assertContains(r, "Also your reps")
        self.assertContains(r, "Aaron Nam")
        self.assertContains(r, "If anyone is in danger, contact RPI Public Safety now.")

    def test_loop(self):
        r = self.get(url("loop"))
        self.assertContains(r, esc("Issues: Senate's Notion, items marked Public"))
        self.assertContains(r, "Nothing on this page is typed into the website")
        self.assertContains(r, "No update since 14 Aug 2026")
        self.assertContains(r, "Updates (3)")
        self.assertContains(r, "RPI controls this")
        r = self.get(url("loop") + "?status=done")
        self.assertContains(r, "Commons dining hall")
        self.assertNotContains(r, "Elevator out of order")

    def test_how(self):
        r = self.get(url("how"))
        self.assertContains(r, "10% of all Union members")
        self.assertContains(r, "40%")
        self.assertContains(r, "Union Constitution, Art. XII")
        self.assertContains(r, "What lives where")
        self.assertContains(r, "Written on this site")
        self.assertContains(r, "two separate groups")
        self.assertContains(r, "Who fills each kind of seat")
        self.assertContains(r, "To be elected this fall")
        self.assertContains(r, 'id="recall"')

    def test_404s(self):
        self.get(url("reps", "1999"), status=404)
        self.get("/lab/your-reps/people/nobody/", status=404)

    def test_forbidden_words_and_one_h1(self):
        paths = [
            url("home"), url("people"), url("raise"), url("loop"), url("how"),
            url("person", "griffin-oliver"),
        ] + [url("reps", k) for k in d.CONSTITUENCIES]
        for path in paths:
            r = self.get(path)
            html = r.content.decode()
            self.assertNotIn("RUGP", html, path)
            self.assertNotIn("Greek-affiliated", html, path)
            self.assertEqual(html.count("<h1"), 1, path)
            self.assertIn('lang="en"', html)
            self.assertIn('role="region" aria-label="Prototype notice"', html)
            # "Greek" appears only inside the reconciliation note
            if "Greek" in html:
                self.assertIn("two separate groups", html, path)


class DataTests(TestCase):
    def test_seat_counts(self):
        self.assertEqual(len(d.senate_voting_seats()), 29)
        self.assertEqual(len(d.eb_voting_seats()), 20)
        senate = [s for s in d.SEATS if s["body"] == "Student Senate" and s["seat"] != "Grand Marshal"]
        self.assertEqual(len(senate), 29)
        by_key = {}
        for s in senate:
            by_key[s["constituency"]] = by_key.get(s["constituency"], 0) + 1
        for key, c in d.CONSTITUENCIES.items():
            self.assertEqual(by_key.get(key, 0), c["senate_seats"], key)

    def test_nobody_opted_in(self):
        for slug, p in d.PEOPLE.items():
            self.assertFalse(p["public_profile"], slug)
            self.assertIsNone(p["profile_reviewed"], slug)
            for f in ("photo", "bio", "pronouns", "major", "office_hours"):
                self.assertIsNone(p[f], f"{slug}.{f}")

    def test_no_role_inboxes(self):
        for s in d.SEATS:
            self.assertIsNone(s["inbox"])

    def test_people_merged_by_name(self):
        samson = d.PEOPLE["samson-kempiak"]
        self.assertGreaterEqual(len(samson["roles"]), 2)
        self.assertEqual(len(d.PEOPLE), len({p["name"] for p in d.PEOPLE.values()}))

    def test_sources_and_issue_whitelist(self):
        self.assertEqual(d.SOURCES["roster"]["line"], "Roster: entered on this site by each body's roster officer · last change 25 Aug 2026")
        self.assertEqual(d.SOURCES["wagtail"]["line"], "Written on this site · reviewed 21 Oct 2026")
        allowed = {
            "id", "public", "title", "topic", "constituencies", "owner_seat", "source", "raised_on",
            "status", "updates", "outcome", "last_update",
        }
        self.assertEqual(len(d.ISSUES), 6)
        for issue in d.ISSUES:
            self.assertEqual(set(issue), allowed)
            self.assertTrue(issue["public"])
            self.assertEqual(issue["raised_on"].year, 2026)
        statuses = {i["status"] for i in d.ISSUES}
        self.assertTrue({"done", "not_possible", "working", "heard"} <= statuses)

    def test_topic_owner_seats_exist(self):
        for t in d.TOPICS:
            if t.get("owner_seat"):
                self.assertIsNotNone(d.seat_by_label(t["owner_seat"]), t["slug"])

    def test_draft_whys_are_allowed(self):
        for r in d.FILL_RULES.values():
            if r.get("draft"):
                self.assertIn(r["draft"], d.DRAFT_WHYS)
        for s in d.SEATS:
            if s["draft"]:
                self.assertIn(s["draft"], d.DRAFT_WHYS)
        for g in d.GLOSSARY:
            if g.get("draft"):
                self.assertIn(g["draft"], d.DRAFT_WHYS)
        for p in d.POWERS:
            if p["not_set_why"]:
                self.assertIn(p["not_set_why"], d.DRAFT_WHYS)

    def test_no_rugp_in_data(self):
        blob = repr((d.GLOSSARY, d.POWERS, d.TOPICS, d.FILL_RULES, d.OWNERSHIP_BY_BODY, d.OWNERSHIP_SHARED))
        self.assertNotIn("RUGP", blob)
        self.assertNotIn("Greek-affiliated", blob)
        self.assertNotIn("Greek", repr((d.GLOSSARY, d.POWERS, d.TOPICS, d.OWNERSHIP_BY_BODY, d.OWNERSHIP_SHARED, d.CONSTITUENCIES)))


class SingleSourceOfTruthTests(TestCase):
    def test_roster_source_line_and_officer_links(self):
        r = self.client.get(url("reps", "2028"))
        self.assertContains(r, esc("Roster: entered on this site by each body's roster officer · last change 25 Aug 2026"))
        self.assertNotContains(r, "Edit on this site")
        self.assertNotIn("lab_officer", r.cookies)

        r = self.client.get(url("reps", "2028") + "?officer=1")
        self.assertContains(r, "Edit on this site")
        self.assertContains(r, "Viewing as an officer (mock)")
        self.assertContains(r, "On the real site these appear only to signed-in officers.")
        cookie = r.cookies["lab_officer"]
        self.assertEqual(cookie.value, "1")
        self.assertEqual(cookie["path"], "/lab/")
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertEqual(cookie["max-age"], "")  # session cookie

    def test_roster_edit_link_is_on_this_site_not_notion(self):
        # The directory shows only the roster source line, so no Notion link can appear.
        r = self.client.get(url("people") + "?officer=1")
        self.assertContains(r, "Edit on this site")
        self.assertNotContains(r, "Edit in Notion")

    def test_officer_cookie_persists_and_can_be_cleared(self):
        self.client.get(url("loop") + "?officer=1")
        r = self.client.get(url("loop"))
        self.assertContains(r, "Edit in Notion")
        r = self.client.get(url("loop") + "?officer=0")
        self.assertNotContains(r, "Edit in Notion")
        self.assertEqual(r.cookies["lab_officer"].value, "")
        r = self.client.get(url("loop"))
        self.assertNotContains(r, "Edit in Notion")

    def test_rollover_preview(self):
        r = self.client.get(url("reps", "2028") + "?term=next")
        self.assertContains(r, "Rollover preview")
        self.assertNotContains(r, "Aaron Nam")
        self.assertNotContains(r, "Nick Castiglione")
        self.assertContains(r, "Seat open")
        # the real data is untouched
        r = self.client.get(url("reps", "2028"))
        self.assertContains(r, "Aaron Nam")

    def test_person_profile_consent(self):
        r = self.client.get(url("person", "griffin-oliver"))
        self.assertContains(r, "opts in")
        self.assertContains(r, "Not reviewed by this member yet")
        self.assertNotContains(r, "What the site publishes")
        r = self.client.get(url("person", "griffin-oliver") + "?officer=1")
        self.assertContains(r, "What the site publishes")
        self.assertContains(r, "Never published")
        self.assertContains(r, "Hidden")

    def test_contact_goes_to_seat_never_personal(self):
        r = self.client.get(url("reps", "2028"))
        self.assertContains(r, "Contact route not set up yet")
        self.assertNotContains(r, "mailto:")
        r = self.client.get(url("person", "aaron-nam"))
        self.assertNotContains(r, "mailto:")

    def test_loop_and_meetings_source_lines(self):
        r = self.client.get(url("loop"))
        self.assertContains(r, esc("Issues: Senate's Notion, items marked Public"))
        self.assertContains(r, "Nothing on this page is typed into the website")
        r = self.client.get(url("how"))
        self.assertContains(r, esc("Meeting record: Senate's Notion · synced 12 min ago"))
        self.assertContains(r, "entered on this site by the E-Board Secretary")
        self.assertContains(r, "Publishes its records as files")
        self.assertContains(r, "Each body&#x27;s records")
        self.assertContains(r, "Written on this site · reviewed 21 Oct 2026")

    def test_per_body_issue_tracking(self):
        r = self.client.get(url("raise") + "?topic=clubs")
        self.assertContains(r, "doesn&#x27;t publish an issue tracker")
        r = self.client.get(url("raise") + "?topic=dining")
        self.assertContains(r, "Tracked publicly?")
        self.assertContains(r, "Senate committees log issues")
        self.assertEqual(d.TOPIC_BODY, {"clubs": "eboard", "grad": "gc", "class": "uc", "rights": "jboard"})
        self.assertEqual(set(d.ISSUE_TRACKING), {"senate", "eboard", "gc", "uc", "jboard"})

    def test_raise_confirmation_depends_on_body(self):
        body = {"description": "The thing is broken and has been for weeks.", "publish": "yes"}
        r = self.client.post(url("raise"), {**body, "topic": "dining"})
        self.assertContains(r, "the Senate's Notion Issues database")
        r = self.client.post(url("raise"), {**body, "topic": "clubs"})
        self.assertContains(r, "Executive Board doesn't publish an issue tracker")
        self.assertNotContains(r, "Notion Issues database")

    def test_senate_copy_note_on_person_page(self):
        r = self.client.get(url("person", "cee-ray") + "?officer=1")
        self.assertContains(r, "read-only copy for attendance")
        self.assertContains(r, "Kept privately in the Senate")

    def test_loop_says_only_senate_tracks_issues(self):
        r = self.client.get(url("loop"))
        self.assertContains(r, "Only the Senate tracks issues publicly")

    def test_issue_owners_are_senate_owned(self):
        owners = {i["owner_seat"] for i in d.ISSUES}
        self.assertFalse(owners & {"Vice President for Club Relations", "Graduate Council representative"})

    def test_notion_only_for_senate_in_ownership_rows(self):
        for row in d.OWNERSHIP_BY_BODY:
            if row["body"] != "Student Senate":
                self.assertNotIn("Notion", repr(row), row["body"])

    def test_working_on_lookup_for_liaison(self):
        r = self.client.get(url("person", "cee-ray"))
        self.assertContains(r, "The club funding request form is confusing")

    def test_no_forms_duplicating_notion_data(self):
        for path in (url("home"), url("reps", "2028"), url("people"), url("loop"), url("how")):
            html = self.client.get(path).content.decode()
            self.assertNotIn("<textarea", html, path)
            self.assertNotIn('type="email"', html, path)


class ContactOrderTests(TestCase):
    def test_office_fallback_when_contact_email_set(self):
        from home.models import SiteSettings

        SiteSettings.objects.create(contact_email="office@example.com")
        r = self.client.get(url("reps", "2028"))
        self.assertContains(r, "Email the Union office")
        self.assertContains(r, "mailto:office@example.com?subject=For%3A%20")
        self.assertContains(r, "This seat doesn&#x27;t have its own role inbox yet.")
        self.assertNotContains(r, "Contact route not set up yet")


class RaiseFormTests(TestCase):
    def test_valid_post(self):
        r = self.client.post(
            url("raise"),
            {
                "topic": "dining",
                "description": "The dining hall is closed when I get out of lab on weekends.",
                "group": "2028",
                "publish": "yes",
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "would be emailed")
        self.assertContains(r, "characters")
        # The description is never echoed back.
        self.assertNotContains(r, "closed when I get out of lab")
        self.assertNotContains(r, "<textarea")

    def test_short_description_shows_error_summary(self):
        r = self.client.post(url("raise"), {"topic": "dining", "description": "too short", "publish": "no"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'role="alert"')
        self.assertContains(r, "problem")
        self.assertContains(r, 'href="#id_description"')
        self.assertContains(r, 'aria-invalid="true"')
        self.assertNotContains(r, "would be emailed")

    def test_missing_publish_choice(self):
        r = self.client.post(
            url("raise"),
            {"topic": "dining", "description": "x" * 30},
        )
        self.assertContains(r, 'role="alert"')
        self.assertContains(r, "Choose yes or no")

    def test_rights_topic_has_no_form_to_post(self):
        r = self.client.post(
            url("raise"),
            {"topic": "rights", "description": "x" * 30, "publish": "no"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "would be emailed")
        self.assertContains(r, "Judicial Board")


class ReviewFixTests(TestCase):
    """Regression tests for the review round."""

    ALL_PAGES = [
        url("home"), url("loop"), url("how"), url("people"), url("raise"),
        url("reps", "2028"), url("reps", "clubs"), url("reps", "graduate"),
        url("person", "mariam-toure"), url("person", "lilu-kaufman"),
    ]

    def test_how_links_agendas_to_box(self):
        r = self.client.get(url("how"))
        self.assertContains(r, "Open agenda (PDF in Box)", count=len(d.MEETINGS))
        for m in d.MEETINGS:
            self.assertContains(r, f'href="{m["agenda_url"]}"')
            self.assertTrue(m["agenda_url"].startswith(d.MOCK_BOX))
        self.assertContains(r, "Minutes not posted")
        self.assertContains(r, "Agenda: Word file in Box, published as PDF")

    def test_no_bare_acronyms(self):
        import re

        for path in self.ALL_PAGES:
            html = self.client.get(path).content.decode()
            for acronym in ("MLC", "VGMIA", "SCEC", "WTG"):
                self.assertIsNone(re.search(rf"\b{acronym}\b", html), (path, acronym))
            # UPAC only ever appears in brackets after the full name.
            for m in re.finditer(r"\bUPAC\b", html):
                self.assertEqual(html[m.start() - 1], "(", path)
        r = self.client.get(url("person", "mariam-toure"))
        self.assertContains(r, "Chair, Multicultural Leadership Council")
        self.assertContains(self.client.get(url("how")), "Rensselaer Union, room 3202")
        self.assertContains(self.client.get(url("how")), "Executive Board (E-Board)")

    def test_clubs_page_has_roster_source_per_grid(self):
        r = self.client.get(url("reps", "clubs"))
        self.assertGreaterEqual(r.content.decode().count('data-source="roster"'), 3)

    def test_vacant_appointed_seat_does_not_link_elections(self):
        # Class Representative (Class of 2030) is appointed, on every reps page.
        r = self.client.get(url("reps", "2030"))
        self.assertContains(r, "How this seat is filled →")
        r = self.client.get(url("reps", "2028"))
        self.assertContains(r, "How elections work →")  # vacant elected Class Senator seats

    def test_issues_heading_not_open(self):
        r = self.client.get(url("reps", "2027"))
        self.assertContains(r, "Issues for this group")
        self.assertNotContains(r, "Open issues for this group")

    def test_scroll_regions_are_labelled(self):
        r = self.client.get(url("how"))
        self.assertContains(r, 'tabindex="0" role="region" aria-labelledby="fill-rules-cap"')
        self.assertContains(r, 'id="fill-rules-cap"')
        self.assertContains(r, 'aria-labelledby="ownership-cap"')

    def test_draft_key_visible_and_no_title_tooltip(self):
        r = self.client.get(url("how"))
        self.assertContains(r, "Draft: confirm</strong> means")
        self.assertNotContains(r, 'title="Not set by the Union Constitution')

    def test_cee_ray_liaison_listed_once_as_eb_seat(self):
        r = self.client.get(url("person", "cee-ray"))
        html = r.content.decode()
        label = "Senate–E-Board Liaison (chosen by the Senate)"
        # once as the seat itself, plus once for each public issue that seat owns
        owned = sum(1 for i in d.ISSUES if i["owner_seat"] == label)
        self.assertEqual(html.count(label), 1 + owned)
        self.assertNotContains(r, "Set by the body's own bylaws")

    def test_how_rendering_details(self):
        r = self.client.get(url("how"))
        html = r.content.decode()
        self.assertNotIn("20 seats..", html)
        self.assertNotIn("(derived)</span>\n.", html)
        self.assertNotIn("( Lauren", html)
        self.assertContains(r, "Executive Board meeting 01")

    def test_rights_topic_links_to_judicial_board_entry(self):
        r = self.client.get(url("raise") + "?topic=rights")
        self.assertContains(r, url("how") + "#judicial-board")

    def test_demo_clock_is_pinned(self):
        from . import views

        self.assertEqual(views._today(), d.DEMO_TODAY)
        r = self.client.get(url("loop"))
        self.assertContains(r, "No update since", count=1)


class UpcomingEventsTests(TestCase):
    """The home 'This week' line reads real EventPages (not meetings)."""

    def make_event(self, title, event_type, days):
        from datetime import timedelta

        from django.utils import timezone
        from wagtail.models import Page

        from events.models import EventPage

        root = Page.get_first_root_node()
        page = EventPage(
            title=title,
            slug=title.lower().replace(" ", "-"),
            start_date=timezone.localdate() + timedelta(days=days),
            event_type=event_type,
            live=True,
        )
        root.add_child(instance=page)
        return page

    def test_non_meeting_event_appears_and_meeting_does_not(self):
        self.make_event("Open Mic Night", "social", 3)
        self.make_event("Private Budget Huddle", "meeting", 3)
        r = self.client.get(url("home"))
        self.assertContains(r, "Open Mic Night")
        self.assertNotContains(r, "Private Budget Huddle")
