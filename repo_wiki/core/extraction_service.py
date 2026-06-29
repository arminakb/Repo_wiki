from __future__ import annotations

import subprocess
from pathlib import Path
from time import perf_counter

from repo_wiki.compile.dedupe import dedupe_knowledge
from repo_wiki.compile.generator import (
    generate_decision_records,
    generate_implementation_patterns,
    generate_module_patterns,
    generate_project_profile,
    generate_testing_patterns,
)
from repo_wiki.compile.scoring import repository_quality
from repo_wiki.config import Settings
from repo_wiki.domain.enums import SourceType
from repo_wiki.domain.ids import content_hash, stable_id
from repo_wiki.domain.models import (
    ExtractionResult,
    Repository,
    RepositorySnapshot,
    SourceRef,
)
from repo_wiki.extract.file_tree import (
    discover_source_files,
    is_data_dir_path,
    leaves_root,
    language_distribution,
    primary_language,
)
from repo_wiki.extract.markdown import extract_markdown_document
from repo_wiki.extract.package_manifests import (
    detect_frameworks,
    detect_project_type,
    extract_dependencies,
)
from repo_wiki.extract.python_ast import (
    extract_python_calls,
    extract_python_imports,
    extract_python_symbols,
)
from repo_wiki.extract.routes import extract_routes
from repo_wiki.extract.typescript import extract_ts_imports, extract_ts_symbols
from repo_wiki.graph.service import GraphBuilder
from repo_wiki.ingest.filters import (
    is_text_candidate,
    matches_include_patterns,
    should_skip_path,
)
from repo_wiki.ingest.license_detector import (
    detect_license,
    snippet_allowed,
    validate_license_policy,
)


