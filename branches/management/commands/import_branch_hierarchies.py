"""
Management command to create RolePlacement models from a CSV file.

MemberRoleAssignments are global. They are the container that
stores that a member has a given role. The referenced MemberProfiles
and Roles must exist before they can be assigned (see import_members
and import_roles).

Usage:
    python manage.py import_branch_hierarchies branch_hierarchies.csv
    python manage.py import_branch_hierarchies branch_hierarchies.csv --dry-run
    python manage.py import_branch_hierarchies branch_hierarchies.csv --clear
    python manage.py import_branch_hierarchies branch_hierarchies.csv --branch <branch_type>

CSV format (header row required):
    branch,role,tier,title

  - branch: branch to whose member listing page the assignments are to
    be displayed on.
  - role: name of the role to display on the page.
  - tier: integer tier level to display the role in.
  - title: (optional) role title override to be displayed on the page.
"""

import csv

from django.core.management.base import BaseCommand, CommandError


from branches.models import (
    RolePlacement,
    BranchPage,
    MemberListingPage,
    Role,
    BRANCH_CHOICES,
    TierChoices,
)

REQUIRED_COLUMNS = {"branch", "role", "tier"}

class Command(BaseCommand):
    help = "Import RolePlacement models from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to the CSV file to import.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate the CSV and report what would happen, without saving.",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Remove all existing RolePlacements before importing. "
                "If branches are specified, only the RolePlacements for that branch will be removed."
        )
        parser.add_argument(
            "--branch",
            type=str,
            help="Limit importing/clearing to only specified branches. "
                "Multiple branches can be specified by delimiting them with a comma."
        )

    def handle(self, *args, **options):
        csv_path = options["csv_file"]
        dry_run = options["dry_run"]
        clear = options["clear"]
        branch = options["branch"]

        try:
            with open(csv_path, newline="", encoding="utf-8-sig") as f:
                rows = list(csv.DictReader(f))
        except FileNotFoundError:
            raise CommandError(f"File not found: {csv_path}")

        if not rows:
            raise CommandError("CSV file is empty (no data rows).")

        missing = REQUIRED_COLUMNS - set(rows[0].keys())
        if missing:
            raise CommandError(
                f"CSV is missing required columns: {', '.join(sorted(missing))}"
            )

        if not branch:
            branches = [b[0] for b in BRANCH_CHOICES]
        else:
            branches = branch.split(',')
            for branch_id in branches:
                if not branch_id in [b[0] for b in BRANCH_CHOICES]:
                    raise CommandError(
                        f"{branch_id} is not a valid branch"
                    )

        listing_pages = {}
        for branch_page in BranchPage.objects.live().filter(branch_type__in=branches):
            listing = (
                MemberListingPage.objects.live()
                .child_of(branch_page)
                .first()
            )
            if listing:
                listing_pages[branch_page.branch_type] = listing

        if not listing_pages:
            raise CommandError(
                "No MemberListingPages found under any BranchPage. "
                "Create them in the Wagtail admin first."
            )

        if clear and not dry_run:
            count = RolePlacement.objects.filter(page__in=listing_pages.values()).delete()[0]
            self.stdout.write(
                self.style.WARNING(f"Cleared {count} existing role placements.")
            )

        stats = {"created": 0, "skipped": 0, "errors": 0}

        for i, row in enumerate(rows, start=2):  # row 1 is the header
            row = {k: (v or "").strip() for k, v in row.items()}
            branch_id = row.get("branch", "")
            role_code = row.get("role", "")
            tier_str = row.get("tier", "")
            title = row.get("title", "")

            if not branch_id in branches:
                if not branch_id in [b[0] for b in BRANCH_CHOICES]:
                    self.stderr.write(self.style.ERROR(f"Row {i}: {branch_id} not a valid branch, skipping."))
                    stats["errors"] += 1
                else:
                    self.stderr.write(self.style.WARNING(f"Row {i}: {branch_id} not in selected branches, skipping."))
                    stats["skipped"] += 1
                continue
            if not listing_pages[branch_id]:
                self.stderr.write(self.style.ERROR(f"Row {i}: no member listing page for branch {branch_id}, skipping."))
                stats["errors"] += 1
                continue
            if not role_code:
                self.stderr.write(self.style.ERROR(f"Row {i}: missing role, skipping."))
                stats["errors"] += 1
                continue

            try:
                tier = int(tier_str)
            except ValueError:
                self.stderr.write(self.style.ERROR(f"Row {i}: invalid tier {tier}, skipping."))
                stats["errors"] += 1
                continue
            if tier not in TierChoices:
                self.stderr.write(self.style.ERROR(f"Row {i}: invalid tier {tier}, skipping."))
                stats["errors"] += 1
                continue

            try:
                role = Role.objects.get(role_code=role_code)
            except Role.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Row {i}: unable to fetch role '{role_code}', skipping."))
                stats["errors"] += 1
                continue

            if dry_run:
                self.stdout.write(f"Row {i}: would create placement for '{role_code}' on {branch}")
                stats["created"] += 1
                continue

            role.placements.add(RolePlacement(
                role=role,
                page=listing_pages[branch_id],
                tier=tier,
                display_name=title,
            ))
            role.save()
            stats["created"] += 1

        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"{prefix}Branch hierarchy import complete:"))
        self.stdout.write(f"  Role placements created:   {stats['created']}")
        if stats["skipped"]:
            self.stdout.write(self.style.WARNING(f"  Skipped:                {stats['skipped']}"))
        if stats["errors"]:
            self.stdout.write(self.style.ERROR(f"  Errors:                 {stats['errors']}"))