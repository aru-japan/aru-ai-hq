"""Bulk-import Story Bank entries from a CSV (ChatGPT-curated content, per the
established role split: ChatGPT selects/curates/prioritizes Story Bank
content, Claude Code only imports/implements -- this script never invents a
Story, it only maps and writes what's already in the CSV).

Normalizes the incoming English-labeled CSV columns onto Story Bank's
existing Japanese Select vocabulary (Category/Subcategory/Season/Primary
Region/Event Month) rather than creating a parallel English option set --
the same naming-consistency principle Architecture-Specification-v1.0.md
Sec.5/6 established for the other Knowledge Domains.

Formal operating rules (Rei, 2026-07-18):
  - CSVs live in notion-build/automation/data/, named
    StoryBank_Batch###_Category.csv
  - After a successful import, the source CSV is moved (not deleted) to
    notion-build/automation/data/imported/ as a permanent history record
  - A Story spanning multiple prefectures gets exactly one Primary Region
    (first-listed prefecture in the source data); the rest is recorded in
    Notes, never silently dropped
  - An event held multiple times a year gets Event Month = "Multiple" (a
    real Select option), never left blank
  - Every run reports exactly five things: duplicate check, import count,
    total Story Bank count, errors, and pending items (judgment calls that
    need Rei/ChatGPT review) -- nothing else

Usage:
    python3 bulk_import_story_bank.py data/StoryBank_Batch002_Fireworks.csv
"""
import csv
import os
import shutil
import sys

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)

from notion_api import load_env, notion_request, query_database, get_prop  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")
IMPORTED_DIR = os.path.join(AUTOMATION_DIR, "data", "imported")

CATEGORY_MAP = {"Event": "イベント"}
SUBCATEGORY_MAP = {"Fireworks": "花火大会"}
SEASON_MAP = {"Summer": "夏", "Autumn": "秋", "Winter": "冬", "Spring": "春", "All Season": "通年"}

