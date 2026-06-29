from __future__ import annotations

import re

from repo_wiki.domain.ids import new_id
from repo_wiki.domain.models import ContextPack, KnowledgeObject


def build_context_pack(
    *,
    task: str,
    task_type: str,
    constraints: dict,
    ranked: list[tuple[KnowledgeObject, float, dict]],
    citations: list[dict],
    retrieval_trace_id: str,
    max_items: int = 8,
) -> ContextPack:
    max_tokens = int(constraints.get("max_tokens") or 4000)
    selected = ranked[:max_items]
    recommended_patterns = []
    relevant_examples = []
    architecture_rules = []
    tests_to_consider: list[str] = []
    risks: list[str] = []
    implementation_steps: list[str] = []
    risks.extend(str(warning) for warning in constraints.get("warnings", []))

    for obj, score, detail in selected:
        item_citations = [ref for ref in citations if ref["id"] in obj.source_refs]
        item = {
            "id": obj.id,
            "title": obj.title,
            "type": obj.type,
            "summary": obj.summary,
            "score": score,
            "why_relevant": detail["reasons"],
            "citations": item_citations,
        }
        role = context_role(obj, detail, bool(item_citations))
        if role:
            item["role"] = role
        if obj.type == "TestingPattern":
            relevant_examples.append(item)
            path = obj.payload.get("path", obj.title)
            related_test_score = max(
                float(obj.payload.get("related_test_score") or 0.0),
                float(detail.get("related_test_score") or 0.0),
            )
            if related_test_score >= 0.8:
                tests_to_consider.append(
                    f"Use {path} as the best local unit test location for nearby source behavior."
                )
                continue
            tests_to_consider.append(
                f"Follow test structure from {path}."
            )
        elif obj.type == "ProjectProfile":
            architecture_rules.append(item)
        else:
            recommended_patterns.append(item)
            path = obj.payload.get("path")
            if path:
                if obj.source_refs and not item_citations:
                    implementation_steps.append(f"Weak uncited recommendation: inspect {path} manually before editing.")
                    continue
                if role == "edit target":
                    verb = "Edit target"
                elif role == "runtime risk":
                    verb = "Runtime risk"
                elif role == "convention example":
                    verb = "Convention example"
                else:
                    verb = "Inspect exact source file" if obj.type == "CodeExample" else "Inspect"
                implementation_steps.append(f"{verb} {path}.")
        if obj.domain == "auth":
            risks.append("Validate tokens and avoid leaking credentials or session secrets.")
        if obj.domain == "database":
            risks.append("Check migration safety and add tests around persistence behavior.")

    risks.extend(edge_case_risks(task, selected, citations))
    risks.extend(behavioral_constraint_risks(citations))
    if not tests_to_consider:
        tests_to_consider.append("Add or update tests that cover the changed behavior.")
    elif any("best local unit test" in test for test in tests_to_consider):
        tests_to_consider = [
            test for test in tests_to_consider if "best local unit test" in test
        ]
    if not risks:
        risks.append(
            "Check project conventions, error handling, and existing tests before editing."
        )

    citations = dedupe_citations(citations)
    answer = build_answer(task, selected, citations)
    pack = ContextPack(
        id=new_id("ctx"),
        task=task,
        task_type=task_type,
        constraints=constraints,
        recommended_patterns=recommended_patterns,
        relevant_examples=relevant_examples,
        architecture_rules=architecture_rules,
        implementation_steps=implementation_steps[:8],
        tests_to_consider=dedupe_strings(tests_to_consider)[:8],
        risks=dedupe_strings(risks)[:8],
        source_citations=citations,
        answer=answer,
        retrieval_trace_id=retrieval_trace_id,
    )
    pack.markdown = to_markdown(pack)
    compact_to_budget(pack, max_tokens=max_tokens)
    return pack


