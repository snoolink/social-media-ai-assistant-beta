#!/usr/bin/env python3
"""
Remove duplicate files that end with " 2" before the extension.
Example: "IMG_0505 2.MOV" is a duplicate of "IMG_0505.MOV"
"""

import os
import sys
import re

def find_and_remove_duplicates(folder: str, dry_run: bool = True) -> None:
    if not os.path.isdir(folder):
        print(f"Error: '{folder}' is not a valid directory.")
        sys.exit(1)

    # Pattern: filename ending with " 2" before the extension (e.g. "IMG_0505 2.MOV")
    pattern = re.compile(r'^(.*) 2(\.[^.]+)?$', re.IGNORECASE)

    duplicates = []

    for filename in os.listdir(folder):
        match = pattern.match(filename)
        if match:
            base = match.group(1)
            ext = match.group(2) or ''
            original = base + ext
            original_path = os.path.join(folder, original)
            duplicate_path = os.path.join(folder, filename)

            if os.path.exists(original_path):
                duplicates.append((duplicate_path, original_path))
            else:
                print(f"  [SKIP] '{filename}' — original '{original}' not found, leaving it alone.")

    if not duplicates:
        print("No duplicates found.")
        return

    print(f"\nFound {len(duplicates)} duplicate(s):\n")
    for dup, orig in duplicates:
        print(f"  DELETE: {os.path.basename(dup)}")
        print(f"    KEEP: {os.path.basename(orig)}\n")

    if dry_run:
        print("-- Dry run: no files were deleted. Run with --confirm to delete. --")
        return

    confirm = input(f"Delete {len(duplicates)} file(s)? [y/N]: ").strip().lower()
    if confirm != 'y':
        print("Aborted.")
        return

    deleted = 0
    for dup, _ in duplicates:
        try:
            os.remove(dup)
            print(f"Deleted: {os.path.basename(dup)}")
            deleted += 1
        except OSError as e:
            print(f"Error deleting '{dup}': {e}")

    print(f"\nDone. {deleted}/{len(duplicates)} file(s) deleted.")


def main():
    if len(sys.argv) < 2:
        print("Usage: python remove_duplicates.py <folder> [--confirm]")
        print("       --confirm   Actually delete files (default is dry run)")
        sys.exit(1)

    folder = sys.argv[1]
    dry_run = '--confirm' not in sys.argv

    if dry_run:
        print(f"[DRY RUN] Scanning '{folder}' for duplicates...")
    else:
        print(f"Scanning '{folder}' for duplicates...")

    find_and_remove_duplicates(folder, dry_run=dry_run)


if __name__ == '__main__':
    main()