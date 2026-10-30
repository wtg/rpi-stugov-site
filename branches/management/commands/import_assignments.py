"""
Management command to create MemberRoleAssignment snippets from a CSV file.

MemberRoleAssignments are global. They are the container that
stores that a member has a given role. The referenced MemberProfiles
and Roles must exist before they can be assigned(see import_members
and import_roles).

Usage:
    python manage.py import_assignemnts assignments.csv
    python manage.py import_assignemnts assignments.csv --dry-run
    python manage.py import_assignemnts assignments.csv --clear

CSV format (header row required):
    rcs_id,role

  - rcs_id: RCS ID of the member to whom the role is being assigned,
    e.g. "doej9"
  - role: name of the role to give the member,
    e.g. "Class of 2027 Representative"
"""

import csv

from django.core.management.base import BaseCommand, CommandError


from branches.models import (
    Role,
    MemberProfile,
    MemberRoleAssignment,
)


REQUIRED_COLUMNS = {"rcs_id", "role"}


class Command(BaseCommand):
    help = "Import MemberRoleAssignment snippets from a CSV file."

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
            help="Remove all existing MemberRoleAssignments before importing."
        )

    def handle(self, *args, **options):
        csv_path = options["csv_file"]
        dry_run = options["dry_run"]
        clear = options["clear"]

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

        if clear and not dry_run:
            count = MemberRoleAssignment.objects.count()
            MemberRoleAssignment.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f"Cleared {count} existing assignments.")
            )

        stats = {"created": 0, "updated": 0, "errors": 0}

        for i, row in enumerate(rows, start=2):  # row 1 is the header
            row = {k: (v or "").strip() for k, v in row.items()}
            rcs_id = row.get("rcs_id", "")
            role_name = row.get("role", "")

            if not rcs_id:
                self.stderr.write(self.style.ERROR(f"Row {i}: missing RCS ID, skipping."))
                stats["errors"] += 1
                continue
            if not role_name:
                self.stderr.write(self.style.ERROR(f"Row {i}: missing role, skipping."))
                stats["errors"] += 1
                continue

            try:
                member = MemberProfile.objects.get(rcs_id=rcs_id)
            except MemberProfile.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Row {i}: member with RCS ID {rcs_id} not found, skipping."))
                stats["errors"] += 1
                continue
            try:
                role = Role.objects.get(name=role_name)
            except Role.DoesNotExist:
                self.stderr.write(self.style.ERROR(f"Row {i}: role named {role_name} not found, skipping."))
                stats["errors"] += 1
                continue

            if dry_run:
                self.stdout.write(f"Row {i}: would create assignemnt '{member}' - '{role}'")
                stats["created"] += 1
                continue

            MemberRoleAssignment.objects.create(
                member=member,
                role=role,
            )
            stats["created"] += 1

        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"{prefix}Assigment import complete:"))
        self.stdout.write(f"  Assignments created:   {stats['created']}")
        if stats["errors"]:
            self.stdout.write(self.style.ERROR(f"  Errors:                 {stats['errors']}"))