import re
from datetime import date, datetime, timezone as dt_timezone
from unittest import mock

from django.test import TestCase
from django.urls import reverse

from . import data, logic

NS = "lab:front_door:"


def u(name, *args):
    return reverse(NS + name, args=args)


ALL_PAGES = [
    ("home", []),
    ("issue_index", []),
    ("issue_topic", ["dining"]),
    ("issue_topic", ["rights"]),
    ("reps_index", []),
    ("reps", ["2028"]),
    ("reps", ["2030"]),
    ("reps", ["fsl"]),
    ("meetings", []),
    ("meeting", ["senate", "57", 12]),
    ("meeting", ["eboard", "fy27", 1]),
    ("funding", []),
    ("take_part", []),
    ("about", []),
]


class SmokeTests(TestCase):
    def test_every_page_renders(self):
        for name, args in ALL_PAGES:
            with self.subTest(name=name, args=args):
                self.assertEqual(self.client.get(u(name, *args)).status_code, 200)

    def test_every_topic_and_rep_key_renders(self):
        for t in data.TOPICS:
            with self.subTest(topic=t["slug"]):
                self.assertEqual(self.client.get(u("issue_topic", t["slug"])).status_code, 200)
        for key in data.REPS_META:
            with self.subTest(reps=key):
                self.assertEqual(self.client.get(u("reps", key)).status_code, 200)

    def test_mounted_under_lab(self):
        self.assertEqual(u("home"), "/lab/front-door/")
        self.assertEqual(u("meeting", "senate", "57", 12), "/lab/front-door/meetings/senate/57/12/")
        self.assertContains(self.client.get("/lab/"), "Front Door")

    def test_404s(self):
        self.assertEqual(self.client.get("/lab/front-door/your-reps/1999/").status_code, 404)
        self.assertEqual(self.client.get("/lab/front-door/meetings/senate/57/99/").status_code, 404)
        self.assertEqual(self.client.get("/lab/front-door/raise-an-issue/nope/").status_code, 404)

    def test_one_h1_and_landmarks_on_every_page(self):
        for name, args in ALL_PAGES:
            with self.subTest(name=name, args=args):
                html = self.client.get(u(name, *args)).content.decode()
                self.assertEqual(len(re.findall(r"<h1[\s>]", html)), 1)
                for tag in ("<header", "<main", "<footer", 'aria-label="Main"', "Skip to main content", '<html lang="en">'):
                    self.assertIn(tag, html)
                self.assertIn("<details", html)  # mobile menu, no JS

    def test_no_skipped_heading_levels(self):
        for name, args in ALL_PAGES:
            with self.subTest(name=name, args=args):
                html = self.client.get(u(name, *args)).content.decode()
                levels = [int(n) for n in re.findall(r"<h([1-6])[\s>]", html)]
                for prev, cur in zip(levels, levels[1:]):
                    self.assertLessEqual(cur, prev + 1, f"h{prev} then h{cur}")

    def test_banner_on_every_page(self):
        for name, args in ALL_PAGES:
            with self.subTest(name=name, args=args):
                self.assertContains(self.client.get(u(name, *args)), "Prototype layout for testing. Not the official site.")
        self.assertContains(self.client.get(u("home")), "Prototype")

    def test_nav_marks_current_page(self):
        html = self.client.get(u("funding")).content.decode()
        self.assertRegex(html, r'href="/lab/front-door/funding/"[^>]*aria-current="page"')

    def test_search_form_is_get_to_real_search(self):
        html = self.client.get(u("home")).content.decode()
        self.assertIn('action="/search/"', html)
        self.assertIn('name="query"', html)
        self.assertIn('for="site-search"', html)

    def test_no_post_forms(self):
        for name, args in ALL_PAGES:
            html = self.client.get(u(name, *args)).content.decode().lower()
            self.assertNotIn('method="post"', html)


