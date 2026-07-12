"""Researcher Agent: given a topic, gather real grounding context from Notion
(Source Library, Law Update, existing Research) and print a Markdown research brief.

Note: this script performs real Notion queries only. It does not call any external
LLM API (none is configured yet - see docs/Automation-Scripts.md). The analytical
synthesis on top of this gathered context is written by the AI operator (Claude)
during the Pilot Operation, per docs/Pilot-Operation-Guide.md.
"""
import argparse
from _common import get_env, query_database, get_prop


def contains_filter(prop_name, prop_type, text):
    return {"property": prop_name, prop_type: {"contains": text}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    parser.add_argument("--keyword", default=None, help="Search keyword (defaults to --topic)")
    args = parser.parse_args()
    keyword = args.keyword or args.topic

    env = get_env()
    token = env["NOTION_TOKEN"]

    print(f"# Research Brief: {args.topic}\n")
    print("_Notionから実データを取得。分析・要約はAI Operator（Claude）が行う。_\n")

    print("## 情報源（Source Library）")
    sources = query_database(token, env["SOURCE_LIBRARY_DB_ID"], filter_obj=contains_filter("Source Name", "title", keyword))
    if not sources:
        print("- (該当なし)")
    for s in sources:
        print(f"- {get_prop(s, 'Source Name', 'title')} / Tier={get_prop(s, 'Tier', 'select')} / {get_prop(s, 'URL', 'url') or ''}")

    print("\n## 関連する法改正（Law Update）")
    laws = query_database(token, env["LAW_UPDATE_DB_ID"], filter_obj=contains_filter("Law Name", "title", keyword))
    if not laws:
        print("- (該当なし)")
    for law in laws:
        print(f"- {get_prop(law, 'Law Name', 'title')} / Significance={get_prop(law, 'Significance', 'select')} / Effective Date={get_prop(law, 'Effective Date', 'date')}")
        impact = get_prop(law, "Impact Summary", "rich_text")
        if impact:
            print(f"  - Impact Summary: {impact}")
        action = get_prop(law, "Action Required", "rich_text")
        if action:
            print(f"  - Action Required: {action}")

    print("\n## 既存のResearch（重複確認）")
    existing = query_database(token, env["RESEARCH_DB_ID"], filter_obj=contains_filter("Topic", "title", keyword))
    if not existing:
        print("- (既存の関連Researchなし)")
    for r in existing:
        print(f"- {get_prop(r, 'Topic', 'title')} / Status={get_prop(r, 'Status', 'select')}")

    print("\n## 既存記事（重複確認）")
    articles = query_database(token, env["ARTICLES_DB_ID"], filter_obj=contains_filter("Title", "title", keyword))
    if not articles:
        print("- (既存の関連記事なし)")
    for a in articles:
        print(f"- {get_prop(a, 'Title', 'title')} / Status={get_prop(a, 'Status', 'select')}")


if __name__ == "__main__":
    main()
