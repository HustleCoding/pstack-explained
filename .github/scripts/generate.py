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
<meta name="theme-color" content="#20242e">
<style>
@font-face{{
  font-family:"IBM VGA";
  src:url("fonts/WebPlus_IBM_VGA_8x16.woff") format("woff");
  font-weight:400; font-style:normal; font-display:swap;
}}
:root{{
  --bg:#20242e; --ink:#e7eef2; --soft:#c5d0d8; --dim:#9aabba; --faint:#7d8b99;
  --rule:#313846; --rule2:#3e4858; --panel:#262b36;
  --sel:#243e4c; --accent:#9fd4e0; --accent-soft:#243e4c; --accent-line:#3d6474;
  --t-setup:#c678dd; --t-sdlc:#e6c07b; --t-orch:#e06c75; --t-special:#7ec8d4;
  --maxw:920px; --navh:52px;
  --ff:"IBM VGA", ui-monospace, monospace;
  --ff-mono:var(--ff);
}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth; -webkit-text-size-adjust:100%; scroll-padding-top:var(--navh); color-scheme:dark}}
body{{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:var(--ff); font-size:16px; line-height:1.5; font-weight:400;
  font-synthesis:none; -webkit-font-smoothing:none; -moz-osx-font-smoothing:auto;
  text-rendering:optimizeSpeed;
}}
h1,h2,h3,strong,b,button{{font-weight:400}}
::selection{{background:var(--sel); color:var(--ink)}}
.wrap{{max-width:var(--maxw); margin:0 auto; padding:0 clamp(16px,4vw,32px); position:relative}}
code{{font-family:var(--ff-mono); font-size:1em; color:var(--accent)}}
.unofficial{{
  background:#181b24; color:var(--dim); font-size:16px; line-height:1.5;
  padding:8px 0; border-bottom:1px solid var(--rule); border-top:2px solid #3d7d96;
}}
.unofficial .wrap{{display:flex; gap:10px; align-items:baseline; flex-wrap:wrap}}
.unofficial strong{{color:var(--ink)}}
.unofficial span{{color:var(--dim)}}
.unofficial a{{color:var(--accent); text-decoration:none; border-bottom:1px solid var(--accent-line)}}
.unofficial a:hover{{border-bottom-color:var(--accent)}}

header.mast{{padding:clamp(28px,5vw,48px) 0 clamp(20px,3vw,28px)}}
.mark{{display:flex; align-items:center; gap:12px; margin-bottom:16px}}
h1.wordmark{{font-family:var(--ff); font-weight:400; font-size:32px; letter-spacing:0; margin:0; line-height:1}}
h1.wordmark span{{color:var(--accent)}}
.count{{font-family:var(--ff-mono); font-size:16px; color:var(--faint); margin:8px 0 16px; letter-spacing:0}}
.tagline{{font-size:16px; line-height:1.5; color:var(--ink); max-width:68ch; margin:0 0 12px; font-weight:400; letter-spacing:0}}
.tagline em{{font-style:normal; color:var(--ink)}}
.intro-lead{{color:var(--dim); font-size:16px; line-height:1.5; max-width:68ch; margin:0}}

nav.bar{{position:sticky; top:0; z-index:20; background:rgba(32,36,46,.94); backdrop-filter:blur(8px); border-bottom:1px solid var(--rule)}}
nav.bar .wrap{{display:flex; gap:0; padding-top:4px; padding-bottom:4px; overflow-x:auto; scrollbar-width:none}}
nav.bar .wrap::-webkit-scrollbar{{display:none}}
nav.bar a{{color:var(--dim); text-decoration:none; font-size:16px; font-weight:400; white-space:nowrap; padding:8px 10px; border-radius:0}}
nav.bar a:hover,nav.bar a:focus-visible,nav.bar a.on,nav.bar a[aria-current="page"]{{background:var(--sel); color:var(--ink); outline:none}}

section{{padding:clamp(36px,6vw,56px) 0; border-bottom:1px solid var(--rule); scroll-margin-top:var(--navh)}}
.sh{{margin-bottom:clamp(18px,3vw,28px); max-width:72ch}}
.sh .num{{color:var(--accent); font-family:var(--ff-mono); font-size:16px; letter-spacing:0}}
.sh h2{{font-weight:400; font-size:32px; margin:8px 0 12px; letter-spacing:0; line-height:1}}
.sh .lead{{color:var(--dim); font-size:16px; line-height:1.5; margin:0; max-width:68ch}}
.sh .lead a{{color:var(--accent); text-decoration:none; border-bottom:1px solid var(--accent-line)}}
.sh .lead a:hover{{border-bottom-color:var(--accent)}}

.flow{{margin:0 0 22px; font-size:16px; color:var(--dim); line-height:1.8}}
.flow .cmd-tok{{font-family:var(--ff-mono); color:var(--accent); font-size:16px}}
.flow .arr{{color:var(--faint); margin:0 2px}}

