"""
Management command to sync the Box public records folder into BoxFileCache.

Usage:
    python manage.py sync_box_records

Requires BOX_CLIENT_ID, BOX_CLIENT_SECRET, and BOX_ENTERPRISE_ID to be set
in the environment (or in Django settings). Uses the Box Python SDK with
Client Credentials Grant (CCG) authentication — no user interaction needed.

The command:
  1. Authenticates to Box via CCG (service account)
  2. Recursively lists all files in BOX_RECORDS_FOLDER_ID
  3. For each file, creates or updates a BoxFileCache entry
  4. Deletes cache entries for files that no longer exist in Box
  5. Infers record_type from filename substrings

Run this on a cron schedule (e.g. every 15-60 minutes) to keep the
records page in sync with Box.
"""

import re
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from boxsdk import CCGAuth, Client
from boxsdk.exception import BoxAPIException

from records.models import BoxFileCache, BOX_FILE_TYPE_CHOICES


# Map filename substrings to record types.
# Order matters — first match wins.
TYPE_PATTERNS = [
    (r"\bminutes?\b", "minutes"),
    (r"\bagendas?\b", "agenda"),
    (r"\bmotions?\b", "motion"),
    (r"\bconstitutions?\b", "constitution"),
    (r"\bbylaws?\b", "bylaws"),
    (r"\bresolutions?\b", "resolution"),
    (r"\breports?\b", "report"),
    (r"\bbudgets?\b", "budget"),
]


def infer_record_type(filename):
    """
    Guess the record type from the filename.

    Checks filename against TYPE_PATTERNS (case-insensitive).
    Returns the first match, or "other" if nothing matches.
    """
    name_lower = filename.lower()
    for pattern, record_type in TYPE_PATTERNS:
        if re.search(pattern, name_lower):
            return record_type
    return "other"


def get_folder_path(item, root_folder_id):
    """
    Build a human-readable folder path from a Box item's path_collection.

    Strips everything up to and including the root sync folder, so paths
    look like "Senate/Minutes" rather than "All Files/.../Records/Senate/Minutes".
    """
    if not hasattr(item, "path_collection") or not item.path_collection:
        return ""
    entries = item.path_collection.get("entries", [])
    # Find the root folder in the path and take everything after it
    parts = []
    found_root = False
    for entry in entries:
        if entry["id"] == root_folder_id:
            found_root = True
            continue
        if found_root:
            parts.append(entry["name"])
    return "/".join(parts)


class Command(BaseCommand):
    help = "Sync files from the Box public records folder into BoxFileCache."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be synced without making changes.",
        )
        parser.add_argument(
            "--folder-id",
            type=str,
            default=None,
            help="Override BOX_RECORDS_FOLDER_ID from settings.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        folder_id = options["folder_id"] or getattr(
            settings, "BOX_RECORDS_FOLDER_ID", ""
        )

        if not folder_id:
            raise CommandError(
                "BOX_RECORDS_FOLDER_ID is not set. Set it in settings or "
                "pass --folder-id."
            )

        client_id = getattr(settings, "BOX_CLIENT_ID", "")
        client_secret = getattr(settings, "BOX_CLIENT_SECRET", "")
        enterprise_id = getattr(settings, "BOX_ENTERPRISE_ID", "")

        if not all([client_id, client_secret, enterprise_id]):
            raise CommandError(
                "Box API credentials not configured. Set BOX_CLIENT_ID, "
                "BOX_CLIENT_SECRET, and BOX_ENTERPRISE_ID in the environment."
            )

        # Authenticate with Box via Client Credentials Grant (CCG).
        # Requires the app to be authorized by a Box admin first.
        self.stdout.write("Authenticating with Box via CCG...")
        try:
            auth = CCGAuth(
                client_id=client_id,
                client_secret=client_secret,
                enterprise_id=enterprise_id,
            )
            client = Client(auth)
            user = client.user().get()
            self.stdout.write(f"Authenticated as {user.name} ({user.login})")
        except BoxAPIException as e:
            raise CommandError(f"Box authentication failed: {e}")

        # Recursively list all files in the folder
        self.stdout.write(f"Listing files in folder {folder_id}...")
        box_files = {}
        self._list_folder_recursive(client, folder_id, folder_id, box_files)
        self.stdout.write(f"Found {len(box_files)} files in Box.")

        if dry_run:
            self.stdout.write(self.style.WARNING("\n--- DRY RUN ---"))
            for file_id, info in sorted(
                box_files.items(), key=lambda x: x[1]["name"]
            ):
                self.stdout.write(
                    f"  {info['name']} "
                    f"(type={info['record_type']}, "
                    f"path={info['folder_path']})"
                )
            # Show what would be deleted
            stale = BoxFileCache.objects.exclude(
                box_file_id__in=box_files.keys()
            )
            if stale.exists():
                self.stdout.write(
                    f"\nWould delete {stale.count()} stale cache entries:"
                )
                for entry in stale:
                    self.stdout.write(f"  - {entry.name} ({entry.box_file_id})")
            return

        # Upsert files into cache
        created = 0
        updated = 0
        for file_id, info in box_files.items():
            obj, was_created = BoxFileCache.objects.update_or_create(
                box_file_id=file_id,
                defaults={
                    "name": info["name"],
                    "record_type": info["record_type"],
                    "box_folder_path": info["folder_path"],
                    "shared_link": info["shared_link"],
                    "size": info["size"],
                    "modified_at": info["modified_at"],
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        # Delete cache entries for files no longer in Box
        stale = BoxFileCache.objects.exclude(box_file_id__in=box_files.keys())
        deleted_count = stale.count()
        stale.delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Sync complete: {created} created, {updated} updated, "
                f"{deleted_count} deleted."
            )
        )

    def _list_folder_recursive(
        self, client, folder_id, root_folder_id, results
    ):
        """
        Recursively list all files in a Box folder.

        Populates `results` dict keyed by Box file ID with metadata dicts.
        Folders are traversed but not added to results (we only cache files).
        """
        try:
            folder = client.folder(folder_id)
            items = folder.get_items(
                fields=[
                    "id",
                    "name",
                    "size",
                    "modified_at",
                    "shared_link",
                    "path_collection",
                ]
            )
            for item in items:
                if item.type == "folder":
                    self._list_folder_recursive(
                        client, item.id, root_folder_id, results
                    )
                elif item.type == "file":
                    # Parse modified_at from Box's ISO format
                    modified_at = None
                    if item.modified_at:
                        try:
                            modified_at = timezone.make_aware(
                                datetime.fromisoformat(
                                    item.modified_at.replace("Z", "+00:00")
                                ),
                                timezone=timezone.utc,
                            )
                        except (ValueError, TypeError):
                            pass

                    # Get shared link URL if available
                    shared_link = ""
                    if item.shared_link and item.shared_link.get("url"):
                        shared_link = item.shared_link["url"]

                    results[item.id] = {
                        "name": item.name,
                        "record_type": infer_record_type(item.name),
                        "folder_path": get_folder_path(
                            item, root_folder_id
                        ),
                        "shared_link": shared_link,
                        "size": item.size or 0,
                        "modified_at": modified_at,
                    }
        except BoxAPIException as e:
            self.stderr.write(f"Error listing folder {folder_id}: {e}")
