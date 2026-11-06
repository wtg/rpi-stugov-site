"""
Management command to create/update Role snippets from a CSV file.

Roles are global and carry the constituency they represent. They must
exist before assignments can be reference them (see import_assignments).

Usage:
    python manage.py import_roles roles.csv
    python manage.py import_roles roles.csv --dry-run
    python manage.py import_roles roles.csv --clear

CSV format (header row required):
    name,role_code,positions,constituency

  - name: displayed role text, e.g. "Class of 2027 Representative"
  - role_code: unique identifier for this role
  - positions: number of positions this role can have
    (leave empty for no vacancies to be displayed)
  - constituency: a graduating year, "graduate", an FSL association
    ("associated" or "independent"), or "none" (optional; defaults to "none").
    Years must fall within the current selectable window.

Roles are matched/upserted by name.
"""

import csv

from django.core.management.base import BaseCommand, CommandError

from branches.models import (
    Role,
    constituency_choices,
)


REQUIRED_COLUMNS = {"name", "role_code"}


class Command(BaseCommand):
    help = "Import Role snippets from a CSV file."

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
            help="Remove all existing Roles before importing. "
                 "Will cascade removal to all existing assignments and role configs.",
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
            count = Role.objects.count()
            Role.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f"Cleared {count} existing roles.")
            )

        valid_constituencies = {code for code, _ in constituency_choices()}

        stats = {"created": 0, "updated": 0, "errors": 0}

        for i, row in enumerate(rows, start=2):  # row 1 is the header
            row = {k: (v or "").strip() for k, v in row.items()}
            name = row.get("name", "")
            role_code = row.get("role_code", "")
            positions_str = row.get("positions", "")
            constituency = row.get("constituency", "none")

            if not name:
                self.stderr.write(self.style.ERROR(f"Row {i}: missing name, skipping."))
                stats["errors"] += 1
                continue
            if not role_code:
                self.stderr.write(self.style.ERROR(f"Row {i}: missing role code, skipping."))
                stats["errors"] += 1
                continue
            if constituency not in valid_constituencies:
                self.stderr.write(self.style.ERROR(
                    f"Row {i}: invalid constituency '{constituency}'. "
                    f"Must be one of: {', '.join(sorted(valid_constituencies))}"))
                stats["errors"] += 1
                continue

            if not positions_str:
                positions = 0
            else:
                try:
                    positions = int(positions_str)
                except ValueError:
                    self.stderr.write(self.style.ERROR(f"Row {i}: positions '{positions_str}' not an integer, skipping."))
                    stats["errors"] += 1
                    continue

            if dry_run:
                exists = Role.objects.filter(name=name).exists()
                action = "update" if exists else "create"
                self.stdout.write(f"Row {i}: would {action} role '{role_code} ({name})'")
                stats["updated" if exists else "created"] += 1
                continue

            _, created = Role.objects.update_or_create(
                role_code=role_code,
                defaults={
                    "name": name,
                    "role_code": role_code,
                    "positions": positions,
                    "constituency": constituency,
                },
            )
            stats["created" if created else "updated"] += 1

        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"{prefix}Role import complete:"))
        self.stdout.write(f"  Roles created:   {stats['created']}")
        self.stdout.write(f"  Roles updated:   {stats['updated']}")
        if stats["errors"]:
            self.stdout.write(self.style.ERROR(f"  Errors:          {stats['errors']}"))