class ContentTests(TestCase):
    def test_reps_2030_fallback(self):
        r = self.client.get(u("reps", "2030"))
        self.assertContains(r, "represent everyone")
        self.assertContains(r, "elected in the fall semester")
        self.assertContains(r, "Vacant: appointed within three weeks after the fall elections")

    def test_reps_fsl_reconciliation(self):
        r = self.client.get(u("reps", "fsl"))
        self.assertContains(r, "Fraternity and Sorority Life")
        self.assertContains(r, "two separate groups")

    def test_reps_graduate_and_clubs(self):
        self.assertContains(self.client.get(u("reps", "graduate")), "Graduate Council")
        self.assertContains(self.client.get(u("reps", "clubs")), "Clubs don't elect them")

    def test_vacant_seat_shows_fill_rule(self):
        r = self.client.get(u("reps", "2028"))
        self.assertContains(r, "Vacant seat")
        self.assertContains(r, "How this seat gets filled")
        self.assertContains(r, "Source: Union Constitution, Art. XI")

    def test_naming_rules(self):
        for name, args in ALL_PAGES:
            with self.subTest(name=name, args=args):
                html = self.client.get(u(name, *args)).content.decode()
                self.assertNotIn("RUGP", html)
        for name in ("home", "about"):
            html = self.client.get(u(name)).content.decode()
            self.assertNotIn("Greek & Independent", html)
            self.assertNotIn("Greek &amp; Independent", html)

    def test_take_part(self):
        r = self.client.get(u("take_part"))
        self.assertContains(r, "10%")
        self.assertContains(r, "Judicial Board")
        self.assertContains(r, "Union Constitution, Art. XII")
        self.assertContains(r, "How to file")
        self.assertContains(r, "(derived)")
        self.assertNotContains(r, 'class="btn')  # no start buttons on this page
        self.assertContains(r, "Right now the Class of 2028 has 2 vacant Senate seats")

    def test_meeting_senate(self):
        r = self.client.get(u("meeting", "senate", "57", 12))
        self.assertContains(r, "29 voting seats")
        self.assertContains(r, "13 needed (agenda lists 19 voting members)")
        self.assertContains(r, "Agenda link not added to the meeting record yet.")
        self.assertContains(r, "No motions recorded for this meeting in the Senate's Notion.")
        self.assertContains(r, "20 filled on the 30 Jul 2026 roster · 5 vacant · 4 first-year seats to be elected this fall")
        self.assertContains(r, "Senate Treasurer")

    def test_meeting_eboard(self):
        r = self.client.get(u("meeting", "eboard", "fy27", 1))
        self.assertContains(r, "15 to 20 voting seats")
        self.assertContains(r, "The Executive Board records its decisions in its minutes.")
        # the E-Board agenda is shown as the document; its items are never retyped as chips
        self.assertContains(r, "Prototype only: what this document says")
        self.assertNotContains(r, "Outcome not recorded yet")

    def test_meeting_days_since_is_computed(self):
        with mock.patch.object(logic, "today", return_value=date(2026, 10, 21)):
            r = self.client.get(u("meeting", "senate", "57", 12))
        self.assertContains(r, "Minutes link not added yet (83 days since meeting)")

    def test_home_this_week_empty_state(self):
        with mock.patch.object(logic, "today", return_value=date(2026, 10, 21)):
            r = self.client.get(u("home"))
        self.assertContains(r, "No Senate or Executive Board meetings are listed for the next 7 days.")
        self.assertContains(r, "See past meetings and records")

    def test_home_this_week_with_meeting(self):
        with mock.patch.object(logic, "today", return_value=date(2026, 7, 28)):
            r = self.client.get(u("home"))
        self.assertContains(r, "Thu 30 Jul 2026")
        self.assertContains(r, "Anyone can speak at the start and end.")
        self.assertNotContains(r, "No Senate or Executive Board meetings are listed")

    def test_home_open_seat_count_is_computed(self):
        n = len([s for s in data.SEATS if s["holder"] is None and s["body"] in ("senate", "eboard")])
        self.assertContains(self.client.get(u("home")), f"{n} seats are open right now.")

    def test_home_decisions_are_badged_samples(self):
        r = self.client.get(u("home"))
        self.assertContains(r, "Recently decided")
        self.assertContains(r, 'class="pill-sample"')
        self.assertEqual(r.content.decode().count('data-source="motions"'), 1)
        self.assertContains(r, "Motion text (PDF in Box)")

    def test_notice_only_when_unexpired(self):
        from datetime import timedelta

        live = {"text": "Office closed Monday", "expires": date(2026, 10, 21) + timedelta(days=14)}
        with mock.patch.object(data, "NOTICE", live), mock.patch.object(logic, "today", return_value=date(2026, 10, 21)):
            self.assertContains(self.client.get(u("home")), "Office closed Monday")
        stale = {"text": "Office closed Monday", "expires": date(2026, 10, 1)}
        with mock.patch.object(data, "NOTICE", stale), mock.patch.object(logic, "today", return_value=date(2026, 10, 21)):
            self.assertNotContains(self.client.get(u("home")), "Office closed Monday")

    def test_topic_pages(self):
        r = self.client.get(u("issue_topic", "dining"))
        self.assertContains(r, "Who handles this")
        self.assertContains(r, "If nothing changes")
        self.assertContains(r, "Contact address to be confirmed")
        self.assertContains(r, "If anyone is in danger, contact RPI Public Safety now.")
        self.assertNotContains(self.client.get(u("issue_topic", "website")), "If nothing changes")
        self.assertContains(self.client.get(u("issue_topic", "rights")), "How to bring a case to the Judicial Board")

    def test_topic_filter_is_get(self):
        r = self.client.get(u("issue_index"), {"q": "dining"})
        self.assertContains(r, "Problem with dining or meal plans?")
        self.assertNotContains(r, "Off-campus or Troy community issue?")

    def test_funding(self):
        r = self.client.get(u("funding"))
        self.assertContains(r, "Quoted from Executive Board Agenda 01")
        self.assertNotContains(r, "% left")
        self.assertContains(r, "Draft for testing.")
        self.assertContains(r, "$126,635.47")
        self.assertContains(r, "Not applicable")
        self.assertContains(r, "Start request (link to be confirmed)")

    def test_about(self):
        r = self.client.get(u("about"))
        for text in ("What lives where", "Upload New Version", "Written on this site", "To publish a meeting", "Roster not listed yet",
                     "Each body's records", "The Public Records Standard", "accessibility tags"):
            self.assertContains(r, text)
        self.assertContains(r, 'id="how-this-site-works"')
        self.assertContains(r, 'id="get-involved"')
        self.assertContains(r, 'id="funding-owner"')
        self.assertNotContains(r, "RUGP")

    def test_meetings_index(self):
        r = self.client.get(u("meetings"))
        self.assertContains(r, "Box folder embed goes here")
        self.assertContains(r, 'id="decided"')
        self.assertContains(r, 'id="files"')
        self.assertContains(r, "Past meetings")
        self.assertContains(r, "days since meeting")

    def test_no_raw_template_syntax_on_any_page(self):
        for name, args in ALL_PAGES:
            with self.subTest(name=name, args=args):
                html = self.client.get(u(name, *args)).content.decode()
                self.assertNotIn("{#", html)
                self.assertNotIn("#}", html)
                self.assertNotIn("{%", html)
                self.assertNotIn("%}", html)
                self.assertNotIn("{{", html)

    def test_no_multiline_hash_comments_in_templates(self):
        # {# #} comments end at the line break; a multi-line one prints raw.
        from pathlib import Path

        root = Path(__file__).resolve().parents[2] / "templates" / "lab" / "front-door"
        for f in root.glob("*.html"):
            for n, line in enumerate(f.read_text().splitlines(), 1):
                if "{#" in line:
                    self.assertIn("#}", line, f"{f.name}:{n}")

    def test_speaking_rule_follows_each_agenda(self):
        senate = self.client.get(u("meeting", "senate", "57", 12))
        self.assertContains(senate, "during the Invitation to Speak at the start and end of the meeting")
        eboard = self.client.get(u("meeting", "eboard", "fy27", 1))
        self.assertContains(eboard, "during the Invitation to Speak at the end of the meeting")
        self.assertNotContains(eboard, "start and end")
        self.assertContains(eboard, "Draft: confirm")
        self.assertContains(eboard, "Confirm with: E-Board bylaws")
        with mock.patch("django.utils.timezone.now", return_value=datetime(2026, 8, 25, 12, 0, tzinfo=dt_timezone.utc)):
            card = self.client.get(u("home"))
        self.assertContains(card, "Anyone can speak at the end.")
        self.assertNotContains(card, "Anyone can speak at the start and end.")

    def test_speak_phrase_is_computed_from_section_positions(self):
        self.assertEqual(logic.speak_phrase(data.MEETINGS[0]), "at the start and end")
        self.assertEqual(logic.speak_phrase(data.MEETINGS[1]), "at the end")
        self.assertIsNone(logic.speak_phrase({"sections": [{"title": "Reports"}]}))

    def test_topic_speaking_line_names_the_owning_body(self):
        clubs = self.client.get(u("issue_topic", "clubs"))
        self.assertContains(clubs, "speak at the next Executive Board meeting")
        self.assertContains(clubs, "Invitation to Speak at the end of the meeting")
        self.assertContains(clubs, u("meeting", "eboard", "fy27", 1))
        dining = self.client.get(u("issue_topic", "dining"))
        self.assertContains(dining, "speak at the next Student Senate meeting")
        self.assertContains(dining, "Invitation to Speak at the start and end of the meeting")

    def test_vacant_seat_links_match_how_the_seat_is_filled(self):
        run, appointed = u("take_part") + "#run", u("take_part") + "#appointed"
        # a vacant elected Senate seat: run for office
        r = self.client.get(u("reps", "2028"))
        self.assertContains(r, f'href="{run}">Run for office')
        # vacant appointed E-Board seats: never "Run for office"
        for key in ("graduate", "clubs"):
            with self.subTest(key=key):
                r = self.client.get(u("reps", key))
                self.assertContains(r, f'href="{appointed}">How appointments work')
        html = self.client.get(u("reps", "clubs")).content.decode()
        self.assertNotIn("Run for office", html)
        # the at-large card is on every reps page and is appointed
        self.assertNotIn(f'href="{run}">Run for office', self.client.get(u("reps", "independent")).content.decode().split("Also representing everyone")[1])
        # unit check across every vacant seat
        for seat in data.SEATS:
            action = logic.seat_action(seat)
            if seat["fill_rule"] == "eb_appointed":
                self.assertEqual(action["label"], "How appointments work")
            elif seat["fill_rule"] == "eb_peer":
                self.assertIsNone(action)

    def test_peer_seat_names_who_chooses(self):
        r = self.client.get(u("meeting", "eboard", "fy27", 1))
        self.assertContains(r, "chosen by the Undergraduate Council")


