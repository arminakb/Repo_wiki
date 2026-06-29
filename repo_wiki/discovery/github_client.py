from __future__ import annotations

import json
import os
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from repo_wiki.discovery.topic_expander import expand_topic

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
PERMISSIVE_LICENSES = {
    "apache-2.0",
    "bsd-2-clause",
    "bsd-3-clause",
    "isc",
    "mit",
    "mpl-2.0",
}


@dataclass(frozen=True)
class RepoCandidate:
    full_name: str
    url: str
    stars: int = 0
    license: str | None = None
    language: str | None = None
    description: str | None = None


def discover_repositories(
    topic: str,
    *,
    language: str | None = None,
    min_stars: int = 200,
    license_policy: str = "permissive",
    limit: int = 10,
) -> list[RepoCandidate]:
    candidates: dict[str, RepoCandidate] = {}
    per_query = max(limit, 10)
    for query in expand_topic(topic):
        for candidate in search_repositories(
            query,
            language=language,
            min_stars=min_stars,
            limit=per_query,
        ):
            if license_policy == "permissive" and candidate.license not in PERMISSIVE_LICENSES:
                continue
            candidates.setdefault(candidate.url, candidate)
            if len(candidates) >= limit:
                break
        if len(candidates) >= limit:
            break
    return sorted(candidates.values(), key=lambda repo: repo.stars, reverse=True)[:limit]


def search_repositories(
    query: str,
    *,
    language: str | None = None,
    min_stars: int = 200,
    limit: int = 10,
) -> list[RepoCandidate]:
    terms = [query, f"stars:>={min_stars}"]
    if language:
        terms.append(f"language:{language}")
    params = urlencode(
        {
            "q": " ".join(terms),
            "sort": "stars",
            "order": "desc",
            "per_page": max(1, min(limit, 100)),
        }
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "repo-wiki",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(f"{GITHUB_SEARCH_URL}?{params}", headers=headers)
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub search failed ({exc.code}): {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Could not reach GitHub API: {exc.reason}") from exc

    return [parse_candidate(item) for item in payload.get("items", [])]


def parse_candidate(item: dict) -> RepoCandidate:
    license_info = item.get("license") or {}
    return RepoCandidate(
        full_name=str(item.get("full_name") or ""),
        url=str(item.get("html_url") or ""),
        stars=int(item.get("stargazers_count") or 0),
        license=license_info.get("spdx_id", "").lower() or None,
        language=item.get("language"),
        description=item.get("description"),
    )
