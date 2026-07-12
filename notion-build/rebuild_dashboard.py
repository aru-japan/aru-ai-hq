"""Rebuild the Dashboard page as the Editor-in-Chief home screen: archive the old
placeholder blocks and replace them with the 9 requested sections, in priority order.

Notion's public API still cannot create a live "Linked view of database" block, so
this script produces the scaffold (headings + exact Filter/Sort instructions) for
Rei to embed manually, same approach as the original Dashboard build.
"""
from notion_api import load_env, notion_request

ENV_PATH = ".env"


def heading(text):
    return {"object": "block", "type": "heading_2",
            "heading_2": {"rich_text": [{"type": "text", "text": {"content": text}}]}}


def callout(text, emoji="💡"):
    return {"object": "block", "type": "callout",
            "callout": {"rich_text": [{"type": "text", "text": {"content": text}}],
                        "icon": {"type": "emoji", "emoji": emoji}}}


def divider():
    return {"object": "block", "type": "divider", "divider": {}}


def main():
    env = load_env(ENV_PATH)
    token = env["NOTION_TOKEN"]
    page_id = env["DASHBOARD_PAGE_ID"]

    print("Archiving existing Dashboard blocks...")
    resp = notion_request(token, "GET", f"/blocks/{page_id}/children?page_size=100")
    for b in resp["results"]:
        notion_request(token, "PATCH", f"/blocks/{b['id']}", {"archived": True})
    print(f"  archived {len(resp['results'])} block(s)")

    children = [
        callout(
            "編集長ホーム画面。上から「今すぐ判断が必要なもの」→「今日の予定」→「外部シグナル」の順に並んでいる。"
            "各見出しの下に「Linked view of database」を埋め込むこと（NotionパブリックAPIでは自動埋め込み不可のため、手動設定が必要）。",
            "🏠"
        ),
        divider(),

        heading("① Publish Approval Pending"),
        callout("Translation / Filter: Publish Approval=Pending / Sort: Quality Overall Score 降順（対応しやすいものから）", "🔴"),

        heading("② Article Review Waiting"),
        callout("Articles / Filter: Status is AI Draft or Human Review / Sort: Urgency 降順 → Updated Date 昇順", "📄"),

        heading("③ Translation Review Waiting"),
        callout("Translation / Filter: Quality Result is empty or Not Reviewed / Sort: 作成日 昇順（古いものから）", "🌍"),

        heading("④ SNS Draft Waiting"),
        callout("SNS Queue / Filter: Status=Draft and Review Result is not Pass / Sort: 作成日 昇順", "📣"),

        heading("⑤ Today's Editorial Calendar"),
        callout("Editorial Calendar / Filter: Status is Idea, Planned, or In Progress / Sort: Urgency 降順 → Planned Date 昇順", "📅"),

        heading("⑥ Today's Research"),
        callout("Research / Filter: Status=New / Sort: Priority 降順 → Urgency 降順", "🔍"),

        heading("⑦ Source Monitor Alerts"),
        callout("Source Monitor / Filter: Change Detected=true / Sort: Checked At 降順（直近の変化が上に）", "📡"),

        heading("⑧ Recent Law Updates"),
        callout("Law Update / Filter: なし（全件）/ Sort: Effective Date 降順", "⚖️"),

        heading("⑨ Recent Event Calendar"),
        callout("Event Calendar / Filter: Status is not Cancelled / Sort: Event Date 昇順（近いものが上に）", "🎉"),
    ]

    print("Appending new Dashboard structure (9 sections)...")
    # Notion allows up to 100 children per append call; this fits in one call.
    notion_request(token, "PATCH", f"/blocks/{page_id}/children", {"children": children})
    print("DONE. Dashboard page rebuilt with 9 sections.")


if __name__ == "__main__":
    main()