class TimezoneTests(TestCase):
    def test_today_is_eastern_not_utc(self):
        # 00:30 UTC on 31 Jul is 8:30 PM ET on 30 Jul
        with mock.patch("django.utils.timezone.now", return_value=datetime(2026, 7, 31, 0, 30, tzinfo=dt_timezone.utc)):
            self.assertEqual(logic.today(), date(2026, 7, 30))

    def test_senate_meeting_stays_in_this_week_during_the_meeting(self):
        with mock.patch("django.utils.timezone.now", return_value=datetime(2026, 7, 31, 0, 30, tzinfo=dt_timezone.utc)):
            r = self.client.get(u("home"))
            html = r.content.decode()
            week = html.split('id="this-week"')[1].split("</ul>")[0]
            self.assertIn("Student Senate", week)
            self.assertIn('datetime="2026-07-30"', week)
            self.assertNotContains(r, "No Senate or Executive Board meetings are listed")
            self.assertContains(self.client.get(u("meetings")), 'datetime="2026-07-30"')

    def test_days_since_uses_the_eastern_date_in_the_evening(self):
        # 8:30 PM ET on 21 Oct is already 22 Oct in UTC
        with mock.patch("django.utils.timezone.now", return_value=datetime(2026, 10, 22, 0, 30, tzinfo=dt_timezone.utc)):
            r = self.client.get(u("meeting", "senate", "57", 12))
        self.assertContains(r, "(83 days since meeting)")
        self.assertNotContains(r, "(84 days since meeting)")


