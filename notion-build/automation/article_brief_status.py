"""Read-only Brief-completion checker for a single Research record, per
docs/Article-Brief-Specification-v1.0.md.

Reports two explicitly separate things (2026-07-19 correction, per Rei's review):
  - Mechanical Check: what can be verified without human judgement (Sec.6 cond 2/3/5
    fully; cond 1/4 can only ever reach REVIEW, never OK, by this script alone).
  - Final Brief Status: 執筆可能 / 編集者確認待ち / 材料不足. "執筆可能" requires the
    Mechanical Check to be unblocked AND an editor-authored "Brief Status: 執筆可能"
    line already present in Editor's Notes -- this script never writes that line.

Performs Notion GET/query only -- no writes, no new properties.

    python3 article_brief_status.py --keyword "外国人の社会保険"
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

LABELS = {
    "1_reader_need_answered": "① Reader NeedにClaimが答えている",
    "2_claim_supported_by_evidence": "② ClaimをEvidenceが支えている",
    "3_evidence_traceable_to_source": "③ EvidenceがSourceまで追跡できる",
    "4_source_confidence_and_freshness": "④ Sourceの信頼性と鮮度",
    "5_no_unresolved_claims": "⑤ 未解決のConflicted/Needs Reviewがない",
}


def find_research_by_keyword(token, research_db_id, keyword):
    results = query_database(token, research_db_id, filter_obj={
        "property": "Topic", "title": {"contains": keyword}
    })
    return results[0] if results else None


def make_source_exists_checker(token, source_library_db_id):
    cache = {}

    def _exists(title):
        if title not in cache:
            results = query_database(token, source_library_db_id, filter_obj={
                "property": "Source Name", "title": {"equals": title}
            })
            cache[title] = bool(results)
        return cache[title]
    return _exists


def check_research_freshness(token, research_page):
    """Operating-Manual §13 "Freshness" rule, read-only: no Related Law Updates
    linked -> no detected staleness signal (treated as fresh: True). Any linked
    Law Update whose Status isn't Confirmed -> stale (False). All Confirmed -> True.
    Returns None only if a linked Law Update page can't be read."""
    rel = research_page["properties"].get("Related Law Updates", {}).get("relation", [])
    if not rel:
        return True
    for ref in rel:
        try:
            law_page = notion_request(token, "GET", f"/pages/{ref['id']}")
        except Exception:
            return None
        if get_prop(law_page, "Update Status", "select") != "Confirmed":
            return False
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keyword", required=True)
    args = parser.parse_args()

    env = load_env(ENV_PATH)
    token = env["NOTION_TOKEN"]

    research = find_research_by_keyword(token, env["RESEARCH_DB_ID"], args.keyword)
    if not research:
        print(f"ERROR: no Research record found matching '{args.keyword}'")
        sys.exit(1)

    topic = get_prop(research, "Topic", "title")
    notes = get_prop(research, "Editor's Notes", "rich_text")
    print(f"# Article Brief Status: {topic}\n")

    parsed = article_brief.parse_editor_notes(notes)
    if not parsed["reader_need"] and not parsed["claims"]:
        print("Editor's NotesにArticle Brief形式（## Reader Need / ## Claims）が見つかりません。")
        print("従来形式のEditor's Notesとして扱われ、Brief完成条件は判定できません。\n")
        print("--- 現在のEditor's Notes（先頭200文字） ---")
        print((notes or "")[:200] or "(空欄)")
        return

    print(f"Reader Need: {parsed['reader_need']}")
    print(f"Claims: {len(parsed['claims'])}件, Evidence: {len(parsed['evidence'])}件\n")

    exists_fn = make_source_exists_checker(token, env["SOURCE_LIBRARY_DB_ID"])
    freshness = check_research_freshness(token, research)
    result = article_brief.check_completion(parsed, source_exists_fn=exists_fn, freshness_confirmed=freshness)

    print("## Mechanical Check")
    for key, label in LABELS.items():
        r = result["mechanical_check"][key]
        print(f"[{r['status']}] {label}")
        print(f"       {r['note']}")

    print(f"\n## Final Brief Status: {result['final_brief_status']}")
    print(f"   {result['final_brief_status_note']}")

    if parsed["brief_status_line"]:
        print(f"\n編集者記録（Editor's Notes）: Brief Status: {parsed['brief_status_line']}")
    else:
        print("\n（Editor's Notes末尾にBrief Statusの記録がまだありません。このスクリプトが自動記入することはありません）")


if __name__ == "__main__":
    main()
