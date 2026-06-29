from __future__ import annotations

import re
from typing import Any

from repo_wiki.domain.models import SourceFile
from repo_wiki.extract.lines import line_for_offset, line_offsets


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
FENCE_RE = re.compile(r"^```\s*([A-Za-z0-9_+-]*)\s*$", re.MULTILINE)
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def extract_markdown_document(file: SourceFile) -> dict[str, Any] | None:
    if file.language != "Markdown" or not file.content:
        return None
    line_starts = line_offsets(file.content)
    headings = [
        {
            "level": len(match.group(1)),
            "title": match.group(2).strip(),
            "line": line_for_offset(line_starts, match.start()),
        }
        for match in HEADING_RE.finditer(file.content)
    ]
    code_fences = [
        {
            "language": match.group(1).strip() or None,
            "line": line_for_offset(line_starts, match.start()),
        }
        for match in FENCE_RE.finditer(file.content)
    ]
    links = [
        {"text": match.group(1).strip(), "target": match.group(2).strip()}
        for match in LINK_RE.finditer(file.content)
    ]
    return {
        "path": file.path,
        "headings": headings,
        "code_fences": code_fences,
        "links": links,
        "top_heading": headings[0]["title"] if headings else None,
    }
