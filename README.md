# repo-wiki

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-experimental-orange)

Local-first repository intelligence for coding agents: ingest real codebases, extract cited implementation knowledge, and generate compact context packs for AI coding workflows.

## What is repo-wiki?

repo-wiki is an experimental retrieval and context-pack engine for coding agents. It indexes local or public repositories, extracts deterministic code intelligence, stores cited knowledge in SQLite, and returns compact task-specific context packs through CLI, HTTP, and MCP-compatible interfaces.

The project is a v0.1 research/engineering prototype, not a production system.

## Why it exists

Autonomous coding agents often waste time finding the right files, guessing test locations, or trusting noisy context. repo-wiki explores whether repository-specific, cited context packs can improve those workflows without sending an entire codebase to a model.

## Key features

- Local-first repository ingestion for local paths and public GitHub URLs.
- Python, TypeScript, and JavaScript extraction.
- Source, symbol, route, package, Markdown, test, and dependency metadata.
- SQLite storage with FTS5, graph tables, retrieval traces, feedback, and context packs.
- Deterministic local hash-vector scoring plus lexical retrieval and graph expansion.
- Role-labeled context packs with source citations.
- Stable `context_pack.v1` context-pack schema marker.
- CLI, lightweight HTTP API, optional FastAPI app factory, and MCP-compatible stdio adapter.
- Benchmark reports for retrieval quality, multi-repo retrieval, coding-agent A/B tests, and holdout checks.

## Architecture

```text
Repository
   ↓
Ingestion
   ↓
Source / docs / tests / configs extraction
   ↓
SQLite + FTS + vector scoring + graph tables
   ↓
Hybrid retrieval
   ↓
Role-labeled cited context pack
   ↓
Coding agent / developer
```

See [docs/architecture.md](docs/architecture.md), [ARCHITECTURE.md](ARCHITECTURE.md), and [SAS.md](SAS.md) for more detail.

## Quickstart

```bash
python3 -m pip install -e .
python3 -m repo_wiki.interfaces.cli init
python3 -m repo_wiki.interfaces.cli ingest local .
python3 -m repo_wiki.interfaces.cli query "where should I add validation for a new config option?"
```

If installed as a package, use the script form:

```bash
repo-wiki ingest local ./my-project
repo-wiki retrieve "add parser behavior and tests"
repo-wiki status
repo-wiki doctor
```

## CLI examples

```bash
python3 -m repo_wiki.interfaces.cli bootstrap --list
python3 -m repo_wiki.interfaces.cli ingest github https://github.com/example/project
python3 -m repo_wiki.interfaces.cli knowledge list
python3 -m repo_wiki.interfaces.cli graph neighbors <object_id>
python3 -m repo_wiki.interfaces.cli feedback submit --context-pack <ctx_id> --accepted
python3 -m repo_wiki.interfaces.cli benchmark report --output docs/benchmarks/mvp-results.md
python3 -m repo_wiki.interfaces.cli api serve --host 127.0.0.1 --port 8000
python3 -m repo_wiki.interfaces.cli mcp serve
```

## Verification

```bash
python3 -m unittest tests.test_retrieval_quality -v
python3 -m unittest tests.test_end_to_end -v
python3 -m compileall repo_wiki
python3 -m ruff check .
```

## Benchmark results

Benchmarks are documented under [docs/benchmarks/](docs/benchmarks/), including the fixture-backed retrieval suite at `docs/benchmarks/retrieval-quality.md`. Claims here are intentionally limited to the runs recorded in the repository.

Early benchmarks show that retrieval v0.1 can find useful implementation context across multiple repositories, including a 5-repository blind holdout with 4 pass / 1 partial / 0 fail.

retrieval v0.1 blind holdout:

- 5 new repositories.
- 4 pass, 1 partial, 0 fail.
- Average score: 7.8/10.
- Top-10 expected hits: 12/15.
- Citation coverage: 100%.

Initial coding-agent A/B results were mixed; repo-wiki did not yet consistently improve coding outcomes. The project currently treats retrieval quality and coding-agent usefulness as separate evaluation targets.

## Example use cases

- Ask a coding agent for a cited context pack before editing an unfamiliar repo.
- Find likely source, runtime, test, and convention files for a bounded task.
- Compare retrieval behavior across repositories before running implementation benchmarks.
- Inspect repository structure through CLI, HTTP, or MCP-compatible tooling.

## Current limitations

- v0.1 retrieval is heuristic and still fails on some generic or ambiguous tasks.
- TypeScript/JavaScript parsing is lightweight compared with compiler-grade analysis.
- Behavioral constraint extraction catches simple local guards, not full program semantics.
- Coding-agent A/B results are early and mixed.
- Benchmarks are local and bounded; they are not proof of production readiness.
- No security review has been completed for production deployment.

## Roadmap

See [docs/roadmap.md](docs/roadmap.md).

Near-term work focuses on retrieval-only regression checks, better source-to-test pairing, improved context-to-action planning, stronger MCP integration, and broader coding-agent A/B evaluation.

## Project status

repo-wiki is an experimental v0.1 portfolio project. It is useful for demonstrating local-first repository intelligence, retrieval engineering, cited context packs, and benchmark discipline. It should not be presented as a proven production coding-agent system.

## License

MIT. See [LICENSE](LICENSE).