def to_markdown(pack: ContextPack) -> str:
    lines = [
        f"# Context Pack: {pack.task}",
        "",
        f"- Task type: `{pack.task_type}`",
        f"- Retrieval trace: `{pack.retrieval_trace_id}`",
        "",
        "## Answer",
        pack.answer or "No direct answer was derived from the retrieved context.",
        "",
        "## Recommended Patterns",
    ]
    for item in pack.recommended_patterns:
        reasons = "; ".join(item["why_relevant"]) or "retrieved from indexed knowledge"
        lines.extend(
            [
                f"### {item['title']}",
                f"- Score: {item['score']}",
                *([f"- Role: {item['role']}"] if item.get("role") else []),
                f"- Why: {reasons}",
                f"- Summary: {item['summary']}",
                "",
            ]
        )
    lines.append("## Architecture Rules")
    for item in pack.architecture_rules:
        lines.extend([f"- {item['title']}: {item['summary']}"])
    lines.extend(["", "## Implementation Steps"])
    for step in pack.implementation_steps:
        lines.append(f"- {step}")
    lines.extend(["", "## Tests To Consider"])
    for test in pack.tests_to_consider:
        lines.append(f"- {test}")
    lines.extend(["", "## Risks"])
    for risk in pack.risks:
        lines.append(f"- {risk}")
    lines.extend(["", "## Citations"])
    for citation in pack.source_citations:
        line_range = ""
        if citation.get("start_line"):
            line_range = f":{citation['start_line']}"
            if citation.get("end_line"):
                line_range += f"-{citation['end_line']}"
        license_name = citation.get("license") or "unknown license"
        lines.append(f"- `{citation['path']}{line_range}` ({license_name})")
    return "\n".join(lines).strip() + "\n"


def compact_to_budget(pack: ContextPack, *, max_tokens: int) -> None:
    if max_tokens <= 0:
        return
    while approximate_tokens(pack.markdown) > max_tokens and pack.source_citations:
        pack.source_citations.pop()
        pack.markdown = to_markdown(pack)
    for section_name in ("recommended_patterns", "relevant_examples", "architecture_rules"):
        section = getattr(pack, section_name)
        while approximate_tokens(pack.markdown) > max_tokens and section:
            section.pop()
            pack.markdown = to_markdown(pack)
    while approximate_tokens(pack.markdown) > max_tokens and pack.implementation_steps:
        pack.implementation_steps.pop()
        pack.markdown = to_markdown(pack)
    while approximate_tokens(pack.markdown) > max_tokens and pack.tests_to_consider:
        pack.tests_to_consider.pop()
        pack.markdown = to_markdown(pack)
    while approximate_tokens(pack.markdown) > max_tokens and pack.risks:
        pack.risks.pop()
        pack.markdown = to_markdown(pack)


def approximate_tokens(text: str) -> int:
    return max(1, len(text.split()))


def build_answer(
    task: str,
    selected: list[tuple[KnowledgeObject, float, dict]],
    citations: list[dict],
) -> str:
    query_paths = path_terms(task)
    exact_citation_paths = [
        citation["path"]
        for citation in citations
        if citation.get("path") and path_match(query_paths, str(citation["path"]))
    ]
    selected_paths = [
        str(obj.payload.get("path", ""))
        for obj, _, _ in selected
        if obj.payload.get("path")
    ]
    citation_paths = [citation["path"] for citation in citations if citation.get("path")]
    paths = dedupe_strings([*exact_citation_paths, *selected_paths, *citation_paths])
    lower_task = task.lower()
    facts = dedupe_strings(
        [*citation_facts(citations, query_paths, lower_task), *answer_facts(selected)]
    )
    sentences: list[str] = []
    if paths and re.search(r"\b(where|which|what file|what module|modules?)\b", lower_task):
        sentences.append("Relevant files: " + ", ".join(paths[:5]) + ".")
    if facts:
        if re.search(r"\bwhat does\b", lower_task) and paths:
            sentences.append(f"{paths[0]} covers " + ", ".join(facts[:16]) + ".")
        else:
            sentences.append("Key signals: " + ", ".join(facts[:16]) + ".")
    if not sentences and selected:
        sentences.append(selected[0][0].summary)
    return " ".join(sentences[:3])


def context_role(obj: KnowledgeObject, detail: dict, cited: bool = True) -> str | None:
    if obj.type == "TestingPattern" or float(detail.get("related_test_score", 0.0)):
        return "related test"
    if not cited and obj.source_refs:
        return None
    if (
        float(detail.get("symbol_match_score", 0.0))
        or float(detail.get("path_match_score", 0.0)) >= 0.9
        or float(detail.get("edit_target_score", 0.0)) >= 0.8
    ):
        return "edit target"
    if float(detail.get("behavior_boundary_score", 0.0)):
        return "runtime risk"
    if float(detail.get("convention_score", 0.0)):
        return "convention example"
    if float(detail.get("runtime_signal_score", 0.0)):
        return "runtime risk"
    return None


