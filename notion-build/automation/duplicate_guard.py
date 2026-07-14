"""Duplicate Prevention Guard -- Version 4 Phase 4.

ARu's principle: **1 Research Topic = 1 Article.** If content needs updating,
update the existing Article -- never spawn a second Research+Article pipeline
for the same topic. This module is checked BEFORE any generation happens, not
after -- prevention, not detection.

This exists because of the 2026-07-14 incident where 13 topics were generated
twice (an overlapping background run) plus 2 older duplicates, discovered only
after 30 Articles/Translations/90 SNS posts had already been created and had
to be manually investigated and archived. check_before_generate() is the
single entry point both generate_article_pipeline.py (single-article CLI) and
bulk_generate_articles.py (batch) call before spending any AI Gateway call or
creating any Notion record.

Checks, in order, stopping at the first stage that doesn't exist:
    ① Research.Topic (exact match)
    ② a non-Archived Article converted from that Research
    ③ a Translation for that Article
    ④ SNS Queue posts for that Article
"""
import os
import sys
import json
import datetime

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)

from notion_api import notion_request, query_database, get_prop  # noqa: E402

LOG_DIR = os.path.join(AUTOMATION_DIR, "logs")
LOG_PATH = os.path.join(LOG_DIR, "duplicate_prevention.jsonl")


def _log(event):
    os.makedirs(LOG_DIR, exist_ok=True)
    event = dict(event)
    event["timestamp"] = datetime.datetime.now().isoformat()
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def _find_non_archived_article(token, research_pages):
    """Among the Converted Article relations on any of these Research pages,
    return the first non-Archived Article id + its owning Research id, or
    (None, None) if none of them have a live Article yet."""
    for r in research_pages:
        for aid in get_prop(r, "Converted Article", "relation"):
            article = notion_request(token, "GET", f"/pages/{aid}")
            if get_prop(article, "Status", "select") != "Archived":
                return aid, r["id"]
    return None, None


def check_before_generate(token, env, topic_text, expect_research=False):
    """Call this BEFORE generating anything for `topic_text`.

    expect_research=False (bulk_generate_articles.py, which creates the Research
        record itself as part of the run): any existing Research with this exact
        Topic text is already the anomaly to prevent -- creating a second one
        would repeat the 2026-07-14 bug. Blocks at stage='Research' minimum.
    expect_research=True (generate_article_pipeline.py run_article, which by
        design operates on an ALREADY-EXISTING Converted Research): Research
        existing is normal and expected, not a violation. Only blocks if a
        non-Archived Article (or deeper stage) already exists for it.

    Returns None if safe to generate. Otherwise returns
    {'stage': 'Research'|'Article'|'Translation'|'SNS', 'research_id', 'article_id'}
    and logs an 'Already Exists' event.
    """
    research_matches = query_database(token, env["RESEARCH_DB_ID"], filter_obj={
        "property": "Topic", "title": {"equals": topic_text}
    })
    if not research_matches:
        return None  # ① Research does not exist yet -> safe

    if not expect_research:
        stage = "Research"
        matched_research_id = research_matches[0]["id"]
        article_id, aid_research = _find_non_archived_article(token, research_matches)
        if article_id:
            stage = "Article"
            matched_research_id = aid_research
    else:
        article_id, matched_research_id = _find_non_archived_article(token, research_matches)
        if not article_id:
            return None  # Research exists (expected here), no Article yet -> safe
        stage = "Article"

    if article_id:
        translations = query_database(token, env["TRANSLATION_DB_ID"], filter_obj={
            "property": "Parent Article", "relation": {"contains": article_id}
        })
        if translations:
            stage = "Translation"
            sns = query_database(token, env["SNS_QUEUE_DB_ID"], filter_obj={
                "property": "Related Article", "relation": {"contains": article_id}
            })
            if sns:
                stage = "SNS"

    result = {"stage": stage, "research_id": matched_research_id, "article_id": article_id}
    _log({
        "event": "Already Exists", "topic": topic_text, "stage": stage,
        "research_id": matched_research_id, "article_id": article_id,
    })
    return result


def log_generated(topic_text, article_id):
    _log({"event": "Generated", "topic": topic_text, "article_id": article_id})
