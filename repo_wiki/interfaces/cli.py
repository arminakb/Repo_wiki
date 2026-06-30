from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from pathlib import Path

from repo_wiki.benchmarks.report import build_benchmark_report, write_benchmark_report
from repo_wiki.bootstrap.loader import list_packs, load_pack
from repo_wiki.config import Settings
from repo_wiki.core.ingestion_service import IngestionService
from repo_wiki.core.metrics_service import MetricsService
from repo_wiki.core.reflexion_service import ReflexionService
from repo_wiki.core.retrieval_service import RetrievalService
from repo_wiki.discovery.github_client import discover_repositories
from repo_wiki.inspector.detector import LocalProjectInspector
from repo_wiki.live.engine import LiveResearchEngine
from repo_wiki.retrieval.quality_gate import evaluate_context_pack
from repo_wiki.storage.sqlite import SQLiteStore

PROFILE_TOKENS = {
    "local_small": 2000,
    "local_medium": 4000,
    "local_large": 8000,
    "frontier": 16000,
}


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = Settings.from_env(Path.cwd())
    settings.ensure_dirs()
    store = SQLiteStore(settings.sqlite_path)

    store.initialize()

    try:
        if args.command in {None, "init"}:
            return handle_init(settings, store)
        if args.command == "quickstart":
            return handle_quickstart(args, settings, store)
        if args.command == "discover":
            return handle_discover(args, settings, store)
        if args.command == "bootstrap":
            return handle_bootstrap(args, settings, store)
        if args.command == "status":
            return handle_status(settings, store)
        if args.command == "doctor":
            return handle_doctor(settings, store)
        if args.command == "ingest":
            return handle_ingest(args, settings, store)
        if args.command == "extract":
            return handle_extract(args, store)
        if args.command == "compile":
            return handle_compile(args, store)
        if args.command in {"retrieve", "query"}:
            return handle_retrieve(args, settings, store)
        if args.command == "knowledge":
            return handle_knowledge(args, store)
        if args.command == "graph":
            return handle_graph(args, store)
        if args.command == "repositories":
            return handle_repositories(args, store)
        if args.command == "feedback":
            return handle_feedback(args, store)
        if args.command == "metrics":
            print_json(MetricsService(store).metrics())
            return 0
        if args.command == "backup":
            return handle_backup(args, store)
        if args.command == "benchmark":
            return handle_benchmark(args, store)
        if args.command == "api":
            from repo_wiki.interfaces.http import serve

            serve(host=args.host, port=args.port, store=store)
            return 0
        if args.command == "mcp":
            from repo_wiki.interfaces.mcp import run_stdio_server

            run_stdio_server(store)
            return 0
    except Exception as exc:  # CLI boundary converts expected and unexpected errors.
        print(f"error: {exc}", file=sys.stderr)
        return 1

    parser.print_help()
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="repo-wiki")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="Initialize local storage")

    quickstart = sub.add_parser("quickstart", help="Discover, ingest, and verify a topic")
    quickstart.add_argument("--for", dest="topic", required=True)
    quickstart.add_argument("--limit", type=int, default=10)
    quickstart.add_argument("--min-stars", type=int, default=200)

    discover = sub.add_parser("discover", help="Find public GitHub repositories")
    discover.add_argument("--topic", required=True)
    discover.add_argument("--language")
    discover.add_argument("--min-stars", type=int, default=200)
    discover.add_argument("--license", default="permissive")
    discover.add_argument("--limit", type=int, default=10)
    discover.add_argument("--auto-ingest", action="store_true")

    bootstrap = sub.add_parser("bootstrap", help="Ingest a curated starter pack")
    bootstrap.add_argument("--pack")
    bootstrap.add_argument("--list", action="store_true")

    ingest = sub.add_parser("ingest", help="Ingest repositories")
    ingest_sub = ingest.add_subparsers(dest="ingest_command", required=True)
    ingest_local = ingest_sub.add_parser("local", help="Index a local repository")
    ingest_local.add_argument("path")
    ingest_local.add_argument("--license-policy", default=None)
    ingest_local.add_argument("--include", action="append", default=[])
    ingest_local.add_argument("--exclude", action="append", default=[])
    ingest_github = ingest_sub.add_parser("github", help="Index a public GitHub repository")
    ingest_github.add_argument("url")
    ingest_github.add_argument("--branch", default=None)
    ingest_github.add_argument("--license-policy", default=None)
    ingest_github.add_argument("--include", action="append", default=[])
    ingest_github.add_argument("--exclude", action="append", default=[])
    ingest_status = ingest_sub.add_parser("status", help="Show synchronous ingest job status")
    ingest_status.add_argument("id")

    extract = sub.add_parser("extract", help="Show extracted repository snapshot status")
    extract.add_argument("repo_id")

    compile_cmd = sub.add_parser("compile", help="Show compiled knowledge status")
    compile_cmd.add_argument("repo_id")
    compile_cmd.add_argument("--llm-provider")
    compile_cmd.add_argument("--no-llm", action="store_true")

    retrieve = sub.add_parser("retrieve", help="Retrieve an agent context pack")
    retrieve.add_argument("task")
    retrieve.add_argument("--language")
    retrieve.add_argument("--framework")
    retrieve.add_argument("--project-type")
    retrieve.add_argument("--domain")
    retrieve.add_argument("--repo")
    retrieve.add_argument("--max-tokens", type=int, default=4000)
    retrieve.add_argument("--license-policy")
    retrieve.add_argument("--limit", type=int, default=8)
    retrieve.add_argument("--format", choices=["json", "markdown"], default="markdown")

    query = sub.add_parser("query", help="Retrieve an agent context pack")
    query.add_argument("task")
    query.add_argument("--language")
    query.add_argument("--framework")
    query.add_argument("--project-type")
    query.add_argument("--domain")
    query.add_argument("--repo")
    query.add_argument("--max-tokens", type=int)
    query.add_argument("--profile", choices=sorted(PROFILE_TOKENS), default="local_medium")
    query.add_argument("--license-policy")
    query.add_argument("--limit", type=int, default=8)
    query.add_argument("--format", choices=["json", "markdown"], default="markdown")
    query.add_argument("--live", action="store_true")
    query.add_argument("--explain", action="store_true")

    sub.add_parser("status", help="Show knowledge base status")
    sub.add_parser("doctor", help="Check local setup")

    knowledge = sub.add_parser("knowledge", help="Inspect knowledge objects")
    knowledge_sub = knowledge.add_subparsers(dest="knowledge_command", required=True)
    knowledge_list = knowledge_sub.add_parser("list")
    knowledge_list.add_argument("--type")
    knowledge_list.add_argument("--language")
    knowledge_list.add_argument("--framework")
    knowledge_list.add_argument("--limit", type=int, default=20)
    knowledge_show = knowledge_sub.add_parser("show")
    knowledge_show.add_argument("id")

    graph = sub.add_parser("graph", help="Inspect graph relationships")
    graph_sub = graph.add_subparsers(dest="graph_command", required=True)
    neighbors = graph_sub.add_parser("neighbors")
    neighbors.add_argument("object_id")
    neighbors.add_argument("--edge-type")
    neighbors.add_argument("--limit", type=int, default=20)
    graph_export = graph_sub.add_parser("export")
    graph_export.add_argument("--format", choices=["mermaid"], default="mermaid")
    graph_export.add_argument("--output", required=True)
    graph_export.add_argument("--limit", type=int, default=200)

    repositories = sub.add_parser("repositories", help="Inspect indexed repositories")
    repositories_sub = repositories.add_subparsers(dest="repositories_command", required=True)
    repositories_list = repositories_sub.add_parser("list")
    repositories_list.add_argument("--limit", type=int, default=20)
    repositories_show = repositories_sub.add_parser("show")
    repositories_show.add_argument("id")

    feedback = sub.add_parser("feedback", help="Submit or inspect feedback")
    feedback_sub = feedback.add_subparsers(dest="feedback_command", required=True)
    submit = feedback_sub.add_parser("submit")
    submit.add_argument("--context-pack")
    submit.add_argument("--accepted", action="store_true")
    submit.add_argument("--tests-passed", action="store_true")
    submit.add_argument("--lint-passed", action="store_true")
    submit.add_argument("--build-passed", action="store_true")
    submit.add_argument("--merged", action="store_true")
    submit.add_argument("--reviewer-approved", action="store_true")
    submit.add_argument("--rollback", action="store_true")
    submit.add_argument("--incident", action="store_true")
    submit.add_argument("--rating", type=int)
    submit.add_argument("--notes")
    feedback_list = feedback_sub.add_parser("list")
    feedback_list.add_argument("--status", default="pending")
    feedback_list.add_argument("--limit", type=int, default=20)
    promote = feedback_sub.add_parser("promote")
    promote.add_argument("id")
    promote.add_argument("--reason")
    reject = feedback_sub.add_parser("reject")
    reject.add_argument("id")
    reject.add_argument("--reason")

    sub.add_parser("metrics", help="Show project metrics")

    backup = sub.add_parser("backup", help="Create or restore local SQLite backups")
    backup_sub = backup.add_subparsers(dest="backup_command", required=True)
    backup_create = backup_sub.add_parser("create")
    backup_create.add_argument("path")
    backup_restore = backup_sub.add_parser("restore")
    backup_restore.add_argument("path")

    benchmark = sub.add_parser("benchmark", help="Generate local benchmark reports")
    benchmark_sub = benchmark.add_subparsers(dest="benchmark_command", required=True)
    benchmark_run = benchmark_sub.add_parser("run")
    benchmark_run.add_argument("--suite", default="mvp", choices=["mvp"])
    benchmark_ingest = benchmark_sub.add_parser("ingest-list")
    benchmark_ingest.add_argument("path")
    benchmark_ingest.add_argument("--branch", default=None)
    benchmark_ingest.add_argument("--license-policy", default=None)
    benchmark_report = benchmark_sub.add_parser("report")
    benchmark_report.add_argument("--output", default="reports/mvp-results.md")

    api = sub.add_parser("api", help="Run the lightweight HTTP API")
    api_sub = api.add_subparsers(dest="api_command", required=True)
    serve = api_sub.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)

    mcp = sub.add_parser("mcp", help="Run the MCP stdio adapter")
    mcp_sub = mcp.add_subparsers(dest="mcp_command", required=True)
    mcp_sub.add_parser("serve")

    return parser


