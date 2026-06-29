from __future__ import annotations

from repo_wiki.domain.models import KnowledgeObject


def rerank(
    candidates: list[tuple[KnowledgeObject, float] | tuple[KnowledgeObject, float, dict]],
    *,
    language: str | None,
    framework: str | None,
    project_type: str | None,
    domain: str | None,
) -> list[tuple[KnowledgeObject, float, dict]]:
    ranked: list[tuple[KnowledgeObject, float, dict]] = []
    for candidate in candidates:
        obj = candidate[0]
        retrieval_detail = candidate[2] if len(candidate) > 2 else {}
        lexical_score = float(retrieval_detail.get("lexical_score", candidate[1]))
        vector_score = float(retrieval_detail.get("vector_score", 0.0))
        graph_score = float(retrieval_detail.get("graph_score", 0.0))
        query_overlap = float(retrieval_detail.get("query_overlap", 0.0))
        path_match_score = float(retrieval_detail.get("path_match_score", 0.0))
        symbol_match_score = float(retrieval_detail.get("symbol_match_score", 0.0))
        edit_target_score = float(retrieval_detail.get("edit_target_score", 0.0))
        behavior_boundary_score = float(retrieval_detail.get("behavior_boundary_score", 0.0))
        runtime_signal_score = float(retrieval_detail.get("runtime_signal_score", 0.0))
        related_test_score = float(retrieval_detail.get("related_test_score", 0.0))
        convention_score = float(retrieval_detail.get("convention_score", 0.0))
        source_file_bonus = 0.18 if retrieval_detail.get("source_file") else 0.0
        noise_penalty = unrelated_noise_penalty(
            obj,
            query_overlap=query_overlap,
            path_match_score=path_match_score,
            symbol_match_score=symbol_match_score,
        )
        metadata_match = 0.0
        reasons: list[str] = []
        if language and obj.language == language:
            metadata_match += 0.25
            reasons.append(f"language matches: {language}")
        if framework and framework in obj.frameworks:
            metadata_match += 0.25
            reasons.append(f"framework matches: {framework}")
        if project_type and obj.project_type == project_type:
            metadata_match += 0.15
            reasons.append(f"project type matches: {project_type}")
        if domain and obj.domain == domain:
            metadata_match += 0.20
            reasons.append(f"domain matches: {domain}")
        quality_score = obj.quality_score
        citation_score = min(len(obj.source_refs) / 3, 1.0)
        final_score = (
            0.20 * lexical_score
            + 0.14 * vector_score
            + 0.08 * graph_score
            + 0.12 * query_overlap
            + 0.14 * quality_score
            + 0.08 * metadata_match
            + 0.04 * citation_score
            + 0.25 * path_match_score
            + 0.18 * symbol_match_score
            + 0.22 * edit_target_score
            + 0.16 * behavior_boundary_score
            + 0.16 * runtime_signal_score
            + 0.20 * related_test_score
            + 0.08 * convention_score
            + source_file_bonus
            - noise_penalty
        )
        if lexical_score:
            reasons.append(f"lexical score: {lexical_score:.2f}")
        if vector_score:
            reasons.append(f"vector score: {vector_score:.2f}")
        if graph_score:
            edge_type = retrieval_detail.get("edge_type", "graph edge")
            reasons.append(f"graph expansion via {edge_type}")
        if query_overlap:
            reasons.append(f"query overlap: {query_overlap:.2f}")
        if path_match_score:
            reasons.append(f"path match: {path_match_score:.2f}")
        if symbol_match_score:
            reasons.append(f"symbol match: {symbol_match_score:.2f}")
        if source_file_bonus:
            reasons.append("direct source file match")
        if edit_target_score:
            reasons.append(f"likely edit target: {edit_target_score:.2f}")
        if behavior_boundary_score:
            reasons.append(f"persistence/runtime boundary: {behavior_boundary_score:.2f}")
        if runtime_signal_score:
            reasons.append(f"related runtime source: {runtime_signal_score:.2f}")
        if related_test_score:
            reasons.append(f"related local test: {related_test_score:.2f}")
        if convention_score:
            reasons.append(f"validation convention: {convention_score:.2f}")
        if noise_penalty:
            reasons.append(f"unrelated noise penalty: {noise_penalty:.2f}")
        if obj.source_refs:
            reasons.append("has source references")
        if obj.quality_score >= 0.7:
            reasons.append(f"quality score: {obj.quality_score:.2f}")
        ranked.append(
            (
                obj,
                round(final_score, 4),
                {
                    "lexical_score": lexical_score,
                    "vector_score": vector_score,
                    "graph_score": graph_score,
                    "metadata_match": round(metadata_match, 4),
                    "query_overlap": round(query_overlap, 4),
                    "path_match_score": round(path_match_score, 4),
                    "symbol_match_score": round(symbol_match_score, 4),
                    "edit_target_score": round(edit_target_score, 4),
                    "behavior_boundary_score": round(behavior_boundary_score, 4),
                    "runtime_signal_score": round(runtime_signal_score, 4),
                    "related_test_score": round(related_test_score, 4),
                    "convention_score": round(convention_score, 4),
                    "quality_score": quality_score,
                    "confidence": obj.confidence,
                    "citation_score": round(citation_score, 4),
                    "noise_penalty": round(noise_penalty, 4),
                    "retrieval": retrieval_detail,
                    "reasons": reasons,
                },
            )
        )
    return sorted(ranked, key=lambda item: item[1], reverse=True)


def unrelated_noise_penalty(
    obj: KnowledgeObject,
    *,
    query_overlap: float,
    path_match_score: float,
    symbol_match_score: float,
) -> float:
    if path_match_score or symbol_match_score or query_overlap >= 0.12:
        return 0.0
    paths = [str(obj.payload.get("path", "")), *[str(path) for path in obj.payload.get("examples", [])]]
    haystack = " ".join([obj.title, obj.summary, " ".join(obj.tags), *paths]).lower()
    if any(marker in haystack for marker in (".github/", "workflow", "issue_template", "dependabot")):
        return 0.18
    if obj.type in {"ProjectProfile", "ArchitecturePattern"}:
        return 0.08
    return 0.0
