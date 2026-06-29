from __future__ import annotations

from collections import Counter
import re

from repo_wiki.compile.scoring import knowledge_quality
from repo_wiki.domain.enums import KnowledgeType
from repo_wiki.domain.ids import stable_id
from repo_wiki.domain.models import (
    Dependency,
    KnowledgeObject,
    Repository,
    SourceFile,
    SourceRef,
    Symbol,
)


def generate_project_profile(
    repo: Repository,
    files: list[SourceFile],
    symbols: list[Symbol],
    dependencies: list[Dependency],
    source_refs: list[SourceRef],
) -> KnowledgeObject:
    languages = ", ".join(repo.detected_languages.keys()) or "unknown languages"
    frameworks = ", ".join(repo.detected_frameworks) or "no major framework detected"
    test_count = sum(1 for file in files if file.is_test)
    docs_count = sum(1 for file in files if file.language == "Markdown")
    dep_names = sorted({dep.name for dep in dependencies})[:12]
    ref_ids = [ref.id for ref in source_refs[:8]]
    quality = knowledge_quality(
        repo_quality_score=repo.quality_score,
        citation_quality=0.6 if ref_ids else 0.0,
        test_evidence=1.0 if test_count else 0.0,
        docs_evidence=1.0 if docs_count else 0.0,
        pattern_reusability=0.5,
        extraction_confidence=0.8,
    )
    return KnowledgeObject(
        id=stable_id("ko", repo.id, "ProjectProfile"),
        type=KnowledgeType.PROJECT_PROFILE,
        title=f"{repo.name} project profile",
        summary=(
            f"{repo.name} is a {repo.project_type or 'unknown'} project using {languages}. "
            f"Detected frameworks: {frameworks}. It contains {len(files)} indexed files, "
            f"{len(symbols)} symbols, {len(dependencies)} dependencies, {test_count} test files, "
            f"and {docs_count} documentation files."
        ),
        problem="Coding agents need repository conventions before editing.",
        solution=(
            "Use this profile to understand languages, frameworks, tests, docs, "
            "and dependencies."
        ),
        when_to_use=[
            "Before planning changes in this repository",
            "When selecting relevant patterns",
        ],
        language=repo.primary_language,
        frameworks=repo.detected_frameworks,
        project_type=repo.project_type,
        tags=["project-profile", repo.project_type or "unknown", *repo.detected_frameworks],
        quality_score=quality,
        confidence=0.8,
        source_refs=ref_ids,
        payload={
            "file_count": len(files),
            "symbol_count": len(symbols),
            "dependency_count": len(dependencies),
            "test_file_count": test_count,
            "doc_file_count": docs_count,
            "top_dependencies": dep_names,
            "detected_languages": repo.detected_languages,
        },
    )


def generate_implementation_patterns(
    repo: Repository,
    files: list[SourceFile],
    symbols: list[Symbol],
    dependencies: list[Dependency],
    source_refs: list[SourceRef],
    *,
    routes_by_file: dict[str, list[dict]] | None = None,
    docs_by_file: dict[str, dict] | None = None,
) -> list[KnowledgeObject]:
    patterns: list[KnowledgeObject] = []
    refs_by_file = {ref.file_id: ref for ref in source_refs if ref.file_id}
    symbol_counter = Counter(sym.file_id for sym in symbols)
    routes_by_file = routes_by_file or {}
    docs_by_file = docs_by_file or {}
    candidate_files = sorted(
        [
            file
            for file in files
            if not file.is_test and file.language in {"Python", "TypeScript", "JavaScript"}
        ],
        key=lambda file: (symbol_counter[file.id], file.line_count),
        reverse=True,
    )[:12]
    dependency_names = {dep.name.lower() for dep in dependencies}
    for file in candidate_files:
        file_symbols = [sym for sym in symbols if sym.file_id == file.id][:10]
        if not file_symbols and file.line_count < 20:
            continue
        domain = infer_domain(file.path, dependency_names)
        if file.id in routes_by_file:
            domain = "api"
        ref = refs_by_file.get(file.id)
        test_evidence = 1.0 if has_related_test(file, files) else 0.0
        docs_evidence = 1.0 if any(doc.language == "Markdown" for doc in files) else 0.0
        quality = knowledge_quality(
            repo_quality_score=repo.quality_score,
            citation_quality=0.85 if ref and ref.start_line else 0.55,
            test_evidence=test_evidence,
            docs_evidence=docs_evidence,
            pattern_reusability=0.65 if file_symbols else 0.45,
            extraction_confidence=0.75,
        )
        title = pattern_title(file, domain)
        symbol_names = ", ".join(sym.name for sym in file_symbols[:6]) or "module-level code"
        patterns.append(
            KnowledgeObject(
                id=stable_id("ko", repo.id, "ImplementationPattern", file.path),
                type=KnowledgeType.IMPLEMENTATION_PATTERN,
                title=title,
                summary=(
                    f"{file.path} provides {domain} implementation structure with "
                    f"{symbol_names}. Use it as a cited example of this repository's "
                    f"{file.language} conventions."
                ),
                problem=f"Agents need implementation guidance for {domain} work.",
                solution=(
                    f"Follow the module organization, exported symbols, dependency usage, "
                    f"and tests associated with {file.path}."
                ),
                when_to_use=[
                    f"When editing {file.language} {domain} code",
                    f"When matching {repo.project_type or 'project'} conventions",
                ],
                when_not_to_use=["When the target task uses a different framework or language"],
                language=file.language,
                frameworks=repo.detected_frameworks,
                domain=domain,
                project_type=repo.project_type,
                tags=[
                    "implementation-pattern",
                    domain,
                    file.language or "unknown",
                    repo.project_type or "unknown",
                    *(["route"] if file.id in routes_by_file else []),
                    *repo.detected_frameworks,
                ],
                quality_score=quality,
                confidence=0.75,
                source_refs=[ref.id] if ref else [],
                payload={
                    "path": file.path,
                    "symbols": [sym.model_dump() for sym in file_symbols],
                    "key_terms": source_key_terms(file.content or ""),
                    "routes": routes_by_file.get(file.id, []),
                    "doc_context": related_doc_context(file, docs_by_file),
                    "has_related_test": bool(test_evidence),
                    "line_count": file.line_count,
                },
            )
        )
    patterns.extend(
        generate_architecture_patterns(repo, files, dependencies, source_refs, docs_by_file)
    )
    patterns.extend(generate_anti_patterns(repo, files, source_refs))
    return patterns


