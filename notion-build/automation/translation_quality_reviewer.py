"""Phase B3.9: Translation Quality Reviewer.

Scores an unapproved Translation across 5 dimensions (Meaning Accuracy / Naturalness /
Cultural Adaptation / Terminology / Hallucination Risk) using the real AI Gateway,
writes scores + suggestions back onto the Translation page, and sets Quality Result.

Gate:
- Below Pass -> Publish Approval stays "Pending" (never advanced).
- Pass, but Parent Article.Update Level is 2 or 3 -> still "Pending"; human approval
  is required regardless of AI quality score (ARu Constitution Sec.9/13).
- Pass, Parent Article.Update Level == 1, AND Localization Status == "Culturally
  Adapted" -> Publish Approval is advanced to "Not Required" (matches the existing
  Level-1 auto-publish design; the Culturally Adapted requirement from Phase A is
  left untouched, not bypassed).
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

DIMENSIONS = ["MEANING_ACCURACY", "NATURALNESS", "CULTURAL_ADAPTATION", "TERMINOLOGY", "HALLUCINATION_RISK"]
PASS_OVERALL_THRESHOLD = 75
PASS_MEANING_THRESHOLD = 75
PASS_HALLUCINATION_THRESHOLD = 70


def rich_text_chunks(content, chunk_size=1990):
    chunks = [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)] or [""]
    return [{"text": {"content": c}} for c in chunks]


def build_prompt(source_title, source_body, translated_title, translated_body, language):
    return f"""あなたはARu（外国籍の方向け日本生活サポートメディア）のTranslation Quality Reviewerです。
以下は日本語の原文記事と、その{language}への翻訳です。翻訳を5つの観点で評価してください。各観点は0〜100点。

1. MEANING_ACCURACY（意味の正確性）：原文の意味を正確に保持しているか
2. NATURALNESS（自然さ）：対象言語として自然で読みやすいか
3. CULTURAL_ADAPTATION（文化的適応）：日本独自の文化・制度・暗黙のルールを、外国人読者に理解できるよう補足できているか
4. TERMINOLOGY（専門用語の正確性）：法律・行政・医療・生活に関する用語が正確に訳されているか
5. HALLUCINATION_RISK（幻覚リスクの低さ）：原文にない情報や、原文より断定的な表現を追加していないか（追加・誇張があるほど低スコア）

原文タイトル：{source_title}
原文本文：
{source_body}

翻訳タイトル：{translated_title}
翻訳本文：
{translated_body}

出力形式（このまま、数値と提案のみを出力し、他の説明は付けないこと）：
MEANING_ACCURACY: <0-100の数値>
NATURALNESS: <0-100の数値>
CULTURAL_ADAPTATION: <0-100の数値>
TERMINOLOGY: <0-100の数値>
HALLUCINATION_RISK: <0-100の数値>
SUGGESTIONS: <改善提案。300文字程度。具体的に>
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
    meaning = scores["MEANING_ACCURACY"]
    hallucination = scores["HALLUCINATION_RISK"]

    if overall >= PASS_OVERALL_THRESHOLD and meaning >= PASS_MEANING_THRESHOLD and hallucination >= PASS_HALLUCINATION_THRESHOLD:
        result = "Pass"
    elif overall < 50 or meaning < 50 or hallucination < 40:
        result = "Fail"
    else:
        result = "Needs Revision"
    return overall, result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--translation-id", default=None)
    args = parser.parse_args()

    env = load_env(ENV_PATH)
    token = env["NOTION_TOKEN"]
    translation_db = env["TRANSLATION_DB_ID"]

    if args.translation_id:
        translation = notion_request(token, "GET", f"/pages/{args.translation_id}")
    else:
        candidates = query_database(token, translation_db, filter_obj={
            "property": "Publish Approval", "select": {"equals": "Pending"}
        })
        if not candidates:
            print("ERROR: no Translation with Publish Approval=Pending found.")
            sys.exit(1)
        translation = candidates[0]

    translated_title = get_prop(translation, "Translated Title", "rich_text")
    translated_body = get_prop(translation, "Translated Body", "rich_text")
    language = get_prop(translation, "Language", "select")
    localization_status = get_prop(translation, "Localization Status", "select")
    parent_ids = get_prop(translation, "Parent Article", "relation")

    if not parent_ids:
        print("ERROR: Translation has no Parent Article linked.")
        sys.exit(1)
    parent_article = notion_request(token, "GET", f"/pages/{parent_ids[0]}")
    source_title = get_prop(parent_article, "Title", "title")
    source_body = get_prop(parent_article, "Body", "rich_text")
    update_level = get_prop(parent_article, "Update Level", "number") or 1

    print(f"Reviewing Translation: {translated_title} ({language})")
    print(f"  Parent Article Update Level: {update_level}")

    prompt = build_prompt(source_title, source_body, translated_title, translated_body, language)
    provider, text = ai_gateway.complete(prompt, max_tokens=800)
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
        "Quality Meaning Accuracy Score": {"number": scores["MEANING_ACCURACY"]},
        "Quality Naturalness Score": {"number": scores["NATURALNESS"]},
        "Quality Cultural Adaptation Score": {"number": scores["CULTURAL_ADAPTATION"]},
        "Quality Terminology Score": {"number": scores["TERMINOLOGY"]},
        "Quality Hallucination Risk Score": {"number": scores["HALLUCINATION_RISK"]},
        "Quality Result": {"select": {"name": result}},
        "Quality Suggestions": {"rich_text": rich_text_chunks(suggestions)},
        "Quality Review Date": {"date": {"start": datetime.date.today().isoformat()}},
    }

    # Gate logic: never advance Publish Approval below Pass; even on Pass, Update Level
    # 2/3 always requires a human; only Level 1 + Culturally Adapted may auto-clear.
    gate_note = ""
    if result != "Pass":
        update_props["Publish Approval"] = {"select": {"name": "Pending"}}
        gate_note = f"Quality Result={result} -> Publish Approval stays Pending."
    elif update_level in (2, 3):
        update_props["Publish Approval"] = {"select": {"name": "Pending"}}
        gate_note = f"Quality Result=Pass but Update Level {update_level} -> human approval required regardless; Publish Approval stays Pending."
    elif localization_status != "Culturally Adapted":
        update_props["Publish Approval"] = {"select": {"name": "Pending"}}
        gate_note = f"Quality Result=Pass but Localization Status={localization_status} (not Culturally Adapted yet) -> Publish Approval stays Pending."
    else:
        update_props["Publish Approval"] = {"select": {"name": "Not Required"}}
        gate_note = "Quality Result=Pass, Update Level 1, Localization Status=Culturally Adapted -> Publish Approval set to Not Required (auto-clear)."

    notion_request(token, "PATCH", f"/pages/{translation['id']}", {"properties": update_props})
    print(f"\nSAVED quality review to Translation {translation['id']}")
    print(f"GATE: {gate_note}")


if __name__ == "__main__":
    main()
