#!/usr/bin/env python3
"""Categorize apps from apps.json into Theo's four tiers and write apps.md."""

import json
import os
import re
import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
APPS_JSON = REPO_ROOT / "apps.json"
APPS_MD = REPO_ROOT / "apps.md"

CATEGORIES = ["side-project", "startup", "too-big", "markdown-tier"]
CATEGORY_LABELS = {
    "side-project": "Side project",
    "startup": "Startup",
    "too-big": "Too big",
    "markdown-tier": "Markdown tier",
}

CATEGORY_ORDER = ["markdown-tier", "startup", "side-project", "too-big"]

PROMPT = """You are categorizing Product Hunt launches using Theo Browne's framework from his AI Engineer World’s Fair 2026 keynote "What do we build now?".

The four tiers are:
- side-project: a small, personal, or indie project. Usually one or two people, narrow scope, often built for fun or a single problem.
- startup: a product with a market, a team, and a business model. It aims to grow, has users, and could raise funding or revenue.
- too-big: a massive platform or infrastructure product. Think AWS, Salesforce, Gmail, Slack, an operating system, or a foundation model. Not a small team product.
- markdown-tier: something that can be reduced to a markdown file executed by an LLM on a cron job. The "product" is mostly a prompt, workflow, or agent that runs automatically. For example, triaging GitHub PRs, generating daily reports, or monitoring Reddit comments.

Given each app name and tagline, return a JSON array. Each object must have exactly these keys: name, category (one of "side-project", "startup", "too-big", "markdown-tier"), reason (one sentence).

Apps to categorize:
"""


def load_apps():
    with open(APPS_JSON, "r", encoding="utf-8") as f:
        apps = json.load(f)
    for app in apps:
        app["name"] = app["name"].strip()
        app["tagline"] = app["tagline"].strip()
    return apps


def get_api_key():
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    return key


def categorize_batch(batch, api_key):
    apps_text = json.dumps(batch, indent=2)
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "openai/gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a helpful classifier. Always respond with a JSON array and no additional prose."},
                {"role": "user", "content": PROMPT + apps_text},
            ],
            "temperature": 0.2,
            "max_tokens": 2000,
        },
        timeout=120,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return parse_json_response(content)


def parse_json_response(content):
    """Extract and parse JSON from the model response."""
    # Try to strip markdown code fences
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    # Fallback: find first [ and last ]
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("[")
        end = content.rfind("]")
        if start != -1 and end != -1 and end > start:
            return json.loads(content[start : end + 1])
        raise


def categorize_apps(apps, api_key):
    results = []
    batch_size = 10
    for i in range(0, len(apps), batch_size):
        batch = apps[i : i + batch_size]
        print(f"Categorizing batch {i // batch_size + 1}/{(len(apps) - 1) // batch_size + 1}...")
        categorized = categorize_batch(batch, api_key)
        for item in categorized:
            if item["category"] not in CATEGORIES:
                raise ValueError(f"Unexpected category '{item['category']}' for {item['name']}")
        results.extend(categorized)
    return results


def build_markdown(apps, categorized):
    by_category = {cat: [] for cat in CATEGORY_ORDER}
    for app, cat in zip(apps, categorized):
        by_category[cat["category"]].append((app, cat))

    lines = [
        "# App Catalog — Theo’s 2026 Tiers",
        "",
        "A running list of apps categorized using [Theo Browne’s](https://x.com/t3dotgg) framework from the AI Engineer World’s Fair 2026 keynote [“What do we build now?”](https://www.youtube.com/watch?v=xUnRQ9vLXxo).",
        "",
        "Theo argues that AI agents collapse the old project-scope buckets. The tiers are:",
        "",
        "- **Markdown tier** — A workflow that can be reduced to a markdown file run by an LLM on a cron job (e.g., triage PRs, curate comments, generate daily plans).",
        "- **Startup** — A product with a market, a team, and a business model; it aims to grow and generate revenue.",
        "- **Side project** — A small, personal, or indie project. Narrow scope, often built for fun or a single problem.",
        "- **Too big** — A massive platform or infrastructure product (e.g., AWS, Gmail, a foundation model). Not a small-team product.",
        "",
        "---",
        "",
    ]

    for cat in CATEGORY_ORDER:
        label = CATEGORY_LABELS[cat]
        entries = by_category[cat]
        lines.append(f"## {label}")
        lines.append("")
        if not entries:
            lines.append("*No apps in this tier yet.*")
            lines.append("")
            continue
        for app, cat in entries:
            name = app["name"]
            url = app["hunted_url"]
            tagline = app["tagline"]
            reason = cat["reason"]
            lines.append(f"- **[{name}]({url})** — {tagline}")
            lines.append(f"  - *{reason}*")
        lines.append("")

    lines.extend([
        "---",
        "",
        "*Source: [Hunted.space Product Hunt Yearly Ranking 2026](https://hunted.space/top-products/yearly/2026). Categorization is generated by `.github/scripts/categorize_apps.py` using the OpenRouter API.*",
        "",
    ])

    return "\n".join(lines)


def main():
    if not APPS_JSON.exists():
        print(f"Missing {APPS_JSON}", file=sys.stderr)
        sys.exit(1)

    apps = load_apps()
    api_key = get_api_key()
    categorized = categorize_apps(apps, api_key)

    if len(categorized) != len(apps):
        print(f"Warning: expected {len(apps)} categorizations, got {len(categorized)}", file=sys.stderr)

    md = build_markdown(apps, categorized)
    APPS_MD.write_text(md, encoding="utf-8")
    print(f"Wrote {APPS_MD}")


if __name__ == "__main__":
    main()
