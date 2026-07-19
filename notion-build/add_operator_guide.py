"""ARu Studio v4.2 -- first operational-phase improvement (Rei, 2026-07-19):
a short "operator guide" written into each database's own `description`
field (Notion's built-in subtitle text, rendered directly under the title
at the very top of the database page). Purpose: Rei can open any database
cold and immediately know (1) what it's for, (2) when to use it, (3) which
database to go to next, (4) whether AI or a human drives it, (5) a concrete
example, and (6) the next concrete action to take.

Deliberately uses the `description` field rather than page-body blocks --
it's the only mechanism that puts text at the very top of a full-page
database without touching properties, schema, or relations (Rei's explicit
constraint), and it survives independently of the table/view content below.

Story Bank's wording reflects the *actual current implementation*, not the
aspirational Story Bank->QA Card->Article->Deep Guide->SNS pipeline
described in User-Journey-Architecture-v1.0.md Chapter 5: there is no
Story Bank->Article auto-generation pipeline yet (Automation-Scripts.md,
"ARu Studio v4.1" section, known gaps), so the real day-to-day path is
Story Bank idea -> Research (where generate_article_pipeline.py can
actually pick it up) -> Articles, with direct manual Story Bank->Articles
authorship as the fallback for content that doesn't need full Research
treatment. Confirmed with Rei (2026-07-19) rather than left as the
aspirational description.

Safe to re-run: each run simply overwrites the `description` field with the
current text below (idempotent, no properties/relations touched).
"""
import os
from notion_api import load_env, notion_request

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")