def handle_init(settings: Settings, store: SQLiteStore) -> int:
    print("Welcome to repo-wiki.")
    print(f"Storage ready: {settings.data_dir}")
    print('\nNext step:  repo-wiki quickstart --for "fastapi"')
    return 0


def handle_quickstart(
    args: argparse.Namespace, settings: Settings, store: SQLiteStore
) -> int:
    topic = args.topic
    print(f"Searching GitHub for top {topic} repos...")
    repos = discover_repositories(topic, min_stars=args.min_stars, limit=args.limit)
    if not repos:
        raise RuntimeError(f"no repositories found for topic: {topic}")
    print(f"found {len(repos)} candidates")
    print_repo_table(repos)

    service = IngestionService(settings, store)
    indexed = []
    for number, repo in enumerate(repos, start=1):
        print(f"Indexing {repo.full_name} ({number}/{len(repos)})...")
        result = service.ingest_github(repo.url)
        indexed.append(result)

    query = verification_query(topic)
    print(f"Running verification query: {query}")
    retrieved = RetrievalService(store).retrieve(query, framework=topic_to_framework(topic))
    quality = evaluate_context_pack(retrieved["context_pack"])
    print_quickstart_summary(indexed, quality)
    print(f'\nNext step:  repo-wiki query "{query}"')
    return 0


