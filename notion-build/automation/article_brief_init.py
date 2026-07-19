"""Append the empty Article Brief template (Reader Need / Claims / Evidence, per
docs/Article-Brief-Specification-v1.0.md Sec.2.2/Sec.4) to a Research record's
existing `Editor's Notes`.

WRITES to Notion (PATCHes the Research page's Editor's Notes property). This
script has been written and reviewed but, per Rei's 2026-07-19 instruction, has
NOT yet been run against any Notion record (test or production) -- it is included
in this commit as reviewed-but-unexecuted code, pending explicit go-ahead.

Idempotent and non-destructive by design:
  - If "## Reader Need" is already present, it does nothing (does not duplicate
    or touch existing content).
  - Otherwise it APPENDS the template after the existing Editor's Notes text; it
    never overwrites or deletes what an editor already wrote.

    python3 article_brief_init.py --keyword "【テスト】..."
"""
import argparse
import os
import sys

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)

from notion_api import load_env, notion_request, query_database, get_prop  # noqa: E402
import article_brief  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")


def find_research_by_keyword(token, research_db_id, keyword):
    results = query_database(token, research_db_id, filter_obj={
        "property": "Topic", "title": {"contains": keyword}
    })
    return results[0] if results else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keyword", required=True)
    parser.add_argument("--dry-run", action="store_true",
                         help="Print what would be written, without calling the Notion API")
    args = parser.parse_args()

    env = load_env(ENV_PATH)
    token = env["NOTION_TOKEN"]

    research = find_research_by_keyword(token, env["RESEARCH_DB_ID"], args.keyword)
    if not research:
        print(f"ERROR: no Research record found matching '{args.keyword}'")
        sys.exit(1)

    topic = get_prop(research, "Topic", "title")
    notes = get_prop(research, "Editor's Notes", "rich_text") or ""

    if "## Reader Need" in notes:
        print(f"'{topic}': already has an Article Brief template in Editor's Notes. No change made.")
        return

    new_notes = (notes + "\n\n" if notes.strip() else "") + article_brief.EMPTY_TEMPLATE

    if args.dry_run:
        print(f"[DRY RUN] Would append the Article Brief template to '{topic}' Editor's Notes:")
        print("--- new Editor's Notes ---")
        print(new_notes)
        return

    notion_request(token, "PATCH", f"/pages/{research['id']}", {
        "properties": {"Editor's Notes": {"rich_text": [{"text": {"content": new_notes[:2000]}}]}}
    })
    print(f"'{topic}': appended Article Brief template to Editor's Notes.")


if __name__ == "__main__":
    main()
