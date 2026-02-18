"""
Management command to import MemberProfile snippets and place them on
the correct MemberListingPage from a CSV file.

Usage:
    python manage.py import_members members.csv
    python manage.py import_members members.csv --dry-run
    python manage.py import_members members.csv --clear

CSV format (header row required):
    first_name,last_name,email,class_year,major,bio,branch,role,role_title_override

  - branch: one of senate, eboard, uc, gc, jboard
  - role: one of the ROLE_CHOICES keys (grand_marshall, senator, president_union,
    vice_president, secretary, treasurer, council_president, representative,
    chair, vice_chair, member, chief_justice, justice)
  - role_title_override: optional custom title (leave blank to use role default)
  - email, class_year, major, bio: all optional (leave blank if unknown)

The command will:
  1. Create or update MemberProfile snippets (matched by first_name + last_name)
  2. Find the MemberListingPage under the matching BranchPage
  3. Create a BranchMemberPlacement linking the member to that page

Duplicate placements (same member + same page + same role) are skipped.
"""

import csv

from django.core.management.base import BaseCommand, CommandError

from branches.models import (
    BranchMemberPlacement,
    BranchPage,
    MemberListingPage,
    MemberProfile,
    ROLE_CHOICES,
    BRANCH_CHOICES,
)


# Build lookup dicts for validation
VALID_BRANCHES = {code for code, _ in BRANCH_CHOICES}
VALID_ROLES = {code for code, _ in ROLE_CHOICES}

REQUIRED_COLUMNS = {"first_name", "last_name", "branch", "role"}
ALL_COLUMNS = REQUIRED_COLUMNS | {
    "email",
    "class_year",
    "major",
    "bio",
    "role_title_override",
}


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
            help="Remove all existing BranchMemberPlacements before importing. "
                 "Does NOT delete MemberProfile snippets.",
        )

    def handle(self, *args, **options):
        csv_path = options["csv_file"]
        dry_run = options["dry_run"]
        clear = options["clear"]

        # -- Read and validate CSV --
        try:
            with open(csv_path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except FileNotFoundError:
            raise CommandError(f"File not found: {csv_path}")

        if not rows:
            raise CommandError("CSV file is empty (no data rows).")

        # Validate column headers
        headers = set(rows[0].keys())
        missing = REQUIRED_COLUMNS - headers
        if missing:
            raise CommandError(
                f"CSV is missing required columns: {', '.join(sorted(missing))}\n"
                f"Found columns: {', '.join(sorted(headers))}"
            )

        # -- Pre-fetch pages --
        # Build a map: branch_type -> MemberListingPage
        listing_pages = {}
        for branch_page in BranchPage.objects.live():
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

        # -- Clear existing placements if requested --
        if clear and not dry_run:
            count = BranchMemberPlacement.objects.count()
            BranchMemberPlacement.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f"Cleared {count} existing placements.")
            )

        # -- Process rows --
        stats = {
            "profiles_created": 0,
            "profiles_updated": 0,
            "placements_created": 0,
            "placements_skipped": 0,
            "errors": 0,
        }

        for i, row in enumerate(rows, start=2):  # start=2 because row 1 is header
            # Strip whitespace from all values
            row = {k: v.strip() for k, v in row.items()}

            first_name = row.get("first_name", "")
            last_name = row.get("last_name", "")
            branch = row.get("branch", "")
            role = row.get("role", "")

            # Validate required fields
            if not first_name or not last_name:
                self.stderr.write(
                    self.style.ERROR(f"Row {i}: missing first_name or last_name, skipping.")
                )
                stats["errors"] += 1
                continue

            if branch not in VALID_BRANCHES:
                self.stderr.write(
                    self.style.ERROR(
                        f"Row {i}: invalid branch '{branch}'. "
                        f"Must be one of: {', '.join(sorted(VALID_BRANCHES))}"
                    )
                )
                stats["errors"] += 1
                continue

            if role not in VALID_ROLES:
                self.stderr.write(
                    self.style.ERROR(
                        f"Row {i}: invalid role '{role}'. "
                        f"Must be one of: {', '.join(sorted(VALID_ROLES))}"
                    )
                )
                stats["errors"] += 1
                continue

            if branch not in listing_pages:
                self.stderr.write(
                    self.style.ERROR(
                        f"Row {i}: no MemberListingPage found under the "
                        f"'{branch}' branch. Create one in Wagtail first."
                    )
                )
                stats["errors"] += 1
                continue

            # -- Create or update MemberProfile --
            profile_defaults = {}
            if row.get("email"):
                profile_defaults["email"] = row["email"]
            if row.get("class_year"):
                try:
                    profile_defaults["class_year"] = int(row["class_year"])
                except ValueError:
                    self.stderr.write(
                        self.style.WARNING(
                            f"Row {i}: invalid class_year '{row['class_year']}', ignoring."
                        )
                    )
            if row.get("major"):
                profile_defaults["major"] = row["major"]
            if row.get("bio"):
                profile_defaults["bio"] = row["bio"]

            if dry_run:
                # Check if profile exists
                exists = MemberProfile.objects.filter(
                    first_name__iexact=first_name,
                    last_name__iexact=last_name,
                ).exists()
                action = "update" if exists else "create"
                self.stdout.write(
                    f"Row {i}: would {action} profile '{first_name} {last_name}' "
                    f"→ {branch} as {role}"
                )
                if action == "create":
                    stats["profiles_created"] += 1
                else:
                    stats["profiles_updated"] += 1
                stats["placements_created"] += 1
                continue

            profile, created = MemberProfile.objects.update_or_create(
                first_name__iexact=first_name,
                last_name__iexact=last_name,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    **profile_defaults,
                },
            )

            if created:
                stats["profiles_created"] += 1
            else:
                stats["profiles_updated"] += 1

            # -- Create BranchMemberPlacement --
            listing_page = listing_pages[branch]
            role_override = row.get("role_title_override", "")

            _, placement_created = BranchMemberPlacement.objects.get_or_create(
                page=listing_page,
                member=profile,
                role=role,
                defaults={"role_title_override": role_override},
            )

            if placement_created:
                stats["placements_created"] += 1
            else:
                stats["placements_skipped"] += 1

        # -- Summary --
        prefix = "[DRY RUN] " if dry_run else ""
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"{prefix}Import complete:"))
        self.stdout.write(f"  Profiles created:   {stats['profiles_created']}")
        self.stdout.write(f"  Profiles updated:   {stats['profiles_updated']}")
        self.stdout.write(f"  Placements created: {stats['placements_created']}")
        self.stdout.write(f"  Placements skipped: {stats['placements_skipped']}")
        if stats["errors"]:
            self.stdout.write(
                self.style.ERROR(f"  Errors:             {stats['errors']}")
            )
