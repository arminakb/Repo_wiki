from __future__ import annotations

import re
import time
from typing import Any

from repo_wiki.domain.ids import new_id
from repo_wiki.domain.ids import stable_id
from repo_wiki.domain.models import KnowledgeObject
from repo_wiki.domain.models import RetrievalTrace
from repo_wiki.domain.models import SourceFile
from repo_wiki.domain.models import SourceRef
from repo_wiki.domain.models import now_utc
from repo_wiki.retrieval.classifier import (
    classify_task,
    infer_domain,
    infer_framework,
    infer_language,
)
from repo_wiki.retrieval.context import build_context_pack
from repo_wiki.retrieval.rerank import rerank
from repo_wiki.logging import log_event
from repo_wiki.storage.vector import tokenize
from repo_wiki.storage.sqlite import SQLiteStore


class RetrievalService:
    def __init__(self, store: SQLiteStore):
        self.store = store

    def retrieve(
        self,
        task: str,
        *,
        language: str | None = None,
        framework: str | None = None,
        project_type: str | None = None,
        domain: str | None = None,
        repo: str | None = None,
        max_tokens: int = 4000,
        limit: int = 8,
        license_policy: str | None = None,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        limit = max(1, min(limit, 50))
        max_tokens = max(1, max_tokens)
        inferred_language = language or infer_language(task)
        inferred_framework = framework or infer_framework(task)
        inferred_domain = domain or infer_domain(task)
        task_type = classify_task(task)
        query_terms = set(normalized_terms(task))
        query_paths = path_terms(task)
        query_symbols = symbol_terms(task)
        source_candidates = self.store.search_source_files(
            task,
            language=inferred_language,
            repo_id=repo,
            limit=max(limit * 6, 30),
        )
        exact_source_query = " ".join([*query_paths, *sorted(query_symbols)])
        if exact_source_query and (query_terms & (modification_terms() | {"test", "tests", "spec"})):
            source_candidates = merge_source_search_candidates(
                source_candidates,
                self.store.search_source_files(
                    exact_source_query,
                    language=inferred_language,
                    repo_id=repo,
                    limit=max(limit * 3, 15),
                ),
            )
        if task_type == "test_generation":
            source_candidates = merge_source_search_candidates(
                source_candidates,
                self.store.search_source_files(
                    f"tests test spec endpoint {task}",
                    language=inferred_language,
                    repo_id=repo,
                    limit=max(limit * 3, 15),
                ),
            )
        source_candidates = merge_source_search_candidates(
            source_candidates,
            self._search_use_site_source_files(
                source_candidates,
                language=inferred_language,
                repo=repo,
                limit=max(limit * 3, 15),
            ),
        )
        fts_candidates = self.store.search_knowledge(
            task,
            language=inferred_language,
            framework=inferred_framework,
            project_type=project_type,
            repo_id=repo,
            limit=max(limit * 4, 20),
        )
        vector_candidates = self.store.vector_search_knowledge(
            task,
            language=inferred_language,
            framework=inferred_framework,
            project_type=project_type,
            repo_id=repo,
            limit=max(limit * 4, 20),
        )
        if (
            not fts_candidates
            and not vector_candidates
            and (inferred_language or inferred_framework or project_type)
        ):
            fts_candidates = self.store.search_knowledge(task, limit=max(limit * 4, 20))
            vector_candidates = self.store.vector_search_knowledge(task, limit=max(limit * 4, 20))
        candidates = merge_initial_candidates(fts_candidates, vector_candidates)
        candidates = merge_source_candidates(
            candidates,
            source_candidates,
            task_type=task_type,
            query_terms=query_terms,
            query_paths=query_paths,
            query_symbols=query_symbols,
            domain=inferred_domain,
        )
        graph_seed_count = min(len(candidates), max(1, limit // 4))
        expanded = self.store.graph_expand_knowledge(
            [obj.id for obj, _ in candidates[:graph_seed_count]],
            max_depth=2,
            max_neighbors_per_node=12,
            min_confidence=0.5,
            repo_id=repo,
        )
        candidate_map: dict[str, tuple[Any, float, dict[str, Any]]] = {
            obj.id: (
                obj,
                max(scores["lexical_score"], scores["vector_score"]),
                {**scores, "query_overlap": query_overlap(query_terms, obj)},
            )
            for obj, scores in candidates
        }
        for obj, graph_score, detail in expanded:
            current = candidate_map.get(obj.id)
            expanded_score = max(0.05, graph_score * 0.5)
            payload = {"retriever": "graph", "graph_score": graph_score, **detail}
            payload["query_overlap"] = query_overlap(query_terms, obj)
            if current is None:
                candidate_map[obj.id] = (obj, expanded_score, payload)
            else:
                candidate_map[obj.id] = (
                    current[0],
                    max(current[1], expanded_score),
                    {
                        **current[2],
                        "graph_score": graph_score,
                        "graph": detail,
                        "query_overlap": max(
                            float(current[2].get("query_overlap", 0.0)),
                            float(payload["query_overlap"]),
                        ),
                    },
                )
        ranked = rerank(
            with_match_scores(
                list(candidate_map.values()),
                query_paths=query_paths,
                query_symbols=query_symbols,
                ref_paths=ref_paths_for_candidates(self.store, candidate_map.values()),
            ),
            language=inferred_language,
            framework=inferred_framework,
            project_type=project_type,
            domain=inferred_domain,
        )
        ranked = dedupe_ranked_by_path(ranked)
        selected_refs = []
        for obj, _, _ in ranked[:limit]:
            selected_refs.extend(obj.source_refs)
        citations = [
            ref.model_dump()
            for ref in self.store.get_source_refs(dict.fromkeys(selected_refs).keys())
            if citation_allowed(ref, license_policy)
        ]
        citation_rank = {ref_id: index for index, ref_id in enumerate(dict.fromkeys(selected_refs))}
        citations.sort(key=lambda citation: citation_rank.get(citation["id"], len(citation_rank)))
        citation_contents = self.store.get_source_ref_contents(citation["id"] for citation in citations)
        add_citation_context(citations, citation_contents, query_paths, query_symbols, query_terms)
        warnings = retrieval_warnings(
            task,
            ranked[:limit],
            citations,
            query_paths=query_paths,
            query_symbols=query_symbols,
        )
        trace = RetrievalTrace(
            id=new_id("trace"),
            task=task,
            retrievers_used=["fts", "vector", "source", "metadata", "graph"],
            candidate_count=len(candidate_map),
            reranked_count=len(ranked),
            returned_count=min(len(ranked), limit),
            latency_ms=int((time.perf_counter() - started) * 1000),
            filters={
                "language": inferred_language,
                "framework": inferred_framework,
                "project_type": project_type,
                "domain": inferred_domain,
                "repo": repo,
                "license_policy": license_policy,
                "max_tokens": max_tokens,
                "warnings": warnings,
            },
            payload={
                "candidate_counts": {
                    "fts": len(fts_candidates),
                    "vector": len(vector_candidates),
                    "source": len(source_candidates),
                    "merged": len(candidates),
                    "graph_expanded": len(expanded),
                    "total": len(candidate_map),
                },
                "warnings": warnings,
                "ranking": [
                    {"id": obj.id, "score": score}
                    for obj, score, _ in ranked[:limit]
                ],
                "ranking_details": [
                    {
                        "id": obj.id,
                        "title": obj.title,
                        "score": score,
                        "type": obj.type,
                        "path": obj.payload.get("path"),
                        "reasons": detail.get("reasons", []),
                        "lexical_score": detail.get("lexical_score", 0.0),
                        "vector_score": detail.get("vector_score", 0.0),
                        "graph_score": detail.get("graph_score", 0.0),
                        "query_overlap": detail.get("query_overlap", 0.0),
                        "path_match_score": detail.get("path_match_score", 0.0),
                        "symbol_match_score": detail.get("symbol_match_score", 0.0),
                        "edit_target_score": detail.get("edit_target_score", 0.0),
                        "behavior_boundary_score": detail.get("behavior_boundary_score", 0.0),
                        "runtime_signal_score": detail.get("runtime_signal_score", 0.0),
                        "related_test_score": detail.get("related_test_score", 0.0),
                        "convention_score": detail.get("convention_score", 0.0),
                        "noise_penalty": detail.get("noise_penalty", 0.0),
                    }
                    for obj, score, detail in ranked[:limit]
                ],
            },
        )
        self.store.save_retrieval_trace(trace)
        pack = build_context_pack(
            task=task,
            task_type=task_type,
            constraints=trace.filters,
            ranked=ranked,
            citations=citations,
            retrieval_trace_id=trace.id,
            max_items=limit,
        )
        self.store.save_context_pack(pack)
        log_event(
            "retrieval.completed",
            trace_id=trace.id,
            candidate_count=trace.candidate_count,
            returned_count=trace.returned_count,
            latency_ms=trace.latency_ms,
        )
        return {"context_pack": pack.model_dump(), "markdown": pack.markdown, "trace_id": trace.id}

    def _search_use_site_source_files(
        self,
        source_candidates: list[tuple[SourceFile, SourceRef | None, float]],
        *,
        language: str | None,
        repo: str | None,
        limit: int,
    ) -> list[tuple[SourceFile, SourceRef | None, float]]:
        symbol_query = " ".join(
            term
            for file, _, _ in source_candidates
            if not file.is_test
            for term in [*source_symbols(file), *imported_names(file.content or "")]
        )
        if not symbol_query:
            return []
        return self.store.search_source_files(
            symbol_query,
            language=language,
            repo_id=repo,
            limit=limit,
        )


def imported_names(content: str) -> list[str]:
    names: list[str] = []
    for match in re.finditer(r"^\s*from\s+[\w.]+\s+import\s+([A-Za-z0-9_,\s]+)", content, re.M):
        names.extend(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", match.group(1)))
    for match in re.finditer(r"^\s*import\s+([A-Za-z0-9_.,\s]+)", content, re.M):
        names.extend(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", match.group(1)))
    return list(dict.fromkeys(names))[:20]


def merge_initial_candidates(
    fts_candidates: list[tuple[Any, float]],
    vector_candidates: list[tuple[Any, float]],
) -> list[tuple[Any, dict[str, Any]]]:
    merged: dict[str, tuple[Any, dict[str, Any]]] = {}
    for obj, score in fts_candidates:
        merged[obj.id] = (
            obj,
            {
                "lexical_score": score,
                "vector_score": 0.0,
                "retriever": "fts",
            },
        )
    for obj, score in vector_candidates:
        current = merged.get(obj.id)
        if current is None:
            merged[obj.id] = (
                obj,
                {
                    "lexical_score": 0.0,
                    "vector_score": score,
                    "retriever": "vector",
                },
            )
            continue
        scores = current[1]
        scores["vector_score"] = max(scores["vector_score"], score)
        scores["retriever"] = "fts+vector"
    return sorted(
        merged.values(),
        key=lambda item: (
            max(item[1]["lexical_score"], item[1]["vector_score"]),
            item[0].quality_score,
        ),
        reverse=True,
    )


def dedupe_ranked_by_path(
    ranked: list[tuple[KnowledgeObject, float, dict[str, Any]]],
) -> list[tuple[KnowledgeObject, float, dict[str, Any]]]:
    seen_paths: set[str] = set()
    output: list[tuple[KnowledgeObject, float, dict[str, Any]]] = []
    for obj, score, detail in ranked:
        path = str((obj.payload or {}).get("path") or "")
        if path and path in seen_paths:
            continue
        if path:
            seen_paths.add(path)
        output.append((obj, score, detail))
    return output


def merge_source_search_candidates(
    primary: list[tuple[SourceFile, SourceRef | None, float]],
    extra: list[tuple[SourceFile, SourceRef | None, float]],
) -> list[tuple[SourceFile, SourceRef | None, float]]:
    merged = {file.id: (file, ref, score) for file, ref, score in primary}
    for file, ref, score in extra:
        current = merged.get(file.id)
        if current is None or score > current[2]:
            merged[file.id] = (file, ref, score)
    return list(merged.values())


def merge_source_candidates(
    candidates: list[tuple[Any, dict[str, Any]]],
    source_candidates: list[tuple[SourceFile, SourceRef | None, float]],
    *,
    task_type: str,
    query_terms: set[str],
    query_paths: list[str],
    query_symbols: set[str],
    domain: str | None,
) -> list[tuple[Any, dict[str, Any]]]:
    merged: dict[str, tuple[Any, dict[str, Any]]] = {
        obj.id: (obj, scores) for obj, scores in candidates
    }
    source_metrics = {
        file.id: {
            "path_score": path_match_score(query_paths, [file.path]),
            "symbol_score": source_symbol_match_score(query_symbols, file),
            "overlap": source_query_overlap(query_terms, file),
            "edit_target": edit_target_score(file, query_terms, query_symbols, task_type),
            "behavior_boundary": behavior_boundary_score(file, query_terms),
            "convention": convention_score(file, query_terms),
            "source_focus": source_focus_score(file, query_terms),
        }
        for file, _, _ in source_candidates
    }
    anchor_files = [
        file
        for file, _, _ in source_candidates
        if (
            source_metrics[file.id]["path_score"]
            or source_metrics[file.id]["symbol_score"]
            or source_metrics[file.id]["source_focus"]
        )
    ]
    related_source_files = [
        file
        for file, _, _ in source_candidates
        if not file.is_test
        and (
            file in anchor_files
            or source_metrics[file.id]["edit_target"] > 0.0
            or source_metrics[file.id]["behavior_boundary"] > 0.0
            or source_metrics[file.id]["source_focus"] > 0.0
            or related_source_score(file, anchor_files, query_terms) > 0.0
        )
    ]
    related_source_paths = {file.path for file in related_source_files}
    test_related_source_files = [
        file
        for file in related_source_files
        if (
            file in anchor_files
            or source_metrics[file.id]["edit_target"] > 0.0
            or source_metrics[file.id]["behavior_boundary"] > 0.0
            or source_metrics[file.id]["symbol_score"] > 0.0
        )
    ]
    api_area_test_sources = {file.path for file in test_related_source_files}
    modification_task = bool(query_terms & modification_terms())
    for file, ref, lexical_score in source_candidates:
        path_score = float(source_metrics[file.id]["path_score"])
        symbol_score = float(source_metrics[file.id]["symbol_score"])
        overlap = float(source_metrics[file.id]["overlap"])
        runtime_score = (
            related_source_score(file, anchor_files, query_terms)
            if modification_task
            else 0.0
        )
        runtime_score = max(runtime_score, float(source_metrics[file.id]["source_focus"]))
        related_test = related_test_score(
            file,
            related_source_files,
            query_symbols,
            query_terms,
            api_area_test_sources=api_area_test_sources,
        )
        edit_target = float(source_metrics[file.id]["edit_target"])
        behavior_boundary = float(source_metrics[file.id]["behavior_boundary"])
        convention = float(source_metrics[file.id]["convention"])
        if not should_promote_source_file(
            file,
            task_type=task_type,
            domain=domain,
            path_score=path_score,
            symbol_score=symbol_score,
            overlap=overlap,
            edit_target_score=edit_target,
            behavior_boundary_score=behavior_boundary,
            runtime_score=runtime_score,
            related_test_score=related_test,
            convention_score=convention,
        ):
            continue
        obj = source_file_knowledge_object(
            file,
            ref,
            symbol_score=symbol_score,
            edit_target_score=edit_target,
            behavior_boundary_score=behavior_boundary,
            runtime_score=runtime_score,
            related_test_score=related_test,
            convention_score=convention,
        )
        source_score = max(lexical_score, 0.15)
        if symbol_score:
            source_score = max(source_score, 0.95)
        elif path_score:
            source_score = max(source_score, 0.9)
        elif edit_target:
            source_score = max(source_score, 0.9)
        elif behavior_boundary:
            source_score = max(source_score, 0.88)
        elif runtime_score:
            source_score = max(source_score, 0.82)
        elif related_test:
            source_score = max(source_score, 0.78)
        elif convention:
            source_score = max(source_score, 0.74)
        elif file.is_test and task_type == "test_generation":
            source_score = max(source_score, 0.65)
        detail = {
            "lexical_score": source_score,
            "vector_score": 0.0,
            "retriever": "source",
            "query_overlap": overlap,
            "source_file": True,
            "edit_target_score": edit_target,
            "behavior_boundary_score": behavior_boundary,
            "runtime_signal_score": runtime_score,
            "related_test_score": related_test,
            "convention_score": convention,
        }
        current = merged.get(obj.id)
        if current is None:
            merged[obj.id] = (obj, detail)
            continue
        current_detail = current[1]
        merged[obj.id] = (
            current[0],
            {
                **current_detail,
                "lexical_score": max(
                    float(current_detail.get("lexical_score", 0.0)),
                    source_score,
                ),
                "query_overlap": max(
                    float(current_detail.get("query_overlap", 0.0)),
                    overlap,
                ),
                "runtime_signal_score": max(
                    float(current_detail.get("runtime_signal_score", 0.0)),
                    runtime_score,
                ),
                "related_test_score": max(
                    float(current_detail.get("related_test_score", 0.0)),
                    related_test,
                ),
                "edit_target_score": max(
                    float(current_detail.get("edit_target_score", 0.0)),
                    edit_target,
                ),
                "behavior_boundary_score": max(
                    float(current_detail.get("behavior_boundary_score", 0.0)),
                    behavior_boundary,
                ),
                "convention_score": max(
                    float(current_detail.get("convention_score", 0.0)),
                    convention,
                ),
                "retriever": f"{current_detail.get('retriever', 'knowledge')}+source",
            },
        )
    anchor_source_files = [
        file
        for file in related_source_files
        if modification_task
        and (
            source_metrics[file.id]["edit_target"]
            or source_metrics[file.id]["source_focus"]
            or source_metrics[file.id]["symbol_score"]
            or source_metrics[file.id]["path_score"]
        )
    ]
    for obj, scores in list(merged.values()):
        path = str((obj.payload or {}).get("path") or "")
        if (
            not path
            or path in related_source_paths
            or obj.type == "TestingPattern"
            or not anchor_source_files
        ):
            continue
        runtime_score = related_object_score(obj, anchor_source_files, query_terms)
        if runtime_score <= 0.0:
            continue
        scores["runtime_signal_score"] = max(
            float(scores.get("runtime_signal_score", 0.0)),
            runtime_score,
        )
        scores["lexical_score"] = max(float(scores.get("lexical_score", 0.0)), 0.82)
        scores["retriever"] = f"{scores.get('retriever', 'knowledge')}+runtime"
    return sorted(
        merged.values(),
        key=lambda item: (
            max(item[1]["lexical_score"], item[1].get("vector_score", 0.0)),
            item[0].quality_score,
        ),
        reverse=True,
    )


def source_file_knowledge_object(
    file: SourceFile,
    ref: SourceRef | None,
    *,
    symbol_score: float = 0.0,
    edit_target_score: float = 0.0,
    behavior_boundary_score: float = 0.0,
    runtime_score: float = 0.0,
    related_test_score: float = 0.0,
    convention_score: float = 0.0,
) -> KnowledgeObject:
    symbols = source_symbols(file)
    symbol_text = ", ".join(symbols[:6]) or "module-level code"
    source_refs = [ref.id] if ref else []
    obj_type = "TestingPattern" if file.is_test else "CodeExample"
    domain = source_domain(file)
    summary = source_file_summary(
        file,
        symbol_text,
        symbol_score,
        edit_target_score,
        behavior_boundary_score,
        runtime_score,
        related_test_score,
        convention_score,
    )
    return KnowledgeObject(
        id=stable_id("ko", file.snapshot_id, "SourceFile", file.path),
        type=obj_type,
        title=f"{'Test' if file.is_test else 'Source'} file {file.path}",
        summary=summary,
        problem="Agents need exact source context for code modification tasks.",
        solution=f"Inspect and edit {file.path} when it matches the task entities.",
        when_to_use=[f"When the task mentions symbols or behavior from {file.path}"],
        language=file.language,
        domain=domain,
        tags=[
            "source-file",
            "test" if file.is_test else "source",
            domain,
            file.language or "unknown",
            *path_tokens(file.path),
            *symbols,
        ],
        quality_score=0.82 if not file.is_test else 0.78,
        confidence=0.85,
        source_refs=source_refs,
        payload={
            "path": file.path,
            "symbols": [{"name": symbol} for symbol in symbols],
            "key_terms": source_key_terms(file.content or ""),
            "line_count": file.line_count,
            "is_test": file.is_test,
            "edit_target_score": edit_target_score,
            "behavior_boundary_score": behavior_boundary_score,
            "runtime_signal_score": runtime_score,
            "related_test_score": related_test_score,
            "convention_score": convention_score,
        },
        created_at=now_utc(),
        updated_at=now_utc(),
    )


def source_file_summary(
    file: SourceFile,
    symbol_text: str,
    symbol_score: float,
    edit_target_score: float,
    behavior_boundary_score: float,
    runtime_score: float,
    related_test_score: float,
    convention_score: float,
) -> str:
    if file.is_test and related_test_score:
        return (
            f"{file.path} is the best local unit test location for nearby source files. "
            f"It defines {symbol_text} and should cover the changed behavior."
        )
    if edit_target_score or (
        symbol_score and "config" in set(token.lower() for token in path_tokens(file.path))
    ):
        return (
            f"{file.path} is the likely edit target and validation boundary for {symbol_text}. "
            "Use this file for config invariants before runtime code receives invalid values."
        )
    if convention_score:
        return (
            f"{file.path} is a validation convention example for nearby source files. "
            f"It defines {symbol_text}; copy its local validation style before adding new checks."
        )
    if behavior_boundary_score:
        return (
            f"{file.path} is the persistence/runtime boundary for {symbol_text}. "
            "Inspect it to keep stored state and update behavior consistent with validation."
        )
    if runtime_score:
        return (
            f"{file.path} shows runtime risk for task terms that overlap its behavior. "
            f"It defines {symbol_text}; inspect it to see how invalid inputs can affect execution."
        )
    return (
        f"{file.path} defines {symbol_text}. "
        "Use this exact file when the task names its symbols, path, or nearby behavior."
    )


def should_promote_source_file(
    file: SourceFile,
    *,
    task_type: str,
    domain: str | None,
    path_score: float,
    symbol_score: float,
    overlap: float,
    edit_target_score: float = 0.0,
    behavior_boundary_score: float = 0.0,
    runtime_score: float = 0.0,
    related_test_score: float = 0.0,
    convention_score: float = 0.0,
) -> bool:
    if path_score or symbol_score:
        return True
    if (
        edit_target_score
        or behavior_boundary_score
        or runtime_score
        or related_test_score
        or convention_score
    ):
        return True
    if file.is_test and task_type == "test_generation" and overlap >= 0.08:
        return True
    if domain and source_domain(file) == domain and overlap >= 0.14:
        return True
    return overlap >= 0.18


def related_source_score(
    file: SourceFile,
    anchor_files: list[SourceFile],
    query_terms: set[str],
) -> float:
    if file.is_test or not anchor_files:
        return 0.0
    task_overlap = behavioral_overlap(query_terms, file)
    if task_overlap < 2:
        return 0.0
    best = 0.0
    for anchor in anchor_files:
        if anchor.path == file.path:
            continue
        file_terms = set(normalized_terms(" ".join([file.path, file.content or ""])))
        anchor_terms = {stem_key(anchor.path), *[term.lower() for term in source_symbols(anchor)]}
        if path_parent(file.path) == path_parent(anchor.path) and file_terms & anchor_terms:
            best = max(best, 0.75)
        proximity = source_path_proximity(file.path, anchor.path)
        if proximity <= 0.0:
            continue
        best = max(best, min(1.0, proximity + min(task_overlap, 4) * 0.1))
    return round(best, 4)


def related_object_score(
    obj: Any,
    anchor_files: list[SourceFile],
    query_terms: set[str],
) -> float:
    path = str((obj.payload or {}).get("path") or "")
    if not path:
        return 0.0
    haystack = " ".join(
        [
            obj.title,
            obj.summary,
            " ".join(str(symbol.get("name", "")) for symbol in (obj.payload or {}).get("symbols", [])),
            " ".join(str(term) for term in (obj.payload or {}).get("key_terms", [])),
        ]
    ).lower()
    best = 0.0
    for anchor in anchor_files:
        if path == anchor.path or path_parent(path) != path_parent(anchor.path):
            continue
        anchor_terms = {stem_key(anchor.path), *[term.lower() for term in source_symbols(anchor)]}
        if anchor_terms & set(normalized_terms(haystack)):
            best = max(best, 0.75)
    return round(best, 4)


def related_test_score(
    file: SourceFile,
    related_sources: list[SourceFile],
    query_symbols: set[str],
    query_terms: set[str],
    *,
    api_area_test_sources: set[str] | None = None,
) -> float:
    if not file.is_test or not related_sources:
        return 0.0
    content = (file.content or "").lower()
    score = 0.0
    if any(symbol.lower() in content for symbol in query_symbols):
        score = max(score, 0.55)
    file_terms = set(normalized_terms(" ".join([file.path, file.content or ""])))
    for source in related_sources:
        focused_source = entity_focus_matches(
            source_symbols(source),
            query_terms,
            source.path,
            source.content or "",
        )
        source_stem = stem_key(source.path)
        test_stem = stem_key(file.path)
        exact_source_test = same_stem(source_stem, test_stem) and (
            focused_source or source_stem in query_terms or test_stem in query_terms
        )
        if exact_source_test:
            score = max(score, 0.95)
        elif len(query_terms & file_terms) >= 2 and focused_source:
            score = max(score, 0.3)
        if source.path not in (api_area_test_sources or set()) and not exact_source_test:
            continue
        proximity = test_path_proximity(
            file.path,
            source.path,
            allow_api_area=source.path in (api_area_test_sources or set()),
        )
        api_area_pair = (
            source.path in (api_area_test_sources or set())
            and api_test_area(file.path)
            and api_test_area(file.path) == api_source_area(source.path)
        )
        if proximity >= 0.85 and not (exact_source_test or api_area_pair):
            proximity = 0.35
        if proximity:
            score = max(score, proximity)
    return round(score, 4)


def edit_target_score(
    file: SourceFile,
    query_terms: set[str],
    query_symbols: set[str],
    task_type: str,
) -> float:
    if file.is_test:
        return 0.0
    if not is_code_source_file(file):
        return 0.0
    if task_type not in {
        "api_integration",
        "backend_feature",
        "bug_fix",
        "database_change",
        "refactor",
        "security_change",
        "test_generation",
    }:
        return 0.0
    terms = set(normalized_terms(" ".join([file.path, " ".join(source_symbols(file))])))
    content_terms = set(normalized_terms(file.content or ""))
    task_focus = query_terms - generic_task_terms()
    specific_focus = task_focus - generic_entity_terms() - code_structure_terms()
    shared_focus = task_focus & (terms | content_terms)
    symbols = source_symbols(file)
    symbol_hit = bool({symbol.lower() for symbol in query_symbols} & {symbol.lower() for symbol in symbols})
    shared_specific = specific_focus & (terms | content_terms)
    if not symbol_hit and not shared_specific:
        return 0.0

    score = 0.0
    modification_task = bool(query_terms & modification_terms())
    api_boundary = is_api_boundary(file)
    if api_boundary and request_model_symbols(symbols) and entity_focus_matches(
        symbols, query_terms, file.path, file.content or ""
    ):
        score = max(score, 0.8)
    if api_boundary and endpoint_handler_symbols(symbols, query_terms) and entity_focus_matches(
        symbols, query_terms, file.path, file.content or ""
    ):
        score = max(score, 0.75)
    if symbol_hit:
        score = max(score, 1.0)
    if score >= 0.8 and len(shared_focus) >= 3:
        score = min(1.0, score + 0.15)
    return round(score, 4)


def is_code_source_file(file: SourceFile) -> bool:
    path = file.path.lower()
    return path.endswith(
        (
            ".py",
            ".ts",
            ".tsx",
            ".js",
            ".jsx",
            ".go",
            ".rs",
            ".java",
            ".kt",
            ".cs",
            ".rb",
            ".php",
            ".swift",
            ".c",
            ".cc",
            ".cpp",
            ".h",
            ".hpp",
        )
    )


def source_focus_score(file: SourceFile, query_terms: set[str]) -> float:
    if file.is_test:
        return 0.0
    task_focus = query_terms - generic_task_terms()
    stem_terms = set(identifier_terms(stem_key(file.path)))
    if not (stem_terms & task_focus):
        return 0.0
    specific_focus = task_focus - generic_entity_terms() - code_structure_terms()
    file_terms = set(normalized_terms(" ".join([file.path, file.content or ""])))
    return 0.75 if specific_focus & file_terms else 0.0


def convention_score(file: SourceFile, query_terms: set[str]) -> float:
    path_terms = set(path_tokens(file.path.lower()))
    if file.is_test or not any(term.startswith("valid") for term in path_terms):
        return 0.0
    file_terms = set(normalized_terms(" ".join([file.path, file.content or ""])))
    if "validation" in query_terms and len((query_terms - generic_task_terms()) & file_terms) >= 2:
        return 0.7
    return 0.0


def behavior_boundary_score(file: SourceFile, query_terms: set[str]) -> float:
    if file.is_test:
        return 0.0
    path_terms = set(path_tokens(file.path.lower()))
    if not ({"database", "db", "service", "manager", "config"} & path_terms):
        return 0.0
    if len((query_terms - generic_task_terms()) & set(normalized_terms(file.path))) < 2:
        return 0.0
    symbols = source_symbols(file)
    if endpoint_handler_symbols(symbols, query_terms) and entity_focus_matches(
        symbols, query_terms, file.path, file.content or ""
    ):
        return 0.75
    return 0.0


def is_api_boundary(file: SourceFile) -> bool:
    parts = set(file.path.lower().split("/"))
    content = file.content or ""
    return "api" in parts or "@router." in content or "APIRouter" in content


def request_model_symbols(symbols: list[str]) -> list[str]:
    markers = ("Create", "Update", "Request", "Input", "Config")
    return [symbol for symbol in symbols if any(marker in symbol for marker in markers)]


def entity_focus_matches(
    symbols: list[str],
    query_terms: set[str],
    path: str = "",
    content: str = "",
) -> bool:
    entity_terms = query_terms - generic_task_terms() - generic_entity_terms()
    if not entity_terms:
        return True
    symbol_terms = (
        set(identifier_terms(" ".join(symbols)))
        | set(normalized_terms(path))
        | set(identifier_terms(content))
    )
    return bool(entity_terms & symbol_terms)


def endpoint_handler_symbols(symbols: list[str], query_terms: set[str]) -> list[str]:
    verbs = {"add", "create", "creating", "update", "updating", "delete"}
    wanted = verbs & query_terms
    if not wanted:
        return []
    return [
        symbol
        for symbol in symbols
        if any(verb in set(identifier_terms(symbol)) for verb in wanted)
    ]


def identifier_terms(text: str) -> list[str]:
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", text)
    spaced = re.sub(r"(?<=[A-Z])(?=[A-Z][a-z])", " ", spaced)
    spaced = spaced.replace("_", " ").replace("-", " ")
    return normalized_terms(spaced)


def generic_task_terms() -> set[str]:
    return {
        "add",
        "change",
        "create",
        "creating",
        "delete",
        "fix",
        "implement",
        "negative",
        "positive",
        "refactor",
        "reject",
        "rejects",
        "test",
        "tests",
        "unit",
        "update",
        "updating",
        "validate",
        "validation",
    }


def modification_terms() -> set[str]:
    return {
        "add",
        "change",
        "create",
        "creating",
        "delete",
        "fix",
        "implement",
        "refactor",
        "reject",
        "rejects",
        "support",
        "update",
        "updating",
        "validate",
        "validation",
    }


def generic_entity_terms() -> set[str]:
    return {
        "and",
        "api",
        "blank",
        "buffer",
        "config",
        "configuration",
        "endpoint",
        "endpoints",
        "error",
        "errors",
        "fastapi",
        "file",
        "files",
        "for",
        "html",
        "import",
        "importer",
        "json",
        "key",
        "keys",
        "malformed",
        "name",
        "names",
        "or",
        "parse",
        "parser",
        "provider",
        "server",
        "so",
        "storage",
        "test",
        "tests",
        "tests.",
        "the",
        "to",
        "url",
        "urls",
        "with",
    }


def code_structure_terms() -> set[str]:
    return {
        "app",
        "apps",
        "jsx",
        "lib",
        "libs",
        "package",
        "packages",
        "pipeline",
        "py",
        "src",
        "test",
        "tests",
        "ts",
        "tsx",
    }


def behavioral_overlap(query_terms: set[str], file: SourceFile) -> int:
    file_terms = set(normalized_terms(" ".join([file.path, file.content or ""])))
    return len((query_terms - generic_task_terms()) & file_terms)


def source_path_proximity(path: str, anchor_path: str) -> float:
    path_stem = stem_key(path)
    anchor_stem = stem_key(anchor_path)
    if path_parent(path) == path_parent(anchor_path) and not same_stem(path_stem, anchor_stem):
        return 0.7
    if path_parent(path) == path_parent(anchor_path):
        return 0.55
    file_terms = useful_path_terms(path)
    anchor_terms = useful_path_terms(anchor_path)
    shared = file_terms & anchor_terms
    if len(shared) >= 2:
        return 0.35
    return 0.0


def test_path_proximity(test_path: str, source_path: str, *, allow_api_area: bool = True) -> float:
    test_terms = useful_path_terms(test_path)
    source_terms = useful_path_terms(source_path)
    shared = test_terms & source_terms
    if (
        allow_api_area
        and api_test_area(test_path)
        and api_test_area(test_path) == api_source_area(source_path)
    ):
        return 0.9
    if path_parent(test_path) == path_parent(source_path) and shared:
        return 0.85
    if stem_key(source_path) in test_path.lower() or stem_key(test_path) in source_path.lower():
        return 0.85
    if len(shared) >= 2:
        return 0.65
    if shared:
        return 0.35
    return 0.0


def path_parent(path: str) -> str:
    return path.rsplit("/", 1)[0] if "/" in path else ""


def useful_path_terms(path: str) -> set[str]:
    ignored = {
        "config",
        "graphrag",
        "models",
        "package",
        "packages",
        "py",
        "python",
        "src",
        "test",
        "tests",
        "unit",
    }
    return {token.lower() for token in path_tokens(path) if token.lower() not in ignored}


def stem_key(path: str) -> str:
    stem = path.rsplit("/", 1)[-1].rsplit(".", 1)[0].lower()
    for suffix in (".test", ".spec", "_test"):
        stem = stem.removesuffix(suffix)
    return stem.removeprefix("test_")


def same_stem(left: str, right: str) -> bool:
    return bool(
        left
        and right
        and (
            left == right
            or left.endswith(f"_{right}")
            or right.endswith(f"_{left}")
        )
    )


def api_source_area(path: str) -> str | None:
    parts = path.lower().split("/")
    if "api" not in parts:
        return None
    index = parts.index("api")
    if index + 1 >= len(parts):
        return None
    return parts[index + 1]


def api_test_area(path: str) -> str | None:
    stem = stem_key(path)
    return stem or None


def source_symbols(file: SourceFile) -> list[str]:
    if not file.content:
        return []
    symbols: list[str] = []
    for match in re.finditer(r"^\s*(?:class|def)\s+([A-Za-z_][A-Za-z0-9_]*)", file.content, re.M):
        symbols.append(match.group(1))
    for match in re.finditer(
        r"^\s*(?:export\s+)?(?:class|function|const|let|var|interface|type)\s+([A-Za-z_][A-Za-z0-9_]*)",
        file.content,
        re.M,
    ):
        symbols.append(match.group(1))
    return list(dict.fromkeys(symbols))[:20]


def source_symbol_match_score(query_symbols: set[str], file: SourceFile) -> float:
    if not query_symbols:
        return 0.0
    wanted = {symbol.lower() for symbol in query_symbols}
    found = {symbol.lower() for symbol in source_symbols(file)}
    if wanted & found:
        return 1.0
    content = (file.content or "").lower()
    if any(symbol.lower() in content for symbol in query_symbols):
        return 0.9
    path = file.path.lower()
    return 0.7 if any(symbol.lower() in path for symbol in query_symbols) else 0.0


def source_query_overlap(query_terms: set[str], file: SourceFile) -> float:
    if not query_terms:
        return 0.0
    text = " ".join(
        [
            file.path,
            " ".join(source_symbols(file)),
            file.content or "",
        ]
    )
    object_terms = set(normalized_terms(text))
    if not object_terms:
        return 0.0
    return round(len(query_terms & object_terms) / len(query_terms), 4)


def source_domain(file: SourceFile) -> str:
    terms = set(path_tokens(file.path))
    if file.is_test:
        return "testing"
    for domain, needles in {
        "auth": {"auth", "login", "password", "session", "user"},
        "api": {"api", "route", "controller", "endpoint"},
        "database": {"database", "db", "schema", "migration", "sql"},
        "ui": {"component", "page", "frontend", "view", "ui"},
        "config": {"config", "settings"},
    }.items():
        if terms & needles:
            return domain
    return "general"


def path_tokens(path: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[A-Za-z0-9]+", path.replace("_", " "))
        if len(token) >= 2
    ]


def normalized_terms(text: str) -> list[str]:
    terms: list[str] = []
    for term in tokenize(text.replace("_", " ")):
        terms.append(term)
        terms.extend(
            part
            for part in re.findall(r"[a-z0-9]+", term.lower())
            if len(part) >= 2
        )
    return list(dict.fromkeys(terms))


def path_terms(text: str) -> list[str]:
    return list(
        dict.fromkeys(
            match.rstrip(".,;:)")
            for match in re.findall(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+", text)
        )
    )


def symbol_terms(text: str) -> set[str]:
    ignored = {
        "Add",
        "Change",
        "Create",
        "Delete",
        "Extend",
        "Fix",
        "Implement",
        "Refactor",
        "Remove",
        "Update",
        "Validate",
        "Django",
        "Express",
        "FastAPI",
        "Flask",
        "NextJS",
        "React",
        "Vue",
    }
    acronym_words = {
        "API",
        "JSON",
        "URL",
        "URLs",
    }
    terms = {
        term
        for quoted in re.findall(r"`([^`]+)`|['\"]([A-Za-z_][A-Za-z0-9_-]+)['\"]", text)
        for term in quoted
        if len(term) >= 3
    }
    for term in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", text):
        if len(term) < 3 or term in ignored or term in acronym_words:
            continue
        if term[0].isupper() or "_" in term or re.search(r"[a-z][A-Z]", term):
            terms.add(term)
    return terms


def ref_paths_for_candidates(store: SQLiteStore, candidates: object) -> dict[str, list[str]]:
    candidate_list = list(candidates)
    ref_ids = {
        ref_id
        for obj, _, _ in candidate_list
        for ref_id in obj.source_refs
    }
    refs = {ref.id: ref.path for ref in store.get_source_refs(ref_ids)}
    return {
        obj.id: [refs[ref_id] for ref_id in obj.source_refs if ref_id in refs]
        for obj, _, _ in candidate_list
    }


def with_match_scores(
    candidates: list[tuple[Any, float, dict[str, Any]]],
    *,
    query_paths: list[str],
    query_symbols: set[str],
    ref_paths: dict[str, list[str]],
) -> list[tuple[Any, float, dict[str, Any]]]:
    return [
        (
            obj,
            score,
            {
                **detail,
                "path_match_score": path_match_score(query_paths, object_paths(obj, ref_paths)),
                "symbol_match_score": symbol_match_score(query_symbols, obj),
            },
        )
        for obj, score, detail in candidates
    ]


def object_paths(obj: Any, ref_paths: dict[str, list[str]]) -> list[str]:
    payload = obj.payload or {}
    paths = [str(payload.get("path", "")), *ref_paths.get(obj.id, [])]
    paths.extend(str(path) for path in payload.get("examples", []))
    return [path for path in dict.fromkeys(paths) if path]


def path_match_score(query_paths: list[str], candidate_paths: list[str]) -> float:
    if not query_paths or not candidate_paths:
        return 0.0
    best = 0.0
    for query_path in query_paths:
        query = query_path.lower().strip("/")
        query_stem = stem_key(query)
        query_stem_terms = set(identifier_terms(query_stem)) - generic_entity_terms() - weak_path_stems()
        for path in candidate_paths:
            candidate = path.lower().strip("/")
            if (
                candidate == query
                or candidate.endswith("/" + query)
                or query.endswith("/" + candidate)
            ):
                best = max(best, 1.0)
            elif query.startswith(candidate + "/"):
                best = max(best, 0.6)
            elif (
                query_stem_terms
                and same_stem(query_stem, stem_key(candidate))
                and useful_path_terms(query) & useful_path_terms(candidate)
            ):
                best = max(best, 0.92)
    return best


def weak_path_stems() -> set[str]:
    return {"index", "main", "util", "utils", "helper", "helpers", "route", "routes"}


def symbol_match_score(query_symbols: set[str], obj: Any) -> float:
    if not query_symbols:
        return 0.0
    symbols = {
        str(symbol.get("name", ""))
        for symbol in (obj.payload or {}).get("symbols", [])
        if isinstance(symbol, dict)
    }
    if not symbols:
        return 0.0
    wanted = {symbol.lower() for symbol in query_symbols}
    found = {symbol.lower() for symbol in symbols}
    return 1.0 if wanted & found else 0.0


def retrieval_warnings(
    task: str,
    ranked: list[tuple[Any, float, dict[str, Any]]],
    citations: list[dict],
    *,
    query_paths: list[str],
    query_symbols: set[str],
) -> list[str]:
    if not query_paths and not query_symbols:
        return []
    returned_text = " ".join(
        [
            *[obj.title for obj, _, _ in ranked],
            *[obj.summary for obj, _, _ in ranked],
            *[str(obj.payload.get("path", "")) for obj, _, _ in ranked],
            *[str(citation.get("path", "")) for citation in citations],
        ]
    ).lower()
    missing_symbols = [
        symbol for symbol in sorted(query_symbols) if symbol.lower() not in returned_text
    ]
    missing_paths = [
        path for path in query_paths if path.lower().strip("/") not in returned_text
    ]
    if missing_symbols or missing_paths:
        missing = ", ".join([*missing_symbols, *missing_paths])
        return [
            "Potential low-quality retrieval: missing exact task entities: "
            f"{missing}. Inspect exact entity/path matches manually before editing; "
            "treat generic top results as provisional."
        ]
    return []


def add_citation_context(
    citations: list[dict],
    contents: dict[str, str],
    query_paths: list[str],
    query_symbols: set[str],
    query_terms: set[str],
) -> None:
    if query_paths:
        citations.sort(
            key=lambda citation: path_match_score(
                query_paths, [str(citation.get("path", ""))]
            ),
            reverse=True,
        )
    for citation in citations:
        citation["key_terms"] = source_key_terms(contents.get(citation["id"], ""))
        notes = behavior_notes(contents.get(citation["id"], ""), query_symbols, query_terms)
        if notes:
            citation["behavior_notes"] = notes


def source_key_terms(content: str, limit: int = 16) -> list[str]:
    terms: list[str] = []
    for match in re.finditer(r"^\s*from\s+([\w.]+)\s+import\s+([A-Za-z0-9_,\s]+)", content, re.M):
        terms.extend(match.group(1).split("."))
        terms.extend(re.findall(r"[A-Za-z][A-Za-z0-9_]*", match.group(2)))
    for match in re.finditer(r"^\s*import\s+([A-Za-z0-9_.,\s]+)", content, re.M):
        terms.extend(re.findall(r"[A-Za-z][A-Za-z0-9_]*", match.group(1)))
    for token in re.findall(r"[A-Za-z][A-Za-z0-9_]*", content):
        if token in {"const", "let", "var", "return", "function", "class", "def", "from", "import"}:
            continue
        readable = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", token).replace("_", " ")
        terms.extend([token, readable] if readable != token else [token])
    return prioritized_terms(terms)[:limit]


def behavior_notes(content: str, query_symbols: set[str], query_terms: set[str], limit: int = 2) -> list[str]:
    if not content:
        return []
    notes: list[str] = []
    lines = content.splitlines()
    windows = symbol_windows(lines, query_symbols)
    windows.extend(term_windows(lines, query_terms))
    for start, end in windows:
        for index in range(start, end):
            line = lines[index].strip()
            if not re.match(r"(if|elif)\b", line):
                continue
            window = "\n".join(lines[index : min(end, index + 4)]).lower()
            condition = re.sub(r"\s+", " ", line.rstrip(":"))
            if "return" in window:
                notes.append(f"Behavioral constraint: check early return branch `{condition}`.")
            elif any(term in line.lower() for term in ("allowlist", "denylist", "default", "valid")):
                notes.append(f"Behavioral constraint: check guard branch `{condition}`.")
            if len(notes) >= limit:
                return list(dict.fromkeys(notes))
    return list(dict.fromkeys(notes))


def symbol_windows(lines: list[str], query_symbols: set[str]) -> list[tuple[int, int]]:
    windows: list[tuple[int, int]] = []
    lowered = [line.lower() for line in lines]
    for symbol in query_symbols:
        needle = symbol.lower()
        for index, line in enumerate(lowered):
            if needle in line:
                start = max(0, index - 1)
                if re.match(r"\s*(class|def)\s+", lines[index]):
                    start = index
                windows.append((start, method_window_end(lines, index)))
                break
    return windows


def method_window_end(lines: list[str], start_index: int) -> int:
    line = lines[start_index]
    indent = len(line) - len(line.lstrip())
    for index in range(start_index + 1, len(lines)):
        current = lines[index]
        stripped = current.strip()
        if not stripped:
            continue
        current_indent = len(current) - len(current.lstrip())
        if current_indent <= indent and re.match(r"(class|def)\s+", stripped):
            return index
    return min(len(lines), start_index + 40)


def term_windows(lines: list[str], query_terms: set[str]) -> list[tuple[int, int]]:
    focus_terms = (query_terms - generic_task_terms() - generic_entity_terms()) | {
        term for term in query_terms if term in {"allowlist", "denylist", "default", "valid"}
    }
    if not focus_terms:
        return []
    windows: list[tuple[int, int]] = []
    for index, line in enumerate(line.lower() for line in lines):
        if focus_terms & set(normalized_terms(line)):
            windows.append((max(0, index - 1), min(len(lines), index + 8)))
    return windows[:8]


def prioritized_terms(terms: list[str]) -> list[str]:
    priority = (
        "systemapikey",
        "apikey",
        "accesscode",
        "access",
        "auth",
        "json",
        "modelargs",
        "transformer",
        "config",
        "checkpoint",
        "safetensor",
    )
    unique = list(dict.fromkeys(terms))

    def rank(term: str) -> tuple[int, int]:
        compact = re.sub(r"[^a-z0-9]", "", term.lower())
        for index, needle in enumerate(priority):
            if needle in compact:
                return (0, index)
        return (1, 0)

    return sorted(unique, key=rank)


def query_overlap(query_terms: set[str], obj: Any) -> float:
    if not query_terms:
        return 0.0
    payload = obj.payload or {}
    text = " ".join(
        [
            obj.title,
            obj.summary,
            obj.problem or "",
            obj.solution or "",
            " ".join(obj.tags),
            str(payload.get("path", "")),
            " ".join(str(symbol.get("name", "")) for symbol in payload.get("symbols", [])),
        ]
    )
    object_terms = set(normalized_terms(text))
    if not object_terms:
        return 0.0
    return round(len(query_terms & object_terms) / len(query_terms), 4)


def citation_allowed(ref: Any, license_policy: str | None) -> bool:
    if license_policy is None:
        return True
    if license_policy == "allow_all_public":
        return True
    if license_policy == "metadata_only":
        return True
    if license_policy == "permissive_only" and ref.license is None:
        return True
    return bool(ref.snippet_allowed)
