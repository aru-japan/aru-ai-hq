"""ARu Studio v4.1 Editorial Intelligence -- Stage 3: Law Update pipeline.

Implements the 8-step flow Rei specified (A-H) as a Human-in-the-loop queue:
change detection -> candidate creation -> human confirmation -> impact
extraction -> human edit -> downstream sync -> publish -> version bump.
The AI never sets Published and never auto-confirms legal significance --
every stage transition that matters (Monitoring->Confirmed,
Reflecting to Article->Approval Required->Article Published) is made by a
human directly in Notion; this script only acts on transitions a human has
already made, consistent with enforce_publish_gate.py's existing philosophy.

Step mapping (A/B already exist in source_watcher.py, unchanged here):
  A. Source Monitor confirms sources         -- existing source_watcher.py
  B. Change detected                         -- existing source_watcher.py (Change Detected=true)
  C. Law Update candidate created             -- create_law_update_candidates() (also assigns an
                                                  initial Priority from Urgency -- reuses Law Update's
                                                  existing Priority property, High/Medium/Low, rather
                                                  than adding a new one)
  D. Previous/new information saved          -- folded into C (New Rule from Diff/Change Summary;
                                                 Previous Rule intentionally left blank -- no raw
                                                 prior full-text snapshot exists anywhere in the
                                                 schema (only a SimHash fingerprint), and fabricating
                                                 it would violate the no-guessing rule)
  E. Affected QA/Article/Deep Guide/Premium/SNS
     extracted, Priority refined by breadth    -- run_impact_analysis() (Category-based matching,
                                                  writes a structured breakdown into Law Update's
                                                  existing Impact Summary field, and re-scores Priority
                                                  now that the true breadth of impact is known)
  F. Flip to "needs review"                   -- folded into E (sets Articles.Current Validity =
                                                 "Review Due" -- a new, narrower "is the underlying
                                                 fact still valid" signal, deliberately NOT touching
                                                 Freshness Status / Publishing Status, which remain
                                                 owned by article_freshness_monitor.py / publishing_center.py)
  G. Translation / SNS Queue sync             -- sync_downstream_on_resolution() (Translation only;
                                                 SNS Queue has no "needs update" field in this schema
                                                 addition, see Known Gaps in the docstring below)
  H. Version / Last Verified Date bump        -- bump_on_publish()

Periodic review scheduling (Next Review computation, review-due extraction
across Story Bank/Articles) lives in review_scheduler.py, not here -- it's a
distinct concern (calendar-driven, not change-detection-driven) that also
serves content Law Update never touches.

Human decision points (never advanced by this script):
  - Monitoring -> Confirmed          : a human decides the detected change is real/significant
  - Reflecting to Article -> Approval Required : a human finishes editing
  - Approval Required -> Article Published     : a human approves and publishes (via existing
                                                  Publishing Center flow, never this script)

Known gap: SNS Queue has no per-record "needs update" field added in Stage 1
(it wasn't in Rei's requested property list), so step G only flags
Translations (Needs Re-Translation=true). Flagged in the completion report,
not silently patched over.
"""
import os
import sys
from datetime import date

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)

from notion_api import load_env, notion_request, query_database, get_prop  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")


def log(msg):
    print(msg)


def relation_ids(page, prop_name):
    prop = page["properties"].get(prop_name)
    if not prop or prop["type"] != "relation":
        return []
    return [r["id"] for r in prop["relation"]]


def set_relation(token, page_id, prop_name, page_ids):
    notion_request(token, "PATCH", f"/pages/{page_id}", {
        "properties": {prop_name: {"relation": [{"id": pid} for pid in page_ids]}}
    })


# Reuses Law Update's existing Priority property (High/Medium/Low) rather
# than adding a new "computed priority" field. Deterministic, not AI-judged:
# Urgency alone at candidate-creation time (breadth unknown yet), refined
# once run_impact_analysis() knows how many QA/Articles/SNS posts are
# actually affected -- a change that's merely "High" urgency but turns out
# to touch a dozen articles deserves to outrank one that touches none.
def compute_priority(urgency, affected_count=0):
    if urgency == "Critical":
        return "High"
    if urgency == "High":
        return "High" if affected_count >= 3 else "Medium"
    if urgency == "Medium":
        return "Medium" if affected_count >= 3 else "Low"
    return "Low"


# ---- C/D: create Law Update candidates from detected Source Monitor changes ----

