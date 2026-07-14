"""Publishing Center -- Version 4 Phase 3.

Lets the editor-in-chief (Rei) see at a glance which articles are ready for the
ARu app, which are already live, and which need attention -- and pick what goes
into the app next without guessing.

No new database: adds a small set of properties to the existing Articles DB and
three new Dashboard sections. `ARu App URL`/actual publishing is a human action
outside this system (there is no ARu app publishing API to call, and this script
does not assume one) -- Publishing Status=Published is a *management* record of
"a human has manually put this content into the app," never something a script
sets on its own.

Property responsibilities (to avoid overlapping with what already exists):
  - Status (existing)            : editorial/QA workflow inside Notion
                                    (Draft/AI Draft/Human Review/Approved/...).
                                    Untouched by this script.
  - Review Result (existing)     : does the Article content itself pass AI review.
  - Translation.Quality Result   : does a given language's translation pass AI review.
  - Translation.Publish Approval : the Constitution Sec.9/13 human-approval gate
                                    for Update Level 2/3 (or Level 1 not yet
                                    culturally adapted). This script reads it,
                                    never writes it -- only translation_quality_
                                    reviewer.py and a human (setting "Approved")
                                    may change it.
  - Freshness Status (existing)  : is the content still within its review
                                    interval (article_freshness_monitor.py owns
                                    this). This script reads it to decide
                                    Publishing Status transitions.
  - Publishing Status (new)      : is this specific article live in the ARu app,
                                    ready to go, or in need of attention --
                                    the one thing none of the above answer alone.

Publishing Status values: Draft / Ready to Publish / Published / Needs Update /
Archived / Duplicate. Transitions performed by this script:
  - Draft <-> Ready to Publish: automatic, based on evaluate_readiness() below.
    Never advances past Ready to Publish -- Published is always a human action.
  - Published -> Needs Update: automatic, when Freshness Status flips to
    "Needs Update" (article_freshness_monitor.py integration).
  - Needs Update -> (Published or Ready to Publish): automatic recovery once
    Freshness Status returns to "Fresh", restoring whichever state
    "Previous Publishing Status" recorded.
  - -> Published: only ever set by a human in the Notion UI. This script's job
    on the next run is only to backfill Published Date / Published By (from
    the page's real last_edited_by, not invented) once it notices the change.
  - Archived / Duplicate: never touched by this script once set (a terminal
    call -- Duplicate is set by a human resolving a duplicate-article
    investigation, never automatically; see duplicate_guard.py for the
    prevention side of that).
"""
import os
import sys
import time
import datetime
import argparse
from collections import Counter

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
REPO_ROOT = os.path.dirname(NOTION_BUILD_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, AUTOMATION_DIR)

from notion_api import load_env, notion_request, query_database, get_prop  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")

PUBLISHING_STATUS_OPTIONS = ["Draft", "Ready to Publish", "Published", "Needs Update", "Archived", "Duplicate"]


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def ensure_schema(token, articles_db_id):
    status_options = [{"name": s} for s in PUBLISHING_STATUS_OPTIONS]
    notion_request(token, "PATCH", f"/databases/{articles_db_id}", {
        "properties": {
            "Publishing Status": {"select": {"options": status_options}},
            "Published By": {"people": {}},
            "ARu App URL": {"url": {}},
            "Previous Publishing Status": {"select": {"options": status_options}},
            "Publishing Status Updated Date": {"date": {}},
        }
    })


def get_translations_for_article(token, translation_db_id, article_id):
    return query_database(token, translation_db_id, filter_obj={
        "property": "Parent Article", "relation": {"contains": article_id}
    })


def get_research_page(token, article):
    research_ids = get_prop(article, "Source Research", "relation")
    if not research_ids:
        return None
    try:
        return notion_request(token, "GET", f"/pages/{research_ids[0]}")
    except RuntimeError:
        return None


def evaluate_readiness(article, translations, research_page):
    """Returns (is_ready: bool, reasons: list[str] of every unmet criterion)."""
    reasons = []

    review_result = get_prop(article, "Review Result", "select")
    if review_result != "Pass":
        reasons.append(f"Article Review Result={review_result} (Pass required)")

    if not translations:
        reasons.append("No Translation exists yet")
    else:
        for t in translations:
            lang = get_prop(t, "Language", "select")
            qr = get_prop(t, "Quality Result", "select")
            if qr != "Pass":
                reasons.append(f"Translation({lang}) Quality Result={qr} (Pass required)")
            pa = get_prop(t, "Publish Approval", "select")
            if pa not in ("Not Required", "Approved"):
                reasons.append(f"Translation({lang}) Publish Approval={pa} (Not Required/Approved required)")

    freshness = get_prop(article, "Freshness Status", "select")
    if freshness != "Fresh":
        reasons.append(f"Freshness Status={freshness} (Fresh required)")

    if not get_prop(article, "Title", "title"):
        reasons.append("Title missing")
    if not get_prop(article, "Body", "rich_text"):
        reasons.append("Body missing")
    if not get_prop(article, "Category", "select"):
        reasons.append("Category missing")
    if not get_prop(article, "Last Verified Date", "date"):
        reasons.append("Last Verified Date missing")

    # Articles has no standalone "Summary" property; the closest real equivalent
    # is the Summary written on the originating Research record.
    if not (research_page and get_prop(research_page, "Summary", "rich_text")):
        reasons.append("Summary missing (no linked Source Research with a Summary)")

    return (len(reasons) == 0), reasons