def generate_architecture_patterns(
    repo: Repository,
    files: list[SourceFile],
    dependencies: list[Dependency],
    source_refs: list[SourceRef],
    docs_by_file: dict[str, dict],
) -> list[KnowledgeObject]:
    if not repo.detected_frameworks and repo.project_type == "unknown":
        return []
    docs_refs = [
        ref.id
        for ref in source_refs
        if ref.file_id in docs_by_file or ref.path.lower() in {"readme.md", "docs/architecture.md"}
    ][:4]
    fallback_refs = [ref.id for ref in source_refs[:2]]
    dep_names = sorted({dep.name for dep in dependencies})[:10]
    return [
        KnowledgeObject(
            id=stable_id(
                "ko",
                repo.id,
                "ArchitecturePattern",
                repo.project_type,
                ",".join(repo.detected_frameworks),
            ),
            type=KnowledgeType.ARCHITECTURE_PATTERN,
            title=f"{repo.name} {repo.project_type or 'project'} architecture pattern",
            summary=(
                f"{repo.name} organizes as a {repo.project_type or 'project'} project with "
                f"{', '.join(repo.detected_frameworks) or 'deterministic local conventions'} and "
                f"{len(files)} indexed files."
            ),
            problem=(
                "Agents need architecture-level constraints before choosing files and "
                "patterns."
            ),
            solution=(
                "Prefer existing framework boundaries, dependency choices, and documented "
                "conventions."
            ),
            when_to_use=["Before larger feature work", "When deciding module boundaries"],
            when_not_to_use=["When working in an unrelated repository"],
            language=repo.primary_language,
            frameworks=repo.detected_frameworks,
            domain="architecture",
            project_type=repo.project_type,
            tags=[
                "architecture-pattern",
                repo.project_type or "unknown",
                *repo.detected_frameworks,
            ],
            quality_score=knowledge_quality(
                repo_quality_score=repo.quality_score,
                citation_quality=0.75 if docs_refs else 0.5,
                test_evidence=1.0 if any(file.is_test for file in files) else 0.0,
                docs_evidence=1.0 if docs_refs else 0.4,
                pattern_reusability=0.6,
                extraction_confidence=0.75,
            ),
            confidence=0.75,
            source_refs=docs_refs or fallback_refs,
            payload={
                "project_type": repo.project_type,
                "frameworks": repo.detected_frameworks,
                "top_dependencies": dep_names,
                "docs": list(docs_by_file.values())[:4],
            },
        )
    ]


