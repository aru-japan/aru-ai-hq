"""Bulk-import Story Bank entries from a CSV (ChatGPT-curated content, per the
established role split: ChatGPT selects/curates Story Bank content, Claude
Code only imports/implements -- this script never invents a Story, it only
maps and writes what's already in the CSV).

Normalizes the incoming English-labeled CSV columns onto Story Bank's
existing Japanese Select vocabulary (Category/Subcategory/Season/Region/
Event Month) rather than creating a parallel English option set -- the same
naming-consistency principle Architecture-Specification-v1.0.md Sec.5/6
established for the other Knowledge Domains.

Usage:
    python3 bulk_import_story_bank.py data/story_bank_batch_001.csv
"""
import csv
import os
import sys

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)

from notion_api import load_env, notion_request, query_database, get_prop  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")

CATEGORY_MAP = {"Event": "イベント"}
SUBCATEGORY_MAP = {"Fireworks": "花火大会"}
SEASON_MAP = {"Summer": "夏", "Autumn": "秋", "Winter": "冬", "Spring": "春", "All Season": "通年"}
# Prefecture (or prefecture-pair) -> the existing 9-region Select value.
# "Fukuoka/Yamaguchi" spans two conventional regions (Kyushu/Chugoku) --
# mapped to 九州・沖縄 as a judgment call (Kanmon Straits fireworks are
# jointly hosted, Region is single-select, not multi-select). Flagged in the
# run's own report rather than decided silently.
REGION_MAP = {
    "Tokyo": "関東", "Kanagawa": "関東", "Chiba": "関東",
    "Niigata": "中部", "Nagano": "中部", "Aichi": "中部", "Shizuoka": "中部",
    "Akita": "東北", "Yamagata": "東北",
    "Shiga": "近畿", "Mie": "近畿",
    "Hokkaido": "北海道",
    "Fukuoka": "九州・沖縄",
    "Fukuoka/Yamaguchi": "九州・沖縄",  # judgment call -- see module docstring
}
MONTH_MAP = {
    "January": "1月", "February": "2月", "March": "3月", "April": "4月",
    "May": "5月", "June": "6月", "July": "7月", "August": "8月",
    "September": "9月", "October": "10月", "November": "11月", "December": "12月",
}
YES_NO_MAP = {"Yes": True, "No": False}


def existing_titles(token, db_id):
    pages = query_database(token, db_id)
    return {get_prop(p, "Title", "title") for p in pages}


def build_properties(row, warnings, row_num):
    title = row["Title"].strip()

    category = CATEGORY_MAP.get(row["Category"], row["Category"])
    subcategory = SUBCATEGORY_MAP.get(row["Subcategory"], row["Subcategory"])
    season = SEASON_MAP.get(row["Season"], row["Season"])
    region_raw = row["Region"].strip()
    region = REGION_MAP.get(region_raw)
    if region is None:
        warnings.append(f"  row {row_num} ({title}): unrecognized Region '{region_raw}', left unset")
    if "/" in region_raw:
        warnings.append(f"  row {row_num} ({title}): Region '{region_raw}' spans two conventional regions, "
                         f"Region is single-select -- mapped to '{region}' as a judgment call, please review")

    evergreen = YES_NO_MAP.get(row["Evergreen"].strip(), False)
    premium = YES_NO_MAP.get(row["Premium Candidate"].strip(), False)

    event_month_raw = row["Event Month"].strip()
    event_month = []
    if event_month_raw in MONTH_MAP:
        event_month = [MONTH_MAP[event_month_raw]]
    elif event_month_raw and event_month_raw != "Multiple":
        warnings.append(f"  row {row_num} ({title}): unrecognized Event Month '{event_month_raw}', left unset")
    elif event_month_raw == "Multiple":
        warnings.append(f"  row {row_num} ({title}): Event Month='Multiple' has no specific month in the source "
                         f"data -- left unset rather than guessing which months")

    props = {
        "Title": {"title": [{"text": {"content": title}}]},
        "Category": {"select": {"name": category}},
        "Subcategory": {"select": {"name": subcategory}},
        "Season": {"multi_select": [{"name": season}]},
        "Priority": {"select": {"name": row["Priority"].strip()}},
        "Target User": {"select": {"name": row["Target User"].strip()}},
        "Evergreen": {"checkbox": evergreen},
        "Premium Candidate": {"checkbox": premium},
        "Source Status": {"select": {"name": row["Source Status"].strip()}},
        "Story Status": {"select": {"name": row["Story Status"].strip()}},
    }
    if region:
        props["Region"] = {"select": {"name": region}}
    if event_month:
        props["Event Month"] = {"multi_select": [{"name": m} for m in event_month]}
    return props, title


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 bulk_import_story_bank.py <path-to-csv>")
    csv_path = sys.argv[1]

    env = load_env(ENV_PATH)
    token = env["NOTION_TOKEN"]
    db_id = env["STORY_BANK_DB_ID"]

    print(f"Reading {csv_path}...")
    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"  {len(rows)} row(s) in CSV")

    print("Querying existing Story Bank titles for duplicate check...")
    existing = existing_titles(token, db_id)
    print(f"  {len(existing)} existing record(s) (including Archived, unchanged by this run)")

    warnings = []
    imported = 0
    skipped_duplicate = []

    for i, row in enumerate(rows, start=1):
        title = row["Title"].strip()
        if title in existing:
            skipped_duplicate.append(title)
            continue
        props, title = build_properties(row, warnings, i)
        notion_request(token, "POST", "/pages", {"parent": {"database_id": db_id}, "properties": props})
        existing.add(title)
        imported += 1
        print(f"  [{i}/{len(rows)}] imported: {title}")

    print()
    print("=" * 70)
    print("Story Bank Import Summary")
    print("=" * 70)
    print(f"CSV rows: {len(rows)}")
    print(f"Imported: {imported}")
    print(f"Skipped (duplicate title): {len(skipped_duplicate)}")
    if skipped_duplicate:
        for t in skipped_duplicate:
            print(f"  - {t}")
    if warnings:
        print(f"\nWarnings ({len(warnings)}) -- judgment calls or unmapped values, please review:")
        for w in warnings:
            print(w)
    print()


if __name__ == "__main__":
    main()
