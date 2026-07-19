"""Phase B3.8: Reviewer Agent, extended for the ARu Official Article Template.

Scores an Article across 5 dimensions (Accuracy / Evidence / Readability / Risk /
Localization) using the real AI Gateway, writes the scores + suggestions back onto
the Article page, and sets Review Result (Pass / Needs Revision / Fail).

Template compliance is checked in two layers, both folded into the existing
Review Suggestions field (no new review properties):
  - Deterministic (this file, reusing article_template.validate_sections):
    which of the 8 official sections are present/missing -- cannot hallucinate
    a false pass, since it's a straight parse of Body, not an AI judgment call.
  - AI-judged (the review prompt below): whether Premium Section adds real
    value beyond the free sections, whether any sections are duplicated, and
    whether claims are clearly distinguished as fact vs. interpretation vs.
    recommendation -- these require judgment, so they stay in the AI's
    existing SUGGESTIONS output rather than becoming new deterministic checks.

Gate: Update Level >= 2 articles must have Review Result = Pass before they may be
moved to Status = Published (enforced here and re-checked in enforce_publish_gate.py).
"""
import argparse
import os
import re
import sys

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
REPO_ROOT = os.path.dirname(NOTION_BUILD_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))
sys.path.insert(0, AUTOMATION_DIR)

from notion_api import load_env, notion_request, query_database, get_prop  # noqa: E402
import ai_gateway  # noqa: E402
from article_template import get_template, template_for_content, parse_body_sections, validate_sections  # noqa: E402
import article_brief  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")

DIMENSIONS = ["ACCURACY", "EVIDENCE", "READABILITY", "RISK", "LOCALIZATION"]
PASS_OVERALL_THRESHOLD = 70
PASS_RISK_THRESHOLD = 60  # Risk is safety-critical: a low Risk score cannot be offset by other dimensions


def build_template_compliance_note(body, template="standard"):
    """Deterministic (not AI-guessed) section-presence check, reusing the same
    parser render_article_layout.py and template_migration_report.py use --
    so this can never report a false pass on a section that isn't really
    there. `template` selects which registered template's section list this
    Article should be checked against (resolved by the caller from Category
    and Content Type via article_template.template_for_content(), same as
    every other consumer)."""
    section_order = get_template(template)["section_order"]
    sections = parse_body_sections(body, template=template)
    missing, mandatory_missing = validate_sections(sections, template=template)
    if not missing:
        return f"【テンプレート準拠：{template}】全{len(section_order)}セクション確認済み。"
    parts = []
    for name in section_order:
        status = "欠落" if name in missing else "OK"
        parts.append(f"{name}: {status}")
    note = f"【テンプレート準拠：{template}】" + "／".join(parts)
    if mandatory_missing:
        note += f" ※必須セクション欠落: {', '.join(mandatory_missing)}"
    return note


def build_review_prompt(title, body, update_level):
    return f"""あなたはARu（外国籍の方向け日本生活サポートメディア）のReviewer Agentです。
以下の記事を5つの観点で評価してください。各観点は0〜100点。

1. Accuracy（正確性）：事実関係に誤りや古い情報がないか
2. Evidence（出典の妥当性）：主張が出典・一次情報に基づいているか
3. Readability（読みやすさ）：外国籍の読者にとって分かりやすい文章か
4. Risk（リスクの低さ）：個別の法的・医療的助言と誤解される断定的表現がないか、免責が適切か（Update Level={update_level}）
5. Localization（文化的配慮）：一般化・ステレオタイプがなく、文化的背景の説明があるか

以下の観点もSUGGESTIONSに含めてください：
- Premium Sectionは無料部分の繰り返しではなく、実用的な新しい価値（場所・タイミング・費用・予約・アクセス・現地マナー・よくある間違い等）を追加できているか
- セクション間で内容が重複していないか
- 事実（fact）・解釈（interpretation）・推奨（recommendation）が文章上区別できる書き方になっているか

記事タイトル：{title}

記事本文：
{body}

出力形式（このまま、数値と提案のみを出力し、他の説明は付けないこと）：
ACCURACY: <0-100の数値>
EVIDENCE: <0-100の数値>
READABILITY: <0-100の数値>
RISK: <0-100の数値>
LOCALIZATION: <0-100の数値>
SUGGESTIONS: <改善提案。300文字程度。具体的に。Premium Sectionの価値・重複・fact/interpretation/recommendationの区別についても触れること>
"""