def generate_anti_patterns(
    repo: Repository,
    files: list[SourceFile],
    source_refs: list[SourceRef],
) -> list[KnowledgeObject]:
    patterns: list[KnowledgeObject] = []
    refs_by_file = {ref.file_id: ref for ref in source_refs if ref.file_id}
    large_files = [
        file
        for file in files
        if file.line_count >= 500
        and not file.is_test
        and file.language in {"Python", "TypeScript", "JavaScript"}
    ][:4]
    for file in large_files:
        ref = refs_by_file.get(file.id)
        patterns.append(
            KnowledgeObject(
                id=stable_id("ko", repo.id, "AntiPattern", file.path),
                type=KnowledgeType.ANTI_PATTERN,
                title=f"Large module risk in {file.path}",
                summary=(
                    f"{file.path} is {file.line_count} lines; edits should avoid "
                    "increasing module sprawl."
                ),
                problem="Large modules are harder for agents to reason about and test safely.",
                solution=(
                    "Prefer focused changes, extracted helpers, and tests around touched "
                    "behavior."
                ),
                when_to_use=["When editing a large source file"],
                language=file.language,
                frameworks=repo.detected_frameworks,
                domain=infer_domain(file.path, set()),
                project_type=repo.project_type,
                tags=["anti-pattern", "large-module", file.language or "unknown"],
                quality_score=knowledge_quality(
                    repo_quality_score=repo.quality_score,
                    citation_quality=0.85 if ref else 0.4,
                    test_evidence=0.2,
                    docs_evidence=0.2,
                    pattern_reusability=0.45,
                    extraction_confidence=0.8,
                ),
                confidence=0.8,
                source_refs=[ref.id] if ref else [],
                payload={"path": file.path, "line_count": file.line_count},
            )
        )
    return patterns


def generate_testing_patterns(
    repo: Repository,
    files: list[SourceFile],
    source_refs: list[SourceRef],
) -> list[KnowledgeObject]:
    refs_by_file = {ref.file_id: ref for ref in source_refs if ref.file_id}
    test_files = [file for file in files if file.is_test][:8]
    patterns: list[KnowledgeObject] = []
    for file in test_files:
        ref = refs_by_file.get(file.id)
        domain = infer_domain(file.path, set())
        patterns.append(
            KnowledgeObject(
                id=stable_id("ko", repo.id, "TestingPattern", file.path),
                type=KnowledgeType.TESTING_PATTERN,
                title=f"{domain.title()} testing pattern in {file.path}",
                summary=(
                    f"{file.path} shows how this project tests {domain} behavior in "
                    f"{file.language or 'source'} files."
                ),
                problem="Agents need test examples that match project conventions.",
                solution=(
                    "Use the test structure, naming, fixtures, and assertions as local "
                    "guidance."
                ),
                when_to_use=[f"When adding or updating {domain} tests"],
                language=file.language,
                frameworks=repo.detected_frameworks,
                domain=domain,
                project_type=repo.project_type,
                tags=[
                    "testing-pattern",
                    domain,
                    file.language or "unknown",
                    *repo.detected_frameworks,
                ],
                quality_score=knowledge_quality(
                    repo_quality_score=repo.quality_score,
                    citation_quality=0.85 if ref else 0.4,
                    test_evidence=1.0,
                    docs_evidence=0.5,
                    pattern_reusability=0.55,
                    extraction_confidence=0.8,
                ),
                confidence=0.8,
                source_refs=[ref.id] if ref else [],
                payload={"path": file.path, "line_count": file.line_count},
            )
        )
    return patterns


def generate_decision_records(
    repo: Repository,
    source_refs: list[SourceRef],
    docs_by_file: dict[str, dict],
) -> list[KnowledgeObject]:
    refs_by_file = {ref.file_id: ref for ref in source_refs if ref.file_id}
    records: list[KnowledgeObject] = []
    for file_id, doc in docs_by_file.items():
        path = str(doc.get("path", ""))
        if "/adr/" not in f"/{path.lower()}":
            continue
        ref = refs_by_file.get(file_id)
        title = doc.get("top_heading") or path
        records.append(
            KnowledgeObject(
                id=stable_id("ko", repo.id, "DecisionRecord", path),
                type=KnowledgeType.DECISION_RECORD,
                title=title,
                summary=f"{path} records an architecture decision for this repository.",
                problem="Agents need local architecture decisions before changing code.",
                solution="Follow this ADR unless newer project evidence supersedes it.",
                when_to_use=[
                    "Before edits that affect architecture, storage, interfaces, or policy"
                ],
                language=repo.primary_language,
                frameworks=repo.detected_frameworks,
                domain="architecture",
                project_type=repo.project_type,
                tags=["decision-record", "adr", repo.project_type or "unknown"],
                quality_score=knowledge_quality(
                    repo_quality_score=repo.quality_score,
                    citation_quality=0.85 if ref else 0.4,
                    test_evidence=0.2,
                    docs_evidence=1.0,
                    pattern_reusability=0.7,
                    extraction_confidence=0.85,
                ),
                confidence=0.85,
                source_refs=[ref.id] if ref else [],
                payload={"path": path, "headings": doc.get("headings", [])},
            )
        )
    return records