def apply_transition(token, article_id, current_status, new_status, today, extra_props=None, dry_run=False):
    props = {
        "Publishing Status": {"select": {"name": new_status}},
        "Publishing Status Updated Date": {"date": {"start": today}},
    }
    if current_status:
        props["Previous Publishing Status"] = {"select": {"name": current_status}}
    if extra_props:
        props.update(extra_props)
    if dry_run:
        return
    notion_request(token, "PATCH", f"/pages/{article_id}", {"properties": props})


def sync_publishing_status(env, dry_run=False):
    token = env["NOTION_TOKEN"]
    articles_db = env["ARTICLES_DB_ID"]
    translation_db = env["TRANSLATION_DB_ID"]
    today = datetime.date.today().isoformat()

    log("Ensuring Articles DB schema has Publishing Status properties...")
    if not dry_run:
        ensure_schema(token, articles_db)

    log("Querying all Articles...")
    articles = query_database(token, articles_db)
    log(f"  {len(articles)} article(s)")

    stats = Counter()
    detail_lines = []

    for article in articles:
        title = get_prop(article, "Title", "title")
        pub_status = get_prop(article, "Publishing Status", "select")
        freshness = get_prop(article, "Freshness Status", "select")
        prev = get_prop(article, "Previous Publishing Status", "select")

        if pub_status in ("Archived", "Duplicate"):
            stats[f"{pub_status} (untouched)"] += 1
            continue

        if pub_status == "Published":
            published_date = get_prop(article, "Published Date", "date")
            if not published_date:
                last_editor_ids = article.get("last_edited_by", {})
                last_editor_id = last_editor_ids.get("id") if isinstance(last_editor_ids, dict) else None
                props = {
                    "Published Date": {"date": {"start": today}},
                    "Publishing Status Updated Date": {"date": {"start": today}},
                }
                if last_editor_id:
                    props["Published By"] = {"people": [{"id": last_editor_id}]}
                if not dry_run:
                    notion_request(token, "PATCH", f"/pages/{article['id']}", {"properties": props})
                stats["Published (metadata backfilled)"] += 1
                detail_lines.append(f"  BACKFILLED Published Date/By: {title}")
            if freshness == "Needs Update":
                apply_transition(token, article["id"], "Published", "Needs Update", today, dry_run=dry_run)
                stats["Published -> Needs Update (freshness)"] += 1
                detail_lines.append(f"  Published -> Needs Update (stale): {title}")
            else:
                stats["Published (stays)"] += 1
            continue

        if pub_status == "Needs Update":
            if freshness == "Fresh":
                restore_to = prev if prev in ("Published", "Ready to Publish") else "Ready to Publish"
                apply_transition(token, article["id"], "Needs Update", restore_to, today, dry_run=dry_run)
                stats[f"Needs Update -> {restore_to} (recovered)"] += 1
                detail_lines.append(f"  Needs Update -> {restore_to} (fresh again): {title}")
            else:
                stats["Needs Update (stays)"] += 1
            continue

        # Draft / Ready to Publish / unset -> evaluate readiness
        translations = get_translations_for_article(token, translation_db, article["id"])
        research_page = get_research_page(token, article)
        is_ready, reasons = evaluate_readiness(article, translations, research_page)
        if freshness == "Needs Update" and is_ready:
            is_ready = False
            reasons.append("Freshness Status=Needs Update (blocks Ready to Publish)")

        target = "Ready to Publish" if is_ready else "Draft"
        if pub_status != target:
            apply_transition(token, article["id"], pub_status, target, today, dry_run=dry_run)
            stats[f"-> {target}"] += 1
            if target == "Draft" and reasons:
                detail_lines.append(f"  -> Draft: {title}")
                for r in reasons:
                    detail_lines.append(f"      - {r}")
            else:
                detail_lines.append(f"  -> {target}: {title}")
        else:
            stats[f"{target} (unchanged)"] += 1

    return stats, detail_lines


def print_report(stats, detail_lines, dry_run):
    print("\n" + "=" * 70)
    print(f"Publishing Center Sync {'(DRY RUN)' if dry_run else ''}")
    print("=" * 70)
    for line in detail_lines:
        print(line)
    print("\nSummary:")
    for k in sorted(stats.keys()):
        print(f"  {k}: {stats[k]}")
    print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing to Notion")
    args = parser.parse_args()

    env = load_env(ENV_PATH)
    stats, detail_lines = sync_publishing_status(env, dry_run=args.dry_run)
    print_report(stats, detail_lines, args.dry_run)


if __name__ == "__main__":
    main()