def handle_discover(
    args: argparse.Namespace, settings: Settings, store: SQLiteStore
) -> int:
    repos = discover_repositories(
        args.topic,
        language=args.language,
        min_stars=args.min_stars,
        license_policy=args.license,
        limit=args.limit,
    )
    print_repo_table(repos)
    if args.auto_ingest:
        service = IngestionService(settings, store)
        for number, repo in enumerate(repos, start=1):
            print(f"Indexing {repo.full_name} ({number}/{len(repos)})...")
            service.ingest_github(repo.url)
        print('\nNext step:  repo-wiki query "how should I use this stack?"')
    else:
        print('\nNext step:  repo-wiki discover --topic "' + args.topic + '" --auto-ingest')
    return 0


def handle_bootstrap(
    args: argparse.Namespace, settings: Settings, store: SQLiteStore
) -> int:
    if args.list:
        packs = list_packs()
        for pack in packs:
            print(f"{pack.name}\t{pack.language or '-'}\t{len(pack.repos)} repos\t{pack.description}")
        print("\nNext step:  repo-wiki bootstrap --pack python-web-apis")
        return 0
    if not args.pack:
        raise ValueError("--pack is required unless --list is used")

    pack = load_pack(args.pack)
    service = IngestionService(settings, store)
    print(f"Bootstrapping {pack.name}: {pack.description}")
    for number, repo in enumerate(pack.repos, start=1):
        print(f"Indexing {repo.url} ({number}/{len(pack.repos)})...")
        service.ingest_github(repo.url)
    print(f"\nKnowledge base ready from pack: {pack.name}")
    print('\nNext step:  repo-wiki query "how should I use this stack?"')
    return 0