# Full 47-prefecture -> conventional 8-region (+Hokkaido) breakdown, same
# vocabulary as Source Library's Region field. Built out in full (not just
# the prefectures seen in Batch 001) since future batches span other
# categories (Summer Festival etc.) and will reference many more.
PREFECTURE_TO_REGION = {
    "Hokkaido": "北海道",
    "Aomori": "東北", "Iwate": "東北", "Miyagi": "東北", "Akita": "東北", "Yamagata": "東北", "Fukushima": "東北",
    "Ibaraki": "関東", "Tochigi": "関東", "Gunma": "関東", "Saitama": "関東",
    "Chiba": "関東", "Tokyo": "関東", "Kanagawa": "関東",
    "Niigata": "中部", "Toyama": "中部", "Ishikawa": "中部", "Fukui": "中部", "Yamanashi": "中部",
    "Nagano": "中部", "Gifu": "中部", "Shizuoka": "中部", "Aichi": "中部",
    "Mie": "近畿", "Shiga": "近畿", "Kyoto": "近畿", "Osaka": "近畿", "Hyogo": "近畿", "Nara": "近畿", "Wakayama": "近畿",
    "Tottori": "中国", "Shimane": "中国", "Okayama": "中国", "Hiroshima": "中国", "Yamaguchi": "中国",
    "Tokushima": "四国", "Kagawa": "四国", "Ehime": "四国", "Kochi": "四国",
    "Fukuoka": "九州・沖縄", "Saga": "九州・沖縄", "Nagasaki": "九州・沖縄", "Kumamoto": "九州・沖縄",
    "Oita": "九州・沖縄", "Miyazaki": "九州・沖縄", "Kagoshima": "九州・沖縄", "Okinawa": "九州・沖縄",
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


def resolve_region(region_raw, title, pending):
    """Returns (primary_region, note_text_or_None). A region spanning
    multiple prefectures (e.g. "Fukuoka/Yamaguchi") gets its first-listed
    prefecture as Primary Region; the rest goes to Notes, per Rei's rule --
    never silently dropped."""
    parts = [p.strip() for p in region_raw.split("/") if p.strip()]
    if not parts:
        pending.append(f"{title}: Primary Region blank in source data")
        return None, None

    primary_pref = parts[0]
    primary_region = PREFECTURE_TO_REGION.get(primary_pref)
    if primary_region is None:
        pending.append(f"{title}: unrecognized prefecture '{primary_pref}', Primary Region left unset")

    note = None
    if len(parts) > 1:
        note = f"Also spans: {', '.join(parts[1:])}（複数県にまたがるためPrimary Regionは{primary_pref}のみ設定）"
        pending.append(f"{title}: Region spans multiple prefectures ({region_raw}) -- "
                        f"Primary Region set to {primary_pref}, rest recorded in Notes")
    return primary_region, note


def resolve_event_month(event_month_raw, title, pending):
    if not event_month_raw:
        return []
    if event_month_raw == "Multiple":
        return ["Multiple"]
    if event_month_raw in MONTH_MAP:
        return [MONTH_MAP[event_month_raw]]
    pending.append(f"{title}: unrecognized Event Month '{event_month_raw}', left unset")
    return []


def build_properties(row, pending):
    title = row["Title"].strip()

    category = CATEGORY_MAP.get(row["Category"], row["Category"])
    subcategory = SUBCATEGORY_MAP.get(row["Subcategory"], row["Subcategory"])
    season = SEASON_MAP.get(row["Season"], row["Season"])
    region_raw = row.get("Region", row.get("Primary Region", "")).strip()
    primary_region, region_note = resolve_region(region_raw, title, pending)

    evergreen = YES_NO_MAP.get(row["Evergreen"].strip(), False)
    premium = YES_NO_MAP.get(row["Premium Candidate"].strip(), False)

    event_month = resolve_event_month(row["Event Month"].strip(), title, pending)

    notes_parts = [n for n in [region_note, row.get("Notes", "").strip() or None] if n]

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
    if primary_region:
        props["Primary Region"] = {"select": {"name": primary_region}}
    if event_month:
        props["Event Month"] = {"multi_select": [{"name": m} for m in event_month]}
    if notes_parts:
        props["Notes"] = {"rich_text": [{"text": {"content": " / ".join(notes_parts)}}]}
    return props, title


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python3 bulk_import_story_bank.py <path-to-csv>")
    csv_path = sys.argv[1]

    env = load_env(ENV_PATH)
    token = env["NOTION_TOKEN"]
    db_id = env["STORY_BANK_DB_ID"]

    with open(csv_path, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    existing = existing_titles(token, db_id)
    pre_existing_count = len(existing)

    pending = []
    errors = []
    imported = 0
    skipped_duplicate = []

    for row in rows:
        title = row["Title"].strip()
        if title in existing:
            skipped_duplicate.append(title)
            continue
        try:
            props, title = build_properties(row, pending)
            notion_request(token, "POST", "/pages", {"parent": {"database_id": db_id}, "properties": props})
            existing.add(title)
            imported += 1
        except Exception as e:
            errors.append(f"{title}: {e}")

    moved_to = None
    if imported > 0 and not errors:
        os.makedirs(IMPORTED_DIR, exist_ok=True)
        dest = os.path.join(IMPORTED_DIR, os.path.basename(csv_path))
        shutil.move(csv_path, dest)
        moved_to = dest

    print("=" * 70)
    print("Story Bank Import Report")
    print("=" * 70)
    print(f"重複チェック: 既存{pre_existing_count}件と照合、重複{len(skipped_duplicate)}件"
          + (f"（{', '.join(skipped_duplicate)}）" if skipped_duplicate else ""))
    print(f"インポート件数: {imported}件")
    print(f"Story Bank総件数: {pre_existing_count + imported}件")
    print(f"エラー: {len(errors)}件" + ("" if not errors else ""))
    for e in errors:
        print(f"  - {e}")
    print(f"保留事項: {len(pending)}件")
    for p in pending:
        print(f"  - {p}")
    if moved_to:
        print(f"\nCSVを移動しました: {moved_to}")
    elif imported > 0 and errors:
        print(f"\nエラーがあったため、CSVは移動していません（{csv_path}のまま）")


if __name__ == "__main__":
    main()
