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
<meta name="theme-color" content="#ffffff">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root{{
    --bg:#ffffff; --ink:#1a1a1a; --soft:#3d3d3d; --dim:#6b6b6b; --faint:#9b9b9b;
    --rule:#ededed; --rule2:#e0e0e0;
    --accent:#b45309; --accent-soft:#fdf4ea; --accent-line:#e8c39a;
    --maxw:880px; --navh:54px;
    --ff:"Hanken Grotesk",system-ui,-apple-system,sans-serif;
    --ff-mono:"IBM Plex Mono",ui-monospace,monospace;
  }}
  *{{box-sizing:border-box}}
  html{{scroll-behavior:smooth; -webkit-text-size-adjust:100%}}
  body{{
    margin:0; background:var(--bg); color:var(--ink);
    font-family:var(--ff); font-size:17px; line-height:1.65;
    -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility;
  }}
  .wrap{{max-width:var(--maxw); margin:0 auto; padding:0 clamp(20px,5vw,40px); position:relative}}
  code{{font-family:var(--ff-mono); font-size:.92em; color:var(--accent)}}

  header.mast{{padding:clamp(56px,9vw,96px) 0 clamp(36px,5vw,52px)}}
  .mark{{display:flex; align-items:center; gap:13px; margin-bottom:22px}}
  .glyph{{width:26px; height:26px; position:relative; flex:none}}
  .glyph i{{position:absolute; left:0; height:20%; background:var(--accent); border-radius:1px}}
  .glyph i:nth-child(1){{bottom:0; width:100%; opacity:.4}}
  .glyph i:nth-child(2){{bottom:40%; width:68%; opacity:.65}}
  .glyph i:nth-child(3){{bottom:80%; width:40%}}
  h1.wordmark{{font-family:var(--ff); font-weight:700; font-size:clamp(36px,6vw,50px); letter-spacing:-.025em; margin:0; line-height:1}}
  h1.wordmark span{{color:var(--accent)}}
  .tagline{{font-size:clamp(19px,2.6vw,23px); line-height:1.45; color:var(--soft); max-width:52ch; margin:0 0 18px; font-weight:500; letter-spacing:-.005em}}
  .tagline em{{font-style:normal; color:var(--ink); border-bottom:2px solid var(--accent-line)}}
  .intro-lead{{color:var(--dim); font-size:16px; line-height:1.6; max-width:62ch; margin:0}}

  nav.bar{{position:sticky; top:0; z-index:20; background:rgba(255,255,255,.9); backdrop-filter:blur(8px); border-bottom:1px solid var(--rule)}}
  nav.bar .wrap{{display:flex; gap:2px; padding-top:7px; padding-bottom:7px; overflow-x:auto; scrollbar-width:none}}
  nav.bar .wrap::-webkit-scrollbar{{display:none}}
  nav.bar a{{color:var(--dim); text-decoration:none; font-size:14px; font-weight:500; white-space:nowrap; padding:8px 13px; border-radius:8px; transition:background .15s,color .15s}}
  nav.bar a:hover,nav.bar a:focus-visible{{background:var(--accent-soft); color:var(--accent); outline:none}}
  nav.bar a[aria-current="page"]{{background:var(--accent-soft); color:var(--accent)}}

  section{{padding:clamp(52px,8vw,84px) 0; border-bottom:1px solid var(--rule); scroll-margin-top:var(--navh)}}
  .sh{{margin-bottom:clamp(26px,4vw,38px); max-width:64ch}}
  .sh .num{{color:var(--accent); font-family:var(--ff-mono); font-size:12px; letter-spacing:.04em}}
  .sh h2{{font-weight:600; font-size:clamp(24px,3.6vw,31px); margin:7px 0 12px; letter-spacing:-.018em; line-height:1.15}}
  .sh .lead{{color:var(--dim); font-size:16px; line-height:1.6; margin:0; max-width:60ch}}

  .changelog-meta{{margin:0 0 18px; font-size:14px; color:var(--dim)}}
  .changelog-meta a{{color:var(--accent); text-decoration:none; border-bottom:1px solid var(--accent-line)}}
  .changelog-meta a:hover{{border-bottom-color:var(--accent)}}
  .changelog-meta .ch-time{{font-family:var(--ff-mono); color:var(--faint)}}
  .changelog-list{{animation:rise .5s both}}
  .changelog-entry{{display:flex; gap:18px; align-items:flex-start; padding:15px 0; border-bottom:1px solid var(--rule); animation:rise .5s both}}
  .changelog-entry:last-child{{border-bottom:none}}
  .changelog-date{{flex:none; width:84px; font-family:var(--ff-mono); font-size:12.5px; color:var(--faint); text-align:right; padding-top:3px}}
  .changelog-body{{flex:1}}
  .changelog-title{{font-weight:600; font-size:16px; line-height:1.35; color:var(--ink); margin-bottom:5px}}
  .changelog-title a{{color:inherit; text-decoration:none; border-bottom:1px solid var(--rule)}}
  .changelog-title a:hover{{color:var(--accent); border-bottom-color:var(--accent)}}
  .changelog-meta .ch-sha{{font-family:var(--ff-mono); font-size:12px; color:var(--faint)}}
  .changelog-empty{{color:var(--faint); font-size:15px; margin:12px 0 0}}

  footer{{padding:clamp(40px,6vw,60px) 0 calc(40px + env(safe-area-inset-bottom)); color:var(--faint); font-size:14px; line-height:1.7}}
  footer p{{margin:0 0 8px; max-width:62ch}}
  footer a{{color:var(--accent); text-decoration:none; border-bottom:1px solid var(--accent-line)}}
  footer a:hover{{border-bottom-color:var(--accent)}}

  @keyframes rise{{from{{opacity:0; transform:translateY(10px)}} to{{opacity:1; transform:none}}}}
  @keyframes fade{{from{{opacity:0}} to{{opacity:1}}}}
  @media (prefers-reduced-motion:reduce){{
    *{{animation:none !important; transition:none !important}}
    html{{scroll-behavior:auto}}
  }}
  @media (max-width:640px){{
    .changelog-entry{{flex-direction:column; gap:6px}}
    .changelog-date{{text-align:left}}
  }}
