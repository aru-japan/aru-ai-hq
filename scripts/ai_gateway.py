"""AI Gateway: a single, provider-agnostic interface for calling either Claude
(Anthropic) or OpenAI, so the rest of ARu Studio's automation never needs to know
which provider is configured.

Uses only the Python standard library (urllib) - no `anthropic` / `openai` SDK
package install required.

Config: reads CLAUDE_API_KEY / OPENAI_API_KEY from notion-build/.env (the same
.env already used by the Notion automation scripts, so there is a single source
of configuration for the whole project).

Usage:
    python3 ai_gateway.py --input "要約したいテキスト"
    python3 ai_gateway.py --input "..." --provider openai
    python3 ai_gateway.py --input "..." --target-chars 150
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPTS_DIR)
ENV_PATH = os.path.join(REPO_ROOT, "notion-build", ".env")

CLAUDE_MODEL = "claude-haiku-4-5-20251001"
OPENAI_MODEL = "gpt-4o-mini"


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


def _post_json(url, headers, body, timeout=60):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    for k, v in headers.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        raise RuntimeError(f"HTTP {e.code} from {url}: {err_body}") from None


def call_claude(api_key, prompt, max_tokens=300, model=CLAUDE_MODEL):
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    resp = _post_json("https://api.anthropic.com/v1/messages", headers, body)
    parts = resp.get("content", [])
    return "".join(p.get("text", "") for p in parts if p.get("type") == "text").strip()


def call_openai(api_key, prompt, max_tokens=300, model=OPENAI_MODEL):
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    resp = _post_json("https://api.openai.com/v1/chat/completions", headers, body)
    return resp["choices"][0]["message"]["content"].strip()


def pick_provider(env, requested=None):
    """Decide which provider to use: explicit request > whichever key is present
    (Claude preferred if both are set, since ARu Studio is built primarily with Claude)."""
    claude_key = env.get("CLAUDE_API_KEY", "")
    openai_key = env.get("OPENAI_API_KEY", "")

    if requested == "claude":
        if not claude_key:
            raise RuntimeError("CLAUDE_API_KEY is not set in notion-build/.env")
        return "claude", claude_key
    if requested == "openai":
        if not openai_key:
            raise RuntimeError("OPENAI_API_KEY is not set in notion-build/.env")
        return "openai", openai_key

    if claude_key:
        return "claude", claude_key
    if openai_key:
        return "openai", openai_key
    raise RuntimeError(
        "Neither CLAUDE_API_KEY nor OPENAI_API_KEY is set in notion-build/.env. "
        "Add one of them to use the AI Gateway."
    )


def complete(prompt, provider=None, max_tokens=1500):
    """General-purpose text generation. Returns (provider_name, text)."""
    env = load_env(ENV_PATH)
    provider_name, api_key = pick_provider(env, provider)

    if provider_name == "claude":
        result = call_claude(api_key, prompt, max_tokens=max_tokens)
    else:
        result = call_openai(api_key, prompt, max_tokens=max_tokens)

    return provider_name, result


def summarize(text, provider=None, target_chars=200):
    prompt = (
        f"以下の文章を、日本語で{target_chars}文字程度に要約してください。"
        f"前置きや「要約します」等の言葉は不要で、要約の本文だけを出力してください。\n\n"
        f"---\n{text}\n---"
    )
    return complete(prompt, provider=provider, max_tokens=target_chars * 2)


def main():
    parser = argparse.ArgumentParser(description="ARu Studio AI Gateway - provider-agnostic summarizer")
    parser.add_argument("--input", required=True, help="Text to summarize")
    parser.add_argument("--provider", choices=["claude", "openai"], default=None,
                         help="Force a specific provider (default: auto-detect from configured keys)")
    parser.add_argument("--target-chars", type=int, default=200)
    args = parser.parse_args()

    try:
        provider_used, summary = summarize(args.input, provider=args.provider, target_chars=args.target_chars)
    except RuntimeError as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    print(f"[provider: {provider_used}]")
    print(summary)
    print(f"\n(文字数: {len(summary)})")


if __name__ == "__main__":
    main()
