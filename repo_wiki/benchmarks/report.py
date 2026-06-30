from __future__ import annotations

from pathlib import Path
from statistics import mean
from typing import Any

from repo_wiki.core.metrics_service import MetricsService
from repo_wiki.core.retrieval_service import RetrievalService
from repo_wiki.domain.models import now_utc
from repo_wiki.storage.sqlite import SQLiteStore


DEFAULT_TASKS = (
    "backend: implement FastAPI auth endpoint with tests",
    "frontend: add Next.js route handler with validation",
    "testing: add pytest coverage for password reset",
    "refactor: simplify service layer and update tests",
    "bug-fix: fix route validation error handling",
)


def build_benchmark_report(
    store: SQLiteStore,
    *,
    tasks: tuple[str, ...] = DEFAULT_TASKS,
    expected_paths: dict[str, tuple[str, ...]] | None = None,
    repo: str | None = None,
) -> tuple[str, dict[str, Any]]:
    metrics = MetricsService(store).metrics()
    retrieval_results = []
    expected_paths = expected_paths or {}
    if metrics.get("knowledge_objects", 0):
        service = RetrievalService(store)
        for task in tasks:
            result = service.retrieve(task, limit=5, repo=repo)
            pack = result["context_pack"]
            trace = store.get_retrieval_trace(result["trace_id"]) or {}
            payload = trace.get("payload", {})
            returned_paths = {
                citation["path"]
                for section_name in (
                    "recommended_patterns",
                    "relevant_examples",
                    "architecture_rules",
                )
                for item in pack[section_name]
                for citation in item["citations"]
            }
            expected = set(expected_paths.get(task, ()))
            expected_hits = len(returned_paths & expected)
            returned_items = sum(
                len(pack[name])
                for name in (
                    "recommended_patterns",
                    "relevant_examples",
                    "architecture_rules",
                )
            )
            cited_items = sum(
                1
                for name in (
                    "recommended_patterns",
                    "relevant_examples",
                    "architecture_rules",
                )
                for item in pack[name]
                if item["citations"]
            )
            retrieval_results.append(
                {
                    "task": task,
                    "trace_id": result["trace_id"],
                    "latency_ms": trace.get("latency_ms", 0),
                    "returned_items": returned_items,
                    "cited_items": cited_items,
                    "citation_coverage": round(cited_items / returned_items, 2)
                    if returned_items
                    else 0,
                    "citation_count": len(pack["source_citations"]),
                    "candidate_counts": payload.get("candidate_counts", {}),
                    "expected_hits": expected_hits,
                    "expected_total": len(expected),
                }
            )

    total_expected = sum(item["expected_total"] for item in retrieval_results)
    expected_hit_count = sum(item["expected_hits"] for item in retrieval_results)
    per_category = summarize_categories(retrieval_results)
    report_metrics = {
        **metrics,
        "benchmark_tasks": len(retrieval_results),
        "average_returned_items": round(
            mean(item["returned_items"] for item in retrieval_results), 2
        )
        if retrieval_results
        else 0,
        "average_citation_count": round(
            mean(item["citation_count"] for item in retrieval_results), 2
        )
        if retrieval_results
        else 0,
        "average_latency_ms": round(
            mean(item["latency_ms"] for item in retrieval_results), 2
        )
        if retrieval_results
        else 0,
        "average_citation_coverage": round(
            mean(item["citation_coverage"] for item in retrieval_results), 2
        )
        if retrieval_results
        else 0,
        "expected_hit_count": expected_hit_count,
        "expected_total": total_expected,
        "top_k_precision": round(expected_hit_count / total_expected, 2)
        if total_expected
        else 0,
        "per_category": per_category,
    }
    return render_markdown(report_metrics, retrieval_results), report_metrics


def write_benchmark_report(store: SQLiteStore, output: Path) -> dict[str, Any]:
    markdown, metrics = build_benchmark_report(store)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown, encoding="utf-8")
    return metrics