</style>
</head>
<body>

<header class="mast">
  <div class="wrap">
    <div class="mark">
      <div class="glyph" aria-hidden="true"><i></i><i></i><i></i></div>
      <h1 class="wordmark">p<span>stack</span></h1>
    </div>
    <p class="tagline">Upstream changelog for the <code>pstack</code> plugin in <code>cursor/plugins</code>.</p>
    <p class="intro-lead">This page is updated automatically every Monday by a GitHub Actions workflow that polls the pstack directory and appends any new commits.</p>
  </div>
</header>

<nav class="bar">
  <div class="wrap">
    <a href="index.html">Home</a>
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
    <p>pstack is <a href="https://x.com/poteto" target="_blank" rel="noopener">poteto's</a> set of engineering skills for coding agents, installed with <code>/add-plugin pstack</code>. This page is an unofficial reading aid.</p>
    <p>Source and deploy: <a href="https://github.com/HustleCoding/pstack-explained" target="_blank" rel="noopener">HustleCoding/pstack-explained</a>, live at this URL via GitHub Actions.</p>
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
        "Type `/poteto-mode` and describe a task. pstack matches the task to a playbook, then runs the appropriate skills as the steps fire.",
        "Twenty principles apply across every playbook, biasing the work toward small diffs and real verification.",
        "",
        "## Playbooks",
        "",
        "A playbook is a step-by-step recipe for one kind of task. `/poteto-mode` copies the matched one in full before any work starts.",
        "",
    ]
    for pb in data.get("PLAYBOOKS", []):
        meta = "(meta playbook)" if pb.get("meta") else ""
        lines.append(f"### {pb.get('n', '')} {meta}".strip())
        lines.append(f"Trigger: {pb.get('t', '')}")
        if pb.get("detail"):
            lines.append(f"Detail: {pb.get('detail')}")
        lines.append("")

    lines.extend([
        "## Skills",
        "",
        "Skills are the individual moves. Reach for one directly when you want a specific result instead of the full route.",
        "",
    ])
    for sk in data.get("SKILLS", []):
        lines.append(f"### {sk.get('cmd', '')}")
        lines.append(f"When to use: {sk.get('when', '')}")
        lines.append("")

    lines.extend([
        "## Principles",
        "",
        "Twenty rules in five families. Each principle has a name, when it applies, and the rule to follow.",
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