def create_law_update_candidates(env, dry_run=False):
    token = env["NOTION_TOKEN"]
    monitors = query_database(token, env["SOURCE_MONITOR_DB_ID"])
    created = []
    for m in monitors:
        if not get_prop(m, "Change Detected", "checkbox"):
            continue
        if relation_ids(m, "Related Law Updates"):
            continue  # already has a candidate, skip

        entry_title = get_prop(m, "Monitor Entry", "title") or "(無題の監視エントリ)"
        diff_summary = get_prop(m, "Diff Summary", "rich_text") or ""
        change_summary = get_prop(m, "Change Summary", "rich_text") or ""
        impact_level = get_prop(m, "Impact Level", "select")
        source_ids = relation_ids(m, "Source")

        title = f"{entry_title} — 変更検知（未確認）"
        new_rule_text = diff_summary or change_summary or ""

        props = {
            "Law Name": {"title": [{"text": {"content": title}}]},
            "Update Status": {"select": {"name": "Monitoring"}},
            "Verification Status": {"select": {"name": "Unverified"}},
            "AI Generated": {"checkbox": True},
            "Human Reviewed": {"checkbox": False},
            "Announcement Date": {"date": {"start": date.today().isoformat()}},
        }
        if new_rule_text:
            props["New Rule"] = {"rich_text": [{"text": {"content": new_rule_text[:2000]}}]}
        if impact_level:
            props["Urgency"] = {"select": {"name": impact_level}}
            props["Priority"] = {"select": {"name": compute_priority(impact_level)}}
        if source_ids:
            props["Related Source Library"] = {"relation": [{"id": pid} for pid in source_ids]}

        if dry_run:
            created.append((title, None))
            continue

        page = notion_request(token, "POST", "/pages", {
            "parent": {"database_id": env["LAW_UPDATE_DB_ID"]}, "properties": props
        })
        set_relation(token, m["id"], "Related Law Updates", [page["id"]])
        created.append((title, page["id"]))
        log(f"  candidate created: {title}")
    return created


# ---- E/F: for human-confirmed Law Updates, extract affected QA/Article/Deep Guide/Premium/SNS ----

def _content_type_breakdown(articles_subset):
    """Groups matched Articles by their existing Content Type property.
    Unset Content Type (pre-v4.1 articles) is counted separately rather than
    silently folded into "Basic Article" -- it genuinely isn't classified yet."""
    counts = {"Headline": 0, "Basic Article": 0, "Deep Guide": 0, "Premium": 0, "Update Notice": 0, "(未分類)": 0}
    for a in articles_subset:
        ct = get_prop(a, "Content Type", "select") or "(未分類)"
        counts[ct] = counts.get(ct, 0) + 1
    return {k: v for k, v in counts.items() if v > 0}


def run_impact_analysis(env, dry_run=False):
    token = env["NOTION_TOKEN"]
    law_updates = query_database(token, env["LAW_UPDATE_DB_ID"])
    story_bank = query_database(token, env["STORY_BANK_DB_ID"])
    articles = query_database(token, env["ARTICLES_DB_ID"])

    results = []
    for lu in law_updates:
        if get_prop(lu, "Update Status", "select") != "Confirmed":
            continue
        if relation_ids(lu, "Affected Stories") or relation_ids(lu, "Affected Articles"):
            continue  # already analyzed

        affected_category = get_prop(lu, "Affected Category", "select")
        if not affected_category:
            results.append((get_prop(lu, "Law Name", "title"), "skipped: Affected Category not set")); continue

        matched_stories = [p for p in story_bank if get_prop(p, "Category", "select") == affected_category]
        matched_qa = [p for p in matched_stories if get_prop(p, "QA Question", "rich_text")]
        matched_articles = [p for p in articles if get_prop(p, "Category", "select") == affected_category]
        matched_article_ids = [p["id"] for p in matched_articles]
        matched_sns = [s for a in matched_articles for s in relation_ids(a, "Related to SNS Queue (Related Article)")]
        matched_sns = list(dict.fromkeys(matched_sns))  # de-dupe, preserve order

        breakdown = _content_type_breakdown(matched_articles)
        breakdown_text = "、".join(f"{k}: {v}件" for k, v in breakdown.items()) or "0件"
        affected_count = len(matched_stories) + len(matched_articles)
        priority = compute_priority(get_prop(lu, "Urgency", "select"), affected_count)
        impact_summary = (
            f"影響範囲 -- QA(Story Bank): {len(matched_qa)}件 / 記事: {len(matched_articles)}件"
            f"（{breakdown_text}）/ 関連SNS投稿: {len(matched_sns)}件"
        )

        if dry_run:
            results.append((get_prop(lu, "Law Name", "title"),
                             f"would link {len(matched_stories)} stories, {len(matched_articles)} articles, "
                             f"priority={priority} -- {impact_summary}"))
            continue

        if matched_stories:
            set_relation(token, lu["id"], "Affected Stories", [p["id"] for p in matched_stories])
        if matched_article_ids:
            set_relation(token, lu["id"], "Affected Articles", matched_article_ids)
            for aid in matched_article_ids:
                notion_request(token, "PATCH", f"/pages/{aid}", {
                    "properties": {"Current Validity": {"select": {"name": "Review Due"}}}
                })
        notion_request(token, "PATCH", f"/pages/{lu['id']}", {
            "properties": {
                "Update Status": {"select": {"name": "Reflecting to Article"}},
                "Priority": {"select": {"name": priority}},
                "Impact Summary": {"rich_text": [{"text": {"content": impact_summary}}]},
            }
        })
        results.append((get_prop(lu, "Law Name", "title"),
                         f"linked {len(matched_stories)} stories, {len(matched_articles)} articles, "
                         f"priority={priority} -> Reflecting to Article"))
    return results