GUIDES = {
    "STORY_BANK_DB_ID": (
        "役割：記事・QA・SNSになるアイデアを保管する場所\n"
        "使うタイミング：新しいネタを思いついた時\n"
        "次：通常はResearchへ登録し、必要に応じてArticlesへ手動で記事化\n"
        "担当：人（ChatGPTが作成支援）\n"
        "例：「日本の花火大会50選」\n"
        "\n"
        "次の作業：\n"
        "通常はResearchへ登録し、必要に応じてArticlesへ手動で記事化します。"
    ),
    "RESEARCH_DB_ID": (
        "役割：実際に記事化する候補\n"
        "使うタイミング：今日の記事を決める時\n"
        "次：Articles\n"
        "担当：AI＋人\n"
        "例：「外国人向け熱中症対策」\n"
        "\n"
        "次の作業：\n"
        "Articlesへ進みます。"
    ),
    "ARTICLES_DB_ID": (
        "役割：完成記事\n"
        "使うタイミング：記事を書く時\n"
        "次：公開・翻訳・SNS\n"
        "担当：AI（生成）＋人（最終承認・公開操作）\n"
        "例：「外国人が日本で健康保険に入る手順」\n"
        "\n"
        "次の作業：\n"
        "Translation・SNS Queueを進め、準備が整ったら公開します。"
    ),
    "TRANSLATION_DB_ID": (
        "役割：記事の多言語版\n"
        "使うタイミング：Articlesが完成し、多言語展開する時\n"
        "次：SNS Queue／公開判断\n"
        "担当：AI（生成）＋人（品質レビュー・重要度が高い記事は承認必須）\n"
        "例：健康保険記事の英語・中国語・ベトナム語版\n"
        "\n"
        "次の作業：\n"
        "SNS Queueへ進むか、公開判断へ進みます。"
    ),
    "SOURCE_LIBRARY_DB_ID": (
        "役割：定期的に見張る公式情報源(役所サイト等)の台帳\n"
        "使うタイミング：新しい信頼できる情報源を知った時に登録\n"
        "次：Source Monitor（自動で変化を監視）\n"
        "担当：人（登録）＋AI（自動巡回）\n"
        "例：「出入国在留管理庁」の在留資格ページ\n"
        "\n"
        "次の作業：\n"
        "登録すればSource Monitorが自動で見張ります。"
    ),
    "SOURCE_MONITOR_DB_ID": (
        "役割：Source Libraryの情報源に変化がないか自動検知した記録\n"
        "使うタイミング：基本は見るだけ(AIが自動生成、日々触る必要はない)\n"
        "次：Research（記事化候補へ）／Law Update（法律系の場合）\n"
        "担当：AI（自動検知）\n"
        "例：「入管サイトのビザ手続きページが更新された」\n"
        "\n"
        "次の作業：\n"
        "内容に応じてResearchまたはLaw Updateへ進みます。"
    ),
    "LAW_UPDATE_DB_ID": (
        "役割：法改正・行政ルール変更を専門に追跡するリスト\n"
        "使うタイミング：Source Monitorで法律・制度系の変化が検知された時に確認する\n"
        "次：Articles（既存記事の更新）\n"
        "担当：AI（候補作成）＋人（内容確認・承認は必須）\n"
        "例：「在留資格の更新手続きが変更された」\n"
        "\n"
        "次の作業：\n"
        "内容を確認・承認したらArticlesへ進みます。"
    ),
    "EVENT_CALENDAR_DB_ID": (
        "役割：祭り・花火大会・季節イベントなど日付のあるイベントの台帳\n"
        "使うタイミング：新しいイベント情報(開催日・場所)を知った時に登録\n"
        "次：Articles（イベント記事化）\n"
        "担当：人（登録）＋AI（記事化候補として活用）\n"
        "例：「隅田川花火大会 2026年7月26日開催」\n"
        "\n"
        "次の作業：\n"
        "Articlesへ進みます。"
    ),
    "EDITORIAL_CALENDAR_DB_ID": (
        "役割：いつ何を書く・公開するかのスケジュール表\n"
        "使うタイミング：ネタは決まったが執筆・公開時期を計画する時\n"
        "次：Articles（実際の執筆着手）\n"
        "担当：人（計画）\n"
        "例：「夏祭り特集を7月中に3本公開する」\n"
        "\n"
        "次の作業：\n"
        "執筆を始めるタイミングでArticlesへ進みます。"
    ),
    "EXPERIENCE_INTELLIGENCE_DB_ID": (
        "役割：まだ記事化されていない「兆し」(需要のギャップ・トレンド等)を発見する信号層\n"
        "使うタイミング：AIが検知した新しい機会・需要を確認する時\n"
        "次：Research（記事化候補への昇格）\n"
        "担当：AI（自動検知）＋人（確認・昇格判断）\n"
        "例：「『在留カード紛失』についての質問が急増している」\n"
        "\n"
        "次の作業：\n"
        "昇格を判断したらResearchへ進みます。"
    ),
    "SNS_QUEUE_DB_ID": (
        "役割：公開記事のSNS投稿文(Instagram/Threads/X)を管理する場所\n"
        "使うタイミング：Articlesが公開された後、SNS告知を確認・投稿する時\n"
        "次：（パイプラインの終端。実際の投稿は人が行う）\n"
        "担当：AI（下書き生成）＋人（最終確認・実投稿）\n"
        "例：健康保険記事のInstagram投稿文ドラフト\n"
        "\n"
        "次の作業：\n"
        "内容を確認し、実際にSNSへ投稿します。"
    ),
}


def rt(text):
    return [{"type": "text", "text": {"content": text}}]


def set_description(token, db_id, label, text):
    notion_request(token, "PATCH", f"/databases/{db_id}", {"description": rt(text)})
    print(f"Set description on {label} ({len(text)} chars).")


def main():
    env = load_env(ENV_PATH)
    token = env.get("NOTION_TOKEN", "")
    if not token:
        print("ERROR: NOTION_TOKEN missing in .env")
        return

    for env_key, text in GUIDES.items():
        db_id = env.get(env_key, "")
        label = env_key.replace("_DB_ID", "")
        if not db_id:
            print(f"WARNING: {env_key} missing in .env, skipping {label}.")
            continue
        set_description(token, db_id, label, text)


if __name__ == "__main__":
    main()
