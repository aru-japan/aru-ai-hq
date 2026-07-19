"""ARu Studio v4.1 -- "Production Stage" property (Rei, 2026-07-19, extended
2026-07-19 to also cover Articles): the production pipeline a piece of
content moves through --

    Today's QA -> Headline Ready -> Basic Writing -> Deep Writing ->
    Translation -> SNS -> Ready -> Published

Added independently to BOTH Story Bank and Articles, tracking two different
things: Story Bank's Production Stage is the *originating Story's* overall
position (one Story can spawn several Articles of different Content Types
at different stages at once, so a single field on Story Bank can only ever
be an approximation of the furthest-along descendant); Articles' Production
Stage is each specific Article record's own position through to publication.

Explicitly NOT a replacement for either DB's existing Status-like field, per
Rei's clarification: "Status is editorial/approval state, Production Stage
is the production workflow -- keep the roles separated."
  - Story Bank's Story Status (New/Approved/In Production/Archived) --
    coarse editorial triage, doesn't distinguish *which* production step
    "In Production" means, and folding these 8 stages into it would break
    existing filters/automation that key off New/Approved/Archived as
    terminal-ish states rather than a sequential pipeline.
  - Articles' Status (Draft/AI Draft/Human Review/Approved/Published/
    Archived/Updating/Approval Required) -- the editorial/approval workflow
    (is this article reviewed and signed off), not the production workflow
    (which writing/translation/SNS step it's physically at). A Human
    Review-approved article can still be sitting in "Translation" from a
    Production Stage point of view.
  - Articles' Content Type (Headline/Basic Article/Deep Guide/Premium) --
    classifies *what kind* of content a record IS, not what stage of the
    production sequence it's currently at.

Options are defined in pipeline order (not severity order like Priority/
Urgency) since this is read as a Kanban sequence, not sorted descending for
"most severe first" -- also what makes a Notion Board view grouped by this
property read left-to-right as the real pipeline (see
Studio-v4.1-View-Setup-Guide.md; Board views can't be created via API, same
limitation as every other View in this project).

Schema only -- existing records are NOT backfilled with a stage. Assigning a
specific stage to real content (Story Bank's Batch #001 fireworks, none of
which have gone through the QA-card step, or existing Articles that predate
this property) would be guessing at editorial state that hasn't actually
been tracked. Left blank until a record genuinely enters the pipeline.
"""
import os
from notion_api import load_env, notion_request

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")

PRODUCTION_STAGE_OPTIONS = [
    "Today's QA", "Headline Ready", "Basic Writing", "Deep Writing",
    "Translation", "SNS", "Ready", "Published",
]


def add_production_stage(token, db_id, label):
    db = notion_request(token, "GET", f"/databases/{db_id}")
    if "Production Stage" in db["properties"]:
        print(f"'Production Stage' already exists on {label}, skipping.")
        return False
    notion_request(token, "PATCH", f"/databases/{db_id}", {
        "properties": {
            "Production Stage": {
                "select": {"options": [{"name": n} for n in PRODUCTION_STAGE_OPTIONS]}
            }
        }
    })
    print(f"Added 'Production Stage' to {label} with {len(PRODUCTION_STAGE_OPTIONS)} options: "
          f"{PRODUCTION_STAGE_OPTIONS}")
    return True


def main():
    env = load_env(ENV_PATH)
    token = env.get("NOTION_TOKEN", "")

    story_bank_id = env.get("STORY_BANK_DB_ID", "")
    articles_id = env.get("ARTICLES_DB_ID", "")
    if not token or not story_bank_id or not articles_id:
        print("ERROR: NOTION_TOKEN, STORY_BANK_DB_ID, or ARTICLES_DB_ID missing in .env")
        return

    add_production_stage(token, story_bank_id, "Story Bank")
    add_production_stage(token, articles_id, "Articles")


if __name__ == "__main__":
    main()
