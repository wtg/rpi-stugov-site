"""
Management command to import MemberProfile snippets from a CSV file.

MemberProfiles are global. They must exist before assignments can reference
them (see import_assignments).

Usage:
    python manage.py import_members members.csv
    python manage.py import_members members.csv --dry-run
    python manage.py import_members members.csv --clear
    python manage.py import_members members.csv --use-names

CSV format (header row required):
    first_name,last_name,rcs_id,class_year,major,bio

  - rcs_id: the RCS ID of the member.
  - class_year, major, bio: all optional (leave blank if unknown)

MemberProfiles are matched/upserted by RCS ID unless directed to use names.
"""

import csv

from django.core.management.base import BaseCommand, CommandError

from branches.models import (
    MemberProfile,
)


REQUIRED_COLUMNS = {"first_name", "last_name", "rcs_id"}


class Command(BaseCommand):
    help = "Import member profiles and branch placements from a CSV file."

    def add_arguments(self, parser):
        parser.add_argument(
            "csv_file",
            type=str,
            help="Path to the CSV file to import.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate the CSV and report what would happen, without saving.",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Remove all existing MemberProfiles before importing."
        )
        parser.add_argument(
            "--use-names",
            action="store_true",
            help="Use first and last name for matching instead of rcs_id."
        )

    def handle(self, *args, **options):
        csv_path = options["csv_file"]
        dry_run = options["dry_run"]
        clear = options["clear"]
        use_names = options["use_names"]

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
            count = MemberProfile.objects.all().delete()[0]
            self.stdout.write(
                self.style.WARNING(f"Cleared {count} existing placements.")
            )

        # -- Process rows --
        stats = {
            "created": 0,
            "updated": 0,
            "errors": 0,
        }

        for i, row in enumerate(rows, start=2):  # start=2 because row 1 is header
            row = {k: (v or "").strip() for k, v in row.items()}
            first_name = row.get("first_name", "")
            last_name = row.get("last_name", "")
            rcs_id = row.get("rcs_id", "")

            if not first_name or not last_name:
                self.stderr.write(
                    self.style.ERROR(f"Row {i}: missing first or last name, skipping.")
                )
                stats["errors"] += 1
                continue
            if not rcs_id:
                self.stderr.write(
                    self.style.ERROR(f"Row {i}: missing rcs_id, skipping.")
                )
                stats["errors"] += 1
                continue

            if dry_run:
                if use_names:
                    exists = MemberProfile.objects.filter(
                        first_name__iexact=first_name,
                        last_name__iexact=last_name,
                    ).exists()
                    action = "update" if exists else "create"
                    self.stdout.write(
                        f"Row {i}: would {action} profile '{first_name} {last_name}' "
                    )
                else:
                    exists = MemberProfile.objects.filter(
                        rcs_id__iexact=rcs_id,
                    ).exists()
                    action = "update" if exists else "create"
                    self.stdout.write(
                        f"Row {i}: would {action} profile '{rcs_id}' "
                    )
                stats["created" if action == "create" else "updated"] += 1
                continue

            profile_defaults = {
                "first_name": first_name,
                "last_name": last_name,
                "rcs_id": rcs_id,
            }
            if row.get("class_year"):
                profile_defaults["class_year"] = row["class_year"]
            if row.get("major"):
                profile_defaults["major"] = row["major"]
            if row.get("bio"):
                profile_defaults["bio"] = row["bio"]

            if use_names:
                _, created = MemberProfile.objects.update_or_create(
                    first_name__iexact=first_name,
                    last_name__iexact=last_name,
                    defaults=profile_defaults,
                )
            else:
                _, created = MemberProfile.objects.update_or_create(
                    rcs_id__iexact=rcs_id,
                    defaults=profile_defaults,
                )
            stats["created" if created else "updated"] += 1

        # -- Summary --
        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"{prefix}Member profile import complete:"))
        self.stdout.write(f"  Profiles created:   {stats['created']}")
        self.stdout.write(f"  Profiles updated:   {stats['updated']}")
        if stats["errors"]:
            self.stdout.write(
                self.style.ERROR(f"  Errors:             {stats['errors']}")
            )
