"""Writer Agent: given a topic, check existing Article/Editorial Calendar coverage in
Notion and print a Markdown article-draft scaffold (category, audience, update level
suggestion, and an outline). The prose itself is written by the AI operator (Claude)
during Pilot Operation; this script only gathers real context and never writes to Notion.
"""
import argparse
from _common import get_env, query_database, get_prop

LEVEL_1_CATEGORIES = {"イベント", "日本文化", "旅行情報", "生活情報", "ニュース", "トレンド"}
LEVEL_2_CATEGORIES = {"法律・制度"}


def contains_filter(prop_name, prop_type, text):
    return {"property": prop_name, prop_type: {"contains": text}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    parser.add_argument("--keyword", default=None)
    parser.add_argument("--category", default="法律・制度")
    args = parser.parse_args()
    keyword = args.keyword or args.topic

    env = get_env()
    token = env["NOTION_TOKEN"]

    print(f"# Article Draft Scaffold: {args.topic}\n")
    print("_Notionの既存カバレッジを確認。本文の執筆はAI Operator（Claude）が行う。_\n")

    print("## 既存記事の重複確認")
    articles = query_database(token, env["ARTICLES_DB_ID"], filter_obj=contains_filter("Title", "title", keyword))
    if not articles:
        print("- 既存記事なし → 新規作成が妥当")
    for a in articles:
        print(f"- 既存: {get_prop(a, 'Title', 'title')} (Status={get_prop(a, 'Status', 'select')}) → 新規作成ではなく更新を検討")

    print("\n## Editorial Calendarとの照合")
    calendar_entries = query_database(token, env["EDITORIAL_CALENDAR_DB_ID"], filter_obj=contains_filter("Planned Topic", "title", keyword))
    if not calendar_entries:
        print("- 対応する編集計画なし（Pilot運用のため今回はEditorial Calendarへの登録は行わない）")
    for c in calendar_entries:
        print(f"- 計画あり: {get_prop(c, 'Planned Topic', 'title')} (Status={get_prop(c, 'Status', 'select')})")

    suggested_level = 2 if args.category in LEVEL_2_CATEGORIES else 1
    print("\n## 推奨メタデータ")
    print(f"- Category: {args.category}")
    print(f"- 推奨 Update Level: {suggested_level}（{'法律・制度カテゴリのため人間レビュー必須' if suggested_level == 2 else '自動公開カテゴリ'}）")
    print("- Audience: 在住外国人, 留学生, 技能実習生, 特定技能")
    print("- Urgency: Medium（Law Updateとの関連が確認されれば見直す）")

    print("\n## 本文アウトライン（Writer Agentが以下を執筆）")
    print("1. 導入：何が変わる／何をすべきか")
    print("2. 背景（なぜこの手続きが必要か、文化的・制度的背景）")
    print("3. 具体的な手順")
    print("4. 注意点・よくある間違い")
    print("5. 相談先（専門家・窓口の案内）")


if __name__ == "__main__":
    main()
