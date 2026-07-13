#!/usr/bin/env python3
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

UPSTREAM_OWNER = "cursor"
UPSTREAM_REPO = "plugins"
UPSTREAM_PATH = "pstack"
UPSTREAM_BRANCH = "main"
CHANGELOG_FILE = "changelog.json"

PER_PAGE = 100
MAX_PAGES = 100
MAX_ENTRIES = 100

SOURCE_URL = f"https://github.com/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/tree/{UPSTREAM_BRANCH}/{UPSTREAM_PATH}"


def get_token():
    for key in ("GITHUB_TOKEN", "GH_TOKEN", "GITHUB_PAT"):
        token = os.environ.get(key)
        if token:
            return token
    return None


def api_request(url, token):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "pstack-explained-sync")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        print(f"HTTP error {e.code} for {url}: {body[:500]}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"Request failed for {url}: {e}", file=sys.stderr)
        raise


def fetch_commits(token, since=None, last_sha=None):
    commits = []
    truncated = False
    for page in range(1, MAX_PAGES + 1):
        params = {
            "path": UPSTREAM_PATH,
            "sha": UPSTREAM_BRANCH,
            "per_page": PER_PAGE,
            "page": page,
        }
        if since:
            params["since"] = since
        qs = urllib.parse.urlencode(params)
        url = f"https://api.github.com/repos/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/commits?{qs}"
        page_commits = api_request(url, token)
        if not page_commits:
            break
        commits.extend(page_commits)
        if last_sha and any(c.get("sha") == last_sha for c in page_commits):
            break
        if len(page_commits) < PER_PAGE:
            break
        if page == MAX_PAGES:
            truncated = True
    if truncated:
        print(f"Warning: reached max page limit ({MAX_PAGES}); fetched {len(commits)} commits. Some older commits may be missing.", file=sys.stderr)
    return commits


def parse_entry(commit_item):
    commit = commit_item.get("commit", {})
    commit_author = commit.get("author", {})
    raw_message = commit.get("message", "")
    title = raw_message.split("\n")[0].strip()

    gh_author = commit_item.get("author")
    if gh_author and gh_author.get("login"):
        author = gh_author["login"]
        author_url = gh_author.get("html_url") or f"https://github.com/{author}"
    else:
        author = commit_author.get("name", "unknown")
        email = commit_author.get("email", "")
        author_url = f"mailto:{email}" if email and "@" in email else ""

    sha = commit_item.get("sha", "")
    return {
        "sha": sha,
        "date": commit_author.get("date", ""),
        "title": title,
        "author": author,
        "authorUrl": author_url,
        "url": commit_item.get("html_url") or f"https://github.com/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/commit/{sha}",
    }


def load_changelog():
    if not os.path.exists(CHANGELOG_FILE):
        return {
            "source": SOURCE_URL,
            "sourceUrl": SOURCE_URL,
            "lastUpdatedAt": "",
            "lastCommitSha": "",
            "entries": [],
        }
    with open(CHANGELOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_changelog(data):
    with open(CHANGELOG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    token = get_token()
    if not token:
        print("No GITHUB_TOKEN found; using unauthenticated requests (low rate limit).", file=sys.stderr)

    old = load_changelog()
    entries = old.get("entries", [])
    last_sha = old.get("lastCommitSha", "")
    since = entries[0].get("date") if entries else None

    try:
        commits = fetch_commits(token, since=since, last_sha=last_sha)
    except Exception as e:
        print(f"Failed to fetch upstream commits: {e}", file=sys.stderr)
        sys.exit(1)

    if not commits:
        print("No commits returned from upstream.")
        sys.exit(0)

    if last_sha:
        try:
            idx = next(i for i, c in enumerate(commits) if c.get("sha") == last_sha)
            new_commits = commits[:idx]
            print(f"Found last known commit {last_sha[:8]} at index {idx}.")
        except StopIteration:
            new_commits = commits
            print(f"Warning: last known commit {last_sha[:8]} not in fetched history; using {len(commits)} commits since {since}.", file=sys.stderr)
    else:
        new_commits = commits

    if not new_commits:
        print("No new pstack commits since last sync.")
        sys.exit(0)

    new_entries = [parse_entry(c) for c in new_commits]
    existing_map = {e["sha"]: e for e in old.get("entries", [])}
    new_count = sum(1 for e in new_entries if e["sha"] not in existing_map)
    for entry in new_entries:
        existing_map[entry["sha"]] = entry

    combined = sorted(existing_map.values(), key=lambda x: x["date"], reverse=True)
    combined = combined[:MAX_ENTRIES]
    latest = combined[0]

    data = {
        "source": old.get("source", SOURCE_URL),
        "sourceUrl": old.get("sourceUrl", SOURCE_URL),
        "lastUpdatedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "lastCommitSha": latest["sha"],
        "entries": combined,
    }
    save_changelog(data)
    print(f"Updated {CHANGELOG_FILE}: +{new_count} new entries, {len(combined)} total, last={latest['sha'][:8]}.")


if __name__ == "__main__":
    main()
