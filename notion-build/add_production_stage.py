"""ARu Studio v4.1 -- adds Story Bank's "Production Stage" property (Rei,
2026-07-19): a single Story's journey from QA origination through to
Published --

    Today's QA -> Headline Ready -> Basic Writing -> Deep Writing ->
    Translation -> SNS -> Ready -> Published

This is a distinct axis from two existing Story Bank/Articles fields, kept
deliberately separate rather than folded in (per the reuse-over-new
directive, this was still weighed first -- see docs/Automation-Scripts.md):
  - Story Status (New/Approved/In Production/Archived) -- coarse editorial
    triage, doesn't distinguish *which* production step "In Production"
    means, and folding these 8 stages into it would break existing
    filters/automation that key off "New"/"Approved"/"Archived" as terminal-
    ish states rather than a sequential pipeline.
  - Articles.Content Type (Headline/Basic Article/Deep Guide/Premium) --
    classifies *what kind* of content a record IS, not what stage of the
    production sequence a Story is currently at.

Options are defined in pipeline order (not severity order like Priority/
Urgency) since this is read as a Kanban sequence, not sorted descending for
"most severe first".

Schema only -- existing Story Bank records are NOT backfilled with a stage.
Per the Story Bank anti-fabrication rule, assigning a specific stage to
real ChatGPT-curated content (e.g. the Batch #001 fireworks entries, none of
which have gone through the QA-card step yet) would be guessing at
editorial state that hasn't actually happened. Left blank until a record
genuinely enters the pipeline.
"""
import os
from notion_api import load_env, notion_request

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")

PRODUCTION_STAGE_OPTIONS = [
    "Today's QA", "Headline Ready", "Basic Writing", "Deep Writing",
    "Translation", "SNS", "Ready", "Published",
]


def main():
    env = load_env(ENV_PATH)
    token = env.get("NOTION_TOKEN", "")
    db_id = env.get("STORY_BANK_DB_ID", "")

    if not token or not db_id:
        print("ERROR: NOTION_TOKEN or STORY_BANK_DB_ID missing in .env")
        return

    db = notion_request(token, "GET", f"/databases/{db_id}")
    if "Production Stage" in db["properties"]:
        print("'Production Stage' already exists, skipping.")
        return

    notion_request(token, "PATCH", f"/databases/{db_id}", {
        "properties": {
            "Production Stage": {
                "select": {"options": [{"name": n} for n in PRODUCTION_STAGE_OPTIONS]}
            }
        }
    })
    print(f"Added 'Production Stage' to Story Bank with {len(PRODUCTION_STAGE_OPTIONS)} options: "
          f"{PRODUCTION_STAGE_OPTIONS}")


if __name__ == "__main__":
    main()