class SingleSourceOfTruthTests(TestCase):
    def test_source_lines_on_meeting(self):
        r = self.client.get(u("meeting", "senate", "57", 12))
        self.assertContains(r, "Meeting record: Senate's Notion · synced 12 min ago", html=True)  # html=True: the apostrophe is escaped
        self.assertContains(r, "Document: Box")

    def test_officer_links_toggle(self):
        url = u("meeting", "senate", "57", 12)
        self.assertNotContains(self.client.get(url), "Edit in Notion")
        r = self.client.get(url, {"officer": "1"})
        self.assertContains(r, "Edit in Notion")
        self.assertContains(r, "On the real site these links appear only to signed-in officers.")
        self.assertIn("lab_officer", r.cookies)
        self.assertEqual(r.cookies["lab_officer"].value, "1")
        self.assertEqual(r.cookies["lab_officer"]["path"], "/lab/")
        self.assertEqual(r.cookies["lab_officer"]["samesite"], "Lax")
        # the cookie keeps officer mode on for later pages
        self.assertContains(self.client.get(url), "Edit in Notion")
        # ?officer=0 turns it off and clears the cookie
        r = self.client.get(url, {"officer": "0"})
        self.assertNotContains(r, "Edit in Notion")
        self.assertEqual(r.cookies["lab_officer"].value, "")
        self.assertNotContains(self.client.get(url), "Edit in Notion")

    def test_officer_mode_reveals_no_extra_data(self):
        url = u("about")
        plain = self.client.get(url).content.decode()
        self.client.get(url, {"officer": "1"})
        officer = self.client.get(url).content.decode()
        strip = lambda h: re.sub(r"\s·\s<a [^>]*>(?:Edit in [A-Za-z]+|Add the link in Notion|Open in Box|Edit on this site|Add the link on this site|Share it in Box)</a>\s<span class=\"fd-xs\">\(mock link\)</span>", "", h)
        banner = re.compile(r"<div class=\"banner\">.*?</div>", re.S)
        self.assertEqual(banner.sub("", strip(officer)), banner.sub("", plain))

    def test_toggle_link_in_banner(self):
        self.assertContains(self.client.get(u("home")), "Viewing as a student · <a href=\"?officer=1\">Show officer links</a>", html=False)
        self.assertContains(self.client.get(u("home"), {"officer": "1"}), "Viewing as an officer (mock)")

    def test_wagtail_pages_end_with_wagtail_source_line(self):
        for name, args in [("home", []), ("issue_index", []), ("issue_topic", ["dining"]), ("funding", []), ("take_part", []), ("about", [])]:
            with self.subTest(name=name):
                html = self.client.get(u(name, *args)).content.decode()
                main = html.split("</main>")[0]
                self.assertIn('data-source="wagtail"', main)
                self.assertIn("Written on this site · reviewed 21 Oct 2026", main)

    def test_quoted_budget_source_has_open_in_box_for_officers(self):
        r = self.client.get(u("funding"), {"officer": "1"})
        self.assertContains(r, "Open in Box")
        self.assertContains(r, "https://rpi.box.com/")

    def test_sources_built_from_sync(self):
        s = data.build_sources({**data.SYNC, "notion_minutes_ago": 3})
        self.assertEqual(s["meeting_senate"]["line"], "Meeting record: Senate's Notion · synced 3 min ago")
        self.assertEqual(data.SOURCES["file"]["line"], "Document: Word file in Box, published as PDF · link checked 19 Oct 2026")
        self.assertEqual(data.SOURCES["meeting_eboard"]["line"], "Meeting record: entered on this site by the E-Board Secretary · updated 24 Aug 2026")
        self.assertEqual(data.SOURCES["roster"]["line"], "Roster: entered on this site by each body's roster officer · last change 25 Aug 2026")
        for old in ("meeting", "agenda_items", "file_missing", "decision"):
            self.assertNotIn(old, data.SOURCES)

    def test_box_embed_logic(self):
        folder = {"label": "x", "path": "p/", "shared_url": "https://rpi.box.com/s/abc123"}
        with mock.patch.dict(data.BOX_FOLDERS, {"senate": folder}):
            html = self.client.get(u("meeting", "senate", "57", 12)).content.decode()
        self.assertIn("https://rpi.box.com/embed/s/abc123", html)
        self.assertIn("Open the folder in Box", html)
        self.assertIn("hidden sm:block", html)
        # a /v/ vanity link never becomes an embed
        folder["shared_url"] = "https://rpi.box.com/v/archive"
        with mock.patch.dict(data.BOX_FOLDERS, {"senate": folder}):
            html = self.client.get(u("meeting", "senate", "57", 12)).content.decode()
        self.assertNotIn("/embed/", html)
        self.assertIn("Box folder embed goes here", html)

    def test_no_invented_contact_routes(self):
        self.assertTrue(all(s["inbox"] is None for s in data.SEATS))
        # the empty test DB has no contact_email, so no page may offer a mailto
        for name, args in ALL_PAGES:
            with self.subTest(name=name, args=args):
                self.assertNotContains(self.client.get(u(name, *args)), "mailto:")

    def test_contact_email_is_used_when_site_settings_has_one(self):
        site = {f: "" for f in logic.SETTING_FIELDS}
        site["contact_email"] = "office@example.test"
        with mock.patch.object(logic, "site_settings", return_value=site):
            r = self.client.get(u("reps", "2028"))
            self.assertContains(r, "mailto:office@example.test?subject=For%3A%20Class%20of%202028%20Senator")
            r = self.client.get(u("issue_topic", "dining"))
            self.assertContains(r, "mailto:office@example.test?subject=For%3A%20RLDC%20chair%3A%20Dining%20issue")
            self.assertContains(r, "This committee doesn't have its own email address yet.")

    def test_site_settings_extras_omitted_when_blank(self):
        html = self.client.get(u("home")).content.decode()
        self.assertNotIn("Office hours:", html)
        self.assertNotIn("Union Discord", html)

    def test_prototype_reads_do_not_write(self):
        from home.models import SiteSettings

        before = SiteSettings.objects.count()
        self.client.get(u("home"))
        self.assertEqual(SiteSettings.objects.count(), before)

    def test_meeting_data_has_no_hand_typed_status(self):
        for m in data.MEETINGS:
            self.assertNotIn("agenda_status", m)
            self.assertNotIn("minutes_status", m)

    def test_agenda_status_comes_only_from_the_link(self):
        url_ = u("meeting", "senate", "57", 12)
        none = self.client.get(url_).content.decode()
        self.assertNotIn("Posted in Box", none)
        self.assertNotIn("Agenda posted", none)
        self.assertIn("Agenda link not added to the meeting record yet.", none)
        self.assertIn("The Box folder link hasn't been added yet.", none)
        meetings = [dict(m) for m in data.MEETINGS]
        meetings[0]["agenda_url"] = "https://rpi.box.com/s/agenda12"
        with mock.patch.object(data, "MEETINGS", meetings):
            linked = self.client.get(url_).content.decode()
            self.assertIn("Open agenda (PDF in Box)", linked)
            self.assertNotIn("Agenda link not added", linked)

    def test_link_checked_line_only_beside_a_real_link(self):
        r = self.client.get(u("meeting", "senate", "57", 12))
        self.assertNotContains(r, "link checked")
        self.assertContains(r, "Document: Box · no link added to the meeting record yet")
        self.assertNotContains(self.client.get(u("meetings")), "link checked")
        # officers get the action that fixes it, in Notion
        self.assertContains(self.client.get(u("meeting", "senate", "57", 12), {"officer": "1"}), "Add the link in Notion")
        meetings = [dict(m) for m in data.MEETINGS]
        meetings[0]["agenda_url"] = "https://rpi.box.com/s/agenda12"
        with mock.patch.object(data, "MEETINGS", meetings):
            self.assertContains(self.client.get(u("meeting", "senate", "57", 12)), "Document: Word file in Box, published as PDF · link checked 19 Oct 2026")
        folder = {"label": "x", "path": "p/", "shared_url": "https://rpi.box.com/s/abc123"}
        with mock.patch.dict(data.BOX_FOLDERS, {"senate": folder}):
            self.assertContains(self.client.get(u("meetings")), "Document: Word file in Box, published as PDF · link checked 19 Oct 2026")

    def test_names_come_from_the_roster_not_the_content(self):
        # Change the roster; every page that names the person follows.
        roles = [dict(r) for r in data.ROLE_ASSIGNMENTS]
        for r in roles:
            if r["role"] == "elections_chair":
                r["holder"], r["acting"] = "Pat Example '29", False
            if r["role"] == "rldc_chair":
                r["holder"] = "Robin Example '28"
        seats = [dict(s) for s in data.SEATS]
        for s_ in seats:
            if s_["role"] == "gm":
                s_["holder"] = "Gale Example '27"
            if s_["role"] == "vp_club_relations":
                s_["holder"] = "Val Example '27"
        with mock.patch.object(data, "ROLE_ASSIGNMENTS", roles), mock.patch.object(data, "ROLE_BY_KEY", {r["role"]: r for r in roles}), \
                mock.patch.object(data, "SEATS", seats):
            take_part = self.client.get(u("take_part")).content.decode()
            about = self.client.get(u("about")).content.decode()
            self.assertIn("Pat Example", take_part)
            self.assertNotIn("Lauren Antao", take_part)
            self.assertIn("Pat Example", about)
            self.assertNotIn("Lauren Antao", about.split('id="committees"')[0] + about.split('id="get-involved"')[1])
            self.assertIn("Gale Example", about)
            self.assertNotIn("Jordan Krishnayah", about)
            self.assertIn("Robin Example", self.client.get(u("issue_topic", "dining")).content.decode())
            clubs = self.client.get(u("issue_topic", "clubs")).content.decode()
            self.assertIn("Val Example", clubs)
            self.assertNotIn("Jesse Kim", clubs)
            self.assertIn("Val Example", self.client.get(u("funding")).content.decode())
            self.assertIn("Gale Example", self.client.get(u("issue_topic", "other")).content.decode())

    def test_no_roster_names_typed_into_templates_or_topics(self):
        from pathlib import Path

        names = [h.split(" '")[0] for h in {s["holder"] for s in data.SEATS if s["holder"]} | {r["holder"] for r in data.ROLE_ASSIGNMENTS if r["holder"]}]
        root = Path(__file__).resolve().parents[2] / "templates" / "lab" / "front-door"
        for f in root.glob("*.html"):
            text = f.read_text()
            for n in names:
                self.assertNotIn(n, text, f"{n} typed into {f.name}")
        for coll in (data.TOPICS, data.BODIES, data.COMMITTEES, data.EB_COMMITTEES, data.SENATE_NONVOTING):
            blob = repr(coll)
            for n in names:
                self.assertNotIn(n, blob)

    def test_resolved_names_have_a_roster_source_line(self):
        for name, args in [("issue_topic", ["dining"]), ("issue_topic", ["clubs"]), ("about", []), ("funding", []), ("take_part", []), ("reps", ["graduate"])]:
            with self.subTest(name=name, args=args):
                self.assertContains(self.client.get(u(name, *args)), 'data-source="roster"')
        about = self.client.get(u("about")).content.decode()
        # Right now lines and both committee tables each sit next to a roster line
        self.assertGreaterEqual(about.count('data-source="roster"'), 5)

    def test_topic_owner_resolves_to_holder_and_inbox(self):
        t = data.TOPIC_BY_SLUG["dining"]
        self.assertEqual(logic.topic_chair(t), "Shruthi Anandraman '28")
        self.assertIsNone(logic.topic_inbox(t))
        roles = [dict(r) for r in data.ROLE_ASSIGNMENTS]
        for r in roles:
            if r["role"] == "rldc_chair":
                r["inbox"] = "rldc@example.test"
        with mock.patch.object(data, "ROLE_BY_KEY", {r["role"]: r for r in roles}):
            self.assertEqual(logic.topic_inbox(t), "rldc@example.test")
        self.assertEqual(logic.topic_chair(data.TOPIC_BY_SLUG["clubs"]), "Jesse Kim '26 '27G (VP for Club Relations)")
        self.assertEqual(logic.topic_chair(data.TOPIC_BY_SLUG["rights"]), "Roster not listed yet")

    def test_every_topic_and_committee_role_resolves(self):
        for t in data.TOPICS:
            self.assertIsNotNone(logic.seat_for(t["owner_seat"]), t["slug"])
        for c in data.COMMITTEES + data.EB_COMMITTEES:
            self.assertIsNotNone(logic.seat_for(c["chair_role"]), c["name"])
        for b in data.BODIES:
            if b["leader_role"]:
                self.assertIsNotNone(logic.seat_for(b["leader_role"]))

    def test_no_tailwind_class_collisions(self):
        html = self.client.get(u("home")).content.decode()
        for cls in ("text-sm", "text-xs", "text-muted", "sr-only"):
            self.assertNotRegex(html, r'class="[^"]*(?<![\w-])%s(?![\w-])[^"]*"' % cls)


