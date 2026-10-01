#!/usr/bin/env python3
"""Generate AI-friendly static files from changelog.json and index.html data."""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from html import escape

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CHANGELOG_FILE = os.path.join(REPO_ROOT, "changelog.json")
CHANGELOG_HTML_FILE = os.path.join(REPO_ROOT, "changelog.html")
CHANGELOG_MD_FILE = os.path.join(REPO_ROOT, "changelog.md")
LLMS_FULL_FILE = os.path.join(REPO_ROOT, "llms-full.txt")
INDEX_FILE = os.path.join(REPO_ROOT, "index.html")
EXTRACT_DATA_JS = os.path.join(REPO_ROOT, ".github", "scripts", "extract-data.js")

SITE_URL = "https://hustlecoding.github.io/pstack-explained"
SOURCE_URL = "https://github.com/cursor/plugins/tree/main/pstack"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Generated {path}")


def extract_index_data():
    try:
        result = subprocess.run(
            ["node", EXTRACT_DATA_JS, INDEX_FILE],
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)
    except FileNotFoundError:
        print("Node.js is required to extract index.html data. Install Node or run in an environment that has it.", file=sys.stderr)
        raise
    except subprocess.CalledProcessError as e:
        print(f"extract-data.js failed: {e.stderr}", file=sys.stderr)
        raise