.band{{margin-bottom:clamp(28px,4vw,40px); animation:rise .5s both}}
.band:last-child{{margin-bottom:0}}
.band-head{{display:flex; align-items:center; gap:10px; margin-bottom:8px}}
.band-head .tick{{width:8px; height:8px; border-radius:0; flex:none}}
.band-head h3{{font-weight:400; font-size:16px; margin:0; letter-spacing:0}}
.band-head .ct{{color:var(--faint); font-family:var(--ff-mono); font-size:16px}}
.band-head .ln{{flex:1; height:1px; background:var(--rule)}}
.band-desc{{color:var(--dim); font-size:16px; margin:0 0 12px; max-width:68ch}}
.bricks{{display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:8px}}
.brick{{
  text-align:left; background:var(--panel); border:1px solid var(--rule); border-left:3px solid var(--c);
  color:var(--ink); padding:12px 14px; border-radius:0; cursor:pointer; font-family:var(--ff);
  transition:background .18s; animation:rise .5s both;
}}
.brick:hover{{background:#2a3140}}
.brick:focus-visible{{outline:2px solid var(--accent); outline-offset:2px}}
.brick .pn{{font-weight:400; font-size:16px; line-height:1.35}}
.brick .pa{{color:var(--faint); font-size:16px; margin-top:6px; line-height:1.45}}
.tmpl-note{{color:var(--faint); font-size:16px; margin-top:16px; max-width:70ch; line-height:1.5}}
.tmpl-note a{{color:var(--accent); text-decoration:none; border-bottom:1px solid var(--accent-line)}}
.tmpl-note a:hover{{border-bottom-color:var(--accent)}}

.changelog-meta{{margin:0 0 16px; font-size:16px; color:var(--dim); line-height:1.5}}
.changelog-meta a{{color:var(--accent); text-decoration:none; border-bottom:1px solid var(--accent-line)}}
.changelog-meta a:hover{{border-bottom-color:var(--accent)}}
.changelog-meta .ch-time{{font-family:var(--ff-mono); color:var(--faint)}}
.changelog-list{{animation:rise .5s both}}
.changelog-entry{{display:flex; gap:16px; align-items:flex-start; padding:12px 0; border-bottom:1px solid var(--rule); animation:rise .5s both}}
.changelog-entry:last-child{{border-bottom:none}}
.changelog-date{{flex:none; width:112px; font-family:var(--ff-mono); font-size:16px; color:var(--faint); text-align:right; padding-top:0}}
.changelog-body{{flex:1}}
.changelog-title{{font-weight:400; font-size:16px; line-height:1.45; color:var(--ink); margin-bottom:4px}}
.changelog-title a{{color:inherit; text-decoration:none; border-bottom:1px solid var(--rule)}}
.changelog-title a:hover{{color:var(--accent); border-bottom-color:var(--accent)}}
.changelog-meta .ch-sha{{font-family:var(--ff-mono); font-size:16px; color:var(--faint)}}
.changelog-empty{{color:var(--faint); font-size:16px; margin:12px 0 0}}

footer{{padding:clamp(32px,5vw,48px) 0 calc(32px + env(safe-area-inset-bottom)); color:var(--faint); font-size:16px; line-height:1.5}}
footer p{{margin:0 0 10px; max-width:70ch}}
footer a{{color:var(--accent); text-decoration:none; border-bottom:1px solid var(--accent-line)}}
footer a:hover{{border-bottom-color:var(--accent)}}

.overlay{{position:fixed; inset:0; background:rgba(8,10,14,.82); display:none; align-items:center; justify-content:center; z-index:60; padding:clamp(16px,4vw,24px)}}
.overlay.open{{display:flex; animation:fade .2s}}
.dialog{{background:#2c3342; border:1px solid var(--accent-line); border-radius:0; max-width:640px; width:100%; padding:clamp(20px,4vw,28px); position:relative; animation:rise .26s both; max-height:86vh; overflow:auto}}
.dialog .cat{{font-family:var(--ff-mono); font-size:16px; letter-spacing:0; text-transform:uppercase; color:var(--accent)}}
.dialog h3{{font-weight:400; font-size:32px; margin:8px 0 16px; line-height:1; letter-spacing:0}}
.dialog .field{{margin:14px 0}}
.dialog .field .k{{color:var(--faint); font-size:16px; letter-spacing:0; text-transform:uppercase; margin-bottom:4px; font-family:var(--ff-mono)}}
.dialog .field .v{{color:var(--ink); font-size:16px; line-height:1.5}}
.dialog .close{{position:absolute; top:12px; right:12px; background:transparent; border:1px solid var(--rule2); color:var(--dim); width:36px; height:36px; border-radius:0; cursor:pointer; font-family:var(--ff); font-size:18px; line-height:1; display:flex; align-items:center; justify-content:center}}
.dialog .close:hover{{color:var(--ink); border-color:var(--accent); background:var(--sel)}}

@keyframes rise{{from{{opacity:0; transform:translateY(8px)}} to{{opacity:1; transform:none}}}}
@keyframes fade{{from{{opacity:0}} to{{opacity:1}}}}
@media (prefers-reduced-motion:reduce){{
  *{{animation:none !important; transition:none !important}}
  html{{scroll-behavior:auto}}
}}
@media (max-width:640px){{
  .bricks{{grid-template-columns:1fr}}
  .flow{{line-height:1.8}}
  .changelog-entry{{flex-direction:column; gap:6px}}
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
      <h1 class="wordmark"><span>&gt;</span> pstack</h1>
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
    <p>Terminal face: <a href="https://int10h.org/oldschool-pc-fonts/" target="_blank" rel="noopener">PxPlus IBM VGA 8x16</a> by VileR, CC BY-SA 4.0.</p>
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