def handle_status(settings: Settings, store: SQLiteStore) -> int:
    metrics = MetricsService(store).metrics()
    db_size = settings.sqlite_path.stat().st_size if settings.sqlite_path.exists() else 0
    print(f"Knowledge base: {settings.sqlite_path} ({db_size} bytes)")
    print("")
    for key in (
        "indexed_repositories",
        "knowledge_objects",
        "graph_nodes",
        "graph_edges",
        "staged_knowledge",
        "context_packs",
    ):
        print(f"{key.replace('_', ' ').title():24} {metrics.get(key, 0)}")
    languages = ", ".join(metrics.get("supported_languages", [])) or "none indexed yet"
    print(f"{'Supported Languages':24} {languages}")
    print("\nNext step:  repo-wiki doctor")
    return 0


def handle_doctor(settings: Settings, store: SQLiteStore) -> int:
    checks = []
    checks.append(("git on PATH", shutil.which("git") is not None, "Install git and retry."))
    checks.append(("config load", True, "Fix repo-wiki.toml syntax."))
    try:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        probe = settings.data_dir / ".write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        writable = True
    except OSError:
        writable = False
    checks.append(("storage path writable", writable, f"Fix permissions for {settings.data_dir}."))

    try:
        integrity = store.integrity_check()
        db_ok = integrity == "ok"
    except sqlite3.Error:
        db_ok = False
    checks.append(("SQLite integrity", db_ok, f"Reinitialize or inspect {settings.sqlite_path}."))
    checks.append(("schema version", bool(store.schema_version()), "Run repo-wiki init."))
    checks.append(
        (
            "optional FastAPI",
            optional_dependency("fastapi"),
            "Install fastapi only if you need the FastAPI app factory.",
        )
    )

    failed = False
    for name, ok, fix in checks:
        print(f"{'OK' if ok else 'FAIL'}  {name}")
        if not ok:
            failed = True
            print(f"      fix: {fix}")
    print("\nNext step:  repo-wiki status")
    return 1 if failed else 0


def optional_dependency(module_name: str) -> bool:
    try:
        __import__(module_name)
    except ImportError:
        return True
    return True


def handle_ingest(args: argparse.Namespace, settings: Settings, store: SQLiteStore) -> int:
    if args.ingest_command == "status":
        print_json({"job_id": args.id, "status": "completed", "mode": "synchronous"})
        return 0
    service = IngestionService(settings, store)
    if args.ingest_command == "local":
        result = service.ingest_local(
            args.path,
            license_policy=args.license_policy,
            include=args.include,
            exclude=args.exclude,
        )
    else:
        result = service.ingest_github(
            args.url,
            branch=args.branch,
            license_policy=args.license_policy,
            include=args.include,
            exclude=args.exclude,
        )
    print_json(
        {
            "repo_id": result.repository.id,
            "snapshot_id": result.snapshot.id,
            "files": len(result.files),
            "symbols": len(result.symbols),
            "dependencies": len(result.dependencies),
            "knowledge_objects": len(result.knowledge_objects),
            "graph_nodes": len(result.graph_nodes),
            "graph_edges": len(result.graph_edges),
            "extraction_events": result.extraction_events,
            "metrics": result.metrics,
        }
    )
    return 0


