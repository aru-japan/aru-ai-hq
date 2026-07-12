"""Phase B3.10: SNS Quality Reviewer.

Scores a Draft SNS Queue post across 5 dimensions (Accuracy / Platform Fit /
Engagement / Cultural Sensitivity / Risk) using the real AI Gateway, writes scores +
suggestions back onto the SNS Queue page, and sets Review Result.

Gate: below Pass, Status stays "Draft" (never advanced to Scheduled/Posted). This
script does not itself advance Status even on Pass - per ARu Constitution Sec.16,
SNS posting for Update Level 2/3 content additionally requires the linked Article's
Publish Approval, which is out of scope for this script and checked elsewhere.
"""
import argparse
import os
import re
import sys
import datetime

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
REPO_ROOT = os.path.dirname(NOTION_BUILD_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

from notion_api import load_env, notion_request, query_database, get_prop  # noqa: E402
import ai_gateway  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")

DIMENSIONS = ["ACCURACY", "PLATFORM_FIT", "ENGAGEMENT", "CULTURAL_SENSITIVITY", "RISK"]
PASS_OVERALL_THRESHOLD = 75
PASS_ACCURACY_THRESHOLD = 75
PASS_RISK_THRESHOLD = 70


def rich_text_chunks(content, chunk_size=1990):
    chunks = [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)] or [""]
    return [{"text": {"content": c}} for c in chunks]


def build_prompt(platform, article_title, article_body, caption):
    return f"""あなたはARu（外国籍の方向け日本生活サポートメディア）のSNS Quality Reviewerです。
以下の{platform}向け投稿文を、元記事の内容と照らし合わせて5つの観点で評価してください。各観点は0〜100点。

1. ACCURACY（正確性）：投稿文が元記事の内容と一致しているか、誇張や歪みがないか
2. PLATFORM_FIT（プラットフォーム適合度）：{platform}に適した長さ・構成・トーンか
   （Instagram=視覚的・温かいトーン／Threads=会話的・問いかけを含む／Xは140字程度で簡潔）
3. ENGAGEMENT（エンゲージメント）：読み手が反応・保存・共有したくなる内容か
4. CULTURAL_SENSITIVITY（文化的配慮）：外国籍ユーザーにも誤解なく伝わる表現か、ステレオタイプがないか
5. RISK（リスクの低さ）：誤解・断定・炎上につながる表現がないか

元記事タイトル：{article_title}
元記事本文：
{article_body}

投稿文（{platform}向け）：
{caption}

出力形式（このまま、数値と提案のみを出力し、他の説明は付けないこと）：
ACCURACY: <0-100の数値>
PLATFORM_FIT: <0-100の数値>
ENGAGEMENT: <0-100の数値>
CULTURAL_SENSITIVITY: <0-100の数値>
RISK: <0-100の数値>
SUGGESTIONS: <改善提案。200文字程度。具体的に>
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


def decide_result(scores):
    overall = round(sum(scores.values()) / 5)
    accuracy = scores["ACCURACY"]
    risk = scores["RISK"]
    if overall >= PASS_OVERALL_THRESHOLD and accuracy >= PASS_ACCURACY_THRESHOLD and risk >= PASS_RISK_THRESHOLD:
        result = "Pass"
    elif overall < 50 or accuracy < 50 or risk < 40:
        result = "Fail"
    else:
        result = "Needs Revision"
    return overall, result


def review_one(token, sns_page):
    platform = get_prop(sns_page, "Platform", "select")
    caption = get_prop(sns_page, "Caption", "rich_text")
    title = get_prop(sns_page, "Title", "title")
    article_ids = get_prop(sns_page, "Related Article", "relation")

    if not article_ids:
        print(f"  SKIP (no Related Article linked): {title}")
        return None

    article = notion_request(token, "GET", f"/pages/{article_ids[0]}")
    article_title = get_prop(article, "Title", "title")
    article_body = get_prop(article, "Body", "rich_text")

    print(f"Reviewing [{platform}]: {title}")
    prompt = build_prompt(platform, article_title, article_body, caption)
    provider, text = ai_gateway.complete(prompt, max_tokens=600)
    scores, suggestions = parse_review(text)

    if any(v is None for v in scores.values()):
        raise RuntimeError(f"Could not parse all 5 scores from AI response:\n{text}")

    overall, result = decide_result(scores)

    print(f"  provider={provider}")
    for dim in DIMENSIONS:
        print(f"  {dim}: {scores[dim]}")
    print(f"  OVERALL: {overall}")
    print(f"  RESULT: {result}")
    print(f"  SUGGESTIONS: {suggestions[:150]}...")

    update_props = {
        "Review Accuracy Score": {"number": scores["ACCURACY"]},
        "Review Platform Fit Score": {"number": scores["PLATFORM_FIT"]},
        "Review Engagement Score": {"number": scores["ENGAGEMENT"]},
        "Review Cultural Sensitivity Score": {"number": scores["CULTURAL_SENSITIVITY"]},
        "Review Risk Score": {"number": scores["RISK"]},
        "Review Result": {"select": {"name": result}},
        "Review Suggestions": {"rich_text": rich_text_chunks(suggestions)},
        "Review Date": {"date": {"start": datetime.date.today().isoformat()}},
    }

    # Gate: below Pass, keep Status = Draft explicitly (never advance).
    current_status = get_prop(sns_page, "Status", "select")
    if result != "Pass":
        update_props["Status"] = {"select": {"name": "Draft"}}
        gate_note = f"Result={result} -> Status held at Draft."
    else:
        gate_note = (f"Result=Pass (was Status={current_status}). This script does not itself "
                     f"advance Status to Scheduled/Posted; that still requires the linked "
                     f"Article's Publish Approval and human sign-off (ARu Constitution Sec.16).")

    notion_request(token, "PATCH", f"/pages/{sns_page['id']}", {"properties": update_props})
    print(f"  SAVED. GATE: {gate_note}\n")
    return {"platform": platform, "overall": overall, "result": result, "scores": scores, "suggestions": suggestions}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sns-id", default=None, help="Review a specific SNS Queue page id")
    parser.add_argument("--all-drafts", action="store_true", help="Review every Status=Draft record")
    args = parser.parse_args()

    env = load_env(ENV_PATH)
    token = env["NOTION_TOKEN"]
    sns_db = env["SNS_QUEUE_DB_ID"]

    if args.sns_id:
        targets = [notion_request(token, "GET", f"/pages/{args.sns_id}")]
    else:
        targets = query_database(token, sns_db, filter_obj={
            "property": "Status", "select": {"equals": "Draft"}
        })
        if not args.all_drafts and targets:
            targets = targets[:1]

    if not targets:
        print("No matching SNS Queue records found.")
        sys.exit(1)

    results = []
    for page in targets:
        r = review_one(token, page)
        if r:
            results.append(r)

    print(f"DONE. {len(results)} SNS post(s) reviewed.")


if __name__ == "__main__":
    main()
