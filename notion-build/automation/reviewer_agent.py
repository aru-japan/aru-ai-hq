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
from article_template import SECTION_ORDER, parse_body_sections, validate_sections  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")

DIMENSIONS = ["ACCURACY", "EVIDENCE", "READABILITY", "RISK", "LOCALIZATION"]
PASS_OVERALL_THRESHOLD = 70
PASS_RISK_THRESHOLD = 60  # Risk is safety-critical: a low Risk score cannot be offset by other dimensions


def build_template_compliance_note(body):
    """Deterministic (not AI-guessed) section-presence check, reusing the same
    parser render_article_layout.py and template_migration_report.py use --
    so this can never report a false pass on a section that isn't really
    there."""
    sections = parse_body_sections(body)
    missing, mandatory_missing = validate_sections(sections)
    if not missing:
        return "【テンプレート準拠】全8セクション確認済み。"
    parts = []
    for name in SECTION_ORDER:
        status = "欠落" if name in missing else "OK"
        parts.append(f"{name}: {status}")
    note = "【テンプレート準拠】" + "／".join(parts)
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


def review_article(article):
    title = get_prop(article, "Title", "title")
    body = get_prop(article, "Body", "rich_text")
    update_level = get_prop(article, "Update Level", "number") or 1

    prompt = build_review_prompt(title, body, update_level)
    provider, text = ai_gateway.complete(prompt, max_tokens=800)
    scores, suggestions = parse_review(text)

    if any(v is None for v in scores.values()):
        raise RuntimeError(f"Could not parse all 5 scores from AI response:\n{text}")

    compliance_note = build_template_compliance_note(body)
    suggestions = f"{compliance_note}\n\n{suggestions}" if suggestions else compliance_note

    overall = round(sum(scores.values()) / 5)
    risk = scores["RISK"]

    if overall >= PASS_OVERALL_THRESHOLD and risk >= PASS_RISK_THRESHOLD:
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

    provider, scores, overall, result, suggestions = review_article(article)
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