# ---- G: once a human resolves an Article's Current Validity back to Current, flag Translations ----

def sync_downstream_on_resolution(env, dry_run=False):
    token = env["NOTION_TOKEN"]
    articles = query_database(token, env["ARTICLES_DB_ID"])
    translations = query_database(token, env["TRANSLATION_DB_ID"])

    results = []
    for a in articles:
        if get_prop(a, "Current Validity", "select") != "Current":
            continue
        linked_lu = relation_ids(a, "Related to Law Update (Affected Articles)") or relation_ids(a, "Source Law Update")
        if not linked_lu:
            continue
        related_translations = [t for t in translations if a["id"] in relation_ids(t, "Parent Article")]
        for t in related_translations:
            if get_prop(t, "Needs Re-Translation", "checkbox"):
                continue
            if dry_run:
                results.append((get_prop(t, "Translation Name", "title"), "would flag Needs Re-Translation"))
                continue
            notion_request(token, "PATCH", f"/pages/{t['id']}", {
                "properties": {"Needs Re-Translation": {"checkbox": True}}
            })
            results.append((get_prop(t, "Translation Name", "title"), "flagged Needs Re-Translation"))
    return results


# ---- H: after Publishing Status flips to Published, bump Version / Last Verified Date ----

def bump_on_publish(env, dry_run=False):
    token = env["NOTION_TOKEN"]
    articles = query_database(token, env["ARTICLES_DB_ID"])
    today = date.today().isoformat()

    results = []
    for a in articles:
        if get_prop(a, "Publishing Status", "select") != "Published":
            continue
        if get_prop(a, "Current Validity", "select") not in ("Review Due", "Outdated", "Under Review"):
            continue  # only bump articles that were mid-update-cycle, not every published article
        version = get_prop(a, "Version", "number") or 0
        title = get_prop(a, "Title", "title")
        if dry_run:
            results.append((title, f"would set Version={version + 1}, Last Verified Date={today}, Current Validity=Current"))
            continue
        notion_request(token, "PATCH", f"/pages/{a['id']}", {
            "properties": {
                "Version": {"number": version + 1},
                "Last Verified Date": {"date": {"start": today}},
                "Current Validity": {"select": {"name": "Current"}},
            }
        })
        results.append((title, f"Version -> {version + 1}, Last Verified Date -> {today}"))
    return results


def main():
    dry_run = "--dry-run" in sys.argv
    env = load_env(ENV_PATH)

    log("=" * 70)
    log("Law Update Pipeline (ARu Studio v4.1, Stage 3)" + (" [DRY RUN]" if dry_run else ""))
    log("=" * 70)

    log("\n[C/D] Creating Law Update candidates from detected Source Monitor changes...")
    created = create_law_update_candidates(env, dry_run)
    log(f"  {len(created)} candidate(s)")

    log("\n[E/F] Running impact analysis on human-confirmed Law Updates...")
    analyzed = run_impact_analysis(env, dry_run)
    for name, outcome in analyzed:
        log(f"  {name}: {outcome}")

    log("\n[G] Syncing Translations for resolved Articles...")
    synced = sync_downstream_on_resolution(env, dry_run)
    for name, outcome in synced:
        log(f"  {name}: {outcome}")

    log("\n[H] Bumping Version/Last Verified Date on published, previously-flagged Articles...")
    bumped = bump_on_publish(env, dry_run)
    for name, outcome in bumped:
        log(f"  {name}: {outcome}")


if __name__ == "__main__":
    main()
