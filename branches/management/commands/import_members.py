"""
Management command to import MemberProfile snippets and place them on
the correct MemberListingPage from a CSV file.

Roles are now branch-specific Role snippets, so run `import_roles` first to
create them; this command resolves each role name to an existing Role.

Usage:
    python manage.py import_members members.csv
    python manage.py import_members members.csv --dry-run
    python manage.py import_members members.csv --clear

CSV format (header row required):
    first_name,last_name,email,class_year,major,bio,branch,roles

  - branch: one of senate, eboard, uc, gc, jboard
  - roles: one or more Role names (matched within the row's branch),
    separated by semicolons, e.g.
    "Multicultural Leadership Chair;Class of 2028 Representative"
    (semicolons avoid conflicting with CSV commas)
  - email, class_year, major, bio: all optional (leave blank if unknown)

The command will:
  1. Create or update MemberProfile snippets (matched by first_name + last_name)
  2. Find the MemberListingPage under the matching BranchPage
  3. Create a BranchMemberPlacement linking the member to that page and
     assign the resolved Role snippets via the roles M2M

Duplicate placements (same member + same page) merge their roles.
"""

import csv

from django.core.management.base import BaseCommand, CommandError

from branches.models import (
    BranchMemberPlacement,
    BranchMemberRole,
    BranchPage,
    MemberListingPage,
    MemberProfile,
    Role,
    BRANCH_CHOICES,
)


# Build lookup dict for validation
VALID_BRANCHES = {code for code, _ in BRANCH_CHOICES}

REQUIRED_COLUMNS = {"first_name", "last_name", "branch", "roles"}


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

        # -- Pre-fetch roles, keyed by (branch, name) --
        roles_by_key = {
            (role.branch, role.name): role for role in Role.objects.all()
        }
        if not roles_by_key:
            raise CommandError(
                "No Role snippets found. Run `import_roles` first."
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
            row = {k: (v or "").strip() for k, v in row.items()}

            first_name = row.get("first_name", "")
            last_name = row.get("last_name", "")
            branch = row.get("branch", "")
            roles_raw = row.get("roles", "")

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

            # Parse semicolon-separated role names and resolve them to Role
            # snippets within this row's branch. Dedupe (preserving order) so a
            # repeated name doesn't create duplicate role assignments.
            role_names = list(
                dict.fromkeys(r.strip() for r in roles_raw.split(";") if r.strip())
            )
            if not role_names:
                self.stderr.write(
                    self.style.ERROR(f"Row {i}: no roles specified, skipping.")
                )
                stats["errors"] += 1
                continue

            roles = []
            unknown = []
            for role_name in role_names:
                role = roles_by_key.get((branch, role_name))
                if role is None:
                    unknown.append(role_name)
                else:
                    roles.append(role)
            if unknown:
                self.stderr.write(
                    self.style.ERROR(
                        f"Row {i}: no '{branch}' role(s) named {unknown}. "
                        f"Create them in roles.csv / import_roles first."
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
                    f"→ {branch} as {', '.join(role_names)}"
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

            # One placement per person per page; roles are stored as
            # BranchMemberRole grandchildren (one row per role). Add any
            # missing roles and commit via the Clusterable placement save.
            placement, placement_created = BranchMemberPlacement.objects.get_or_create(
                page=listing_page,
                member=profile,
            )

            existing_ids = set(
                placement.role_assignments.values_list("role_id", flat=True)
            )
            missing = [role for role in roles if role.id not in existing_ids]
            if missing:
                for role in missing:
                    placement.role_assignments.add(BranchMemberRole(role=role))
                placement.save()
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