def answer_facts(selected: list[tuple[KnowledgeObject, float, dict]]) -> list[str]:
    facts: list[str] = []
    for obj, _, _ in selected[:5]:
        for key in extract_key_terms(obj)[:16]:
            facts.append(key)
        if not facts:
            facts.extend(summary_terms(obj.summary))
    return dedupe_strings(facts)


def citation_facts(citations: list[dict], query_paths: list[str], task_lower: str) -> list[str]:
    facts: list[str] = []
    ranked_citations = citations
    if not query_paths and "where" in task_lower:
        ranked_citations = sorted(
            citations,
            key=lambda citation: citation_query_score(task_lower, citation),
            reverse=True,
        )
    for citation in ranked_citations:
        if query_paths and not path_match(query_paths, str(citation.get("path", ""))):
            continue
        if not query_paths and "where" in task_lower and not citation_matches_task(
            task_lower, citation
        ):
            continue
        facts.extend(str(term) for term in citation.get("key_terms", []))
    return facts


def edge_case_risks(
    task: str,
    selected: list[tuple[KnowledgeObject, float, dict]],
    citations: list[dict],
) -> list[str]:
    text = " ".join(
        [
            task,
            *[obj.summary for obj, _, _ in selected],
            *[str(term) for citation in citations for term in citation.get("key_terms", [])],
        ]
    ).lower()
    if "#" in text and ("comment" in text or "escape" in text or "whitespace" in text):
        return [
            "Preserve parser edge cases for literal # values, escaped hash sequences, and whitespace-prefixed comments."
        ]
    return []


def behavioral_constraint_risks(citations: list[dict]) -> list[str]:
    return dedupe_strings(
        [
            str(note)
            for citation in citations
            for note in citation.get("behavior_notes", [])
        ]
    )


def citation_query_score(task_lower: str, citation: dict) -> int:
    words = query_fact_words(task_lower)
    haystack = citation_haystack(citation)
    return len(words & set(re.findall(r"[a-z0-9]+", haystack)))


def citation_matches_task(task_lower: str, citation: dict) -> bool:
    return bool(
        query_fact_words(task_lower)
        & set(re.findall(r"[a-z0-9]+", citation_haystack(citation)))
    )


def query_fact_words(task_lower: str) -> set[str]:
    strong = {"json", "config", "auth", "api", "key", "access", "transformer"}
    words = {
        word
        for word in re.findall(r"[a-z0-9]+", task_lower)
        if len(word) >= 4 and word not in {"where", "which", "what", "does", "loaded", "consumes"}
    }
    return words | (strong & set(re.findall(r"[a-z0-9]+", task_lower)))


def citation_haystack(citation: dict) -> str:
    return " ".join(
        [str(citation.get("path", "")), *[str(term) for term in citation.get("key_terms", [])]]
    ).lower()


def extract_key_terms(obj: KnowledgeObject) -> list[str]:
    payload = obj.payload or {}
    terms: list[str] = []
    for symbol in payload.get("symbols", []):
        if isinstance(symbol, dict) and symbol.get("name"):
            terms.extend(identifier_terms(str(symbol["name"])))
    for token in payload.get("key_terms", []):
        terms.extend(identifier_terms(str(token)))
    for route in payload.get("routes", []):
        if isinstance(route, dict) and route.get("path"):
            terms.append(str(route["path"]))
    return terms


def identifier_terms(token: str) -> list[str]:
    readable = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", token).replace("_", " ")
    return dedupe_strings([token, readable]) if readable != token else [token]


def summary_terms(summary: str) -> list[str]:
    return [
        term
        for term in re.findall(r"`([^`]+)`|\b([A-Z][A-Za-z0-9_]{2,})\b", summary)
        for term in term
        if term
    ][:6]


def path_terms(text: str) -> list[str]:
    return list(dict.fromkeys(re.findall(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+", text)))


def path_match(query_paths: list[str], candidate_path: str) -> bool:
    candidate = candidate_path.lower().strip("/")
    return any(
        candidate == query.lower().strip("/")
        or candidate.endswith("/" + query.lower().strip("/"))
        for query in query_paths
    )


def dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def dedupe_citations(citations: list[dict]) -> list[dict]:
    seen: set[tuple] = set()
    output: list[dict] = []
    for citation in citations:
        key = (
            citation.get("path"),
            citation.get("start_line"),
            citation.get("end_line"),
            citation.get("license"),
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(citation)
    return output
