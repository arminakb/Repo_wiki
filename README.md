# repo-wiki

repo-wiki is a local-first repository intelligence tool that helps AI coding agents understand real codebases before editing them.

Status: experimental v0.1 / portfolio project.

## What It Does

repo-wiki indexes a local repository or public GitHub repository, extracts deterministic code and documentation signals, stores them in SQLite, and retrieves cited context packs for coding tasks.

It is designed to answer practical questions before an edit:

- Which files are likely edit targets?
- Which tests should be inspected or updated?
- Which runtime paths, conventions, and risks are nearby?
- What citations support the recommendation?

## Why It Matters

AI coding agents often fail because they start editing with shallow repository context. repo-wiki explores a smaller, local-first alternative to sending an entire codebase to a model: retrieve compact, cited, task-specific context first, then let the agent or developer inspect the evidence.

## Key Features

- Local and public GitHub repository ingestion.
- Python, TypeScript, JavaScript, Markdown, package manifest, route, config, and test extraction.
- SQLite storage with FTS-backed search, graph tables, retrieval traces, feedback, and context packs.
- Hybrid retrieval using lexical search, deterministic local vector scoring, metadata filters, graph expansion, source/test pairing, and reranking.
- Role-labeled context packs with file-level citations.
- CLI, lightweight HTTP API, optional FastAPI app factory, and MCP-compatible stdio adapter.
- Retrieval quality tests and benchmark summaries.

## Architecture

```text
Repository
  -> ingestion
  -> source / docs / tests / config extraction
  -> SQLite + FTS + local vector scoring + graph tables
  -> hybrid retrieval and reranking
  -> cited context_pack.v1
  -> coding agent or developer
```

repo-wiki is graph-enhanced, not graph-only. Graph relationships are used as one retrieval signal alongside lexical, metadata, vector, source/test, and citation signals.

See [docs/architecture.md](docs/architecture.md) for more detail.

## Quickstart

```bash
git clone https://github.com/arminakb/Repo_wiki.git
cd Repo_wiki

python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .[dev]

python3 -m repo_wiki.interfaces.cli init
python3 -m repo_wiki.interfaces.cli ingest local .
python3 -m repo_wiki.interfaces.cli query "add validation to a config model"
```

Run the focused checks:

```bash
python3 -m unittest tests.test_retrieval_quality -v
python3 -m unittest tests.test_end_to_end -v
python3 -m compileall repo_wiki
```

## CLI Examples

Installed command form:

```bash
repo-wiki init
repo-wiki ingest local .
repo-wiki ingest github https://github.com/example/project
repo-wiki retrieve "add validation to a config model" --format json
repo-wiki query "find the auth endpoint tests" --profile local_medium
repo-wiki status
repo-wiki doctor
repo-wiki metrics
repo-wiki repositories list
repo-wiki knowledge list --limit 10
repo-wiki graph neighbors <object_id>
repo-wiki feedback list
repo-wiki benchmark report --output reports/mvp-results.md
```

Optional interfaces:

```bash
python3 -m repo_wiki.interfaces.cli api serve --host 127.0.0.1 --port 8000
python3 -m repo_wiki.interfaces.cli mcp serve
```

See [docs/examples.md](docs/examples.md) for HTTP and MCP examples.

## Example Use Case

Task:

```text
Add validation to a config model and update focused tests.
```

repo-wiki retrieves a context pack with likely source files, related tests, runtime/use-site files, convention examples, risks, and citations. A coding agent can inspect that pack before editing instead of starting from a broad repository search.

## Benchmarks

repo-wiki is evaluated with retrieval regression tests, a multi-repository retrieval benchmark, an initial coding-agent A/B benchmark, and a blind holdout retrieval benchmark.

Retrieval v0.1 showed promising early results on a 5-repository blind holdout: 4 pass, 1 partial, 0 fail, with 12/15 expected targets found in the top 10 and full citation coverage.

Initial coding-agent A/B results were mixed, so repo-wiki currently treats retrieval quality and coding-agent improvement as separate evaluation targets.

See [docs/benchmarks.md](docs/benchmarks.md) for methodology, results, and limitations.

## Current Status

repo-wiki is an experimental v0.1 portfolio project. It is useful for demonstrating local-first repository indexing, deterministic extraction, retrieval engineering, cited context packs, and benchmark discipline.

Implemented in v0.1:

- Local and public GitHub ingestion.
- SQLite schema initialization and local storage.
- Source, docs, tests, symbols, routes, package manifests, configs, dependencies, and source references.
- Hybrid retrieval and context-pack generation.
- CLI, HTTP, and MCP-compatible stdio interfaces.
- Feedback capture and staged knowledge promotion.
- Focused retrieval quality tests.

## Limitations

- Not production-ready.
- Retrieval is heuristic and can rank noisy files.
- Coding-agent improvement is not proven.
- Language support is limited.
- TypeScript/JavaScript extraction is lightweight, not compiler-grade.
- Large monorepos may need scoped ingestion.
- Benchmark sample sizes are small.
- MCP support is a lightweight JSON-RPC stdio adapter, not a full SDK-based server.

## Next Steps

- Improve source-to-test pairing and noisy-result suppression.
- Broaden language support beyond the current Python/TypeScript/JavaScript focus.
- Expand blind retrieval benchmarks.
- Run larger coding-agent A/B evaluations.
- Improve MCP integration and context-to-action planning.
- Profile retrieval latency on larger repositories.

## License

MIT. See [LICENSE](LICENSE).