def handle_extract(args: argparse.Namespace, store: SQLiteStore) -> int:
    repository = store.get_repository(args.repo_id)
    if repository is None:
        print(f"repository not found: {args.repo_id}", file=sys.stderr)
        return 1
    snapshots = repository.get("snapshots", [])
    print_json(
        {
            "repo_id": args.repo_id,
            "snapshot_id": snapshots[0]["id"] if snapshots else None,
            "status": "completed" if snapshots else "not_indexed",
        }
    )
    return 0


def handle_compile(args: argparse.Namespace, store: SQLiteStore) -> int:
    repository = store.get_repository(args.repo_id)
    if repository is None:
        print(f"repository not found: {args.repo_id}", file=sys.stderr)
        return 1
    objects = store.list_knowledge(limit=1000)
    print_json(
        {
            "repo_id": args.repo_id,
            "knowledge_objects": len(objects),
            "llm_provider": None if args.no_llm else args.llm_provider,
            "status": "completed",
        }
    )
    return 0


def handle_retrieve(args: argparse.Namespace, settings: Settings, store: SQLiteStore) -> int:
    max_tokens = args.max_tokens or PROFILE_TOKENS.get(
        getattr(args, "profile", ""),
        settings.default_max_tokens,
    )
    json_output = args.format == "json"
    language = args.language
    framework = args.framework
    if getattr(args, "command", "") == "query" and (language is None or framework is None):
        stack = LocalProjectInspector().detect_stack(Path.cwd())
        language = language or (stack.languages[0] if stack.languages else None)
        framework = framework or (stack.frameworks[0] if stack.frameworks else None)
    if getattr(args, "command", "") == "query" and not json_output:
        print(f"Using profile: {args.profile} (max {max_tokens:,} tokens)")
    result = RetrievalService(store).retrieve(
        args.task,
        language=language,
        framework=framework,
        project_type=args.project_type,
        domain=args.domain,
        repo=args.repo,
        max_tokens=max_tokens,
        limit=args.limit,
        license_policy=args.license_policy,
    )
    quality = evaluate_context_pack(result["context_pack"])
    if getattr(args, "live", False) and not quality["passed"]:
        settings = Settings.from_env(Path.cwd())
        result = LiveResearchEngine(settings, store).search(
            args.task,
            limit=args.limit,
            max_tokens=max_tokens,
        )
        quality = evaluate_context_pack(result["context_pack"])
    if json_output:
        payload = {**result, "quality": quality}
        print_json(payload)
    else:
        if getattr(args, "command", "") == "query":
            estimated = len(result["markdown"].split())
            fit = "fits" if estimated <= max_tokens else "over budget"
            print(f"Estimated context pack: ~{estimated:,} tokens  {fit}")
            if getattr(args, "explain", False):
                print(f"Quality gate: {quality['recommendation']} ({quality['score']})")
            print("")
        print(result["markdown"], end="")
        if getattr(args, "command", "") == "query":
            print('\nNext step:  repo-wiki feedback submit --context-pack '
                  f"{result['context_pack']['id']} --accepted")
    return 0


def handle_knowledge(args: argparse.Namespace, store: SQLiteStore) -> int:
    if args.knowledge_command == "list":
        objects = store.list_knowledge(
            type=args.type,
            language=args.language,
            framework=args.framework,
            limit=args.limit,
        )
        print_json([obj.model_dump() for obj in objects])
        return 0
    obj = store.get_knowledge(args.id)
    if obj is None:
        print(f"knowledge object not found: {args.id}", file=sys.stderr)
        return 1
    print_json(obj.model_dump())
    return 0


def handle_graph(args: argparse.Namespace, store: SQLiteStore) -> int:
    if args.graph_command == "export":
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(store.export_graph_mermaid(limit=args.limit), encoding="utf-8")
        print_json({"output": str(output), "format": args.format})
        return 0
    print_json(
        store.graph_neighbors(
            args.object_id, edge_type=args.edge_type, limit=args.limit
        )
    )
    return 0


def handle_repositories(args: argparse.Namespace, store: SQLiteStore) -> int:
    if args.repositories_command == "list":
        repositories = store.list_repositories(limit=args.limit)
        print_json([repo.model_dump() for repo in repositories])
        return 0
    repository = store.get_repository(args.id)
    if repository is None:
        print(f"repository not found: {args.id}", file=sys.stderr)
        return 1
    print_json(repository)
    return 0


