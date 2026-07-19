"""ARu Studio v4.2 -- "Article Brief" evolution of Research (Rei, 2026-07-19).

Adds the 3 relations needed so a Research page can consolidate everything an
editor needs to write, without opening other databases:

  Research -> Law Update   ("Related Law Updates", new -- Research had no
                             path to Law Update at all before this)
  Research <-> Story Bank  ("Related QA", new -- the two origin pipelines
                             were previously disconnected)
  Research -> Articles     ("Related Articles", new -- deliberately separate
                             from the existing "Converted Article" relation,
                             which is the single conversion target; this one
                             is for related/similar published articles used
                             for context and duplicate-avoidance)

Also renames Research's existing, currently-unused "Raw Notes" to "Editor's
Notes" (grep-confirmed: only referenced in create_research.py's initial
schema, no automation script reads or writes it) -- this gives editors a
field clearly separated from the AI-only "Summary", per Rei's explicit
request, without adding a new property.

Everything else Rei asked for (Freshness, Why now?, Source Confidence) is
UI-only, built from properties that already exist (Last AI Update, Evidence
Level, Verification Status, AI Generated, Human Reviewed) -- no schema
change needed for those, see docs/Operating-Manual.md's new Article Brief
section for how they're meant to be read.
"""
import os
from notion_api import load_env, notion_request

ENV_PATH = os.path.join(os.path.dirname(__file__), ".env")


def main():
    env = load_env(ENV_PATH)
    token = env["NOTION_TOKEN"]

    research_id = env["RESEARCH_DB_ID"]
    law_update_id = env["LAW_UPDATE_DB_ID"]
    story_bank_id = env["STORY_BANK_DB_ID"]
    articles_id = env["ARTICLES_DB_ID"]

    db = notion_request(token, "GET", f"/databases/{research_id}")
    props = db["properties"]

    # Rename Raw Notes -> Editor's Notes (rich_text, no type change)
    if "Raw Notes" in props and "Editor's Notes" not in props:
        notion_request(token, "PATCH", f"/databases/{research_id}", {
            "properties": {"Raw Notes": {"name": "Editor's Notes"}}
        })
        print("Renamed 'Raw Notes' -> \"Editor's Notes\"")
    else:
        print("'Editor's Notes' already present or 'Raw Notes' missing, skipping rename.")

    # Re-fetch after rename so the relation-add step sees current properties
    db = notion_request(token, "GET", f"/databases/{research_id}")
    props = db["properties"]

    relations = [
        ("Related Law Updates", law_update_id),
        ("Related QA", story_bank_id),
        ("Related Articles", articles_id),
    ]
    for prop_name, target_id in relations:
        if prop_name in props:
            print(f"'{prop_name}' already exists, skipping.")
            continue
        notion_request(token, "PATCH", f"/databases/{research_id}", {
            "properties": {
                prop_name: {
                    "relation": {
                        "database_id": target_id,
                        "type": "dual_property",
                        "dual_property": {},
                    }
                }
            }
        })
        print(f"Added relation '{prop_name}'")


if __name__ == "__main__":
    main()