def format_date(iso_date):
    try:
        return datetime.fromisoformat(iso_date.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except Exception:
        return iso_date


def generate_changelog_md(changelog):
    lines = [
        "# pstack upstream changelog",
        "",
        f"Source: {changelog.get('sourceUrl', SOURCE_URL)}",
        f"Last synced: {changelog.get('lastUpdatedAt', 'unknown')}",
        f"Last commit: {changelog.get('lastCommitSha', '')}",
        "",
        "## Recent changes",
        "",
    ]
    for entry in changelog.get("entries", []):
        date = format_date(entry.get("date", ""))
        title = entry.get("title", "")
        sha = entry.get("sha", "")[:7]
        author = entry.get("author", "")
        url = entry.get("url", "")
        lines.append(f"- [{date}] [{title}]({url}) ({sha}) by {author}")
    if not changelog.get("entries"):
        lines.append("No changelog entries yet.")
    lines.append("")
    return "\n".join(lines)


def generate_changelog_html(changelog):
    entries = changelog.get("entries", [])
    source_url = changelog.get("sourceUrl", SOURCE_URL)
    last_updated = changelog.get("lastUpdatedAt", "")
    last_sha = changelog.get("lastCommitSha", "")

    meta_parts = []
    if source_url:
        meta_parts.append(f'Tracking <a href="{escape(source_url)}" target="_blank" rel="noopener">cursor/plugins/pstack</a>')
    if last_updated:
        try:
            pretty = datetime.fromisoformat(last_updated.replace("Z", "+00:00")).strftime("%B %d, %Y")
        except Exception:
            pretty = last_updated
        meta_parts.append(f'synced <span class="ch-time">{escape(pretty)}</span>')
    meta_html = " · ".join(meta_parts) if meta_parts else ""

    if not entries:
        list_html = '<p class="changelog-empty">No changelog entries yet.</p>'
    else:
        list_html = '<div class="changelog-list">\n'
        for i, e in enumerate(entries):
            date_str = format_date(e.get("date", ""))
            title = escape(e.get("title", ""))
            sha = escape((e.get("sha") or "")[:7])
            author = escape(e.get("author", ""))
            author_url = e.get("authorUrl", "")
            url = e.get("url", "")
            author_link = f'<a href="{escape(author_url)}" target="_blank" rel="noopener">{author}</a>' if author_url and author else author
            url_attr = f' href="{escape(url)}" target="_blank" rel="noopener"' if url else ""
            list_html += f'''      <div class="changelog-entry" style="animation-delay:{i*30}ms">
        <div class="changelog-date">{escape(date_str)}</div>
        <div class="changelog-body">
          <div class="changelog-title"><a{url_attr}>{title}</a></div>
          <div class="changelog-meta"><span class="ch-sha">{sha}</span> · {author_link}</div>
        </div>
      </div>\n'''
        list_html += "    </div>"

    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>pstack · upstream changelog</title>
<meta name="description" content="Weekly upstream changelog for the pstack plugin in cursor/plugins.">
<meta property="og:title" content="pstack · upstream changelog">
<meta property="og:description" content="Weekly upstream changelog for the pstack plugin in cursor/plugins.">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE_URL}/changelog.html">
<meta property="og:image" content="{SITE_URL}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="640">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SITE_URL}/og.png">
<link rel="canonical" href="{SITE_URL}/changelog.html">
<link rel="alternate" type="text/markdown" href="changelog.md" title="Markdown changelog">
<link rel="alternate" type="application/json" href="changelog.json" title="JSON changelog">
<link rel="alternate" type="text/plain" href="llms.txt" title="LLM context for this site">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="favicon-32x32.png">
<link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon.png">
<link rel="shortcut icon" href="favicon.ico">
<meta name="theme-color" content="#f7f4ee">
<style>
@font-face{{
  font-family:"IBM VGA";
  src:url("fonts/WebPlus_IBM_VGA_8x16.woff") format("woff");
  font-weight:400; font-style:normal; font-display:swap;
}}
:root{{
  --bg:#e6e1d6; --paper:#f7f4ee; --ink:#1c1915; --soft:#3d3832; --dim:#6a635a; --faint:#8d867c;
  --line:#e0d9cc; --mark:#7f2d22;
  --t-setup:#7f2d22; --t-sdlc:#3d3832; --t-orch:#7f2d22; --t-special:#3d3832;
  --maxw:760px; --navh:0px;
  --ff:"IBM VGA", ui-monospace, monospace;
  --ff-mono:"IBM VGA", ui-monospace, monospace;
}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth; -webkit-text-size-adjust:100%}}
body{{
  margin:0; background:var(--paper); color:var(--ink); font-family:var(--ff);
  font-size:16px; line-height:24px; font-weight:400; letter-spacing:0; font-synthesis:none;
  -webkit-font-smoothing:none; font-smooth:never;
}}
button,input,textarea,select{{font-family:inherit; font-weight:400; letter-spacing:0; font-synthesis:none; appearance:none; -webkit-appearance:none}}
button:focus,button:focus-visible{{outline:none}}
h1,h2,h3{{font-family:var(--ff); font-weight:400; letter-spacing:0; line-height:40px}}
code{{font-family:var(--ff-mono); font-size:16px}}
.wrap{{max-width:var(--maxw); margin:0 auto; padding:0 24px}}
.sheet{{max-width:860px; margin:28px auto; background:var(--paper); border:1px solid #d4ccbe; min-height:calc(100vh - 56px); padding-bottom:28px}}
.unofficial{{padding:18px 0 0; color:var(--dim); font-size:16px}}
.unofficial .wrap{{display:flex; gap:10px; flex-wrap:wrap; align-items:baseline}}
.unofficial strong{{font-weight:400; color:var(--ink); font-size:16px}}
.unofficial span{{color:var(--dim)}}
.unofficial a{{color:var(--mark); font-size:16px}}
header.mast{{padding:28px 0 8px}}
h1.wordmark{{font-size:32px; margin:0 0 12px; line-height:40px}}
h1.wordmark span{{color:var(--ink)}}
.count{{font-family:var(--ff-mono); font-size:16px; color:var(--faint); margin:0 0 12px}}
.tagline{{font-size:16px; color:var(--soft); margin:0 0 10px; max-width:62ch; line-height:24px}}
.intro-lead{{color:var(--dim); font-size:16px; margin:0}}
nav.bar{{position:sticky; top:0; background:var(--paper); border-bottom:1px solid var(--line); z-index:2}}
nav.bar .wrap{{display:flex; gap:14px; flex-wrap:wrap; padding-top:10px; padding-bottom:10px}}
nav.bar a{{color:var(--dim); text-decoration:none; font-size:16px}}
nav.bar a:hover,nav.bar a[aria-current="page"]{{color:var(--mark)}}
section{{padding:28px 0; border-bottom:1px solid var(--line)}}
.sh h2{{font-size:32px; margin:0 0 8px; line-height:40px}}
.sh .num{{display:none}}
.sh .lead{{color:var(--dim); margin:0; font-size:16px; line-height:24px}}
.flow{{color:var(--dim); font-size:16px}}
.flow .cmd-tok{{font-family:var(--ff-mono); color:var(--mark); font-size:16px}}
.band{{margin:22px 0}}
.band-head{{display:flex; gap:10px; align-items:baseline}}
.band-head h3{{font-family:var(--ff); font-size:16px; font-weight:400; letter-spacing:0; line-height:24px; text-transform:uppercase; color:var(--dim); margin:0}}
.band-head .ct{{color:var(--faint); font-size:16px}}
.band-head .ln,.band-head .tick{{display:none}}
.band-desc{{color:var(--dim); font-size:16px; margin:4px 0 0}}
.bricks{{display:block}}
.brick{{
  display:block; width:100%; text-align:left; background:transparent; color:var(--ink);
  border:0; border-top:1px solid var(--line); border-left:0; border-radius:0; padding:12px 0; cursor:pointer; font-family:var(--ff);
}}
.brick:hover{{background:transparent}}
.brick .pn{{font-family:var(--ff); font-size:16px; font-weight:400; line-height:24px}}
.brick .pa{{color:var(--dim); font-size:16px; margin-top:3px}}
.tmpl-note{{color:var(--dim); font-size:16px}}
.tmpl-note a{{color:var(--mark)}}
.changelog-meta{{color:var(--dim); font-size:16px}}
.changelog-meta a{{color:var(--mark)}}
.changelog-entry{{display:flex; gap:16px; padding:12px 0; border-bottom:1px solid var(--line)}}
.changelog-entry:last-child{{border-bottom:0}}
.changelog-date{{width:160px; flex:none; font-family:var(--ff-mono); font-size:16px; color:var(--faint); text-align:right}}
.changelog-title{{font-size:16px; line-height:24px}}
.changelog-title a{{color:var(--ink); text-decoration:none}}
.changelog-title a:hover{{color:var(--mark)}}
.changelog-meta .ch-sha,.changelog-meta .ch-time{{font-family:var(--ff-mono); font-size:16px; color:var(--faint)}}
footer{{padding:20px 0 8px; color:var(--dim); font-size:16px; line-height:24px}}
footer a{{color:var(--mark)}}
.overlay{{position:fixed; inset:0; background:rgba(28,25,21,.28); display:none; align-items:center; justify-content:center; z-index:60; padding:24px}}
.overlay.open{{display:flex}}
.dialog{{background:var(--paper); border:1px solid #d4ccbe; border-radius:0; max-width:560px; width:100%; padding:28px; position:relative; max-height:86vh; overflow:auto}}
.dialog .cat{{font-family:var(--ff-mono); font-size:16px; letter-spacing:0; text-transform:uppercase; color:var(--faint)}}
.dialog h3{{font-size:32px; line-height:40px; margin:8px 0 12px}}
.dialog .field .k{{font-family:var(--ff-mono); font-size:16px; letter-spacing:0; text-transform:uppercase; color:var(--faint)}}
.dialog .close{{position:absolute; top:16px; right:16px; background:none; border:0; color:var(--dim); cursor:pointer; font-family:var(--ff); font-size:16px; text-decoration:underline; text-underline-offset:3px}}
@media (max-width:640px){{
  .sheet{{margin:0; border:0}}
  h1.wordmark{{font-size:32px}}
  .changelog-entry{{flex-direction:column; gap:4px}}
  .changelog-date{{text-align:left; width:auto}}
}}
</style>
</head>
<body>

<div class="unofficial">
  <div class="wrap">
    <strong>Unofficial reading aid.</strong>
    <span>Not affiliated with poteto, pstack, or Cursor.</span>
    <a href="https://github.com/cursor/plugins/tree/main/pstack" target="_blank" rel="noopener">Upstream source</a>
  </div>
</div>

<header class="mast">
  <div class="wrap">
    <div class="mark">
      <h1 class="wordmark">Changelog</h1>
    </div>
    <p class="tagline">Upstream changelog for the <code>pstack</code> plugin in <code>cursor/plugins</code>.</p>
    <p class="intro-lead">This page is updated automatically every Monday by a GitHub Actions workflow that polls the pstack directory and appends any new commits.</p>
  </div>
</header>

<nav class="bar">
  <div class="wrap">
    <a href="index.html">Home</a>
    <a href="index.html#now">Now</a>
    <a href="index.html#start">Start</a>
    <a href="index.html#playbooks">Playbooks</a>
    <a href="index.html#skills">Skills</a>
    <a href="agent-templates.html">Templates</a>
    <a href="changelog.html" aria-current="page">Changelog</a>
  </div>
</nav>

<section id="changelog">
  <div class="wrap">
    <div class="sh">
      <span class="num">01</span>
      <h2>Upstream changelog</h2>
      <p class="lead">Weekly changes to the <code>pstack</code> plugin in <code>cursor/plugins</code>. We poll the repo and surface any commits that touch the pstack directory.</p>
    </div>
    <div class="changelog-meta" id="changelog-meta">{meta_html}</div>
    {list_html}
  </div>
</section>

<footer>
  <div class="wrap">
    <p>pstack is <a href="https://x.com/poteto" target="_blank" rel="noopener">poteto's</a> set of engineering skills for coding agents, installed with <code>/add-plugin pstack</code>. This page is an unofficial reading aid and is not affiliated with poteto, pstack, or Cursor.</p>
    <p>Source and deploy: <a href="https://github.com/HustleCoding/pstack-explained" target="_blank" rel="noopener">HustleCoding/pstack-explained</a>. Agent-readable context: <a href="llms.txt">llms.txt</a> and <a href="changelog.md">changelog.md</a>.</p>
    <p>Type: <a href="https://int10h.org/oldschool-pc-fonts/" target="_blank" rel="noopener">PxPlus IBM VGA 8x16</a> by VileR, <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noopener">CC BY-SA 4.0</a>.</p>
  </div>
</footer>

</body>
</html>
'''


def generate_llms_full(data, changelog):
    lines = [
        "# pstack explained",
        "",
        "pstack is poteto's set of engineering skills for coding agents, installed with `/add-plugin pstack`.",
        "This site is an unofficial reading aid at https://hustlecoding.github.io/pstack-explained/.",
        "",
        "## Overview",
        "",
        "Start in a Cursor chat with `/add-plugin pstack`, then `/setup-pstack`, then one real task via `/poteto-mode`.",
        "Type `/poteto-mode` and describe a task. pstack matches the task to a playbook, then runs the appropriate skills as the steps fire.",
        "Twenty-three principles apply across every playbook, biasing the work toward small diffs and real verification. The [official guide](https://github.com/cursor/plugins/blob/main/pstack/docs/guide/README.md) covers setup, routing, design, building, verification, overnight work, principles, customization, and recipes.",
        "This site is unofficial and is not affiliated with poteto, pstack, or Cursor.",
        "",
        "## What to type",
        "",
        "Pick the situation and copy the prompt. Swap in your own paths and finish condition.",
        "",
    ]
    for item in data.get("NOW", []):
        lines.append(f"### {item.get('title', '')} ({item.get('g', '')})")
        if item.get("blurb"):
            lines.append(item.get("blurb"))
        if item.get("prompt"):
            lines.append(f"Prompt: {item.get('prompt')}")
        lines.append("")

    if data.get("CHOICES"):
        lines.extend([
            "## Which one",
            "",
            "Pairs that are easy to mix up. Use the side that matches the job.",
            "",
        ])
        for pair in data.get("CHOICES", []):
            lines.append(f"### {pair.get('q', '')}")
            for key in ("a", "b"):
                side = pair.get(key) or {}
                lines.append(f"- {side.get('label', '')}: {side.get('when', '')}")
            lines.append("")

    if data.get("DRIFT"):
        lines.extend([
            "## If it drifts, say this",
            "",
        ])
        for row in data.get("DRIFT", []):
            lines.append(f"- When: {row.get('see', '')}")
            lines.append(f"  Say: {row.get('say', '')}")
        lines.append("")

    lines.extend([
        "## Playbooks",
        "",
        "A playbook is a step-by-step recipe for one kind of task. `/poteto-mode` copies the matched one in full before any work starts.",
        "",
    ])
    for pb in data.get("PLAYBOOKS", []):
        meta = "(meta playbook)" if pb.get("meta") else ""
        lines.append(f"### {pb.get('n', '')} {meta}".strip())
        if pb.get("g"):
            lines.append(f"Group: {pb.get('g')}")
        lines.append(f"Trigger: {pb.get('t', '')}")
        if pb.get("detail"):
            lines.append(f"Detail: {pb.get('detail')}")
        if pb.get("example"):
            lines.append(f"Try: {pb.get('example')}")
        if pb.get("skills"):
            lines.append("Skills often nearby: " + ", ".join(pb.get("skills") or []))
        lines.append("")

    lines.extend([
        "## Skills",
        "",
        "Skills are the individual moves. Reach for one directly when you want a specific result instead of the full route.",
        "",
    ])
    for sk in data.get("SKILLS", []):
        lines.append(f"### {sk.get('cmd', '')}")
        if sk.get("g"):
            lines.append(f"Group: {sk.get('g')}")
        lines.append(f"When to use: {sk.get('when', '')}")
        if sk.get("example"):
            lines.append(f"Try: {sk.get('example')}")
        if sk.get("playbooks"):
            lines.append("Related playbooks: " + ", ".join(sk.get("playbooks") or []))
        lines.append("")

    lines.extend([
        "## Principles",
        "",
        "Twenty-three rules in five families. Each principle has a name, when it applies, the rule to follow, and a phrase you can say to steer.",
        "",
    ])
    groups = {g["key"]: g for g in data.get("GROUPS", [])}
    for g in data.get("GROUPS", []):
        lines.append(f"### {g.get('label', '')}")
        if g.get("desc"):
            lines.append(g.get("desc"))
        lines.append("")
        for p in data.get("PRINCIPLES", []):
            if p.get("g") == g.get("key"):
                lines.append(f"- **{p.get('n', '')}**")
                lines.append(f"  - Applies when: {p.get('applies', '')}")
                lines.append(f"  - Rule: {p.get('rule', '')}")
                if p.get("steer"):
                    lines.append(f"  - Say this to steer: {p.get('steer')}")
                lines.append("")

    lines.extend([
        "## Models per role",
        "",
        "pstack can use a different model for each role. Some roles run several models in parallel so the reviews come from different angles.",
        "Run `/setup-pstack` to detect your models and write the rule. Skills read it and fall back to their own defaults when a line is missing, so you override only what you want.",
        "",
    ])
    for m in data.get("MODELS", []):
        lines.append(f"- **{m.get('r', '')}** ({m.get('k', '')}) — {m.get('o', '')}")
    lines.append("")

    entries = changelog.get("entries", [])
    if entries:
        lines.extend([
            "## Recent upstream changelog",
            "",
            f"Source: {changelog.get('sourceUrl', SOURCE_URL)}",
            f"Last synced: {changelog.get('lastUpdatedAt', 'unknown')}",
            "",
        ])
        for e in entries[:20]:
            date = format_date(e.get("date", ""))
            lines.append(f"- [{date}] {e.get('title', '')} ({e.get('sha', '')[:7]}) by {e.get('author', '')}")
        lines.append("")

    return "\n".join(lines)


def main():
    changelog = load_json(CHANGELOG_FILE)
    save_file(CHANGELOG_MD_FILE, generate_changelog_md(changelog))
    save_file(CHANGELOG_HTML_FILE, generate_changelog_html(changelog))

    data = extract_index_data()
    save_file(LLMS_FULL_FILE, generate_llms_full(data, changelog))
    print("Done.")


if __name__ == "__main__":
    main()
