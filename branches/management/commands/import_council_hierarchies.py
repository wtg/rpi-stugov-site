"""
Management command to create RolePlacement models from a CSV file.

MemberRoleAssignments are global. They are the container that
stores that a member has a given role. The referenced MemberProfiles
and Roles must exist before they can be assigned (see import_members
and import_roles).

Usage:
    python manage.py import_council_hierarchies council_hierarchies.csv
    python manage.py import_council_hierarchies council_hierarchies.csv --dry-run
    python manage.py import_council_hierarchies council_hierarchies.csv --clear
    python manage.py import_council_hierarchies council_hierarchies.csv --class <classes>

CSV format (header row required):
    year,role,tier,title

  - year: class year of the council on which page the assignments
    are to be displayed.
  - role: name of the role to display on the page.
  - tier: integer tier level to display the role in.
  - title: (optional) role title override to be displayed on the page.
"""

import csv

from django.core.management.base import BaseCommand, CommandError


from branches.models import (
    RolePlacement,
    ClassCouncilPage,
    Role,
    TierChoices,
)

REQUIRED_COLUMNS = {"year", "role", "tier"}

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
            help="Remove all existing RolePlacement before importing. "
                "If branches are specified, only the RolePlacement for that branch will be removed."
        )
        parser.add_argument(
            "--class",
            type=str,
            help="Limit importing/clearing to only specified classes. "
                "Multiple classes can be specified by delimiting them with a comma."
        )

    def handle(self, *args, **options):
        csv_path = options["csv_file"]
        dry_run = options["dry_run"]
        clear = options["clear"]
        class_str = options["class"]

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

        live_councils = {c.class_year: c for c in ClassCouncilPage.objects.live()}
        if not live_councils:
            raise CommandError(
                "No ClassCouncilPages found. "
                "Create them in the Wagtail admin first."
            )

        if not class_str:
            classes = live_councils.keys()
        else:
            class_strs = class_str.split(',')
            classes = []
            for class_year_str in class_strs:
                try:
                    class_year = int(class_year_str)
                except ValueError:
                    raise CommandError(
                        f"{class_year_str} is not a valid class year"
                    )
                if not class_year in live_councils.keys():
                    raise CommandError(
                        f"There is no live ClassCouncilPage for the Class of {class_year_str}"
                    )
                classes.append(class_year)

        if clear and not dry_run:
            count = RolePlacement.objects.filter(page__in=[live_councils[c] for c in classes]).delete()[0]
            self.stdout.write(
                self.style.WARNING(f"Cleared {count} existing role configs.")
            )

        stats = {"created": 0, "skipped": 0, "errors": 0}

        for i, row in enumerate(rows, start=2):  # row 1 is the header
            row = {k: (v or "").strip() for k, v in row.items()}
            year_str = row.get("year", "")
            role_code = row.get("role", "")
            tier_str = row.get("tier", "")
            title = row.get("title", "")

            try:
                year = int(year_str)
            except ValueError:
                self.stderr.write(self.style.ERROR(f"Row {i}: {year_str} not a class year, skipping."))
                stats["errors"] += 1
                continue
            if not year in classes:
                if not year in live_councils.keys():
                    self.stderr.write(self.style.ERROR(f"Row {i}: No class council page for Class of {year} , skipping."))
                    stats["errors"] += 1
                else:
                    self.stderr.write(self.style.WARNING(f"Row {i}: Class of {year} not in selected classes, skipping."))
                    stats["skipped"] += 1
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
                self.stdout.write(f"Row {i}: would create config for '{role_code}' on Class of {year} Council")
                stats["created"] += 1
                continue

            role.placements.add(RolePlacement(
                role=role,
                page=live_councils[year],
                display_name=title,
                tier=tier,
            ))
            role.save()
            stats["created"] += 1

        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"{prefix}Class council hierarchy import complete:"))
        self.stdout.write(f"  Role configs created:   {stats['created']}")
        if stats["skipped"]:
            self.stdout.write(self.style.WARNING(f"  Skipped:                {stats['skipped']}"))
        if stats["errors"]:
            self.stdout.write(self.style.ERROR(f"  Errors:                 {stats['errors']}"))