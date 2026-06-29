from __future__ import annotations

from repo_wiki.domain.models import Repository, SourceFile, Symbol


def repository_quality(repo: Repository, files: list[SourceFile], symbols: list[Symbol]) -> float:
    score = 0.35
    if repo.license in {"MIT", "Apache-2.0", "BSD", "ISC"}:
        score += 0.15
    if repo.detected_frameworks:
        score += 0.15
    if any(file.is_test for file in files):
        score += 0.15
    if any(file.language == "Markdown" for file in files):
        score += 0.10
    if symbols:
        score += 0.10
    return min(score, 1.0)


def knowledge_quality(
    *,
    repo_quality_score: float,
    citation_quality: float,
    test_evidence: float,
    docs_evidence: float,
    pattern_reusability: float,
    extraction_confidence: float,
) -> float:
    return round(
        0.20 * repo_quality_score
        + 0.20 * citation_quality
        + 0.20 * test_evidence
        + 0.15 * docs_evidence
        + 0.15 * pattern_reusability
        + 0.10 * extraction_confidence,
        4,
    )
