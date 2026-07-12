import os
import sys
from notion_api import load_env, set_env_value, notion_request

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")


def heading(text):
    return {
        "object": "block", "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]}
    }


def callout(text, emoji="💡"):
    return {
        "object": "block", "type": "callout",
        "callout": {
            "rich_text": [{"type": "text", "text": {"content": text}}],
            "icon": {"type": "emoji", "emoji": emoji},
        }
    }


def divider():
    return {"object": "block", "type": "divider", "divider": {}}


def main():
    env = load_env(ENV_PATH)
    token = env.get("NOTION_TOKEN", "")
    page_id = env.get("ARU_STUDIO_PAGE_ID", "")

    if not token or not page_id:
        print("ERROR: NOTION_TOKEN or ARU_STUDIO_PAGE_ID missing in .env")
        sys.exit(1)

    print("Creating 'Dashboard' page under ARu Studio page...")

    children = [
        callout(
            "このページはARu Studioのホーム画面です。各見出しの下に、対応するデータベースの"
            "「Linked view of database」を埋め込んでください（NotionパブリックAPIではLinked viewを"
            "作成できないため、この8ブロックの雛形のみ自動生成し、埋め込みは手動で行う想定です）。",
            "🏠"
        ),
        divider(),

        heading("☀️ Today's Opportunities"),
        callout("Experience Intelligence / Filter: Intelligence Type=Opportunity, Status is New or Acknowledged / Sort: Opportunity Score 降順", "🟢"),

        heading("🧩 Knowledge Gaps"),
        callout("Experience Intelligence / Filter: Intelligence Type=Gap, Status=New / Sort: Urgency 降順（Legal Gapグループを手動で最上段に）", "🟡"),

        heading("🚨 Critical Updates"),
        callout("Experience Intelligence / Filter: Urgency=Critical / 補助でArticles（Verification Status=Needs Recheck）も追加可", "🔴"),

        heading("🌍 Translation Queue"),
        callout("Translation / Filter: Needs Re-Translation=チェック済み or AI Translation Status=Queued / Sort: Review Level 降順", "🌐"),

        heading("📅 Today's Editorial Tasks"),
        callout("Editorial Calendar / Filter: Status is Idea, Planned, or In Progress / Sort: Urgency 降順 → Planned Date 昇順", "📝"),

        heading("📄 Articles Awaiting Review"),
        callout("Articles / Filter: Status is AI Draft or Human Review / Sort: Urgency 降順 → Updated Date 昇順", "📄"),

        heading("🎉 Upcoming Events"),
        callout("Event Calendar / 未実装（Law Update→Event Calendar→SNS Queueの順で今後作成）。作成後にLinked viewを埋め込む", "⏳"),

        heading("📡 Recent Source Changes"),
        callout("Source Monitor / Filter: なし（全件）/ Sort: Checked At 降順（直近の変化が上に来る）", "📡"),
    ]

    body = {
        "parent": {"type": "page_id", "page_id": page_id},
        "icon": {"type": "emoji", "emoji": "🏠"},
        "properties": {
            "title": [{"type": "text", "text": {"content": "Dashboard"}}]
        },
        "children": children,
    }

    page = notion_request(token, "POST", "/pages", body)
    page_id_created = page["id"]
    print(f"Created Dashboard page. DASHBOARD_PAGE_ID = {page_id_created}")

    set_env_value(ENV_PATH, "DASHBOARD_PAGE_ID", page_id_created)
    print("Wrote DASHBOARD_PAGE_ID to .env")
    print("DONE.")


if __name__ == "__main__":
    main()
