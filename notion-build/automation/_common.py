"""Shared setup for automation scripts: loads .env from the parent notion-build/ folder."""
import os
import sys

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
NOTION_BUILD_DIR = os.path.dirname(AUTOMATION_DIR)
sys.path.insert(0, NOTION_BUILD_DIR)

from notion_api import load_env, notion_request, query_database, get_prop, set_env_value  # noqa: E402

ENV_PATH = os.path.join(NOTION_BUILD_DIR, ".env")


def get_env():
    env = load_env(ENV_PATH)
    if not env.get("NOTION_TOKEN"):
        print("ERROR: NOTION_TOKEN missing in .env")
        sys.exit(1)
    return env
