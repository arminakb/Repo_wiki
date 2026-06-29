from __future__ import annotations

from urllib.error import URLError
from urllib.request import Request, urlopen


def fetch_llms_txt(domain: str) -> str | None:
    request = Request(f"https://{domain}/llms.txt", headers={"User-Agent": "repo-wiki"})
    try:
        with urlopen(request, timeout=5) as response:
            if response.status != 200:
                return None
            return response.read().decode("utf-8", errors="replace")
    except URLError:
        return None
