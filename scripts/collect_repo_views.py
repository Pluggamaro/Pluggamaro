#!/usr/bin/env python3
"""Accumulate GitHub repository traffic views beyond the API's 14-day window.

Reads daily view counts for every public, non-fork repo you own, merges them
into data/repo-views.json (keyed repo -> date -> views) and writes a
shields.io endpoint file with the cumulative total.
Requires env TRAFFIC_TOKEN (needs push/admin read access to the repos).
"""
import json, os, sys, urllib.request, urllib.error
from pathlib import Path

TOKEN = os.environ.get("TRAFFIC_TOKEN")
OWNER = os.environ.get("GITHUB_OWNER", "Pluggamaro")
API = "https://api.github.com"
DATA = Path("data/repo-views.json")
BADGE = Path("data/repo-views-badge.json")

if not TOKEN:
    sys.exit("TRAFFIC_TOKEN is not set")


def get(url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def list_repos():
    repos, page = [], 1
    while True:
        batch = get(f"{API}/user/repos?affiliation=owner&visibility=public&per_page=100&page={page}")
        if not batch:
            return repos
        repos += [r["name"] for r in batch if not r["fork"] and r["owner"]["login"].lower() == OWNER.lower()]
        page += 1


store = json.loads(DATA.read_text()) if DATA.exists() else {}
failed = []
for name in list_repos():
    try:
        views = get(f"{API}/repos/{OWNER}/{name}/traffic/views?per=day")["views"]
    except urllib.error.HTTPError as e:
        failed.append(f"{name} ({e.code})")
        continue
    days = store.setdefault(name, {})
    for v in views:
        day = v["timestamp"][:10]
        days[day] = max(days.get(day, 0), v["count"])  # today's count only grows

total = sum(sum(d.values()) for d in store.values())
DATA.parent.mkdir(exist_ok=True)
DATA.write_text(json.dumps(store, indent=1, sort_keys=True) + "\n")
BADGE.write_text(json.dumps({
    "schemaVersion": 1, "label": "REPO VIEWS",
    "message": f"{total:,}", "color": "FF6B35",
}) + "\n")
print(f"total views tracked: {total}")
if failed:
    print("skipped:", ", ".join(failed))
