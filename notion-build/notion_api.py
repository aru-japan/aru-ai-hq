"""Minimal Notion API client using only the Python standard library (no pip install needed)."""
import json
import os
import urllib.request
import urllib.error

NOTION_VERSION = "2022-06-28"
BASE_URL = "https://api.notion.com/v1"


def load_env(env_path):
    values = {}
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            values[key.strip()] = val.strip()
    return values


def set_env_value(env_path, key, value):
    """Update or append a single KEY=VALUE line in the .env file, preserving everything else."""
    lines = []
    found = False
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith(f"{key}="):
                lines.append(f"{key}={value}\n")
                found = True
            else:
                lines.append(line if line.endswith("\n") else line + "\n")
    if not found:
        lines.append(f"{key}={value}\n")
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def notion_request(token, method, path, body=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Notion-Version", NOTION_VERSION)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        raise RuntimeError(f"Notion API error {e.code}: {err_body}") from None


def query_database(token, database_id, filter_obj=None, sorts=None):
    """Query a database, following pagination, and return the full list of page results."""
    body = {}
    if filter_obj is not None:
        body["filter"] = filter_obj
    if sorts is not None:
        body["sorts"] = sorts

    results = []
    cursor = None
    while True:
        req_body = dict(body)
        if cursor:
            req_body["start_cursor"] = cursor
        resp = notion_request(token, "POST", f"/databases/{database_id}/query", req_body)
        results.extend(resp.get("results", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return results


def get_prop(page, name, kind):
    """Read a property value off a page result in a convenient plain-Python form.

    kind: 'select' | 'multi_select' | 'checkbox' | 'number' | 'date' | 'rich_text' | 'title' | 'relation'
    """
    prop = page.get("properties", {}).get(name)
    if prop is None:
        return None
    if kind == "select":
        sel = prop.get("select")
        return sel.get("name") if sel else None
    if kind == "multi_select":
        return [o["name"] for o in prop.get("multi_select", [])]
    if kind == "checkbox":
        return prop.get("checkbox", False)
    if kind == "number":
        return prop.get("number")
    if kind == "date":
        d = prop.get("date")
        return d.get("start") if d else None
    if kind == "rich_text":
        parts = prop.get("rich_text", [])
        return "".join(p.get("plain_text", "") for p in parts)
    if kind == "title":
        parts = prop.get("title", [])
        return "".join(p.get("plain_text", "") for p in parts)
    if kind == "relation":
        return [r["id"] for r in prop.get("relation", [])]
    if kind == "url":
        return prop.get("url")
    if kind == "rollup":
        rollup = prop.get("rollup", {})
        rtype = rollup.get("type")
        if rtype == "date":
            d = rollup.get("date")
            return d.get("start") if d else None
        if rtype == "number":
            return rollup.get("number")
        if rtype == "array":
            items = rollup.get("array", [])
            out = []
            for item in items:
                itype = item.get("type")
                if itype == "date" and item.get("date"):
                    out.append(item["date"].get("start"))
                elif itype == "number":
                    out.append(item.get("number"))
                elif itype == "select" and item.get("select"):
                    out.append(item["select"].get("name"))
            return out
        return None
    raise ValueError(f"unknown kind: {kind}")