def parse_review(text):
    scores = {}
    for dim in DIMENSIONS:
        m = re.search(rf"{dim}:\s*(\d+)", text)
        scores[dim] = int(m.group(1)) if m else None

    suggestions = ""
    m = re.search(r"SUGGESTIONS:\s*(.+)", text, re.DOTALL)
    if m:
        suggestions = m.group(1).strip()

    return scores, suggestions


def rich_text_chunks(content, chunk_size=1990):
    chunks = [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)] or [""]
    return [{"text": {"content": c}} for c in chunks]


def review_article(article, token=None):
    """token is optional but should always be passed when available: it is what
    lets the 2026-07-19 Grounding Check look up the Article's source Research
    record (via the existing `Source Research` relation) and audit the body
    against the actual approved Article Brief, rather than just AI-judged scores.
    Without it, grounding/truncation/Sources-completeness checks are skipped and
    review falls back to the pre-2026-07-19 score-only behavior."""
    title = get_prop(article, "Title", "title")
    body = get_prop(article, "Body", "rich_text")
    update_level = get_prop(article, "Update Level", "number") or 1
    category = get_prop(article, "Category", "select")
    content_type = get_prop(article, "Content Type", "select")
    template = template_for_content(category, content_type)

    prompt = build_review_prompt(title, body, update_level)
    provider, text = ai_gateway.complete(prompt, max_tokens=800)
    scores, suggestions = parse_review(text)

    if any(v is None for v in scores.values()):
        raise RuntimeError(f"Could not parse all 5 scores from AI response:\n{text}")

    compliance_note = build_template_compliance_note(body, template=template)

    # --- 2026-07-19 fix: forced-Fail checks that no score can override ---------
    # A factual/structural defect here means Pass is wrong regardless of how
    # well-written or well-scored the AI review otherwise finds the article.
    forced_fail_reasons = []
    grounding_note = ""

    if article_brief.is_body_truncated(body):
        forced_fail_reasons.append("本文が途中で終了している可能性（文末が句点・URL等の終端で終わっていない）")

    sections = parse_body_sections(body, template=template)
    missing, _mandatory_missing = validate_sections(sections, template=template)
    if content_type == "Premium" and "Sources" in missing:
        forced_fail_reasons.append("PremiumコンテンツでSourcesセクションが欠落")

    if token:
        source_research_ids = get_prop(article, "Source Research", "relation")
        if source_research_ids:
            research_page = notion_request(token, "GET", f"/pages/{source_research_ids[0]}")
            editor_notes = get_prop(research_page, "Editor's Notes", "rich_text")
            parsed_brief = article_brief.parse_editor_notes(editor_notes)
            if parsed_brief.get("reader_need") or parsed_brief.get("claims"):
                gc = article_brief.grounding_check(body, parsed_brief, today=__import__("datetime").date.today().isoformat())
                if gc["unsupported"]:
                    forced_fail_reasons.append(f"Article Briefにない情報（決定論的） {len(gc['unsupported'])}件")
                if gc["overclaiming"]:
                    forced_fail_reasons.append(f"根拠以上の断定表現 {len(gc['overclaiming'])}件")
                grounding_note = (
                    f"【Grounding Check（決定論的）】Supported {len(gc['supported'])}件／"
                    f"Unsupported {len(gc['unsupported'])}件／断定表現 {len(gc['overclaiming'])}件"
                )
                if gc["unsupported"] or gc["overclaiming"]:
                    grounding_note += "\n" + "\n".join(f"  - {u}" for u in gc["unsupported"] + gc["overclaiming"])

                # 2026-07-20: semantic (sentence-level, AI-judged) pass, combined
                # with the deterministic one above -- catches prose (background/
                # rationale/purpose paraphrases) the pattern-based check misses.
                sgc = article_brief.semantic_grounding_check(body, parsed_brief)
                if sgc["unsupported"]:
                    forced_fail_reasons.append(f"Article Briefにない情報（意味的） {len(sgc['unsupported'])}件")
                mapping_lines = [f"  - {s}" for s in sgc["supported"]] + [f"  - UNSUPPORTED: {u}" for u in sgc["unsupported"]]
                grounding_note += (
                    f"\n\n【Semantic Grounding Check】Supported {len(sgc['supported'])}件／"
                    f"Unsupported {len(sgc['unsupported'])}件\n" + "\n".join(mapping_lines)
                )

    suggestions = "\n\n".join(filter(None, [compliance_note, grounding_note, suggestions]))

    overall = round(sum(scores.values()) / 5)
    risk = scores["RISK"]

    if forced_fail_reasons:
        result = "Fail"
        suggestions = f"【Grounding/構造チェックにより強制Fail】{'; '.join(forced_fail_reasons)}\n\n{suggestions}"
    elif overall >= PASS_OVERALL_THRESHOLD and risk >= PASS_RISK_THRESHOLD:
        result = "Pass"
    elif overall < 50 or risk < 40:
        result = "Fail"
    else:
        result = "Needs Revision"

    return provider, scores, overall, result, suggestions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--article-id", default=None, help="Review a specific Article page id")
    parser.add_argument("--keyword", default=None, help="Review the first AI Draft Article whose Title contains this keyword")
    args = parser.parse_args()

    env = load_env(ENV_PATH)
    token = env["NOTION_TOKEN"]
    articles_db = env["ARTICLES_DB_ID"]

    if args.article_id:
        article = notion_request(token, "GET", f"/pages/{args.article_id}")
    else:
        filter_obj = {"property": "Status", "select": {"equals": "AI Draft"}}
        if args.keyword:
            filter_obj = {"and": [filter_obj, {"property": "Title", "title": {"contains": args.keyword}}]}
        candidates = query_database(token, articles_db, filter_obj=filter_obj)
        if not candidates:
            print("ERROR: no AI Draft article found to review.")
            sys.exit(1)
        article = candidates[0]

    title = get_prop(article, "Title", "title")
    print(f"Reviewing: {title}")

    provider, scores, overall, result, suggestions = review_article(article, token=token)
    print(f"  provider={provider}")
    for dim in DIMENSIONS:
        print(f"  {dim}: {scores[dim]}")
    print(f"  OVERALL: {overall}")
    print(f"  RESULT: {result}")
    print(f"  SUGGESTIONS: {suggestions[:150]}...")

    update_props = {
        "Review Accuracy Score": {"number": scores["ACCURACY"]},
        "Review Evidence Score": {"number": scores["EVIDENCE"]},
        "Review Readability Score": {"number": scores["READABILITY"]},
        "Review Risk Score": {"number": scores["RISK"]},
        "Review Localization Score": {"number": scores["LOCALIZATION"]},
        "Review Result": {"select": {"name": result}},
        "Review Suggestions": {"rich_text": rich_text_chunks(suggestions)},
        "Review Date": {"date": {"start": __import__("datetime").date.today().isoformat()}},
    }
    notion_request(token, "PATCH", f"/pages/{article['id']}", {"properties": update_props})
    print(f"\nSAVED review to Article {article['id']}")

    update_level = get_prop(article, "Update Level", "number") or 1
    if update_level >= 2 and result != "Pass":
        print(f"GATE: Update Level {update_level} article did NOT pass review (Result={result}). "
              f"This article may not proceed to Publish Approval until Review Result = Pass.")
    elif update_level >= 2:
        print(f"GATE: Update Level {update_level} article passed review. Eligible to proceed toward Publish Approval "
              f"(still requires human approval per ARu Constitution Sec.13).")


if __name__ == "__main__":
    main()
