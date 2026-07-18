"""Bulk Source Import -- ARu Intelligence Phase 2.

No CSV import/export existed anywhere in this repo before this script.
`bulk_generate_articles.py` even documents why it deliberately avoids
Notion's *native* CSV import (it can't set Select/Relation properties
correctly). This script takes the same approach every other creation
script in this repo uses -- read structured input, write through the
Notion API directly -- just with `csv.DictReader` as the structured input
instead of a hardcoded Python list, so hundreds of Source Library rows can
be added without hand-creating hundreds of Notion pages.

Required CSV columns: Source Name, URL
Optional columns (sensible defaults applied when blank): Source Type,
Category, Country, Region, City, Importance (default Medium),
Check Frequency (default Weekly)

Dedup: rows whose URL already exists in Source Library are skipped and
logged, never created twice -- same "don't silently duplicate" principle
as duplicate_guard.py, applied here to sources rather than articles.
"""
import os
import csv
import sys
import time

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
REPO_ROOT = os.path.dirname(NOTION_BUILD_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, AUTOMATION_DIR)

from notion_api import load_env, notion_request, query_database, get_prop  # noqa: E402
from source_watcher import ensure_schema, IMPORTANCE_LEVELS  # noqa: E402
from source_categories import SOURCE_CATEGORIES  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")
DEFAULT_CSV_PATH = os.path.join(AUTOMATION_DIR, "data", "source_library_import_template.csv")

DEFAULTS = {
    "Source Type": "政府",
    "Importance": "Medium",
    "Check Frequency": "Weekly",
}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def get_existing_urls(token, source_library_db_id):
    pages = query_database(token, source_library_db_id)
    return {get_prop(p, "URL", "url") for p in pages if get_prop(p, "URL", "url")}


def read_rows(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def build_properties(row):
    props = {
        "Source Name": {"title": [{"text": {"content": row["Source Name"].strip()}}]},
        "URL": {"url": row["URL"].strip()},
        "Status": {"select": {"name": "Active"}},
        "Source Type": {"select": {"name": (row.get("Source Type") or DEFAULTS["Source Type"]).strip()}},
        "Importance": {"select": {"name": (row.get("Importance") or DEFAULTS["Importance"]).strip()}},
        "Check Frequency": {"select": {"name": (row.get("Check Frequency") or DEFAULTS["Check Frequency"]).strip()}},
    }
    if row.get("Category", "").strip():
        props["Category"] = {"select": {"name": row["Category"].strip()}}
    if row.get("Country", "").strip():
        props["Country"] = {"select": {"name": row["Country"].strip()}}
    if row.get("Region", "").strip():
        props["Region"] = {"select": {"name": row["Region"].strip()}}
    if row.get("City", "").strip():
        props["City"] = {"rich_text": [{"text": {"content": row["City"].strip()}}]}
    return props


def import_csv(env, csv_path):
    token = env["NOTION_TOKEN"]
    source_library_db = env["SOURCE_LIBRARY_DB_ID"]
    source_monitor_db = env["SOURCE_MONITOR_DB_ID"]

    log(f"Reading {csv_path}...")
    rows = read_rows(csv_path)
    log(f"  {len(rows)} row(s) found")

    log("Ensuring schema (any new Category/Country/Region/Importance values in the CSV will be added)...")
    # Extend option lists with any values present in the CSV but not yet known,
    # so page creation never fails with an "invalid select option" error.
    categories = set(SOURCE_CATEGORIES)
    countries, regions, importances = set(), set(), set(IMPORTANCE_LEVELS)
    for row in rows:
        if row.get("Category", "").strip():
            categories.add(row["Category"].strip())
        if row.get("Country", "").strip():
            countries.add(row["Country"].strip())
        if row.get("Region", "").strip():
            regions.add(row["Region"].strip())
        if row.get("Importance", "").strip():
            importances.add(row["Importance"].strip())
    ensure_schema(token, source_library_db, source_monitor_db)
    if categories - set(SOURCE_CATEGORIES) or countries or regions:
        notion_request(token, "PATCH", f"/databases/{source_library_db}", {
            "properties": {
                "Category": {"select": {"options": [{"name": c} for c in categories]}},
                "Country": {"select": {"options": [{"name": c} for c in countries]}} if countries else {"select": {"options": []}},
                "Region": {"select": {"options": [{"name": r} for r in regions]}} if regions else {"select": {"options": []}},
            }
        })

    log("Checking existing Source Library URLs for duplicates...")
    existing_urls = get_existing_urls(token, source_library_db)
    log(f"  {len(existing_urls)} existing source(s)")

    created, skipped_duplicate, skipped_invalid, errored = 0, 0, 0, 0
    for row in rows:
        name = (row.get("Source Name") or "").strip()
        url = (row.get("URL") or "").strip()
        if not name or not url:
            log(f"  SKIP (missing Source Name or URL): {row}")
            skipped_invalid += 1
            continue
        if url in existing_urls:
            log(f"  SKIP (already exists): {name} ({url})")
            skipped_duplicate += 1
            continue
        try:
            notion_request(token, "POST", "/pages", {
                "parent": {"database_id": source_library_db},
                "properties": build_properties(row),
            })
            log(f"  CREATED: {name} ({url})")
            existing_urls.add(url)
            created += 1
        except RuntimeError as e:
            log(f"  ERROR creating {name}: {e}")
            errored += 1

    log("")
    log("=" * 70)
    log(f"DONE. {created} created, {skipped_duplicate} skipped (duplicate URL), "
        f"{skipped_invalid} skipped (missing required field), {errored} errored.")
    return created, skipped_duplicate, skipped_invalid, errored


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=DEFAULT_CSV_PATH)
    args = parser.parse_args()

    env = load_env(ENV_PATH)
    import_csv(env, args.csv)


if __name__ == "__main__":
    main()