def render_markdown(metrics: dict[str, Any], retrieval_results: list[dict[str, Any]]) -> str:
    lines = [
        "# MVP Benchmark Results",
        "",
        f"Generated: {now_utc()}",
        "",
        "## Local Index Metrics",
        "",
        f"- Indexed repositories: {metrics.get('indexed_repositories', 0)}",
        f"- Repository snapshots: {metrics.get('repository_snapshots', 0)}",
        f"- Indexed files: {metrics.get('indexed_files', 0)}",
        f"- Extracted symbols: {metrics.get('extracted_symbols', 0)}",
        f"- Dependencies: {metrics.get('dependencies', 0)}",
        f"- Knowledge objects: {metrics.get('knowledge_objects', 0)}",
        f"- Graph nodes: {metrics.get('graph_nodes', 0)}",
        f"- Graph edges: {metrics.get('graph_edges', 0)}",
        f"- Context packs: {metrics.get('context_packs', 0)}",
        f"- Feedback records: {metrics.get('feedback_records', 0)}",
        f"- Staged knowledge records: {metrics.get('staged_knowledge', 0)}",
        "- Supported languages: "
        f"{', '.join(metrics.get('supported_languages', [])) or 'none indexed yet'}",
        f"- Supported interfaces: {', '.join(metrics.get('supported_interfaces', []))}",
        "",
        "## Retrieval Quality Suite",
        "",
    ]
    if not retrieval_results:
        lines.extend(
            [
                "No retrieval smoke tasks were run because the local index has no "
                "knowledge objects.",
                "",
                "Run `repo-wiki ingest local <path>` first, then regenerate this report.",
            ]
        )
    else:
        lines.extend(
            [
                f"- Tasks run: {metrics['benchmark_tasks']}",
                f"- Average returned items: {metrics['average_returned_items']}",
                f"- Average citation count: {metrics['average_citation_count']}",
                f"- Average latency: {metrics['average_latency_ms']} ms",
                f"- Citation coverage: {metrics['average_citation_coverage']}",
                f"- Expected hits: {expected_hits_label(metrics)}",
                f"- Top-k precision: {metrics['top_k_precision']}",
                "",
                "| Task | Trace | Latency ms | Returned Items | Citations | "
                "Citation Coverage | Expected Hits | Candidate Counts |",
                "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for item in retrieval_results:
            candidate_counts = item["candidate_counts"]
            candidate_summary = ", ".join(
                f"{key}={candidate_counts.get(key, 0)}"
                for key in ("fts", "vector", "merged", "graph_expanded", "total")
            )
            lines.append(
                "| "
                + " | ".join(
                    [
                        escape_table_cell(item["task"]),
                        f"`{item['trace_id']}`",
                        str(item["latency_ms"]),
                        str(item["returned_items"]),
                        str(item["citation_count"]),
                        str(item["citation_coverage"]),
                        expected_hits_label(item),
                        escape_table_cell(candidate_summary),
                    ]
                )
                + " |"
            )

        lines.extend(
            [
                "",
                "## Per-Category Quality",
                "",
                "| Category | Tasks | Citation Coverage | Expected Hits | Top-k Precision |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for category, values in metrics["per_category"].items():
            lines.append(
                "| "
                + " | ".join(
                    [
                        escape_table_cell(category),
                        str(values["tasks"]),
                        str(values["citation_coverage"]),
                        expected_hits_label(values),
                        str(values["top_k_precision"]),
                    ]
                )
                + " |"
            )

    lines.extend(
        [
            "",
            "## Reproduce",
            "",
            "```bash",
            "repo-wiki benchmark report --output reports/mvp-results.md",
            "```",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|")


def expected_hits_label(values: dict[str, Any]) -> str:
    total = int(values.get("expected_total", 0))
    if total == 0:
        return "not configured"
    return f"{values.get('expected_hits', values.get('expected_hit_count', 0))}/{total}"


def summarize_categories(retrieval_results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in retrieval_results:
        category = item["task"].split(":", 1)[0].strip() if ":" in item["task"] else "uncategorized"
        grouped.setdefault(category, []).append(item)
    output = {}
    for category, items in grouped.items():
        expected_total = sum(item["expected_total"] for item in items)
        expected_hits = sum(item["expected_hits"] for item in items)
        output[category] = {
            "tasks": len(items),
            "citation_coverage": round(mean(item["citation_coverage"] for item in items), 2),
            "expected_hits": expected_hits,
            "expected_total": expected_total,
            "top_k_precision": round(expected_hits / expected_total, 2)
            if expected_total
            else 0,
        }
    return output