class ExtractionService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.graph_builder = GraphBuilder()

    def extract_local(
        self,
        root: Path,
        *,
        source_type: SourceType = SourceType.LOCAL_REPO,
        url: str | None = None,
        owner: str | None = None,
        name: str | None = None,
        branch: str | None = None,
        visibility: str = "local",
        stars: int | None = None,
        license_policy: str | None = None,
        include_patterns: tuple[str, ...] = (),
        exclude_patterns: tuple[str, ...] = (),
    ) -> ExtractionResult:
        started = perf_counter()
        repo_name = name or root.name
        policy = license_policy or self.settings.license_policy
        validate_license_policy(policy)
        repo_id = stable_id("repo", source_type, url or str(root))
        commit_sha = git_commit_sha(root)
        content_digest = tree_hash(
            root,
            self.settings,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        )
        snapshot_id = stable_id("snap", repo_id, commit_sha or "", content_digest)
        license_name = detect_license(root)

        files = discover_source_files(
            root,
            snapshot_id,
            self.settings,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
        )
        dependencies = extract_dependencies(files)
        frameworks = detect_frameworks(dependencies, files)
        languages = language_distribution(files)
        repo = Repository(
            id=repo_id,
            source_type=source_type,
            owner=owner,
            name=repo_name,
            url=url,
            local_path=str(root),
            default_branch=branch,
            visibility=visibility,
            license=license_name,
            primary_language=primary_language(files),
            detected_languages=languages,
            detected_frameworks=frameworks,
            project_type=detect_project_type(frameworks, files),
            stars=stars,
        )

        symbols = []
        imports_by_file: dict[str, list[str]] = {}
        calls_by_file: dict[str, list[dict]] = {}
        routes_by_file: dict[str, list[dict]] = {}
        docs_by_file: dict[str, dict] = {}
        for file in files:
            file_symbols = [*extract_python_symbols(file), *extract_ts_symbols(file)]
            symbols.extend(file_symbols)
            imports = [*extract_python_imports(file), *extract_ts_imports(file)]
            if imports:
                imports_by_file[file.id] = imports
            calls = extract_python_calls(file)
            if calls:
                calls_by_file[file.id] = calls
            routes = extract_routes(file, file_symbols)
            if routes:
                routes_by_file[file.id] = routes
            doc = extract_markdown_document(file)
            if doc:
                docs_by_file[file.id] = doc
        repo.quality_score = repository_quality(repo, files, symbols)

        snapshot = RepositorySnapshot(
            id=snapshot_id,
            repo_id=repo.id,
            commit_sha=commit_sha,
            branch=branch,
            file_count=len(files),
            line_count=sum(file.line_count for file in files),
            content_hash=content_digest,
            status="completed",
        )

        allow_snippets = snippet_allowed(license_name, policy)
        source_refs = [
            SourceRef(
                id=stable_id("ref", repo.id, snapshot.id, file.path),
                repo_id=repo.id,
                snapshot_id=snapshot.id,
                file_id=file.id,
                path=file.path,
                start_line=1,
                end_line=file.line_count,
                license=license_name,
                snippet_allowed=allow_snippets,
            )
            for file in files
        ]
        refs_by_file = {ref.file_id: ref for ref in source_refs if ref.file_id}
        source_refs.extend(
            SourceRef(
                id=stable_id(
                    "ref",
                    repo.id,
                    snapshot.id,
                    file_id,
                    start_line,
                    end_line,
                ),
                repo_id=repo.id,
                snapshot_id=snapshot.id,
                file_id=file_id,
                path=refs_by_file[file_id].path,
                start_line=start_line,
                end_line=end_line,
                license=license_name,
                snippet_allowed=allow_snippets,
            )
            for file_id, (start_line, end_line) in symbol_spans_by_file(symbols).items()
            if file_id in refs_by_file
        )

        knowledge_objects = [
            generate_project_profile(repo, files, symbols, dependencies, source_refs),
            *generate_implementation_patterns(
                repo,
                files,
                symbols,
                dependencies,
                source_refs,
                routes_by_file=routes_by_file,
                docs_by_file=docs_by_file,
            ),
            *generate_decision_records(repo, source_refs, docs_by_file),
            *generate_module_patterns(repo, files, source_refs),
            *generate_testing_patterns(repo, files, source_refs),
        ]
        knowledge_objects = dedupe_knowledge(knowledge_objects)
        graph_nodes, graph_edges = self.graph_builder.build(
            repo,
            snapshot,
            files,
            symbols,
            dependencies,
            knowledge_objects,
            imports_by_file=imports_by_file,
            calls_by_file=calls_by_file,
            routes_by_file=routes_by_file,
        )
        metrics = {
            "files": len(files),
            "symbols": len(symbols),
            "dependencies": len(dependencies),
            "source_refs": len(source_refs),
            "knowledge_objects": len(knowledge_objects),
            "graph_nodes": len(graph_nodes),
            "graph_edges": len(graph_edges),
            "routes": sum(len(routes) for routes in routes_by_file.values()),
            "markdown_documents": len(docs_by_file),
            "duration_ms": int((perf_counter() - started) * 1000),
        }
        events = [
            {"stage": "file_discovery", "count": len(files)},
            {"stage": "symbol_extraction", "count": len(symbols)},
            {"stage": "dependency_extraction", "count": len(dependencies)},
            {"stage": "knowledge_compilation", "count": len(knowledge_objects)},
            {"stage": "graph_build", "nodes": len(graph_nodes), "edges": len(graph_edges)},
        ]

        return ExtractionResult(
            repository=repo,
            snapshot=snapshot,
            files=files,
            symbols=symbols,
            dependencies=dependencies,
            source_refs=source_refs,
            knowledge_objects=knowledge_objects,
            graph_nodes=graph_nodes,
            graph_edges=graph_edges,
            extraction_events=events,
            metrics=metrics,
        )


def git_commit_sha(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return result.stdout.strip() or None


def symbol_spans_by_file(symbols: list) -> dict[str, tuple[int, int]]:
    spans: dict[str, tuple[int, int]] = {}
    for symbol in symbols:
        if not symbol.start_line or not symbol.end_line:
            continue
        start, end = spans.get(symbol.file_id, (symbol.start_line, symbol.end_line))
        spans[symbol.file_id] = (min(start, symbol.start_line), max(end, symbol.end_line))
    return spans


def tree_hash(
    root: Path,
    settings: Settings | None = None,
    *,
    include_patterns: tuple[str, ...] = (),
    exclude_patterns: tuple[str, ...] = (),
) -> str:
    parts: list[bytes] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if settings and (
            leaves_root(path, root)
            or is_data_dir_path(path, root, settings)
            or should_skip_path(
                path,
                root,
                excludes=settings.default_excludes,
                exclude_patterns=exclude_patterns,
            )
            or not matches_include_patterns(path, root, include_patterns)
            or not is_text_candidate(path)
        ):
            continue
        if ".git" in path.parts:
            continue
        try:
            stat = path.stat()
            if settings and stat.st_size > settings.max_file_size_bytes:
                continue
            relative = path.relative_to(root).as_posix().encode("utf-8")
            parts.append(relative + b"\0" + path.read_bytes())
        except OSError:
            continue
    return content_hash(b"\0".join(parts))
