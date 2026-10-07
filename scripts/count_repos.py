#!/usr/bin/env python3
"""Count every repo you own (public + private) and write a shields.io endpoint file.
Only the total number is published; no repo names are written anywhere."""
import json, os, sys, urllib.request
from pathlib import Path

TOKEN = os.environ.get("REPO_COUNT_TOKEN")
if not TOKEN:
    sys.exit("REPO_COUNT_TOKEN is not set")


def get(url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


total, page = 0, 1
while True:
    batch = get(f"https://api.github.com/user/repos?affiliation=owner&per_page=100&page={page}")
    if not batch:
        break
    total += len(batch)
    page += 1

out = Path("data/repo-count-badge.json")
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps({
    "schemaVersion": 1, "label": "REPOS", "message": str(total), "color": "FF6B35",
}) + "\n")
print("repos:", total)