class DataSanityTests(TestCase):
    def test_senate_seats_total_29(self):
        senate = [s for s in data.SEATS if s["body"] == "senate" and s["fill_rule"] != "gm"]
        self.assertEqual(len(senate), 29)

    def test_senate_count_line(self):
        c = logic.senate_counts()
        self.assertEqual((c["total"], c["filled"], c["vacant"], c["fall"]), (29, 20, 5, 4))

    def test_eboard_voting_seats_between_15_and_20(self):
        eb = [s for s in data.SEATS if s["body"] == "eboard" and s["fill_rule"] != "pu" and s["constituency"] != "officers"]
        self.assertTrue(15 <= len(eb) <= 20, len(eb))

    def test_no_seat_has_an_inbox(self):
        self.assertTrue(all(s["inbox"] is None for s in data.SEATS))
        self.assertTrue(all(r["inbox"] is None for r in data.ROLE_ASSIGNMENTS))

    def test_independent_and_fsl_are_separate_three_seat_groups(self):
        for key in ("independent", "fsl"):
            self.assertEqual(len([s for s in data.SEATS if s["body"] == "senate" and s["constituency"] == key]), 3)

    def test_every_draft_value_is_allowed(self):
        allowed = {"Senate bylaws or rules", "Senate election rules", "E-Board bylaws", "Judicial Board bylaws", "Union staff process", "Site owner"}
        found = set()
        for coll in (data.GLOSSARY, data.FILL_RULES.values(), data.PROCESSES, data.SEATS, data.BUDGET["funds"]):
            for item in coll:
                for k in ("draft", "not_set_why"):
                    if item.get(k):
                        found.add(item[k])
        for m in data.MEETINGS:
            for sec in m["sections"]:
                if sec.get("draft"):
                    found.add(sec["draft"])
        self.assertTrue(found <= allowed, found - allowed)

    def test_glossary_has_no_rugp_and_constitution_entries_carry_cites(self):
        self.assertFalse([g for g in data.GLOSSARY if "RUGP" in g["term"] or "RUGP" in g["text"]])
        self.assertTrue(all(g.get("cite") or g.get("draft") or g["term"] in ("Ex-officio", "Plurality", "Minutes") for g in data.GLOSSARY))

    def test_decisions_are_three_sample_senate_motions(self):
        d = logic.decisions()
        self.assertEqual(len(d), 3)
        self.assertTrue(all(x["sample"] for x in d))
        self.assertTrue(all(x["body"] == "Student Senate" for x in d))
        self.assertFalse([x for x in d if x["status"] == "outcome_not_recorded"])
        self.assertNotIn("outcome_not_recorded", data.STATUS_LABELS)
        self.assertTrue(all(x["status"] in data.STATUS_LABELS and x["motion_file"] and x["motion_file_name"] for x in d))
        self.assertEqual([x["date"] for x in d], sorted([x["date"] for x in d], reverse=True))

    def test_derived_marker(self):
        self.assertIn("Our arithmetic, assuming all 29 seats count", logic.mark("20 of 29 [[derived]]"))