def handle_feedback(args: argparse.Namespace, store: SQLiteStore) -> int:
    service = ReflexionService(store)
    if args.feedback_command == "submit":
        feedback, staged = service.submit_feedback(
            context_pack_id=args.context_pack,
            accepted=args.accepted,
            rating=args.rating,
            tests_passed=args.tests_passed,
            lint_passed=args.lint_passed,
            build_passed=args.build_passed,
            merged=args.merged,
            reviewer_approved=args.reviewer_approved,
            rollback=args.rollback,
            incident=args.incident,
            notes=args.notes,
        )
        print_json({"feedback": feedback.model_dump(), "staged": staged.model_dump()})
        return 0
    if args.feedback_command == "promote":
        print_json(service.promote_staged(args.id, reason=args.reason))
        return 0
    if args.feedback_command == "reject":
        print_json(service.reject_staged(args.id, reason=args.reason))
        return 0
    print_json(service.list_staged(status=args.status, limit=args.limit))
    return 0


def handle_backup(args: argparse.Namespace, store: SQLiteStore) -> int:
    path = Path(args.path)
    if args.backup_command == "create":
        output = store.backup_to(path)
        print_json({"backup": str(output), "status": "created"})
        return 0
    if args.backup_command == "restore":
        store.restore_from(path)
        print_json({"backup": str(path), "status": "restored"})
        return 0
    return 1


def handle_benchmark(args: argparse.Namespace, store: SQLiteStore) -> int:
    if args.benchmark_command == "run":
        _, metrics = build_benchmark_report(store)
        print_json({"suite": args.suite, "metrics": metrics})
        return 0
    if args.benchmark_command == "ingest-list":
        settings = Settings.from_env(Path.cwd())
        service = IngestionService(settings, store)
        urls = [
            line.strip()
            for line in Path(args.path).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        results = []
        for url in urls:
            result = service.ingest_github(
                url,
                branch=args.branch,
                license_policy=args.license_policy,
            )
            results.append(
                {
                    "url": url,
                    "repo_id": result.repository.id,
                    "snapshot_id": result.snapshot.id,
                    "files": len(result.files),
                    "knowledge_objects": len(result.knowledge_objects),
                }
            )
        print_json({"repositories": len(results), "results": results})
        return 0
    if args.benchmark_command == "report":
        output = Path(args.output)
        metrics = write_benchmark_report(store, output)
        print_json({"output": str(output), "metrics": metrics})
        return 0
    return 1


def print_json(value: object) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, default=str))


def print_repo_table(repos: list) -> None:
    if not repos:
        print("No repositories found.")
        return
    print("Name\tStars\tLicense\tLanguage\tURL")
    for repo in repos:
        print(
            f"{repo.full_name}\t{repo.stars}\t{repo.license or '-'}\t"
            f"{repo.language or '-'}\t{repo.url}"
        )


def topic_to_framework(topic: str) -> str | None:
    clean = topic.lower()
    if "fastapi" in clean:
        return "FastAPI"
    if "next" in clean:
        return "Next.js"
    if "django" in clean:
        return "Django"
    return None


def verification_query(topic: str) -> str:
    if "fastapi" in topic.lower():
        return "how to add dependency injection to FastAPI"
    if "next" in topic.lower():
        return "how to add an authenticated Next.js route"
    return f"how to build with {topic}"


def print_quickstart_summary(indexed: list, quality: dict) -> None:
    knowledge_objects = sum(len(result.knowledge_objects) for result in indexed)
    graph_edges = sum(len(result.graph_edges) for result in indexed)
    repo_names = ", ".join(result.repository.name for result in indexed[:3])
    if len(indexed) > 3:
        repo_names += ", ..."
    print("\nKnowledge base ready.")
    print("")
    print(f"  Indexed repos     {len(indexed)}   {repo_names}")
    print(f"  Knowledge objects {knowledge_objects}")
    print(f"  Graph edges       {graph_edges}")
    print(f"  Verification      {quality['recommendation']} (score {quality['score']})")


if __name__ == "__main__":
    raise SystemExit(main())
