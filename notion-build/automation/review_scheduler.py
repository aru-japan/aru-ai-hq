"""ARu Studio v4.1 Editorial Intelligence -- periodic review scheduling.

Computes Next Review (Story Bank / Articles, both added in Stage 1) from the
Update Frequency tier documented in docs/Automation-Scripts.md's standard
update rules table (Critical/High/Medium/Low/Event -> Daily/Weekly/Monthly/
Quarterly/Biannual/Event-Based), and extracts everything currently due for
periodic review. This is a distinct concern from law_update_pipeline.py --
it runs on a calendar, not on a detected change, and covers content a Law
Update never touches (e.g. cultural/lifestyle content on a Quarterly cycle).

Anchor date: Last Reviewed (Story Bank) / Last Verified Date (Articles) --
the existing properties this session already reused elsewhere -- falling
back to the page's own creation date if never reviewed, so long-unreviewed
content doesn't get pushed artificially far into the future.

Event-Based is intentionally NOT auto-computed: a Story/Article only records
an Event Month (a recurring month name, no year), which isn't enough to
derive a specific next-review date without guessing. Left for manual
setting, same anti-fabrication stance as everywhere else in this repo.
"""
import os
import sys
from datetime import date, datetime, timedelta

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)

from notion_api import load_env, notion_request, query_database, get_prop  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")

INTERVAL_DAYS = {
    "Daily": 1, "Weekly": 7, "Monthly": 30, "Quarterly": 90, "Biannual": 180,
    # "Event-Based": intentionally absent -- see module docstring.
}


def log(msg):
    print(msg)


def _anchor_date(page, reviewed_prop):
    reviewed = get_prop(page, reviewed_prop, "date")
    if reviewed:
        return datetime.fromisoformat(reviewed[:10]).date()
    created = page.get("created_time", "")
    if created:
        return datetime.fromisoformat(created[:10]).date()
    return date.today()


def _compute_for_db(env, db_key, reviewed_prop, dry_run):
    token = env["NOTION_TOKEN"]
    pages = query_database(token, env[db_key])
    results = []
    for p in pages:
        frequency = get_prop(p, "Update Frequency", "select")
        if not frequency:
            continue
        interval = INTERVAL_DAYS.get(frequency)
        if interval is None:
            continue  # Event-Based -- left for manual setting, not a bug

        anchor = _anchor_date(p, reviewed_prop)
        computed_next = (anchor + timedelta(days=interval)).isoformat()
        current_next = get_prop(p, "Next Review", "date")
        if current_next == computed_next:
            continue  # already correct, don't write

        title = get_prop(p, "Title", "title")
        if dry_run:
            results.append((title, f"Next Review -> {computed_next} (was {current_next or '未設定'})"))
            continue
        notion_request(token, "PATCH", f"/pages/{p['id']}", {
            "properties": {"Next Review": {"date": {"start": computed_next}}}
        })
        results.append((title, f"Next Review -> {computed_next}"))
    return results


def compute_next_review_for_story_bank(env, dry_run=False):
    return _compute_for_db(env, "STORY_BANK_DB_ID", "Last Reviewed", dry_run)


def compute_next_review_for_articles(env, dry_run=False):
    return _compute_for_db(env, "ARTICLES_DB_ID", "Last Verified Date", dry_run)


def find_review_due(env):
    """Everything with a Next Review on or before today, across both DBs --
    the source of truth for the Dashboard's "更新が必要な記事" / review-due
    reporting and the manual "Review Due" Views documented in
    Studio-v4.1-View-Setup-Guide.md."""
    token = env["NOTION_TOKEN"]
    today = date.today().isoformat()
    due_filter = {"and": [
        {"property": "Next Review", "date": {"is_not_empty": True}},
        {"property": "Next Review", "date": {"on_or_before": today}},
    ]}
    story_bank_due = query_database(token, env["STORY_BANK_DB_ID"], filter_obj=due_filter)
    articles_due = query_database(token, env["ARTICLES_DB_ID"], filter_obj=due_filter)
    return {
        "story_bank": [get_prop(p, "Title", "title") for p in story_bank_due],
        "articles": [get_prop(p, "Title", "title") for p in articles_due],
    }


def main():
    dry_run = "--dry-run" in sys.argv
    env = load_env(ENV_PATH)

    log("=" * 70)
    log("Review Scheduler (ARu Studio v4.1)" + (" [DRY RUN]" if dry_run else ""))
    log("=" * 70)

    log("\nComputing Next Review for Story Bank...")
    sb_results = compute_next_review_for_story_bank(env, dry_run)
    for title, outcome in sb_results:
        log(f"  {title}: {outcome}")
    log(f"  {len(sb_results)} record(s) updated")

    log("\nComputing Next Review for Articles...")
    a_results = compute_next_review_for_articles(env, dry_run)
    for title, outcome in a_results:
        log(f"  {title}: {outcome}")
    log(f"  {len(a_results)} record(s) updated")

    log("\nFinding review-due content...")
    due = find_review_due(env)
    log(f"  Story Bank: {len(due['story_bank'])}件, Articles: {len(due['articles'])}件")


if __name__ == "__main__":
    main()
