#!/usr/bin/env python3
"""Build the benchmark dataset under dataset/benchmark-repos/.

Idempotency: existing repo directories are skipped by default when their metadata is already
present in dataset/benchmark-repos/manifest.json. Stripped repos without manifest metadata fail
loudly because their commit SHA cannot be recovered after .git is removed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset" / "benchmark-repos"
MANIFEST_DIR = DATASET / ".manifest"
MANIFEST = DATASET / "manifest.json"
LANGUAGES = ("python", "typescript")
STAR_THRESHOLD = 200
SMALL_MAX_KB = 2_000
MEDIUM_MAX_KB = 60_000
SMALL_PER_LANGUAGE = 2
MEDIUM_PER_LANGUAGE = 3
MAX_TOTAL_MB = 500
BLOAT_DIRS = {".git", "node_modules", ".venv", "__pycache__", "dist", "build", ".next", "vendor"}


def log(message: str) -> None:
    print(message, flush=True)


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def today() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def fetch_github_json(url: str, token: str | None) -> tuple[dict, dict]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "repo-knowledge-compiler-benchmark",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            headers_out = dict(response.headers)
            remaining = headers_out.get("X-RateLimit-Remaining")
            if remaining == "0":
                reset = headers_out.get("X-RateLimit-Reset", "unknown")
                fail(f"GitHub API rate limit exhausted; reset={reset}")
            return json.loads(response.read().decode("utf-8")), headers_out
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        remaining = exc.headers.get("X-RateLimit-Remaining")
        if exc.code in {403, 429} or remaining == "0":
            fail(f"GitHub API rate limit or abuse limit hit: HTTP {exc.code}: {body[:300]}")
        fail(f"GitHub API request failed: HTTP {exc.code}: {body[:300]}")
    except urllib.error.URLError as exc:
        fail(f"GitHub API request failed: {exc}")


def search_language(language: str, token: str | None) -> list[dict]:
    tier_queries = {
        "small": f"language:{language} stars:>{STAR_THRESHOLD} size:1..{SMALL_MAX_KB} "
        "archived:false fork:false pushed:>2023-01-01",
        "medium": f"language:{language} stars:>{STAR_THRESHOLD} "
        f"size:{SMALL_MAX_KB + 1}..{MEDIUM_MAX_KB} "
        "archived:false fork:false pushed:>2023-01-01",
    }
    responses = []
    candidates: dict[str, dict] = {}
    for tier, query in tier_queries.items():
        params = urllib.parse.urlencode(
            {"q": query, "sort": "stars", "order": "desc", "per_page": 30, "page": 1}
        )
        url = f"https://api.github.com/search/repositories?{params}"
        payload, headers = fetch_github_json(url, token)
        responses.append({"tier": tier, "query": query, "headers": headers, "payload": payload})
        for item in payload.get("items", []):
            item["benchmark_size_tier"] = tier
            candidates[item["full_name"]] = item
        time.sleep(1.1)  # GitHub Search API is separately rate-limited.

    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    (MANIFEST_DIR / f"search-results-{language}.json").write_text(
        json.dumps(
            {
                "language": language,
                "star_threshold": STAR_THRESHOLD,
                "fetch_mode": "authenticated" if token else "unauthenticated",
                "generated_at": today(),
                "responses": responses,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return sorted(candidates.values(), key=lambda repo: (-repo["stargazers_count"], repo["full_name"]))


def select_repositories(language: str, candidates: list[dict]) -> list[dict]:
    small = [repo for repo in candidates if repo["size"] <= SMALL_MAX_KB]
    medium = [repo for repo in candidates if SMALL_MAX_KB < repo["size"] <= MEDIUM_MAX_KB]
    if len(small) < SMALL_PER_LANGUAGE:
        fail(f"not enough small {language} repos from GitHub search: {len(small)}")
    if len(medium) < MEDIUM_PER_LANGUAGE:
        fail(f"not enough medium {language} repos from GitHub search: {len(medium)}")
    selected = small[:SMALL_PER_LANGUAGE] + medium[:MEDIUM_PER_LANGUAGE]
    return sorted(selected, key=lambda repo: (-repo["stargazers_count"], repo["full_name"]))


def enforce_projected_budget(repos: list[dict]) -> tuple[list[dict], list[dict]]:
    kept = list(repos)
    dropped = []
    while sum(repo["size"] for repo in kept) / 1024 > MAX_TOTAL_MB:
        largest = max(kept, key=lambda repo: (repo["size"], -repo["stargazers_count"]))
        largest["drop_reason"] = "projected API size exceeds 500MB budget"
        dropped.append(largest)
        kept.remove(largest)
    if not any(repo["size"] > SMALL_MAX_KB for repo in kept):
        fail("disk budget cannot be met even after dropping all medium-tier repos")
    return kept, dropped


def run(cmd: list[str], cwd: Path | None = None) -> str:
    try:
        proc = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=True)
        return proc.stdout.strip()
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout).strip()
        fail(f"command failed: {' '.join(cmd)}\n{detail}")


def remove_bloat(repo_dir: Path) -> None:
    for name in BLOAT_DIRS:
        target = repo_dir / name
        if target.exists():
            shutil.rmtree(target)
    for pycache in repo_dir.rglob("__pycache__"):
        if pycache.is_dir():
            shutil.rmtree(pycache)


def size_mb(path: Path) -> float:
    total = 0
    for item in path.rglob("*"):
        if item.is_file() and not item.is_symlink():
            total += item.stat().st_size
    return round(total / 1024 / 1024, 1)


def load_existing_manifest() -> dict[str, dict]:
    if not MANIFEST.exists():
        return {}
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {repo["full_name"]: repo for repo in data.get("repos", [])}


def clone_or_reuse(repo: dict, existing: dict[str, dict]) -> dict:
    language = repo["benchmark_language"]
    repo_dir = DATASET / language / repo["name"]
    prior = existing.get(repo["full_name"])
    if repo_dir.exists():
        if not prior:
            fail(f"{repo_dir} exists but has no manifest entry with commit_sha")
        log(f"skip existing {repo['full_name']}")
        prior["size_on_disk_mb"] = size_mb(repo_dir)
        return prior

    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    log(f"clone {repo['full_name']}")
    run(["git", "clone", "--depth", "1", repo["clone_url"], str(repo_dir)])
    commit_sha = run(["git", "-C", str(repo_dir), "rev-parse", "HEAD"])
    remove_bloat(repo_dir)
    return {
        "name": repo["name"],
        "full_name": repo["full_name"],
        "github_url": repo["html_url"],
        "language": language,
        "stars": repo["stargazers_count"],
        "commit_sha": commit_sha,
        "size_on_disk_mb": size_mb(repo_dir),
        "date_fetched": today(),
        "size_tier": "small" if repo["size"] <= SMALL_MAX_KB else "medium",
    }


def enforce_actual_budget(repos: list[dict]) -> tuple[list[dict], list[dict]]:
    kept = list(repos)
    removed = []
    while sum(repo["size_on_disk_mb"] for repo in kept) > MAX_TOTAL_MB:
        largest = max(kept, key=lambda repo: (repo["size_on_disk_mb"], -repo["stars"]))
        repo_dir = DATASET / largest["language"] / largest["name"]
        shutil.rmtree(repo_dir)
        largest["drop_reason"] = "actual disk size exceeds 500MB budget"
        removed.append(largest)
        kept.remove(largest)
    if not any(repo["size_tier"] == "medium" for repo in kept):
        fail("disk budget cannot be met even after dropping all medium-tier repos")
    return kept, removed


def write_manifest(
    repos: list[dict],
    fetch_mode: str,
    projected_drops: list[dict],
    actual_drops: list[dict],
) -> None:
    total = round(sum(repo["size_on_disk_mb"] for repo in repos), 1)
    payload = {
        "repos": sorted(repos, key=lambda repo: (repo["language"], repo["size_tier"], -repo["stars"])),
        "total_size_mb": total,
        "fetch_mode": fetch_mode,
        "generated_at": today(),
        "star_threshold": STAR_THRESHOLD,
        "dropped_repos": [
            {
                "full_name": repo["full_name"],
                "language": repo.get("benchmark_language", repo.get("language")),
                "stars": repo.get("stargazers_count", repo.get("stars")),
                "api_size_mb": round(repo.get("size", 0) / 1024, 1),
                "reason": repo["drop_reason"],
            }
            for repo in projected_drops + actual_drops
        ],
    }
    MANIFEST.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def print_summary(repos: list[dict]) -> None:
    by_language = {}
    for repo in repos:
        by_language.setdefault(repo["language"], []).append(repo)
    print("\nLanguage    | Repos | Total Size")
    print("------------|-------|----------")
    for language in sorted(by_language):
        total = sum(repo["size_on_disk_mb"] for repo in by_language[language])
        print(f"{language.title():<11} | {len(by_language[language]):>5} | {total:>8.1f} MB")
    print("------------|-------|----------")
    total = sum(repo["size_on_disk_mb"] for repo in repos)
    mark = "✓" if total <= MAX_TOTAL_MB else "✗"
    print(f"{'TOTAL':<11} | {len(repos):>5} | {total:>8.1f} MB  {mark} within 500MB budget")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the benchmark repo dataset.")
    parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    fetch_mode = "authenticated" if token else "unauthenticated"
    limit = "5000/hr authenticated" if token else "60/hr unauthenticated"
    log(f"GitHub API mode: {fetch_mode} ({limit})")

    selected = []
    for language in LANGUAGES:
        candidates = search_language(language, token)
        language_selected = select_repositories(language, candidates)
        for repo in language_selected:
            repo["benchmark_language"] = language
        selected.extend(language_selected)

    selected, projected_drops = enforce_projected_budget(selected)
    existing = load_existing_manifest()
    manifest_repos = [clone_or_reuse(repo, existing) for repo in selected]
    manifest_repos, actual_drops = enforce_actual_budget(manifest_repos)
    write_manifest(manifest_repos, fetch_mode, projected_drops, actual_drops)
    print_summary(manifest_repos)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
