from datetime import date

from django.test import SimpleTestCase, TestCase
from django.urls import NoReverseMatch, reverse

from . import data

NS = "lab:the_record"


def unescape_quotes(response):
    """Django escapes ' in template variables but not in template text. Compare both the same way."""
    response.content = response.content.replace(b"&#x27;", b"'")
    return response


def u(name, *args):
    return reverse(f"{NS}:{name}", args=args)


class RecordPagesTests(TestCase):
    def get(self, path, status=200):
        response = self.client.get(path)
        self.assertEqual(response.status_code, status, path)
        return unescape_quotes(response)

    def test_pages_render(self):
        pages = [
            u("home"),
            u("meetings"),
            u("meetings") + "?body=senate",
            u("meetings") + "?body=eboard&term=fy27",
            u("meetings") + "?body=gc",
            u("meetings") + "?body=uc",
            u("meetings") + "?body=jboard",
            u("meeting", "senate", "57", 12),
            u("meeting", "senate", "57", 12) + "?agenda=items",
            u("meeting", "senate", "57", 11) + "?agenda=items",
            u("meeting", "senate", "57", 16) + "?agenda=items",
            u("meeting", "senate", "57", 11),
            u("meeting", "senate", "57", 13),
            u("meeting", "senate", "57", 16),
            u("meeting", "eboard", "fy27", 1),
            u("meeting", "eboard", "fy27", 4),
            u("decisions"),
            u("decisions") + "?status=waiting",
            u("decisions") + "?body=eboard",
            u("rules"),
            u("money"),
            u("desk"),
            u("desk") + "?path=site",
            u("desk") + "?path=wagtail",
            u("desk") + "?path=folder",
            u("health"),
        ]
        for path in pages:
            with self.subTest(path=path):
                self.get(path)
        for d in data.DECISIONS:
            self.get(u("decision", d["id"]))

    def test_urls_mount_under_lab(self):
        self.assertEqual(u("home"), "/lab/the-record/")
        self.assertEqual(u("health"), "/lab/the-record/desk/health/")
        self.assertEqual(u("meeting", "senate", "57", 12), "/lab/the-record/meetings/senate/57/12/")

    def test_every_page_has_banner_and_one_h1(self):
        for path in [u("home"), u("meetings"), u("decisions"), u("money"), u("rules"), u("desk"), u("health")]:
            html = self.get(path).content.decode()
            self.assertIn("Prototype layout for testing. Not the official site. Items marked Sample are made up.", html)
            self.assertIn("Nothing here is connected to Notion or Box.", html)
            self.assertEqual(html.count("<h1"), 1, path)
            self.assertIn('href="#main"', html)
            self.assertNotIn("RUGP", html)

    def test_meeting_senate_12(self):
        html = self.get(u("meeting", "senate", "57", 12)).content.decode()
        self.assertIn("29 voting seats", html)
        self.assertIn("Fraternity and Sorority Life", html)
        self.assertIn("Meeting record: Senate's Notion · synced 12 min ago", html)
        self.assertIn("Zach Nobles", html)  # typed from the PDF, inside the prototype-only details
        self.assertIn("Prototype only: what this document says", html)
        self.assertIn("As the document (today)", html)
        self.assertNotIn("Option for the Senate", html)
        items = self.get(u("meeting", "senate", "57", 12) + "?agenda=items").content.decode()
        self.assertIn("Option for the Senate", items)
        self.assertIn("Nothing listed", items)
        self.assertIn("The Senate hasn't chosen this", items)
        self.assertIn('data-source="agenda_items_option"', items)
        self.assertNotIn('data-source="agenda_items_option"', html)

    def test_meeting_senate_11_is_pdf_only(self):
        html = self.get(u("meeting", "senate", "57", 11)).content.decode()
        self.assertIn("written in Word", html)
        self.assertIn("Sample", html)
        self.assertIn("Not recorded", html)
        # Linked agenda: the PDF button and a Box preview titled with the file name.
        self.assertIn("Open agenda (PDF)", html)
        self.assertIn('title="Box preview: 2026-07-16 Senate 57 #11 Agenda.pdf"', html)
        self.assertIn('src="https://rpi.box.com/embed/s/sample-senate-57-11-agenda"', html)
        items = self.get(u("meeting", "senate", "57", 11) + "?agenda=items").content.decode()
        self.assertIn("This agenda was written in Word, so it has no items in Notion", items)

    def test_meeting_senate_16_agenda_not_posted(self):
        html = self.get(u("meeting", "senate", "57", 16)).content.decode()
        self.assertIn("Agenda not posted yet", html)
        self.assertIn("The agenda hasn't been posted yet", html)

    def test_past_meeting_without_link_says_so_plainly(self):
        html = self.get(u("meeting", "senate", "57", 12)).content.decode()
        self.assertIn("No agenda link on the meeting record yet", html)
        self.assertIn("Prototype note: the real agenda PDF exists in Box", html)
        self.assertIn("Box preview of", html)
        self.assertIn("2026-07-30 Senate 57 #12 Agenda.pdf", html)
        self.assertIn("goes here. The link hasn't been added to the meeting record yet.", html)
        meetings = self.get(u("meetings")).content.decode()
        self.assertIn("No agenda link on the meeting record yet", meetings)

    def test_no_page_claims_to_know_what_is_in_box(self):
        """There is no Box API, so no page may say a file is 'posted in Box' without a pasted link."""
        pages = [
            u("home"),
            u("meetings"),
            u("decisions"),
            u("money"),
            u("rules"),
            u("desk"),
            u("health"),
            u("meeting", "senate", "57", 11),
            u("meeting", "senate", "57", 12),
            u("meeting", "senate", "57", 16),
            u("meeting", "eboard", "fy27", 1),
        ]
        pages += [u("decision", d["id"]) for d in data.DECISIONS]
        for path in pages:
            for suffix in ("", "?officer=1"):
                html = self.get(path + suffix).content.decode().lower()
                with self.subTest(path=path + suffix):
                    self.assertNotIn("posted in box", html)
                    self.assertNotIn("link not added to the meeting record", html)
                    self.assertNotIn("not linked, ", html)

    def test_meeting_states_come_only_from_links(self):
        for m in data.MEETINGS:
            self.assertNotIn("agenda_status", m)
            self.assertNotIn("minutes_status", m)
            self.assertIn(data.agenda_state(m), ("linked", "missing"))
            self.assertIn(data.minutes_state(m), ("linked", "missing"))

    def test_quorum_line_is_glossed_and_marked_draft(self):
        html = self.get(u("meeting", "senate", "57", 12)).content.decode()
        self.assertIn("the minimum number who must be present to vote", html)
        self.assertIn("Voting members", html)
        self.assertIn("typed once there instead of in the Word header", html)

    def test_every_decision_belongs_to_a_meeting_record(self):
        for d in data.DECISIONS:
            with self.subTest(d["id"]):
                self.assertIsNotNone(d["meeting_key"])
                self.assertIsNotNone(data.find_meeting(*d["meeting_key"]))
                self.assertTrue(any(h["meeting"] for h in d["history"]))
                for h in d["history"]:
                    if h["meeting"]:
                        self.assertIsNotNone(data.find_meeting(*h["meeting"]))

    def test_decision_history_links_to_meeting_pages(self):
        html = self.get(u("decision", "sample-senate-appointment")).content.decode()
        self.assertIn(u("meeting", "senate", "57", 13), html)
        self.assertIn(u("meeting", "senate", "57", 14), html)
        self.assertIn("Senate 57 #14, item 4a", html)
        meeting = self.get(u("meeting", "senate", "57", 14)).content.decode()
        self.assertIn(u("decision", "sample-senate-appointment"), meeting)

    def test_decision_term_labels_are_plain(self):
        html = self.get(u("decision", "sample-senate-appointment")).content.decode()
        self.assertIn("57th Senate", html)
        html = self.get(u("decision", "sample-senate-done")).content.decode()
        self.assertIn("57th Senate", html)
        self.assertNotIn("FY27 (2026–27)", html)

    def test_abbreviations_are_spelled_out(self):
        html = self.get(u("meeting", "senate", "57", 12)).content.decode()
        self.assertIn("Vice Grand Marshal for External Affairs", html)
        self.assertNotIn("VGMEA", html)
        desk = self.get(u("desk")).content.decode()
        self.assertIn("Web Technologies Group (WTG) chair", desk)
        self.assertIn("Vice Grand Marshal for Internal Affairs (VGMIA)", desk)
        self.assertNotIn("RU 3202", self.get(u("meeting", "eboard", "fy27", 1)).content.decode())
        self.assertIn("a formal spending approval", self.get(u("money")).content.decode())

    def test_meeting_eboard(self):
        html = self.get(u("meeting", "eboard", "fy27", 1)).content.decode()
        self.assertIn("15 to 20 voting seats", html)
        self.assertIn("Special Ballroom Request", html)
        self.assertNotIn("/decisions/eb-fy27-01", html)
        self.assertIn("entered on this site", html)
        self.assertIn("Item-by-item agendas aren't shown", html)
        self.assertNotIn("Option for the Senate", html)
        self.assertIn("The Executive Board records its decisions in its minutes", html)
        # No Senate-only view switch on an E-Board page, and ?agenda=items is ignored.
        self.assertNotIn("How this agenda is shown", html)
        forced = self.get(u("meeting", "eboard", "fy27", 1) + "?agenda=items").content.decode()
        self.assertNotIn("Option for the Senate", forced)

    def test_meeting_eboard_officer_links_say_this_site(self):
        html = self.get(u("meeting", "eboard", "fy27", 1) + "?officer=1").content.decode()
        self.assertIn("Edit on this site", html)
        self.assertNotIn("Edit in Notion", html)
        self.assertIn("Meeting record: entered on this site by the E-Board Secretary · updated 24 Aug 2026", html)
        self.assertIn("Quorum", html)
        self.assertIn("this site's meeting entry", html)
        senate = self.get(u("meeting", "senate", "57", 12)).content.decode()
        self.assertIn("the Senate's Notion meeting row", senate)

    def test_meetings_page(self):
        html = self.get(u("meetings")).content.decode()
        self.assertNotIn("Recording", html)
        self.assertIn("Box folder embed goes here", html)
        self.assertIn('id="speak"', html)
        self.assertIn('id="files"', html)
        self.assertIn("Bodies that publish records as files", html)
        self.assertIn('id="files-only"', html)
        self.assertIn("Record</th>", html)
        self.assertIn("Entered on this site", html)
        self.assertIn("Senate's Notion", html)
        for name in ("Graduate Council", "Undergraduate Council", "Judicial Board"):
            self.assertIn(name, html)
        self.assertIn("Including the four Class Councils.", html)

    def test_meetings_folder_body_panel(self):
        for key, name in (("gc", "Graduate Council"), ("uc", "Undergraduate Council"), ("jboard", "Judicial Board")):
            html = self.get(u("meetings") + f"?body={key}").content.decode()
            self.assertIn(f"The {name} publishes its records as files", html)
            self.assertIn("doesn't list meetings on this site", html)
            self.assertIn("Box folder embed goes here", html)
            self.assertIn('data-source="folder_only"', html)
            self.assertNotIn('id="up-heading"', html)
            self.assertNotIn("Bodies that publish records as files", html)
        jb = self.get(u("meetings") + "?body=jboard").content.decode()
        self.assertIn("Its conduct and rights cases are confidential.", jb)
        self.assertIn("Confirm with: Judicial Board bylaws", jb)

    def test_home_lists_folder_bodies(self):
        html = self.get(u("home")).content.decode()
        self.assertIn("Each body keeps its records its own way", html)
        for name in ("Graduate Council", "Undergraduate Council", "Judicial Board"):
            self.assertIn(f"{name}: publishes records as files", html)
        self.assertIn(u("meetings") + "?body=gc", html)
        self.assertIn('data-source="folder_only"', html)
        self.assertIn('data-source="motions"', html)

    def test_decisions(self):
        html = self.get(u("decisions") + "?q=webex").content.decode()
        self.assertIn("Puts the Webex link and the full date on every Senate meeting notice.", html)
        self.assertIn("1 decision", html)
        self.assertIn("Decisions here are Senate motions.", html)
        self.assertIn("Motions table", html)
        self.assertNotIn("Structured outcomes are a later phase", html)
        self.assertIn(u("meetings") + "#files-only", html)
        empty = self.get(u("decisions") + "?q=zzzzzz").content.decode()
        self.assertIn("No decisions match.", empty)

    def test_decisions_eboard_panel(self):
        html = self.get(u("decisions") + "?body=eboard").content.decode()
        self.assertIn("records its decisions in its minutes", html)
        self.assertIn("Box folder embed goes here", html)
        self.assertNotIn("No decisions match", html)
        # The old E-Board ballroom items are no longer decisions.
        self.get(u("decision", "eb-fy27-01-a"), status=404)

    def test_decision_detail_without_threshold(self):
        html = self.get(u("decision", "sample-senate-failed")).content.decode()
        self.assertIn("not set by the Constitution", html)
        self.assertIn("Draft: confirm", html)
        self.assertIn("Didn't pass", html)
        self.assertIn('aria-current="step"', html)

    def test_decision_detail_names_the_motion_file(self):
        html = self.get(u("decision", "sample-senate-done")).content.decode()
        self.assertIn("Motion text:", html)
        self.assertIn("2026-09-23 Senate 57 #14 Motion - Webex link on every Senate meeting notice.pdf", html)
        self.assertIn("(Word file in Box, as PDF)", html)
        self.assertIn("https://rpi.box.com/s/sample-motion-sample-senate-done", html)
        self.assertIn('data-source="motions"', html)

    def test_decision_detail_with_threshold(self):
        html = self.get(u("decision", "sample-senate-appointment")).content.decode()
        self.assertIn("2/3 of the Senate", html)
        html = self.get(u("decision", "sample-senate-bylaw")).content.decode()
        self.assertIn("20 of 29", html)
        self.assertIn("Our arithmetic, assuming all 29 Senate seats count", html)

    def test_decision_done_has_three_history_rows_and_note(self):
        d = data.find_decision("sample-senate-done")
        self.assertEqual(len(d["history"]), 3)
        self.assertTrue(d["outcome_note"])
        self.assertIn(d["outcome_note"], self.get(u("decision", d["id"])).content.decode())

    def test_all_plain_summaries_short(self):
        for d in data.DECISIONS:
            self.assertLessEqual(len(d["plain_summary"]), 200, d["id"])
            self.assertTrue(d["plain_summary"])

    def test_money(self):
        html = self.get(u("money")).content.decode()
        self.assertIn("public documents", html)
        self.assertIn("Quoted from Executive Board Agenda 01", html)
        self.assertNotIn("Download CSV", html)
        self.assertNotIn("% left", html)
        self.assertIn("$126,635.47", html)

    def test_money_table_only_on_money_page(self):
        home = self.get(u("home")).content.decode()
        self.assertNotIn("$126,635.47", home)
        self.assertNotIn("Left (as printed)", home)
        self.assertIn("Contingency fund balances are printed on each E-Board agenda.", home)
        self.assertIn("Latest:", home)
        money = self.get(u("money")).content.decode()
        self.assertIn("In production this table is a quotation from one agenda", money)
        self.assertIn("never keeps its own copy", money)
        self.assertNotIn("synced Notion table", money)
        self.assertNotIn("Edit in Notion", self.get(u("money") + "?officer=1").content.decode())
        self.assertIn("Confirm with: Site owner", money)
        self.assertIn("so they may be out of date", money)

    def test_no_money_csv_url(self):
        with self.assertRaises(NoReverseMatch):
            reverse(f"{NS}:money_csv")

    def test_rules(self):
        html = self.get(u("rules")).content.decode()
        self.assertIn("20 of 29", html)
        self.assertIn("10% of all Union members", html)
        self.assertIn("Union Constitution, Art. XII", html)
        for anchor in ("votes", "petitions", "records", "transparency", "judicial-board"):
            self.assertIn(f'id="{anchor}"', html)

    def test_desk_notion_default(self):
        html = self.get(u("desk")).content.decode()
        self.assertIn("Stand-in for Notion", html)
        self.assertIn("Your jobs", html)
        self.assertIn("how-this-site-works", html)
        self.assertIn("Edit in Wagtail", html)  # desk always shows officer links
        self.assertNotIn("Post the next meeting", html)

    def test_desk_two_minute_test_edits_existing_row(self):
        html = self.get(u("desk")).content.decode()
        self.assertIn("2026-10-26 Senate 57 #16 Agenda.pdf", html)
        self.assertIn("open the existing Senate 57 #16 row", html)
        self.assertNotIn("duplicate the last meeting. Change", html)
        # The stand-in panel is prefilled from the existing row; only Agenda is left to fill.
        self.assertIn('name="number" value="16"', html)
        self.assertIn('value="2026-10-26"', html)
        self.assertIn('value="Location to be confirmed"', html)
        self.assertRegex(html, r'<input type="checkbox" name="public"[^>]*\bchecked>')

    def test_desk_site_path_and_wagtail_alias(self):
        for suffix in ("?path=site", "?path=wagtail"):
            html = self.get(u("desk") + suffix).content.decode()
            self.assertIn("never uses this form", html)
            self.assertNotIn("Add agenda items", html)
            self.assertNotIn("Stand-in for Notion", html)
            self.assertNotIn('name="public"', html)
            self.assertNotIn('name="item1"', html)
            self.assertIn('<option value="eboard"', html)
            self.assertNotIn('<option value="senate"', html)
            self.assertIn('value="Rensselaer Union, room 3202"', html)
            self.assertIn('value="19:00', html)
            self.assertIn('name="number" value="5"', html)

    def test_desk_notion_form_is_senate_only(self):
        html = self.get(u("desk")).content.decode()
        self.assertIn('<option value="senate"', html)
        self.assertNotIn('<option value="eboard"', html)
        self.assertNotIn('name="item1"', html)
        self.assertIn("The Senate publishes a meeting with one Notion row and pasted links.", html)
        self.assertIn("never Print to PDF", html)

    def test_desk_path_switch(self):
        html = self.get(u("desk")).content.decode()
        self.assertIn('aria-label="Where this body keeps meeting records"', html)
        self.assertIn("Senate (Notion)", html)
        self.assertIn("Entered on this site (E-Board, example)", html)
        self.assertIn("Folder only (Graduate Council, Undergraduate Council, Judicial Board)", html)
        self.assertIn("Each body chooses. A body's meetings live in one place, never two.", html)
        self.assertEqual(html.count('aria-current="page"'), 2)  # the nav link on the desk page and the path switch

    def test_desk_folder_path_has_no_form(self):
        html = self.get(u("desk") + "?path=folder").content.decode()
        self.assertIn("Records are complete up to today", html)
        self.assertIn("disabled", html)
        self.assertNotIn("<form method=\"post\"", html)
        self.assertNotIn("Stand-in for Notion", html)
        self.assertIn("What students see", html)
        self.assertIn("The Graduate Council publishes its records as files", html)
        self.assertIn("What you give up", html)
        self.assertIn("No automatic deadline checks", html)
        # No POST for a folder-only body: a POST just renders the page.
        response = self.client.post(u("desk") + "?path=folder", {"path": "folder"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("What the site shows", response.content.decode())

    def test_desk_how_this_site_works(self):
        html = self.get(u("desk")).content.decode()
        self.assertIn("Each body's records", html)
        self.assertIn("The Public Records Standard", html)
        self.assertIn("Agenda in the body's public Box folder 24 hours before the meeting", html)
        self.assertIn("The Judicial Board publishes its rulings on what the Constitution means.", html)
        self.assertIn("(example)", html)
        self.assertIn("a 'post a meeting' form for the Senate", html)
        self.assertIn("retyping or parsing a Word agenda, motion or minutes", html)
        self.assertIn("Export Word documents to PDF with accessibility tags", html)
        self.assertIn("Term rollover, done on this site", html)
        self.assertIn("The Senate's Notion copy of the roster updates itself.", html)
        self.assertIn("Motion text", html)
        self.assertIn("2026-09-23 Senate 57 #14 Motion - Webex link on notices.pdf", html)
        self.assertNotIn("Add agenda items", html)

    def test_health(self):
        html = self.get(u("health")).content.decode()
        self.assertIn("Last successful sync", html)
        self.assertIn("Minutes link missing", html)
        self.assertIn("What this page can't see", html)
        self.assertIn("flagged from 24 Oct", html)
        self.assertIn("Quoted budget is older than the newest E-Board meeting record", html)
        self.assertNotIn("Missing (posted in Box", html)
        self.assertIn("Public Records Standard, by body", html)
        self.assertIn("Each body against the Public Records Standard", html)
        self.assertIn("Can't check: folder only", html)
        self.assertIn("3 meetings past 14 days with no minutes link (oldest: #12, 83 days)", html)
        self.assertIn("4 meetings past 14 days with no minutes link (oldest: #1, 57 days)", html)
        self.assertIn("No upcoming meeting listed", html)
        self.assertIn("Roster copy", html)
        self.assertIn("Senate's Notion schema check", html)
        self.assertIn("Senate Motions property", html)
        self.assertIn("Last edited at source", html)
        self.assertIn("Box folder shared link not added", html)
        for n, label in enumerate(
            ["Sync status", "Public Records Standard, by body", "What the site is showing", "Problems", "All clear", "What this page can't see"],
            start=1,
        ):
            self.assertIn(f"{n}. {label}", html)

    def test_404s(self):
        self.get(u("decision", "nope"), status=404)
        self.get(u("meeting", "senate", "57", 99), status=404)
        self.get(u("meeting", "senate", "58", 12), status=404)

    def test_officer_links_hidden_for_students(self):
        path = u("meeting", "senate", "57", 12)
        response = self.get(path)
        html = response.content.decode()
        self.assertIn("Meeting record: Senate's Notion · synced 12 min ago", html)
        self.assertNotIn("Edit in Notion", html)
        self.assertIn("Viewing as a student", html)
        self.assertIn("officer=1", html)
        self.assertNotIn("lab_officer", response.cookies)

    def test_officer_links_shown_and_cookie(self):
        path = u("meeting", "senate", "57", 12)
        response = self.get(path + "?officer=1")
        html = response.content.decode()
        self.assertIn("Edit in Notion", html)
        self.assertIn("Viewing as an officer (mock)", html)
        cookie = response.cookies["lab_officer"]
        self.assertEqual(cookie.value, "1")
        self.assertEqual(cookie["path"], "/lab/")
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertFalse(cookie["max-age"])
        # The cookie persists to the next request...
        self.assertIn("Edit in Notion", self.get(path).content.decode())
        # ...until ?officer=0 clears it.
        off = self.get(path + "?officer=0")
        self.assertNotIn("Edit in Notion", off.content.decode())
        self.assertNotIn("Edit in Notion", self.get(path).content.decode())

    def test_officer_mode_only_reveals_edit_links(self):
        path = u("meeting", "senate", "57", 12)
        student = self.get(path).content.decode()
        officer = self.get(path + "?officer=1").content.decode()
        self.assertEqual(student.count("Zach Nobles"), officer.count("Zach Nobles"))


class DeskPostTests(TestCase):
    VALID = {
        "body": "senate",
        "term": "57",
        "number": "16",
        "date": "2026-10-26",
        "time": "19:00",
        "location": "Location to be confirmed",
        "agenda": "",
        "elapsed": "102",
    }

    SITE = {
        "body": "eboard",
        "term": "fy27",
        "number": "5",
        "date": "2026-11-10",
        "time": "19:00",
        "location": "Rensselaer Union, room 3202",
        "agenda": "",
        "elapsed": "75",
    }

    def post(self, path="notion", **overrides):
        base = self.SITE if path in ("site", "wagtail") else self.VALID
        payload = {**base, "path": path, **overrides}
        payload = {k: v for k, v in payload.items() if v is not None}
        response = self.client.post(u("desk") + f"?path={path}", payload)
        self.assertEqual(response.status_code, 200)
        return unescape_quotes(response).content.decode()

    def test_public_ticked(self):
        html = self.post(public="on", agenda="https://rpi.box.com/s/abc123")
        self.assertIn("synced just now (simulated)", html)
        self.assertIn("Agenda posted (link to rpi.box.com)", html)
        self.assertIn("looks like a Box shared link", html)
        self.assertIn("Time taken: 1 min 42 s", html)
        self.assertNotIn('href="https://rpi.box.com/s/abc123"', html)

    def test_public_unticked(self):
        html = self.post()
        self.assertIn("Public is unticked", html)
        self.assertNotIn("synced just now", html)

    def test_not_a_box_link(self):
        html = self.post(public="on", agenda="https://example.com/x")
        self.assertIn("isn't a Box shared link", html)
        self.assertNotIn('href="https://example.com/x"', html)

    def test_no_agenda_flags(self):
        html = self.post(public="on", date="2026-10-21")  # may be past or near depending on today
        self.assertIn("Checks the health page would run on this row", html)

    def test_missing_date_shows_error_summary(self):
        html = self.post(public="on", date=None)
        self.assertIn('role="alert"', html)
        self.assertIn("There is a problem", html)
        self.assertIn('href="#id_date"', html)

    def test_error_summary_gets_focus_not_the_empty_result(self):
        html = self.post(public="on", date=None)
        self.assertIn('id="error-summary" tabindex="-1"', html)
        self.assertIn('data-focus="error-summary"', html)
        self.assertNotIn('action="?path=notion#result"', html)
        self.assertIn('action="?path=notion"', html)
        ok = self.post(public="on")
        self.assertIn('data-focus="result-heading"', ok)
        self.assertIn('id="result-heading" tabindex="-1"', ok)
        fresh = self.client.get(u("desk")).content.decode()
        self.assertIn('data-focus=""', fresh)

    def test_errors_listed_in_field_order(self):
        html = self.post(public="on", term="fy27", date=None)
        summary = html[html.index('id="error-summary"'):]
        summary = summary[: summary.index("</ul>")]
        self.assertLess(summary.index("Term:"), summary.index("Date:"))

    def test_duplicate_meeting_row_is_flagged(self):
        html = self.post(public="on", date="2026-11-02")
        self.assertIn("Senate 57 #16 already has a row in Meetings. Edit that row instead of adding a second one.", html)
        html = self.post(public="on", location="Room 3202")
        self.assertIn("already has a row in Meetings", html)
        # Same day and place as the existing row: nothing to flag.
        html = self.post(public="on")
        self.assertNotIn("already has a row", html)
        # A number nobody has used is fine.
        html = self.post(public="on", number="17", date="2026-11-09")
        self.assertNotIn("already has a row", html)
        # The E-Board's site entry: same number, different day.
        site = self.post("site", number="1", date="2026-11-02")
        self.assertIn("E-Board FY27 #1 already exists on this site. Edit that meeting instead of adding a second one.", site)
        self.assertNotIn("already exists on this site.", self.post("site"))

    def test_term_must_match_body(self):
        html = self.post(public="on", term="fy27")
        self.assertIn("There is a problem", html)

    def test_time_not_measured_without_js(self):
        html = self.post(public="on", elapsed="")
        self.assertIn("Time not measured", html)

    def test_site_path(self):
        for path in ("site", "wagtail"):
            html = self.post(path)
            self.assertIn("entered on this site by the E-Board Secretary", html)
            self.assertIn("just now", html)
            self.assertIn("Time taken: 1 min 15 s", html)
            self.assertNotIn("Notion", html.split('id="result"', 1)[1].split("</section>", 1)[0])

    def test_site_path_only_accepts_the_eboard(self):
        html = self.post("site", body="senate", term="57")
        self.assertIn("There is a problem", html)
        html = self.post("notion", body="eboard", term="fy27", public="on")
        self.assertIn("There is a problem", html)

    def test_preview_agenda_timing_follows_the_24_hour_rule(self):
        from datetime import timedelta

        from .views import today_ny

        def dated(days):
            return (today_ny() + timedelta(days=days)).isoformat()

        self.assertIn("Overdue: agenda due 24 hours before the meeting", self.post(public="on", date=dated(1)))
        self.assertIn("Overdue: agenda due 24 hours before the meeting", self.post(public="on", date=dated(0)))
        soon = self.post(public="on", date=dated(2))
        self.assertIn("Due soon", soon)
        self.assertNotIn("Overdue: agenda due", soon)
        self.assertIn("Waiting: flagged from", self.post(public="on", date=dated(5)))

    def test_folder_path_post_is_ignored(self):
        response = self.client.post(u("desk") + "?path=folder", {**self.VALID, "path": "folder"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("What the site shows", response.content.decode())

    def test_post_never_persists(self):
        from home.models import SiteSettings

        before = SiteSettings.objects.count()
        self.post(public="on")
        self.assertEqual(SiteSettings.objects.count(), before)


class DataTests(SimpleTestCase):
    def test_senate_snapshot_sums_to_29(self):
        snap = data.SNAPSHOTS["senate"]
        self.assertEqual(sum(g["seats"] for g in snap["groups"]), 29)
        totals = data.snapshot_totals("senate")
        self.assertEqual((totals["seats"], totals["filled"], totals["vacant"], totals["elect_fall"]), (29, 20, 5, 4))
        for g in snap["groups"]:
            self.assertEqual(g["filled"] + g["vacant"] + g["elect_fall"], g["seats"], g["label"])

    def test_eboard_snapshot_in_range(self):
        totals = data.snapshot_totals("eboard")
        self.assertTrue(15 <= totals["seats"] <= 20)
        self.assertEqual((totals["seats"], totals["filled"], totals["vacant"]), (20, 13, 7))

    def test_meeting_checks(self):
        rows = data.meeting_checks(date(2026, 10, 21))
        minutes = [r for r in rows if r["check"] == "Minutes link missing" and "Senate 57 #12" in r["item"]]
        self.assertEqual(len(minutes), 1)
        self.assertEqual(minutes[0]["severity"], "overdue")
        self.assertEqual(minutes[0]["days"], 83)
        self.assertIn("30 Jul 2026 · 83 days", minutes[0]["item"])
        self.assertIn("(Standard: 14 days)", minutes[0]["item"])
        self.assertEqual(minutes[0]["body"], "senate")
        waiting = [r for r in rows if r["severity"] == "waiting"]
        self.assertEqual(len(waiting), 1)
        self.assertIn("Senate 57 #16", waiting[0]["item"])
        self.assertIn("24 Oct", waiting[0]["check"])

    def test_eboard_checks_point_at_this_site(self):
        rows = data.meeting_checks(date(2026, 10, 21))
        eb = [r for r in rows if r["check"] == "Minutes link missing" and "E-Board FY27 #1 " in r["item"]]
        self.assertEqual(len(eb), 1)
        self.assertEqual(eb[0]["severity"], "overdue")
        self.assertEqual(eb[0]["days"], 57)
        self.assertEqual(eb[0]["fix_label"], "Fix on this site")
        self.assertEqual(eb[0]["fix_url"], "/admin/")
        self.assertEqual(eb[0]["body"], "eboard")
        senate = [r for r in rows if r["body"] == "senate" and r["severity"] != "ok"]
        self.assertTrue(all(r["fix_label"] == "Fix in Notion" for r in senate))
        self.assertTrue(all(r["body"] for r in rows))

    def test_public_unticked_applies_to_the_senate_only(self):
        senate = next(m for m in data.MEETINGS if m["body"] == "senate" and m["number"] == 16)
        eboard = next(m for m in data.MEETINGS if m["body"] == "eboard" and m["number"] == 1)
        senate["public"] = eboard["public"] = False
        try:
            rows = data.meeting_checks(date(2026, 10, 21))
        finally:
            senate["public"] = eboard["public"] = True
        flagged = [r for r in rows if "Public is unticked in Notion" in r["check"]]
        self.assertEqual(len(flagged), 1)
        self.assertIn("Senate 57 #16", flagged[0]["item"])

    def test_agenda_check_follows_the_24_hour_rule(self):
        def agenda_rows(today):
            return [r for r in data.meeting_checks(today) if r.get("kind") == "agenda_upcoming"]

        # Senate #16 is on 26 Oct 2026.
        (two,) = agenda_rows(date(2026, 10, 24))
        self.assertEqual(two["severity"], "soon")
        self.assertIn("Agenda link missing: meeting in 2 days", two["check"])
        (one,) = agenda_rows(date(2026, 10, 25))
        self.assertEqual(one["severity"], "overdue")
        self.assertEqual(one["check"], "Agenda due 24 hours before the meeting: link missing")
        (same,) = agenda_rows(date(2026, 10, 26))
        self.assertEqual(same["severity"], "overdue")
        (far,) = agenda_rows(date(2026, 10, 21))
        self.assertEqual(far["severity"], "waiting")
        self.assertEqual(far["check"], "Agenda link not added yet · flagged from 24 Oct")

    def test_standard_checks(self):
        rows = data.standard_checks(date(2026, 10, 21))
        folder_rows = [r for r in rows if r["area"] == "Standard"]
        self.assertEqual([r["body"] for r in folder_rows], ["gc", "uc", "jboard"])
        for r in folder_rows:
            self.assertEqual(r["severity"], "check")
            self.assertEqual(r["fix_label"], "Fix on this site")
            self.assertIn("records last confirmed complete: never", r["check"])
            self.assertIn("(records officer not named)", r["owner_role"])
        link_rows = [r for r in rows if r["check"] == "Box folder shared link not added"]
        self.assertEqual({r["body"] for r in link_rows}, set(data.BOX_FOLDERS))
        self.assertTrue(all(r["fix_label"] == "Fix in Box" for r in link_rows))
        by_body = {r["body"]: r for r in link_rows}
        self.assertEqual(by_body["senate"]["owner_role"], "Senate Secretary")
        self.assertEqual(by_body["gc"]["owner_role"], "Graduate Council records officer")
        # Once a folder has a shared link, its row goes away.
        data.BOX_FOLDERS["gc"]["shared_url"] = data.MOCK_BOX + "s/abc"
        try:
            self.assertNotIn("gc", {r["body"] for r in data.standard_checks(date(2026, 10, 21)) if r["area"] == "Links"})
        finally:
            data.BOX_FOLDERS["gc"]["shared_url"] = None
        self.assertTrue(any(r["body"] == "gc" for r in data.all_checks(date(2026, 10, 21))))

    def test_standard_by_body(self):
        rows = {r["key"]: r for r in data.standard_by_body(date(2026, 10, 21))}
        self.assertEqual(list(rows), ["senate", "eboard", "gc", "uc", "jboard"])
        senate = rows["senate"]
        self.assertEqual(senate["adapter_label"], "Senate's Notion")
        self.assertEqual(senate["records_officer"], "Senate Secretary")
        self.assertEqual(senate["agendas"], "Next: Senate 57 #16, link not added · flagged from 24 Oct")
        self.assertEqual(
            senate["minutes"],
            "3 meetings past 14 days with no minutes link (oldest: #12, 83 days) · #15 due by 28 Oct 2026",
        )
        self.assertEqual(senate["folder_link"], "Not added")
        self.assertEqual(senate["severity"], "overdue")
        eboard = rows["eboard"]
        self.assertTrue(eboard["example"])
        self.assertEqual(eboard["agendas"], "No upcoming meeting listed")
        self.assertEqual(eboard["minutes"], "4 meetings past 14 days with no minutes link (oldest: #1, 57 days)")
        self.assertEqual(eboard["severity"], "overdue")
        for key in ("gc", "uc", "jboard"):
            self.assertEqual(rows[key]["adapter_label"], "Box folder only")
            self.assertEqual(rows[key]["records_officer"], "Not named")
            self.assertEqual(rows[key]["agendas"], "Can\'t check: folder only")
            self.assertEqual(rows[key]["minutes"], "Can\'t check: folder only; records last confirmed: never")
            self.assertEqual(rows[key]["folder_link"], "Not added")
            self.assertEqual(rows[key]["severity"], "check")
            self.assertEqual(rows[key]["severity_label"], "Check")

    def test_seeded_checks_roster_and_schema(self):
        rows = data.seeded_checks(date(2026, 10, 21))
        schema = next(r for r in rows if r["area"] == "Sync" and r["severity"] != "ok")
        self.assertIn("Senate Motions property 'Status'", schema["check"])
        self.assertIn("Motion statuses are hidden until it's fixed.", schema["check"])
        self.assertEqual(schema["item"], "Senate's Notion · Motions")
        for r in rows:
            if r["area"] == "Roster":
                self.assertEqual((r["fix_label"], r["fix_url"]), ("Fix on this site", "/admin/"), r["check"])
        seats = next(r for r in rows if r["check"].startswith("Seats:"))
        self.assertEqual(seats["item"], "E-Board · seats on this site (tick Voting on those seats)")
        copy = next(r for r in rows if r["check"].startswith("Roster copy in the Senate's Notion"))
        self.assertEqual(copy["severity"], "ok")
        self.assertIn("pushed 12 min ago", copy["check"])
        for r in data.membership_checks(date(2026, 10, 21)):
            self.assertEqual((r["fix_label"], r["fix_url"]), ("Record on this site when filled", "/admin/"))

    def test_not_checked_list(self):
        self.assertIn("Attendance: private in the Senate's Notion, never synced.", data.NOT_CHECKED)
        self.assertTrue(any("Graduate Council, Undergraduate Council and Judicial Board folders" in x for x in data.NOT_CHECKED))
        self.assertTrue(any("tagged for accessibility" in x for x in data.NOT_CHECKED))

    def test_meeting_checks_never_use_box_knowledge(self):
        for today in (date(2026, 10, 21), date(2026, 10, 25), date(2026, 8, 5)):
            for r in data.meeting_checks(today):
                self.assertNotIn("posted in Box", r["check"])
        # Upcoming meeting without a link: waiting, then overdue; there is no third state.
        rows = data.meeting_checks(date(2026, 10, 21))
        self.assertEqual([r["severity"] for r in rows if "#16" in r["item"]], ["waiting"])

    def test_sample_past_meetings_raise_realistic_flags(self):
        rows = data.meeting_checks(date(2026, 10, 21))
        flagged = {r["item"].split(" · ")[0] for r in rows if r["check"].startswith("Minutes")}
        for ref in ("Senate 57 #13", "Senate 57 #14", "Senate 57 #15", "E-Board FY27 #2", "E-Board FY27 #3", "E-Board FY27 #4"):
            self.assertIn(ref, flagged)
        agenda = {r["item"].split(" · ")[0] for r in rows if r["check"] == "No agenda link on the meeting record"}
        self.assertIn("Senate 57 #13", agenda)

    def test_stale_budget_check(self):
        rows = data.budget_checks(date(2026, 10, 21))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["check"], "Quoted budget is older than the newest E-Board meeting record")
        self.assertEqual(rows[0]["severity"], "check")
        self.assertEqual(rows[0]["fix_label"], "Fix in Wagtail")
        self.assertIn("E-Board FY27 #4", rows[0]["item"])
        # Before any newer E-Board meeting exists, the quote is current.
        self.assertEqual(data.budget_checks(date(2026, 9, 1)), [])

    def test_minutes_soon_within_14_days(self):
        rows = data.meeting_checks(date(2026, 8, 5))
        soon = [r for r in rows if r["severity"] == "soon" and "Senate 57 #12" in r["item"]]
        self.assertEqual(len(soon), 1)
        self.assertIn("13 Aug 2026", soon[0]["check"])

    def test_sources_built_from_sync(self):
        sources = data.build_sources({**data.SYNC, "notion_minutes_ago": 7})
        self.assertEqual(sources["meeting_senate"]["line"], "Meeting record: Senate's Notion · synced 7 min ago")
        self.assertIn("synced 7 min ago", sources["agenda_items_option"]["line"])
        self.assertIn("synced 7 min ago", sources["motions"]["line"])
        self.assertEqual(sources["wagtail"]["edit_url"], "/admin/")
        self.assertEqual(
            set(sources),
            {
                "meeting_senate",
                "meeting_eboard",
                "folder_only",
                "agenda_items_option",
                "file",
                "motions",
                "in_minutes",
                "roster",
                "quoted_budget",
                "wagtail",
            },
        )

    def test_source_lines_and_edit_links(self):
        src = data.build_sources()
        self.assertEqual(
            src["meeting_eboard"]["line"],
            "Meeting record: entered on this site by the E-Board Secretary · updated 24 Aug 2026",
        )
        self.assertEqual((src["meeting_eboard"]["edit_label"], src["meeting_eboard"]["edit_url"]), ("Edit on this site", "/admin/"))
        self.assertEqual(
            src["folder_only"]["line"],
            "Records: files in this body's Box folder. It doesn't list meetings on this site.",
        )
        self.assertEqual(src["file"]["line"], "Documents: Word files in Box, published as PDF · links checked 19 Oct 2026")
        self.assertEqual(
            src["roster"]["line"],
            "Roster: entered on this site by each body's roster officer · last change 25 Aug 2026",
        )
        self.assertEqual((src["roster"]["edit_label"], src["roster"]["edit_url"]), ("Edit on this site", "/admin/"))
        self.assertEqual(src["in_minutes"]["edit_label"], "Open in Box")
        self.assertEqual(src["motions"]["edit_url"], data.MOCK_NOTION)
        self.assertEqual(data.SYNC["eboard_entry_updated"], date(2026, 8, 24))
        self.assertEqual(data.SYNC["roster_updated"], date(2026, 8, 25))

    def test_bodies_and_folder_bodies(self):
        self.assertEqual(data.BODIES["senate"]["adapter"], "notion")
        self.assertEqual(data.BODIES["senate"]["fix_label"], "Fix in Notion")
        self.assertFalse(data.BODIES["senate"]["example"])
        self.assertEqual(data.BODIES["eboard"]["adapter"], "site")
        self.assertEqual(data.BODIES["eboard"]["fix_url"], "/admin/")
        self.assertTrue(data.BODIES["eboard"]["example"])
        self.assertEqual(list(data.FOLDER_BODIES), ["gc", "uc", "jboard"])
        for key, b in data.FOLDER_BODIES.items():
            self.assertEqual(b["adapter"], "folder")
            self.assertIsNone(b["records_officer"])
            self.assertIsNone(b["records_confirmed"])
            self.assertIn(b["folder"], data.BOX_FOLDERS)
            self.assertIsNone(data.BOX_FOLDERS[b["folder"]]["shared_url"])
        self.assertEqual(data.FOLDER_BODIES["uc"]["note"], "Including the four Class Councils.")
        self.assertEqual(data.FOLDER_BODIES["jboard"]["draft"], "Judicial Board bylaws")
        self.assertEqual(data.BOX_FOLDERS["jboard"]["path"], "Public Records/Judicial Board/2026-27 JBoard 2026-27/")

    def test_every_meeting_has_a_document_name(self):
        for m in data.MEETINGS:
            self.assertIn("record_edited", m)
            self.assertNotIn("notion_edited", m)
            self.assertTrue(m["document_name"].endswith(f"#{m['number']:02d} Agenda.pdf"), m["document_name"])
        self.assertEqual(data.find_meeting("eboard", "fy27", 1)["document_name"], "2026-08-25 EBoard FY27 #01 Agenda.pdf")
        self.assertEqual(data.find_meeting("senate", "57", 12)["document_name"], "2026-07-30 Senate 57 #12 Agenda.pdf")

    def test_records_standard(self):
        self.assertEqual(len(data.RECORDS_STANDARD), 8)
        self.assertTrue(all(r["rule"] and r["check"] for r in data.RECORDS_STANDARD))
        self.assertEqual(data.RECORDS_STANDARD_JBOARD_NOTE["draft"], "Judicial Board bylaws")

    def test_only_the_senate_row_mentions_notion(self):
        for r in data.RECORDS_BY_BODY:
            blob = " ".join(str(v) for v in r.values())
            if r["body"] == "Senate":
                self.assertIn("Notion", blob)
            else:
                self.assertNotIn("Notion", blob, r["body"])
                self.assertTrue(r["example"])
        self.assertEqual(len(data.NEVER_LIST), 7)
        self.assertTrue(data.ROLLOVER_STEPS[1].startswith("Set the body's new term as current on this site."))
        self.assertIn("accessibility tags", " ".join(data.OFFICER_RULES))
        self.assertEqual(len(data.MOTIONS_MOCK), 2)
        for r in data.MOTIONS_MOCK:
            self.assertEqual(set(r), {"motion", "meeting", "status", "file", "public"})

    def test_thresholds_complete(self):
        self.assertEqual(len(data.THRESHOLDS), 17)
        for t in data.THRESHOLDS.values():
            self.assertTrue(t["cite"])

    def test_box_embed_only_for_shared_links(self):
        self.assertEqual(data.box_embed_url("https://rpi.box.com/s/abc"), "https://rpi.box.com/embed/s/abc")
        self.assertIsNone(data.box_embed_url("https://rpi.box.com/v/archive"))
        self.assertIsNone(data.box_embed_url(None))

    def test_decisions_are_senate_motions_with_a_file(self):
        self.assertEqual(data.DECISIONS, data.SAMPLE_DECISIONS)
        for d in data.DECISIONS:
            self.assertEqual(d["body"], "senate", d["id"])
            self.assertTrue(d["motion_file"].startswith(data.MOCK_BOX + "s/sample-motion-"), d["id"])
            self.assertIn("Senate 57 #", d["motion_file_name"])
            self.assertTrue(d["motion_file_name"].endswith(".pdf"))
        done = data.find_decision("sample-senate-done")
        self.assertEqual(done["ref"], "Senate 57 #14, item 8b")
        self.assertEqual(done["motion_file_name"], "2026-09-23 Senate 57 #14 Motion - Webex link on every Senate meeting notice.pdf")
        failed = data.find_decision("sample-senate-failed")
        self.assertEqual(failed["ref"], "Senate 57 #13, item 8a")
        self.assertEqual(failed["status"], "failed")
        thresholds = {d["id"]: d["threshold"] for d in data.DECISIONS}
        self.assertEqual(thresholds["sample-senate-appointment"], "eb_appointment")
        self.assertEqual(thresholds["sample-senate-bylaw"], "senate_bylaws")
        self.assertIsNone(thresholds["sample-senate-failed"])
        self.assertIsNone(thresholds["sample-senate-tabled"])
        self.assertIsNone(thresholds["sample-senate-done"])
        self.assertIsNone(data.find_decision("eb-fy27-01-a"))
        for m in data.MEETINGS:
            for section in m["sections"]:
                for item in section["items"]:
                    self.assertNotIn("decision_id", item)

    def test_statuses_cover_vocabulary(self):
        used = {d["status"] for d in data.DECISIONS}
        for status in ("passed", "failed", "tabled", "done", "waiting"):
            self.assertIn(status, used)
        self.assertEqual(sum(1 for d in data.DECISIONS if d["sample"]), 5)
