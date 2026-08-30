from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTestCase

from home.models import HomePage

from .models import BranchPage


class BranchPageCTATests(WagtailPageTestCase):
    def setUp(self):
        root_page = Page.get_first_root_node()
        self.homepage = HomePage(title="Home")
        root_page.add_child(instance=self.homepage)
        Site.objects.create(
            hostname="testsite",
            root_page=self.homepage,
            is_default_site=True,
        )

    def create_branch(self, body):
        branch = BranchPage(
            title="Student Senate",
            branch_type="senate",
            body=body,
        )
        self.homepage.add_child(instance=branch)
        return branch

    def test_external_call_to_action_renders(self):
        branch = self.create_branch(
            [
                (
                    "call_to_action",
                    {
                        "text": "Join the Senate",
                        "url": "https://example.com/join",
                        "style": "primary",
                    },
                )
            ]
        )

        response = self.client.get(branch.url)

        self.assertContains(response, "Join the Senate")
        self.assertContains(response, 'href="https://example.com/join"')

    def test_internal_call_to_action_still_renders(self):
        branch = self.create_branch(
            [
                (
                    "call_to_action",
                    {
                        "text": "Back to Home",
                        "page": self.homepage,
                        "style": "secondary",
                    },
                )
            ]
        )

        response = self.client.get(branch.url)

        self.assertContains(response, "Back to Home")
        self.assertContains(response, 'href="/"')
