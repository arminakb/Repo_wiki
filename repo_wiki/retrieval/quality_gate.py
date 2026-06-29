from __future__ import annotations

from typing import Any


def evaluate_context_pack(pack: dict[str, Any]) -> dict[str, Any]:
    sections = (
        pack.get("recommended_patterns", []),
        pack.get("relevant_examples", []),
        pack.get("architecture_rules", []),
    )
    items = [item for section in sections for item in section]
    confidence = max((float(item.get("score") or 0.0) for item in items), default=0.0)
    citations = pack.get("source_citations", [])
    checks = {
        "citation_count": len(citations) >= 3,
        "confidence": confidence >= 0.6,
        "has_test_example": bool(pack.get("relevant_examples"))
        or any("test" in str(citation.get("path", "")).lower() for citation in citations),
        "has_risk_note": bool(pack.get("risks")),
        "has_result": bool(items),
    }
    score = sum(checks.values()) / len(checks)
    return {
        "passed": score >= 0.6,
        "score": round(score, 2),
        "confidence": round(confidence, 3),
        "checks": checks,
        "recommendation": "use_local" if score >= 0.6 else "use_live_fallback",
    }
