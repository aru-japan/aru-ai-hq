"""One-off (but re-runnable) backfill: classify every existing Article into
Life Topics (see life_topics.py) so the Coverage Analyzer has real data to
aggregate. New articles are tagged automatically going forward by
generate_article_pipeline.py / bulk_generate_articles.py, so this script only
needs to run again if the taxonomy changes or an article is missing tags.

Skips articles that already have a non-empty Life Topics value, so it's safe
to re-run.
"""
import os
import sys
import time

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
REPO_ROOT = os.path.dirname(NOTION_BUILD_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, AUTOMATION_DIR)

from notion_api import load_env, notion_request, query_database, get_prop  # noqa: E402
from life_topics import classify_life_topics  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def main():
    env = load_env(ENV_PATH)
    token = env["NOTION_TOKEN"]
    articles_db = env["ARTICLES_DB_ID"]

    pages = query_database(token, articles_db, filter_obj={
        "property": "Status", "select": {"does_not_equal": "Archived"}
    })
    log(f"{len(pages)} article(s) to check")

    tagged = 0
    skipped = 0
    for page in pages:
        existing = get_prop(page, "Life Topics", "multi_select")
        if existing:
            skipped += 1
            continue
        title = get_prop(page, "Title", "title")
        body = get_prop(page, "Body", "rich_text")
        topics = classify_life_topics(title, body)
        if not topics:
            log(f"  WARNING: no topics classified for '{title}', skipping")
            continue
        notion_request(token, "PATCH", f"/pages/{page['id']}", {
            "properties": {"Life Topics": {"multi_select": [{"name": t} for t in topics]}}
        })
        log(f"  {title[:50]} -> {topics}")
        tagged += 1

    log(f"DONE. Tagged {tagged}, skipped (already tagged) {skipped}.")


if __name__ == "__main__":
    main()
