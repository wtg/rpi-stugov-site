"""
Management command to create/update Role snippets from a CSV file.

Roles are branch-specific and carry the constituency they represent, so they
must exist before members can be assigned to them (see import_members).

Usage:
    python manage.py import_roles roles.csv
    python manage.py import_roles roles.csv --dry-run

CSV format (header row required):
    name,branch,tier,constituency_class,constituency_fsl

  - name: displayed role text, e.g. "Class of 2027 Representative"
  - branch: one of the BRANCH_CHOICES keys (senate, eboard, uc, gc, jboard)
  - tier: one of the HIERARCHY_TIERS keys
    (presiding, officers, chairs, members, advisors)
  - constituency_class: a graduating year, "graduate", or "none" (optional;
    defaults to "none"). Years must fall within the current selectable window.
  - constituency_fsl: associated, independent, or none (optional; blank = unset)

Roles are matched/upserted by (branch, name).
"""

import csv

from django.core.management.base import BaseCommand, CommandError

from branches.models import (
    Role,
    BRANCH_CHOICES,
    FSL_CHOICES,
    TIER_CHOICES,
    constituency_class_choices,
)


VALID_BRANCHES = {code for code, _ in BRANCH_CHOICES}
VALID_TIERS = {code for code, _ in TIER_CHOICES}
VALID_FSL = {code for code, _ in FSL_CHOICES}

REQUIRED_COLUMNS = {"name", "branch", "tier"}


class Command(BaseCommand):
    help = "Import Role snippets from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to the CSV file to import.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate the CSV and report what would happen, without saving.",
        )

    def handle(self, *args, **options):
        csv_path = options["csv_file"]
        dry_run = options["dry_run"]

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

        valid_classes = {code for code, _ in constituency_class_choices()}

        stats = {"created": 0, "updated": 0, "errors": 0}

        for i, row in enumerate(rows, start=2):  # row 1 is the header
            row = {k: (v or "").strip() for k, v in row.items()}
            name = row.get("name", "")
            branch = row.get("branch", "")
            tier = row.get("tier", "")
            constituency_class = row.get("constituency_class", "") or "none"
            constituency_fsl = row.get("constituency_fsl", "")

            if not name:
                self.stderr.write(self.style.ERROR(f"Row {i}: missing name, skipping."))
                stats["errors"] += 1
                continue
            if branch not in VALID_BRANCHES:
                self.stderr.write(self.style.ERROR(
                    f"Row {i}: invalid branch '{branch}'. "
                    f"Must be one of: {', '.join(sorted(VALID_BRANCHES))}"))
                stats["errors"] += 1
                continue
            if tier not in VALID_TIERS:
                self.stderr.write(self.style.ERROR(
                    f"Row {i}: invalid tier '{tier}'. "
                    f"Must be one of: {', '.join(sorted(VALID_TIERS))}"))
                stats["errors"] += 1
                continue
            if constituency_class not in valid_classes:
                self.stderr.write(self.style.ERROR(
                    f"Row {i}: invalid constituency_class '{constituency_class}'. "
                    f"Must be one of: {', '.join(sorted(valid_classes))}"))
                stats["errors"] += 1
                continue
            if constituency_fsl and constituency_fsl not in VALID_FSL:
                self.stderr.write(self.style.ERROR(
                    f"Row {i}: invalid constituency_fsl '{constituency_fsl}'. "
                    f"Must be one of: {', '.join(sorted(VALID_FSL))}"))
                stats["errors"] += 1
                continue

            if dry_run:
                exists = Role.objects.filter(branch=branch, name=name).exists()
                action = "update" if exists else "create"
                self.stdout.write(f"Row {i}: would {action} role '{branch}: {name}' ({tier})")
                stats["updated" if exists else "created"] += 1
                continue

            _, created = Role.objects.update_or_create(
                branch=branch,
                name=name,
                defaults={
                    "tier": tier,
                    "constituency_class": constituency_class,
                    "constituency_fsl": constituency_fsl,
                },
            )
            stats["created" if created else "updated"] += 1

        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"{prefix}Role import complete:"))
        self.stdout.write(f"  Roles created: {stats['created']}")
        self.stdout.write(f"  Roles updated: {stats['updated']}")
        if stats["errors"]:
            self.stdout.write(self.style.ERROR(f"  Errors:        {stats['errors']}"))