class PerBodyRecordsTests(TestCase):
    """Each body keeps its meeting records its own way; only the Senate uses Notion."""

    def test_senate_meeting_shows_the_document_first_and_the_option_labelled(self):
        r = self.client.get(u("meeting", "senate", "57", 12))
        self.assertContains(r, "Document: Box")
        self.assertContains(r, "Prototype only: what this document says")
        self.assertContains(r, "Option for the Senate")
        self.assertContains(r, 'id="agenda-option"')
        self.assertContains(r, "2026-07-30 Senate 57 #12 Agenda.pdf")
        self.assertContains(r, "hasn't chosen this")
        self.assertContains(r, 'data-source="agenda_items_option"')

    def test_eboard_meeting_is_entered_on_this_site(self):
        url = u("meeting", "eboard", "fy27", 1)
        r = self.client.get(url)
        self.assertContains(r, "entered on this site by the E-Board Secretary")
        self.assertContains(r, "records its decisions in its minutes")
        self.assertContains(r, "Item-by-item agendas aren't shown for the Executive Board.")
        self.assertNotContains(r, "Option for the Senate")
        self.assertNotContains(r, "Senate's Notion")  # the banner mentions Notion; the page body must not
        self.assertNotContains(r, 'class="chip">Proposal')
        officer = self.client.get(url, {"officer": "1"})
        self.assertContains(officer, "Edit on this site")
        self.assertContains(officer, "Add the link on this site")
        self.assertNotContains(officer, "Edit in Notion")

    def test_agenda_preview_embeds_a_box_shared_link(self):
        meetings = [dict(m) for m in data.MEETINGS]
        meetings[0]["agenda_url"] = "https://rpi.box.com/s/agenda12"
        with mock.patch.object(data, "MEETINGS", meetings):
            html = self.client.get(u("meeting", "senate", "57", 12)).content.decode()
        self.assertIn("Open agenda (PDF)", html)
        self.assertIn('title="Box preview: 2026-07-30 Senate 57 #12 Agenda.pdf"', html)
        self.assertIn("https://rpi.box.com/embed/s/agenda12", html)
        self.assertNotIn("Box preview of 2026-07-30", html)

    def test_meetings_page_lists_folder_only_bodies(self):
        r = self.client.get(u("meetings"))
        self.assertContains(r, "Bodies that publish records as files")
        self.assertContains(r, 'id="files-only"')
        self.assertContains(r, "Judicial Board")
        self.assertEqual(r.content.decode().count("publishes its records as files"), 3)
        self.assertContains(r, "Its rulings on what the Constitution means are public.")
        self.assertContains(r, "Decisions listed here are Senate motions.")
        self.assertContains(r, "Entered on this site")
        # "All files" lists only the bodies that list meetings here
        all_files = r.content.decode().split('id="files"')[1].split('id="how"')[0]
        self.assertIn("Student Senate, 57th Senate", all_files)
        self.assertIn("Executive Board, FY27", all_files)
        self.assertNotIn("Judicial Board, 2026–27", all_files)

    def test_empty_week_points_to_folder_only_bodies(self):
        with mock.patch.object(logic, "today", return_value=date(2026, 10, 21)):
            r = self.client.get(u("home"))
        self.assertContains(r, "don't list meetings here")
        self.assertContains(r, u("meetings") + "#files-only")

    def test_about_describes_per_body_records(self):
        r = self.client.get(u("about"))
        self.assertContains(r, "Each body's records, and where they live")
        self.assertContains(r, "The Public Records Standard")
        self.assertContains(r, "accessibility tags")
        self.assertContains(r, "Once a month, confirm on this site that the folder is complete.")
        self.assertContains(r, "Done on this site, by each body on its own schedule.")
        self.assertContains(r, 'Published as files in its Box folder')
        self.assertNotContains(r, "If a body decides not to use Notion")

    def test_only_the_senate_row_mentions_notion(self):
        for row in data.OWNERSHIP_BY_BODY:
            with self.subTest(body=row["body"]):
                if row["body"] == "Student Senate":
                    self.assertIn("Notion", repr(row))
                else:
                    self.assertNotIn("Notion", repr(row))
        self.assertFalse(hasattr(data, "OWNERSHIP"))
        self.assertEqual([r["body"] for r in data.OWNERSHIP_BY_BODY][0], "Student Senate")

    def test_body_records_adapters(self):
        self.assertEqual(data.BODY_RECORDS["senate"]["adapter"], "notion")
        self.assertFalse(data.BODY_RECORDS["senate"]["example"])
        self.assertEqual(data.BODY_RECORDS["eboard"]["adapter"], "site")
        for key in ("gc", "uc", "jboard"):
            self.assertEqual(data.BODY_RECORDS[key]["adapter"], "folder")
            self.assertTrue(data.BODY_RECORDS[key]["example"])
            self.assertIn(key, data.BOX_FOLDERS)
        self.assertEqual([f["key"] for f in logic.folder_bodies()], ["gc", "uc", "jboard"])
        self.assertEqual([f["key"] for f in logic.meeting_body_folders()], ["senate", "eboard"])
        for m in logic.all_meetings(date(2026, 10, 21)):
            self.assertIn(m["record_source"]["key"], ("meeting_senate", "meeting_eboard"))
            self.assertEqual(m["file_missing_source"]["key"], "file_missing_" + m["body"])

    def test_publish_steps_and_rules_follow_the_word_workflow(self):
        self.assertEqual(len(data.PUBLISH_STEPS_BY_ADAPTER), 3)
        for g in data.PUBLISH_STEPS_BY_ADAPTER:
            self.assertIn("accessibility tags", g["steps"][0])
        self.assertTrue(any("Never retype what's in a Word document" in r for r in data.OFFICER_RULES))
        self.assertEqual(len(data.RECORDS_STANDARD), 6)

    def test_issue_topic_copy_does_not_imply_everyone_uses_notion(self):
        r = self.client.get(u("issue_topic", "dining"))
        self.assertContains(r, "Senate committees may log issues in the Senate")
        self.assertContains(r, "don't publish an issue tracker")

    def test_every_source_key_used_in_a_template_exists(self):
        import pathlib

        root = pathlib.Path(__file__).resolve().parents[2] / "templates" / "lab" / "front-door"
        used = set()
        for f in root.glob("*.html"):
            used |= set(re.findall(r"s=sources\.(\w+)", f.read_text()))
        self.assertTrue(used)
        self.assertFalse(used - set(data.SOURCES), used - set(data.SOURCES))