def generate_module_patterns(
    repo: Repository,
    files: list[SourceFile],
    source_refs: list[SourceRef],
) -> list[KnowledgeObject]:
    refs_by_file = {ref.file_id: ref for ref in source_refs if ref.file_id}
    source_files = [
        file
        for file in files
        if not file.is_test and file.language in {"Python", "TypeScript", "JavaScript"}
    ]
    by_dir: dict[str, list[SourceFile]] = {}
    for file in source_files:
        directory = file.path.rsplit("/", 1)[0] if "/" in file.path else ""
        if directory:
            by_dir.setdefault(directory, []).append(file)

    patterns: list[KnowledgeObject] = []
    for directory, examples in sorted(by_dir.items()):
        if len(examples) < 2:
            continue
        refs = [refs_by_file[file.id].id for file in examples if file.id in refs_by_file][:4]
        language = examples[0].language
        patterns.append(
            KnowledgeObject(
                id=stable_id("ko", repo.id, "ModulePattern", directory),
                type=KnowledgeType.MODULE_PATTERN,
                title=f"Module pattern in {directory}",
                summary=(
                    f"{directory} contains {len(examples)} related source files; use it as "
                    "evidence for local module boundaries."
                ),
                problem="Agents need repeated structure before inferring a module convention.",
                solution=f"Keep related {language or 'source'} changes inside {directory}.",
                when_to_use=[f"When editing or adding code near {directory}"],
                language=language,
                frameworks=repo.detected_frameworks,
                domain=infer_domain(directory, set()),
                project_type=repo.project_type,
                tags=["module-pattern", directory, language or "unknown"],
                quality_score=knowledge_quality(
                    repo_quality_score=repo.quality_score,
                    citation_quality=0.85 if refs else 0.4,
                    test_evidence=0.4
                    if any(has_related_test(file, files) for file in examples)
                    else 0.0,
                    docs_evidence=0.4,
                    pattern_reusability=0.8,
                    extraction_confidence=0.8,
                ),
                confidence=0.8,
                source_refs=refs,
                payload={"path": directory, "examples": [file.path for file in examples[:6]]},
            )
        )
    return patterns


def infer_domain(path: str, dependency_names: set[str]) -> str:
    lower = path.lower()
    terms = set(re.findall(r"[a-z0-9]+", lower))
    dependencies = {name.lower() for name in dependency_names}
    database_terms = {"db", "database", "schema", "prisma", "sql", "migration"}
    database_dependencies = {"sqlalchemy", "django", "prisma", "sequelize"}
    checks = {
        "auth": ("auth", "login", "password", "session", "user"),
        "api": ("api", "route", "controller", "endpoint"),
        "ui": ("component", "page", "view", "ui"),
        "config": ("config", "settings"),
        "testing": ("test", "spec"),
    }
    for domain, needles in checks.items():
        if any(needle in terms for needle in needles):
            return domain
    if database_terms & terms or database_dependencies & dependencies:
        return "database"
    return "general"


def source_key_terms(content: str, limit: int = 16) -> list[str]:
    terms: list[str] = []
    import_terms: list[str] = []
    for match in re.finditer(r"^\s*from\s+([\w.]+)\s+import\s+([A-Za-z0-9_,\s]+)", content, re.M):
        import_terms.extend(match.group(1).split("."))
        import_terms.extend(re.findall(r"[A-Za-z][A-Za-z0-9_]*", match.group(2)))
    for match in re.finditer(r"^\s*import\s+([A-Za-z0-9_.,\s]+)", content, re.M):
        import_terms.extend(re.findall(r"[A-Za-z][A-Za-z0-9_]*", match.group(1)))
    terms.extend(humanize_identifier(term) for term in import_terms if term)
    for token in re.findall(r"[A-Za-z][A-Za-z0-9_]*", content):
        if token in {"const", "let", "var", "return", "function", "class", "def", "from", "import"}:
            continue
        terms.append(humanize_identifier(token))
    return list(dict.fromkeys(terms))[:limit]


def humanize_identifier(token: str) -> str:
    split = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", token).replace("_", " ")
    return " ".join(part.lower() if part.isupper() else part for part in split.split())


def pattern_title(file: SourceFile, domain: str) -> str:
    return f"{domain.title()} implementation pattern in {file.path}"


def has_related_test(file: SourceFile, files: list[SourceFile]) -> bool:
    stem = file.path.rsplit(".", 1)[0].lower()
    base = stem.rsplit("/", 1)[-1]
    for candidate in files:
        if not candidate.is_test:
            continue
        lower = candidate.path.lower()
        if base and base in lower:
            return True
    return False


def related_doc_context(file: SourceFile, docs_by_file: dict[str, dict]) -> list[dict]:
    if not docs_by_file:
        return []
    file_parts = set(file.path.lower().replace("-", "_").split("/"))
    matches = []
    for doc in docs_by_file.values():
        headings = " ".join(str(item.get("title", "")).lower() for item in doc.get("headings", []))
        if any(part and part in headings for part in file_parts):
            matches.append(doc)
    return matches[:3]
