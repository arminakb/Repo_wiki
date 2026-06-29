| Dimension | Weight | Score | Brief Justification |
|-----------|--------|-------|---------------------|
| Code Quality & Architecture | 20% | 14/20 | Clear package boundaries and typed models, but inline migrations, heuristic knowledge generation, and non-SAS interface choices remain. |
| Error Handling & Reliability | 15% | 10/15 | 10/10 benchmark ingests succeeded, but default `status` crashed on a locked DB, clone failures are raw, and file-skip errors are mostly silent. |
| Retrieval Accuracy (query results) | 25% | 10/25 | Retrieval usually found nearby files, but direct questions got generic context packs instead of answers; 0/10 answers were fully correct as answers. |
| Performance & Scalability | 15% | 13/15 | Ingest and retrieval were fast on this dataset; full-tree hashing still accumulates file bytes in memory. |
| Usability (CLI / API design) | 10% | 7/10 | CLI, HTTP, and MCP exist and share core services, but output is not Q&A-shaped and one smoke command exposed a stack trace. |
| Test Coverage & Observability | 15% | 12/15 | 27 unit/integration tests pass and traces are stored, but benchmark expected hits are still `0/0` and judged retrieval tests are absent. |
| **Total** | 100% | **66/100** | |

**Final Score: 66/100** - `BETA-QUALITY`

## 4.1 Executive Summary

Repo Knowledge Compiler is a local-first repository ingestion and context-pack retrieval tool. I built a reproducible 10-repo benchmark dataset from the GitHub Search API, ingested all 10 repos, audited the code, and ran 10 real retrieval queries across DeepSeek-V3 and NextChat. The core ingestion/indexing pipeline is useful and fast, but retrieval is not yet a reliable answer engine: it returns cited context packs with relevant files, not precise answers to factual, structural, edge-case, or refactoring questions.

## 4.2 Dataset Pipeline Results

`scripts/build_benchmark_dataset.py` ran end-to-end on 2026-06-22 in unauthenticated GitHub API mode. It saved raw API responses to:

- `dataset/benchmark-repos/.manifest/search-results-python.json`
- `dataset/benchmark-repos/.manifest/search-results-typescript.json`

Selected repos:

| Repo | Language | Tier | Stars | Size MB | Commit |
|------|----------|------|------:|--------:|--------|
| public-apis/public-apis | python | medium | 443386 | 0.3 | d0d45fdc |
| EbookFoundation/free-programming-books | python | medium | 390619 | 2.2 | 5b259858 |
| donnemartin/system-design-primer | python | medium | 354253 | 13.0 | ae9bbd7b |
| deepseek-ai/DeepSeek-V3 | python | small | 103785 | 0.4 | 9b4e9788 |
| karpathy/autoresearch | python | small | 87969 | 0.7 | 228791fb |
| vuejs/vue | typescript | medium | 209951 | 2.4 | 9e887079 |
| yangshun/tech-interview-handbook | typescript | medium | 140431 | 20.3 | 8ee2acb5 |
| ChatGPTNextWeb/NextChat | typescript | medium | 88273 | 7.4 | 89b8f26f |
| chenglou/pretext | typescript | small | 48644 | 7.7 | a79a6a59 |
| virattt/dexter | typescript | small | 27141 | 1.4 | c5cb794b |

No repos were dropped. Manifest total: 55.8 MB. `du -sh dataset/benchmark-repos` reported 62 MB. `find dataset/benchmark-repos -name .git -type d` returned no `.git` directories.

Dataset caveat: the script met the 500 MB maximum and the 5 Python / 5 TypeScript target, but the final stripped footprint is below the example 200-500 MB budget range in `TEST.md`. The discrepancy is real: deterministic star sorting selected several high-star repos whose stripped working trees are small.

Manifest completeness: every repo has `name`, `full_name`, `github_url`, `language`, `stars`, `commit_sha`, `size_on_disk_mb`, `date_fetched`, and `size_tier`. `.gitignore` now excludes `dataset/benchmark-repos/`.

## Phase 0 Contradictions

- `[MAJOR]` `TEST.md` requires reading `REPORT.md`, but no root `REPORT.md` exists. The closest report is `docs/benchmarks/mvp-results.md`.
- `[MAJOR]` `docs/benchmarks/methodology.md:9-12` requires 10 small + 10 medium repos and at least 5 Python + 5 TypeScript repos; `TEST.md:39-41` asks for 2-3 small and 2-3 medium repos per language, and its sample table shows 10 total repos.
- `[MAJOR]` `docs/benchmarks/mvp-results.md:7-29` reports only one indexed repo, Python only, and expected hits `0/0`, while `SAS.md:286-306` requires retrieval logs and cited retrieval and the methodology requires multi-repo quality metrics.
- `[MINOR]` `ROADMAP.md:37-43` lists older known gaps such as no git root, argparse instead of Typer, MCP not SDK-based, and deeper GraphRAG validation. Some are still true; the git-root note was stale in this worktree because `git status` worked.

Baseline commands:

- `python3 -m compileall repo_wiki`: exit 0.
- `python3 -m unittest discover -s tests -v`: 27 tests, OK.
- `python3 -m repo_wiki.interfaces.cli doctor`: OK for git, config, storage, SQLite integrity, schema version, optional FastAPI.
- `python3 -m repo_wiki.interfaces.cli status`: failed with `sqlite3.OperationalError: database is locked` against `.repo-wiki/repo-wiki.db`.

## 4.3 Code Audit Findings

### CRITICAL

No critical issues found.

### MAJOR

`[MAJOR]` - storage / CLI - `repo-wiki status` can crash before CLI error handling when the default SQLite database is locked. `main()` initializes storage before the `try`, and `SQLiteStore.connect()` immediately sets WAL mode. Reproduced with `python3 -m repo_wiki.interfaces.cli status`. Production effect: users see a Python stack trace instead of an actionable CLI error. Recommended fix: move initialization inside the CLI boundary and set a SQLite timeout or retry. `repo_wiki/interfaces/cli.py:34-38`, `repo_wiki/storage/sqlite.py:71-79`.

`[MAJOR]` - retrieval - The system returns generic context packs rather than answering direct questions. `build_context_pack()` turns retrieved objects into "Inspect X and mirror module boundaries" steps, so factual and edge-case questions are not answered even when citations include the right file. Production effect: users must manually inspect citations for answers. Recommended fix: add an answer synthesis layer or rename the CLI behavior as context retrieval only. `repo_wiki/retrieval/context.py:26-77`.

`[MAJOR]` - knowledge compiler - Domain inference misclassifies any path containing `model` as database, which made DeepSeek `inference/model.py` show up as "Database implementation pattern". Production effect: retrieval reasons and risks are misleading. Recommended fix: require stronger database evidence such as DB dependencies, schema paths, or SQL/ORM terms. `repo_wiki/compile/generator.py:453-469`.

`[MAJOR]` - extraction performance - `tree_hash()` appends every included file's bytes into a list before hashing. This is bounded by per-file max size but unbounded by total repo size. Production effect: large repos can create avoidable memory spikes. Recommended fix: stream into a hash object incrementally. `repo_wiki/core/extraction_service.py:284-308`.

`[MAJOR]` - GitHub ingestion reliability - clone is a single `subprocess.run(..., check=True)` with no retry/backoff and raw subprocess exceptions. Production effect: transient network failures abort ingestion without a domain error. Recommended fix: catch clone failures, retry transient errors, and raise `ExtractionFailed` or `UnsupportedSource` with the command stderr. `repo_wiki/ingest/github.py:23-33`.

`[MAJOR]` - storage maintainability - schema and migrations are inline in one module, while SAS and ROADMAP call for explicit versioned migrations. Production effect: upgrades are harder to review and rollback. Recommended fix: move migrations to small files or a lightweight migration package. `repo_wiki/storage/sqlite.py:1212-1238`, `repo_wiki/storage/sqlite.py:1343`.

`[MAJOR]` - MCP - the adapter is JSON-RPC stdio compatible but not based on the official MCP SDK, matching the ROADMAP gap. Production effect: compatibility may drift from MCP clients. Recommended fix: either adopt the SDK or keep a documented ADR-level exception with conformance tests. `repo_wiki/interfaces/mcp.py:92-281`.

### MINOR

`[MINOR]` - extraction - failed file stats/reads are silently skipped in discovery and tree hashing. Production effect: missing files may be invisible except aggregate counts. Recommended fix: record skipped file events. `repo_wiki/extract/file_tree.py:44-53`, `repo_wiki/core/extraction_service.py:303-310`.

`[MINOR]` - doctor - `optional_dependency()` returns `True` whether import succeeds or fails, so the FastAPI check is informational but looks like a real probe. Recommended fix: print "optional / not installed" distinctly. `repo_wiki/interfaces/cli.py:394-399`.

`[MINOR]` - retrieval ranking - FTS query construction ORs many terms, favoring broad matches such as locale files and constants. This contributed to wrong NextChat auth results. Recommended fix: weight exact path/symbol terms above broad token OR matches. `repo_wiki/storage/sqlite.py:1301-1324`.

`[MINOR]` - tests - existing tests are useful, but the benchmark report still shows `Expected hits: 0/0`; judged retrieval accuracy is not protected by golden expected-file tests. `docs/benchmarks/mvp-results.md:23-29`.

### INFO

`[INFO]` - architecture - core services are mostly separated from CLI/HTTP/MCP. CLI, HTTP, and MCP call `IngestionService`, `RetrievalService`, `MetricsService`, and `ReflexionService` rather than duplicating major logic. `repo_wiki/interfaces/cli.py:402-521`, `repo_wiki/interfaces/http.py:150-182`, `repo_wiki/interfaces/mcp.py:213-265`.

`[INFO]` - security - file discovery checks root containment, excludes `.env`, redacts obvious secrets, and enforces snippet policy through `snippet_allowed`. `repo_wiki/extract/file_tree.py:78-114`, `repo_wiki/core/retrieval_service.py:118-122`.

## 4.4 Real-World Use Report

All ingests used `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-eval-data`.

| Repo | Language | Size | Ingest Result |
|------|----------|------|---------------|
| public-apis/public-apis | Python | 0.3 MB | Success: 15 files, 58 symbols, 9 knowledge objects |
| EbookFoundation/free-programming-books | Python | 2.2 MB | Success: 229 files, 6 symbols, 3 knowledge objects |
| donnemartin/system-design-primer | Python | 13.0 MB | Success: 50 files, 204 symbols, 25 knowledge objects |
| deepseek-ai/DeepSeek-V3 | Python | 0.4 MB | Success: 15 files, 52 symbols, 8 knowledge objects |
| karpathy/autoresearch | Python | 0.7 MB | Success: 5 files, 17 symbols, 4 knowledge objects |
| vuejs/vue | TypeScript | 2.4 MB | Success: 493 files, 6383 symbols, 73 knowledge objects |
| yangshun/tech-interview-handbook | TypeScript | 20.3 MB | Success: 486 files, 1759 symbols, 77 knowledge objects |
| ChatGPTNextWeb/NextChat | TypeScript | 7.4 MB | Success: 211 files, 2732 symbols, 38 knowledge objects |
| chenglou/pretext | TypeScript | 7.7 MB | Success: 100 files, 3872 symbols, 23 knowledge objects |
| virattt/dexter | TypeScript | 1.4 MB | Success: 206 files, 2807 symbols, 48 knowledge objects |

Post-ingest metrics:

- Indexed repositories: 10
- Indexed files: 1810
- Extracted symbols: 17890
- Dependencies: 3033
- Knowledge objects: 308
- Graph nodes: 23083
- Graph edges: 25988
- SQLite DB size: 75,059,200 bytes

Repos selected for deep test:

- `deepseek-ai/DeepSeek-V3`: small Python repo with compact inference code, distributed setup, config loading, and FP8/BF16 paths.
- `ChatGPTNextWeb/NextChat`: medium TypeScript/Next.js repo with many API providers, auth, config, client/provider layers, and tests.

### Query Results - DeepSeek-V3

| # | Query | Response Summary | Judgment | Time |
|---|-------|------------------|----------|------|
| 1 | What does ModelArgs configure in inference/model.py? | Returned `inference/model.py` and related files, but did not state the fields. | Partially Correct | 0.466s |
| 2 | How is distributed model parallelism structured in the inference code? | Returned `model.py`, `generate.py`, and `convert.py`, but did not explain `world_size`, rank, split layers, or process group setup. | Partially Correct | 0.424s |
| 3 | Where is the inference config JSON loaded and who consumes ModelArgs? | Returned `model.py` and `convert.py`; missed the direct `generate.py` load in the answer text. | Partially Correct | 0.439s |
| 4 | What happens if a checkpoint safetensor file is missing during generation startup? | Did not answer; returned broad module context. | Wrong | 0.422s |
| 5 | Which modules would change if fp8 quantization were replaced with bf16-only inference? | Returned the main FP8/BF16 files: `fp8_cast_bf16.py`, `kernel.py`, `generate.py`, `convert.py`, `model.py`. | Partially Correct | 0.429s |

### Query Results - NextChat

| # | Query | Response Summary | Judgment | Time |
|---|-------|------------------|----------|------|
| 1 | What does app/api/auth.ts do? | Missed `app/api/auth.ts` in returned patterns and focused on locales/store/client API. | Wrong | 0.445s |
| 2 | How are API provider routes organized in app/api? | Returned the `app/api` module pattern and provider files, but did not explain the organization. | Partially Correct | 0.464s |
| 3 | Where is server-side config loaded and which API modules consume it? | Missed `app/config/server.ts` and key API consumers in the answer. | Wrong | 0.447s |
| 4 | What happens when auth fails in a provider API route? | Cited `app/api/auth.ts` and provider modules but did not state that routes return 401 JSON. | Partially Correct | 0.432s |
| 5 | Which modules would need to change to add a new LLM provider API? | Returned `app/api`, `app/client/api.ts`, and `app/client/platforms/openai.ts`; missed constants/config details. | Partially Correct | 0.444s |

### Exact Query Responses

The CLI returned JSON. The exact answer-bearing response text is the `markdown` field; it is reproduced below without paraphrase.

#### DeepSeek 1

```text
# Context Pack: What does ModelArgs configure in inference/model.py?

- Task type: `backend_feature`
- Retrieval trace: `trace_c143abbabb6d4ea0`

## Recommended Patterns
### Large module risk in inference/model.py
- Score: 0.6399
- Why: language matches: Python; domain matches: database; lexical score: 0.94; vector score: 0.52; graph expansion via graph edge; query overlap: 0.56; has source references
- Summary: inference/model.py is 809 lines; edits should avoid increasing module sprawl.

### Database implementation pattern in inference/model.py
- Score: 0.6032
- Why: language matches: Python; domain matches: database; lexical score: 0.96; vector score: 0.44; query overlap: 0.67; has source references
- Summary: inference/model.py provides database implementation structure with ModelArgs, ParallelEmbedding, linear, Linear, ColumnParallelLinear, RowParallelLinear. Use it as a cited example of this repository's Python conventions.

### General implementation pattern in inference/convert.py
- Score: 0.5274
- Why: language matches: Python; lexical score: 0.91; vector score: 0.52; query overlap: 0.33; has source references
- Summary: inference/convert.py provides general implementation structure with main. Use it as a cited example of this repository's Python conventions.

### General implementation pattern in inference/fp8_cast_bf16.py
- Score: 0.5267
- Why: language matches: Python; lexical score: 0.91; vector score: 0.52; query overlap: 0.33; has source references
- Summary: inference/fp8_cast_bf16.py provides general implementation structure with main, get_tensor. Use it as a cited example of this repository's Python conventions.

### General implementation pattern in inference/generate.py
- Score: 0.5241
- Why: language matches: Python; lexical score: 0.91; vector score: 0.52; query overlap: 0.33; has source references
- Summary: inference/generate.py provides general implementation structure with module-level code. Use it as a cited example of this repository's Python conventions.

## Architecture Rules

## Implementation Steps
- Inspect inference/model.py and mirror its module boundaries.
- Inspect inference/model.py and mirror its module boundaries.
- Inspect inference/convert.py and mirror its module boundaries.
- Inspect inference/fp8_cast_bf16.py and mirror its module boundaries.
- Inspect inference/generate.py and mirror its module boundaries.

## Tests To Consider
- Add or update tests that cover the changed behavior.

## Risks
- Check migration safety and add tests around persistence behavior.

## Citations
- `inference/model.py:20-798` (MIT)
- `inference/fp8_cast_bf16.py:12-103` (MIT)
- `inference/generate.py:1-186` (MIT)
- `inference/convert.py:33-85` (MIT)
```

#### DeepSeek 2

```text
# Context Pack: How is distributed model parallelism structured in the inference code?

- Task type: `backend_feature`
- Retrieval trace: `trace_c1481bf6b4704395`

## Recommended Patterns
### Database implementation pattern in inference/model.py
- Score: 0.5773
- Why: language matches: Python; domain matches: database; lexical score: 0.92; vector score: 0.29; graph expansion via graph edge; query overlap: 0.40; has source references
- Summary: inference/model.py provides database implementation structure with ModelArgs, ParallelEmbedding, linear, Linear, ColumnParallelLinear, RowParallelLinear. Use it as a cited example of this repository's Python conventions.

### Module pattern in inference
- Score: 0.5001
- Why: language matches: Python; lexical score: 0.87; vector score: 0.42; query overlap: 0.20; has source references
- Summary: inference contains 6 related source files; use it as evidence for local module boundaries.

### Large module risk in inference/model.py
- Score: 0.4936
- Why: language matches: Python; domain matches: database; lexical score: 0.94; vector score: 0.23; query overlap: 0.40; has source references
- Summary: inference/model.py is 809 lines; edits should avoid increasing module sprawl.

### General implementation pattern in inference/generate.py
- Score: 0.4729
- Why: language matches: Python; lexical score: 0.91; vector score: 0.20; query overlap: 0.40; has source references
- Summary: inference/generate.py provides general implementation structure with module-level code. Use it as a cited example of this repository's Python conventions.

### General implementation pattern in inference/convert.py
- Score: 0.4617
- Why: language matches: Python; lexical score: 0.86; vector score: 0.28; query overlap: 0.30; has source references
- Summary: inference/convert.py provides general implementation structure with main. Use it as a cited example of this repository's Python conventions.

## Architecture Rules

## Implementation Steps
- Inspect inference/model.py and mirror its module boundaries.
- Inspect inference and mirror its module boundaries.
- Inspect inference/model.py and mirror its module boundaries.
- Inspect inference/generate.py and mirror its module boundaries.
- Inspect inference/convert.py and mirror its module boundaries.

## Tests To Consider
- Add or update tests that cover the changed behavior.

## Risks
- Check migration safety and add tests around persistence behavior.

## Citations
- `inference/model.py:20-798` (MIT)
- `inference/fp8_cast_bf16.py:12-103` (MIT)
- `inference/generate.py:1-186` (MIT)
- `inference/kernel.py:10-196` (MIT)
- `inference/convert.py:33-85` (MIT)
```

#### DeepSeek 3

```text
# Context Pack: Where is the inference config JSON loaded and who consumes ModelArgs?

- Task type: `backend_feature`
- Retrieval trace: `trace_b03bcbf1c5104875`

## Recommended Patterns
### Large module risk in inference/model.py
- Score: 0.4981
- Why: language matches: Python; lexical score: 0.89; vector score: 0.22; graph expansion via graph edge; query overlap: 0.27; has source references
- Summary: inference/model.py is 809 lines; edits should avoid increasing module sprawl.

### Database implementation pattern in inference/model.py
- Score: 0.4846
- Why: language matches: Python; lexical score: 0.93; vector score: 0.25; query overlap: 0.36; has source references
- Summary: inference/model.py provides database implementation structure with ModelArgs, ParallelEmbedding, linear, Linear, ColumnParallelLinear, RowParallelLinear. Use it as a cited example of this repository's Python conventions.

### General implementation pattern in inference/convert.py
- Score: 0.4777
- Why: language matches: Python; lexical score: 0.86; vector score: 0.38; query overlap: 0.27; has source references
- Summary: inference/convert.py provides general implementation structure with main. Use it as a cited example of this repository's Python conventions.

### Module pattern in inference
- Score: 0.4691
- Why: language matches: Python; lexical score: 0.87; vector score: 0.37; query overlap: 0.09; has source references
- Summary: inference contains 6 related source files; use it as evidence for local module boundaries.

### General implementation pattern in inference/fp8_cast_bf16.py
- Score: 0.4533
- Why: language matches: Python; lexical score: 0.86; vector score: 0.26; query overlap: 0.27; has source references
- Summary: inference/fp8_cast_bf16.py provides general implementation structure with main, get_tensor. Use it as a cited example of this repository's Python conventions.

## Architecture Rules

## Implementation Steps
- Inspect inference/model.py and mirror its module boundaries.
- Inspect inference/model.py and mirror its module boundaries.
- Inspect inference/convert.py and mirror its module boundaries.
- Inspect inference and mirror its module boundaries.
- Inspect inference/fp8_cast_bf16.py and mirror its module boundaries.

## Tests To Consider
- Add or update tests that cover the changed behavior.

## Risks
- Check migration safety and add tests around persistence behavior.

## Citations
- `inference/model.py:20-798` (MIT)
- `inference/fp8_cast_bf16.py:12-103` (MIT)
- `inference/generate.py:1-186` (MIT)
- `inference/kernel.py:10-196` (MIT)
- `inference/convert.py:33-85` (MIT)
```

#### DeepSeek 4

```text
# Context Pack: What happens if a checkpoint safetensor file is missing during generation startup?

- Task type: `backend_feature`
- Retrieval trace: `trace_777993b241c3463f`

## Recommended Patterns
### Large module risk in inference/model.py
- Score: 0.359
- Why: language matches: Python; lexical score: 0.70; vector score: 0.24; query overlap: 0.09; has source references
- Summary: inference/model.py is 809 lines; edits should avoid increasing module sprawl.

### Database implementation pattern in inference/model.py
- Score: 0.2346
- Why: language matches: Python; vector score: 0.19; graph expansion via graph edge; has source references
- Summary: inference/model.py provides database implementation structure with ModelArgs, ParallelEmbedding, linear, Linear, ColumnParallelLinear, RowParallelLinear. Use it as a cited example of this repository's Python conventions.

### Module pattern in inference
- Score: 0.2147
- Why: language matches: Python; vector score: 0.27; has source references
- Summary: inference contains 6 related source files; use it as evidence for local module boundaries.

### General implementation pattern in inference/fp8_cast_bf16.py
- Score: 0.185
- Why: language matches: Python; vector score: 0.24; has source references
- Summary: inference/fp8_cast_bf16.py provides general implementation structure with main, get_tensor. Use it as a cited example of this repository's Python conventions.

## Architecture Rules
- DeepSeek-V3 project profile: DeepSeek-V3 is a unknown project using Markdown, YAML, Python. Detected frameworks: no major framework detected. It contains 15 indexed files, 52 symbols, 4 dependencies, 0 test files, and 4 documentation files.

## Implementation Steps
- Inspect inference/model.py and mirror its module boundaries.
- Inspect inference/model.py and mirror its module boundaries.
- Inspect inference and mirror its module boundaries.
- Inspect inference/fp8_cast_bf16.py and mirror its module boundaries.

## Tests To Consider
- Add or update tests that cover the changed behavior.

## Risks
- Check migration safety and add tests around persistence behavior.

## Citations
- `inference/model.py:20-798` (MIT)
- `inference/fp8_cast_bf16.py:12-103` (MIT)
- `inference/configs/config_236B.json:1-20` (MIT)
- `inference/generate.py:1-186` (MIT)
- `README.md:1-362` (MIT)
- `.github/workflows/stale.yml:1-31` (MIT)
- `inference/configs/config_16B.json:1-19` (MIT)
- `README_WEIGHTS.md:1-95` (MIT)
- `.github/ISSUE_TEMPLATE/bug_report.md:1-24` (MIT)
- `.github/ISSUE_TEMPLATE/feature_request.md:1-21` (MIT)
- `inference/configs/config_671B.json:1-22` (MIT)
- `inference/kernel.py:10-196` (MIT)
- `inference/convert.py:33-85` (MIT)
```

#### DeepSeek 5

```text
# Context Pack: Which modules would change if fp8 quantization were replaced with bf16-only inference?

- Task type: `backend_feature`
- Retrieval trace: `trace_bab0fec777b947e0`

## Recommended Patterns
### General implementation pattern in inference/fp8_cast_bf16.py
- Score: 0.4948
- Why: language matches: Python; lexical score: 0.96; vector score: 0.34; query overlap: 0.29; has source references
- Summary: inference/fp8_cast_bf16.py provides general implementation structure with main, get_tensor. Use it as a cited example of this repository's Python conventions.

### General implementation pattern in inference/kernel.py
- Score: 0.488
- Why: language matches: Python; lexical score: 0.93; vector score: 0.40; query overlap: 0.21; has source references
- Summary: inference/kernel.py provides general implementation structure with act_quant_kernel, act_quant, weight_dequant_kernel, weight_dequant, fp8_gemm_kernel, fp8_gemm. Use it as a cited example of this repository's Python conventions.

### General implementation pattern in inference/generate.py
- Score: 0.4579
- Why: language matches: Python; lexical score: 0.86; vector score: 0.42; query overlap: 0.14; has source references
- Summary: inference/generate.py provides general implementation structure with module-level code. Use it as a cited example of this repository's Python conventions.

### General implementation pattern in inference/convert.py
- Score: 0.451
- Why: language matches: Python; lexical score: 0.86; vector score: 0.36; query overlap: 0.14; has source references
- Summary: inference/convert.py provides general implementation structure with main. Use it as a cited example of this repository's Python conventions.

### Large module risk in inference/model.py
- Score: 0.4443
- Why: language matches: Python; lexical score: 0.90; vector score: 0.37; query overlap: 0.14; has source references
- Summary: inference/model.py is 809 lines; edits should avoid increasing module sprawl.

## Architecture Rules

## Implementation Steps
- Inspect inference/fp8_cast_bf16.py and mirror its module boundaries.
- Inspect inference/kernel.py and mirror its module boundaries.
- Inspect inference/generate.py and mirror its module boundaries.
- Inspect inference/convert.py and mirror its module boundaries.
- Inspect inference/model.py and mirror its module boundaries.

## Tests To Consider
- Add or update tests that cover the changed behavior.

## Risks
- Check migration safety and add tests around persistence behavior.

## Citations
- `inference/model.py:20-798` (MIT)
- `inference/fp8_cast_bf16.py:12-103` (MIT)
- `inference/generate.py:1-186` (MIT)
- `inference/kernel.py:10-196` (MIT)
- `inference/convert.py:33-85` (MIT)
```

#### NextChat 1

```text
# Context Pack: What does app/api/auth.ts do?

- Task type: `security_change`
- Retrieval trace: `trace_4da8cf585f634491`

## Recommended Patterns
### Module pattern in app/locales
- Score: 0.5698
- Why: language matches: TypeScript; framework matches: Next.js; lexical score: 0.80; vector score: 0.40; graph expansion via graph edge; query overlap: 0.12; has source references; quality score: 0.71
- Summary: app/locales contains 21 related source files; use it as evidence for local module boundaries.

### General implementation pattern in app/store/chat.ts
- Score: 0.5388
- Why: language matches: TypeScript; framework matches: Next.js; lexical score: 0.83; vector score: 0.27; graph expansion via graph edge; query overlap: 0.25; has source references
- Summary: app/store/chat.ts provides general implementation structure with localStorage, ChatMessageTool, ChatMessage, createMessage, ChatStat, ChatSession. Use it as a cited example of this repository's TypeScript conventions.

### General implementation pattern in app/utils/chat.ts
- Score: 0.5368
- Why: language matches: TypeScript; framework matches: Next.js; lexical score: 0.83; vector score: 0.26; graph expansion via graph edge; query overlap: 0.25; has source references
- Summary: app/utils/chat.ts provides general implementation structure with compressImage, reader, image, canvas, ctx, width. Use it as a cited example of this repository's TypeScript conventions.

### General implementation pattern in app/constant.ts
- Score: 0.5309
- Why: language matches: TypeScript; framework matches: Next.js; lexical score: 0.83; vector score: 0.24; graph expansion via graph edge; query overlap: 0.25; has source references
- Summary: app/constant.ts provides general implementation structure with OWNER, REPO, REPO_URL, PLUGINS_REPO_URL, ISSUE_URL, UPDATE_URL. Use it as a cited example of this repository's TypeScript conventions.

### Api implementation pattern in app/client/api.ts
- Score: 0.5164
- Why: language matches: TypeScript; framework matches: Next.js; lexical score: 0.92; vector score: 0.24; query overlap: 0.38; has source references
- Summary: app/client/api.ts provides api implementation structure with ROLES, MessageRole, Models, TTSModels, ChatModel, MultimodalContent. Use it as a cited example of this repository's TypeScript conventions.

## Architecture Rules

## Implementation Steps
- Inspect app/locales and mirror its module boundaries.
- Inspect app/store/chat.ts and mirror its module boundaries.
- Inspect app/utils/chat.ts and mirror its module boundaries.
- Inspect app/constant.ts and mirror its module boundaries.
- Inspect app/client/api.ts and mirror its module boundaries.

## Tests To Consider
- Add or update tests that cover the changed behavior.

## Risks
- Check project conventions, error handling, and existing tests before editing.

## Citations
- `app/locales/cs.ts:5-84` (MIT)
- `app/constant.ts:1-933` (MIT)
- `app/locales/bn.ts:5-84` (MIT)
- `app/store/chat.ts:42-922` (MIT)
- `app/locales/ar.ts:5-84` (MIT)
- `app/client/api.ts:29-387` (MIT)
- `app/locales/cn.ts:5-872` (MIT)
- `app/utils/chat.ts:15-664` (MIT)
```

#### NextChat 2

```text
# Context Pack: How are API provider routes organized in app/api?

- Task type: `api_integration`
- Retrieval trace: `trace_4042955ff01141b2`

## Recommended Patterns
### Module pattern in app/api
- Score: 0.6051
- Why: language matches: TypeScript; framework matches: Next.js; domain matches: api; lexical score: 0.92; vector score: 0.41; query overlap: 0.44; has source references
- Summary: app/api contains 18 related source files; use it as evidence for local module boundaries.

### Module pattern in app/locales
- Score: 0.5557
- Why: language matches: TypeScript; framework matches: Next.js; lexical score: 0.80; vector score: 0.24; graph expansion via graph edge; query overlap: 0.22; has source references; quality score: 0.71
- Summary: app/locales contains 21 related source files; use it as evidence for local module boundaries.

### Module pattern in app/utils
- Score: 0.5527
- Why: language matches: TypeScript; framework matches: Next.js; lexical score: 0.80; vector score: 0.23; graph expansion via graph edge; query overlap: 0.22; has source references; quality score: 0.71
- Summary: app/utils contains 19 related source files; use it as evidence for local module boundaries.

### Api implementation pattern in app/client/api.ts
- Score: 0.5293
- Why: language matches: TypeScript; framework matches: Next.js; domain matches: api; lexical score: 0.91; vector score: 0.25; query overlap: 0.33; has source references
- Summary: app/client/api.ts provides api implementation structure with ROLES, MessageRole, Models, TTSModels, ChatModel, MultimodalContent. Use it as a cited example of this repository's TypeScript conventions.

## Architecture Rules

## Implementation Steps
- Inspect app/api and mirror its module boundaries.
- Inspect app/locales and mirror its module boundaries.
- Inspect app/utils and mirror its module boundaries.
- Inspect app/client/api.ts and mirror its module boundaries.

## Tests To Consider
- Follow test structure from test/model-provider.test.ts.

## Risks
- Check migration safety and add tests around persistence behavior.

## Citations
- `app/api/anthropic.ts:15-170` (MIT)
- `app/locales/cs.ts:5-84` (MIT)
- `app/utils/auth-settings-events.ts:3-19` (MIT)
- `app/locales/bn.ts:5-84` (MIT)
- `app/api/302ai.ts:13-128` (MIT)
- `app/locales/ar.ts:5-84` (MIT)
- `app/utils/baidu.ts:6-21` (MIT)
- `app/api/auth.ts:6-128` (MIT)
- `app/client/api.ts:29-387` (MIT)
- `app/utils/audio.ts:7-45` (MIT)
- `app/locales/cn.ts:5-872` (MIT)
- `test/model-provider.test.ts:5-26` (MIT)
- `app/api/alibaba.ts:13-129` (MIT)
- `app/utils/chat.ts:15-664` (MIT)
```

#### NextChat 3

```text
# Context Pack: Where is server-side config loaded and which API modules consume it?

- Task type: `api_integration`
- Retrieval trace: `trace_611f6bb65b574e58`

## Recommended Patterns
### General implementation pattern in app/constant.ts
- Score: 0.508
- Why: language matches: TypeScript; framework matches: Next.js; lexical score: 0.76; vector score: 0.23; graph expansion via graph edge; query overlap: 0.23; has source references
- Summary: app/constant.ts provides general implementation structure with OWNER, REPO, REPO_URL, PLUGINS_REPO_URL, ISSUE_URL, UPDATE_URL. Use it as a cited example of this repository's TypeScript conventions.

### Api implementation pattern in app/client/api.ts
- Score: 0.5003
- Why: language matches: TypeScript; framework matches: Next.js; domain matches: api; lexical score: 0.88; vector score: 0.24; query overlap: 0.23; has source references
- Summary: app/client/api.ts provides api implementation structure with ROLES, MessageRole, Models, TTSModels, ChatModel, MultimodalContent. Use it as a cited example of this repository's TypeScript conventions.

### Large module risk in app/client/platforms/openai.ts
- Score: 0.4902
- Why: language matches: TypeScript; framework matches: Next.js; lexical score: 0.83; vector score: 0.44; query overlap: 0.23; has source references
- Summary: app/client/platforms/openai.ts is 535 lines; edits should avoid increasing module sprawl.

### General implementation pattern in app/mcp/actions.ts
- Score: 0.4767
- Why: language matches: TypeScript; framework matches: Next.js; lexical score: 0.86; vector score: 0.25; query overlap: 0.23; has source references
- Summary: app/mcp/actions.ts provides general implementation structure with logger, CONFIG_PATH, clientsMap, getClientsStatus, config, result. Use it as a cited example of this repository's TypeScript conventions.

## Architecture Rules
- NextChat project profile: NextChat is a fullstack project using YAML, Markdown, JavaScript, TypeScript, TOML. Detected frameworks: Jest, Next.js, React. It contains 211 indexed files, 2732 symbols, 1064 dependencies, 4 test files, and 28 documentation files.

## Implementation Steps
- Inspect app/constant.ts and mirror its module boundaries.
- Inspect app/client/api.ts and mirror its module boundaries.
- Inspect app/client/platforms/openai.ts and mirror its module boundaries.
- Inspect app/mcp/actions.ts and mirror its module boundaries.

## Tests To Consider
- Add or update tests that cover the changed behavior.

## Risks
- Check project conventions, error handling, and existing tests before editing.

## Citations
- `app/constant.ts:1-933` (MIT)
- `.github/PULL_REQUEST_TEMPLATE.md:1-29` (MIT)
- `.eslintrc.json:1-8` (MIT)
- `app/mcp/actions.ts:21-385` (MIT)
- `.github/workflows/app.yml:1-111` (MIT)
- `app/client/api.ts:29-387` (MIT)
- `.github/ISSUE_TEMPLATE/2_feature_request_cn.yml:1-21` (MIT)
- `.github/dependabot.yml:1-12` (MIT)
- `app/client/platforms/openai.ts:48-533` (MIT)
- `.github/ISSUE_TEMPLATE/1_bug_report_cn.yml:1-80` (MIT)
- `.github/ISSUE_TEMPLATE/2_feature_request.yml:1-21` (MIT)
- `.github/ISSUE_TEMPLATE/1_bug_report.yml:1-80` (MIT)
```

#### NextChat 4

```text
# Context Pack: What happens when auth fails in a provider API route?

- Task type: `security_change`
- Retrieval trace: `trace_621542b88e8c4595`

## Recommended Patterns
### Api implementation pattern in app/client/api.ts
- Score: 0.4869
- Why: language matches: TypeScript; framework matches: Next.js; lexical score: 0.88; vector score: 0.29; query overlap: 0.22; has source references
- Summary: app/client/api.ts provides api implementation structure with ROLES, MessageRole, Models, TTSModels, ChatModel, MultimodalContent. Use it as a cited example of this repository's TypeScript conventions.

### Module pattern in app/api
- Score: 0.4538
- Why: language matches: TypeScript; framework matches: Next.js; lexical score: 0.88; query overlap: 0.22; has source references
- Summary: app/api contains 18 related source files; use it as evidence for local module boundaries.

### Module pattern in app/locales
- Score: 0.349
- Why: language matches: TypeScript; framework matches: Next.js; lexical score: 0.25; graph expansion via APPLIES_TO_FRAMEWORK; query overlap: 0.11; has source references; quality score: 0.71
- Summary: app/locales contains 21 related source files; use it as evidence for local module boundaries.

## Architecture Rules
- NextChat project profile: NextChat is a fullstack project using YAML, Markdown, JavaScript, TypeScript, TOML. Detected frameworks: Jest, Next.js, React. It contains 211 indexed files, 2732 symbols, 1064 dependencies, 4 test files, and 28 documentation files.

## Implementation Steps
- Inspect app/client/api.ts and mirror its module boundaries.
- Inspect app/api and mirror its module boundaries.
- Inspect app/locales and mirror its module boundaries.

## Tests To Consider
- Follow test structure from test/model-provider.test.ts.

## Risks
- Check migration safety and add tests around persistence behavior.

## Citations
- `app/api/anthropic.ts:15-170` (MIT)
- `app/locales/cs.ts:5-84` (MIT)
- `.github/PULL_REQUEST_TEMPLATE.md:1-29` (MIT)
- `app/locales/bn.ts:5-84` (MIT)
- `app/api/302ai.ts:13-128` (MIT)
- `.eslintrc.json:1-8` (MIT)
- `app/locales/ar.ts:5-84` (MIT)
- `app/api/auth.ts:6-128` (MIT)
- `.github/workflows/app.yml:1-111` (MIT)
- `app/client/api.ts:29-387` (MIT)
- `.github/ISSUE_TEMPLATE/2_feature_request_cn.yml:1-21` (MIT)
- `.github/dependabot.yml:1-12` (MIT)
- `app/locales/cn.ts:5-872` (MIT)
- `test/model-provider.test.ts:5-26` (MIT)
- `.github/ISSUE_TEMPLATE/1_bug_report_cn.yml:1-80` (MIT)
- `.github/ISSUE_TEMPLATE/2_feature_request.yml:1-21` (MIT)
- `app/api/alibaba.ts:13-129` (MIT)
- `.github/ISSUE_TEMPLATE/1_bug_report.yml:1-80` (MIT)
```

#### NextChat 5

```text
# Context Pack: Which modules would need to change to add a new LLM provider API?

- Task type: `api_integration`
- Retrieval trace: `trace_287ca8b3e97e4887`

## Recommended Patterns
### Api implementation pattern in app/client/api.ts
- Score: 0.4781
- Why: language matches: TypeScript; framework matches: Next.js; domain matches: api; lexical score: 0.88; vector score: 0.18; query overlap: 0.18; has source references
- Summary: app/client/api.ts provides api implementation structure with ROLES, MessageRole, Models, TTSModels, ChatModel, MultimodalContent. Use it as a cited example of this repository's TypeScript conventions.

### Module pattern in app/api
- Score: 0.4665
- Why: language matches: TypeScript; framework matches: Next.js; domain matches: api; lexical score: 0.88; query overlap: 0.18; has source references
- Summary: app/api contains 18 related source files; use it as evidence for local module boundaries.

### Large module risk in app/client/platforms/openai.ts
- Score: 0.4514
- Why: language matches: TypeScript; framework matches: Next.js; lexical score: 0.72; vector score: 0.42; query overlap: 0.18; has source references
- Summary: app/client/platforms/openai.ts is 535 lines; edits should avoid increasing module sprawl.

### Large module risk in app/components/exporter.tsx
- Score: 0.4504
- Why: language matches: TypeScript; framework matches: Next.js; lexical score: 0.72; vector score: 0.41; query overlap: 0.18; has source references
- Summary: app/components/exporter.tsx is 695 lines; edits should avoid increasing module sprawl.

## Architecture Rules

## Implementation Steps
- Inspect app/client/api.ts and mirror its module boundaries.
- Inspect app/api and mirror its module boundaries.
- Inspect app/client/platforms/openai.ts and mirror its module boundaries.
- Inspect app/components/exporter.tsx and mirror its module boundaries.

## Tests To Consider
- Follow test structure from test/model-provider.test.ts.

## Risks
- Check migration safety and add tests around persistence behavior.

## Citations
- `app/api/anthropic.ts:15-170` (MIT)
- `app/api/302ai.ts:13-128` (MIT)
- `app/api/auth.ts:6-128` (MIT)
- `app/client/api.ts:29-387` (MIT)
- `test/model-provider.test.ts:5-26` (MIT)
- `app/client/platforms/openai.ts:48-533` (MIT)
- `app/components/exporter.tsx:44-679` (MIT)
- `app/api/alibaba.ts:13-129` (MIT)
```

### Manual Baseline Comparison

DeepSeek manual baseline: `inference/generate.py:112-119` opens the config JSON, constructs `ModelArgs(**json.load(f))`, builds `Transformer(args)`, creates the tokenizer, warms generation, then calls `load_model(...)`. `inference/model.py:20-86` defines the config fields. The tool found `model.py`, but did not directly answer the config-load part.

NextChat manual baseline: `app/api/auth.ts:27-128` parses access code or API key, checks hashed access codes, optionally injects provider-specific system API keys, and returns `{ error: true, msg: ... }` on failure. Provider routes such as `app/api/openai.ts:54-58` convert auth failure to `NextResponse.json(authResult, { status: 401 })`. The tool cited `auth.ts` for query 4 but did not state the 401 behavior; query 1 missed `auth.ts`.

## 4.5 Strengths

- Local ingestion worked across all 10 real repos without crashes.
- The core architecture is clean enough to follow: ingestion, extraction, compilation, storage, retrieval, graph, interfaces, and reflexion are separate packages.
- Retrieval traces record candidate counts, rankings, filters, latency, and trace IDs.
- License-aware citations and secret redaction exist and are tested.
- CLI, HTTP, and MCP adapters call shared services rather than duplicating full pipelines.

## 4.6 Weaknesses & Gaps

- Retrieval is not accurate enough for direct Q&A. It gives "inspect this file" guidance rather than answering the question.
- Domain and task heuristics are too blunt; `model.py` became "database" because of the word `model`.
- The current benchmark docs are not strong evidence: old report has one repo and expected hits `0/0`.
- SQLite lock handling is not production-ready at the CLI boundary.
- Migrations and MCP remain documented compromises rather than production-grade implementations.
- Dataset footprint is below the stated 200-500 MB example range.

## 4.7 Full Score Justification

**Code Quality & Architecture: 14/20.** Deducted 2 for inline schema/migration design, 2 for generic knowledge generation and domain inference, 1 for argparse/MCP SDK deviations from SAS recommendations, and 1 for raw or broad boundary errors.

**Error Handling & Reliability: 10/15.** Deducted 2 for the locked DB stack trace, 1 for no GitHub clone retry/backoff, 1 for silent file-skip behavior, and 1 for noisy parser warnings during ingest.

**Retrieval Accuracy: 10/25.** The tool retrieved useful files for 7 of 10 queries, but produced no fully correct direct answers. It was wrong on NextChat auth, NextChat server config, and DeepSeek missing checkpoint behavior.

**Performance & Scalability: 13/15.** Ingest was fast: largest measured repo ingest was 6.65s via CLI, and all query commands completed in 0.422-0.466s. Deducted 2 for unbounded aggregate memory in tree hashing and lack of evidence on a 1000+ file repo in this benchmark.

**Usability: 7/10.** Deducted 1 for context-pack output not matching question-answer expectations, 1 for stack trace on a smoke command, and 1 for docs/report naming mismatch.

**Test Coverage & Observability: 12/15.** Deducted 1 for `Expected hits: 0/0` in the existing benchmark report, 1 for no regression around locked DB/retry behavior, and 1 for no judged multi-repo retrieval golden suite.

## 4.8 Top 3 Recommendations

1. Add judged retrieval tests with expected files and expected answer facts for 20-50 fixed queries. Make benchmark reports fail if expected hits are `0/0`.
2. Add an answer synthesis layer over retrieved context, or rename the CLI/API behavior to "retrieve context" only. Direct questions must return direct answers with citations.
3. Harden reliability: SQLite timeout/retry and CLI error wrapping, GitHub clone retry/domain errors, and streamed tree hashing.

## Next-Agent Roadmap: Retrieval Quality First

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this task-by-task. Track steps with checkboxes and stop after each task to run the listed checks.

**Goal:** Improve the same 10 deep queries in this report from 0 fully correct direct answers to at least 6 fully correct direct answers.

**Architecture:** Keep the current hybrid retrieval stack. Do not replace it with full GraphRAG. Add a thin deterministic layer: exact path/symbol boosts, safer domain inference, and an extractive `answer` field in context packs. Treat LLM-wiki style wiki pages as a later ingestion improvement after the basic retrieval failure is fixed.

**Tech stack:** Python stdlib, `unittest`, existing SQLite FTS/vector/graph code, existing `ContextPack` Pydantic model.

**Repos / Data:**

- Eval DB: `/tmp/repo-wiki-eval-data`
- DeepSeek repo id: `repo_87ae50091a922d6cab8e`
- NextChat repo id: `repo_7098e0d33e9ab578c066`
- Query output dir from baseline: `/tmp/repo-wiki-eval-queries`
- Benchmark repos: `dataset/benchmark-repos/`

### Roadmap Rules

- Fix retrieval accuracy before migrations, MCP SDK work, or broad refactors.
- Prefer a deterministic answer over adding an LLM dependency.
- Keep the schema backward compatible: add fields with defaults only.
- Keep changes in the files below unless a test reveals a direct need.

Primary edit scope:

- `repo_wiki/core/retrieval_service.py`
- `repo_wiki/retrieval/context.py`
- `repo_wiki/retrieval/rerank.py`
- `repo_wiki/storage/sqlite.py`
- `repo_wiki/compile/generator.py`
- `repo_wiki/domain/models.py`
- `repo_wiki/benchmarks/report.py`
- `tests/test_retrieval_quality.py`

### Task 1: Add Golden Retrieval Cases

**Files:**

- Modify: `tests/test_retrieval_quality.py`

- [ ] Add a compact judged-case table for the known failures. Use existing test setup helpers in `tests/test_retrieval_quality.py`; do not create a benchmark harness yet.

Recommended case shape:

```python
GOLDEN_CASES = [
    {
        "query": "What does app/api/auth.ts do?",
        "repo_id": "repo_7098e0d33e9ab578c066",
        "language": "TypeScript",
        "framework": "Next.js",
        "expected_paths": ["app/api/auth.ts"],
        "expected_answer_terms": ["access code", "api key", "system api key"],
    },
    {
        "query": "Where is the inference config JSON loaded and who consumes ModelArgs?",
        "repo_id": "repo_87ae50091a922d6cab8e",
        "language": "Python",
        "framework": None,
        "expected_paths": ["inference/generate.py", "inference/model.py"],
        "expected_answer_terms": ["json", "ModelArgs", "Transformer"],
    },
]
```

- [ ] Add one `unittest` method that retrieves each case and asserts:
  - each `expected_paths` entry appears in the first 5 citations or first 5 recommended patterns;
  - `context_pack["answer"]` contains every `expected_answer_terms` item case-insensitively.

Test command:

```bash
python3 -m unittest tests.test_retrieval_quality -v
```

Expected before implementation: fails because `answer` does not exist and `app/api/auth.ts` is not ranked.

### Task 2: Add Backward-Compatible `answer`

**Files:**

- Modify: `repo_wiki/domain/models.py`
- Modify: `repo_wiki/retrieval/context.py`

- [ ] Add `answer: str = ""` to `ContextPack`.
- [ ] In `build_context_pack()`, derive `answer` from selected object summaries and citation paths. Keep it simple and deterministic.

Minimum useful behavior:

```python
answer = build_answer(task, selected, citations)
```

`build_answer()` should:

- include top cited path names for "where/which modules" questions;
- use top object summaries for "what does/what happens/how" questions;
- return 1-3 short sentences;
- avoid saying "inspect" as the answer.

- [ ] In `to_markdown()`, insert:

```markdown
## Answer
...
```

before `## Recommended Patterns`.

Checks:

```bash
python3 -m unittest tests.test_retrieval_quality -v
python3 -m unittest discover -s tests -v
```

### Task 3: Boost Exact Path Matches

**Files:**

- Modify: `repo_wiki/core/retrieval_service.py`
- Modify: `repo_wiki/retrieval/rerank.py`
- Test: `tests/test_retrieval_quality.py`

- [ ] Extract path-like tokens from the query. A good-enough regex is enough:

```python
r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)+"
```

- [ ] Add `path_match_score` to ranking detail when a candidate payload path or citation path equals or ends with the query path.
- [ ] In `rerank()`, give exact path matches enough weight to beat broad FTS hits. This query must rank `app/api/auth.ts` above locales, constants, and store files:

```bash
REPO_WIKI_DATA_DIR=/tmp/repo-wiki-eval-data python3 -m repo_wiki.interfaces.cli retrieve "What does app/api/auth.ts do?" --repo repo_7098e0d33e9ab578c066 --language TypeScript --framework Next.js --format json --limit 5
```

Pass condition: top result or first citation is `app/api/auth.ts`, and `answer` mentions access code/API key auth.

### Task 4: Boost Symbol Matches

**Files:**

- Modify: `repo_wiki/core/retrieval_service.py`
- Modify: `repo_wiki/retrieval/rerank.py`
- Test: `tests/test_retrieval_quality.py`

- [ ] Extract CamelCase and identifier terms from the query. Keep the existing `normalized_terms()` behavior, but add a signal for exact symbols in `obj.payload["symbols"][*]["name"]`.
- [ ] Add `symbol_match_score` to ranking detail.
- [ ] Weight exact symbol matches high enough that `ModelArgs` ranks `inference/model.py`.

Acceptance command:

```bash
REPO_WIKI_DATA_DIR=/tmp/repo-wiki-eval-data python3 -m repo_wiki.interfaces.cli retrieve "Where is the inference config JSON loaded and who consumes ModelArgs?" --repo repo_87ae50091a922d6cab8e --language Python --format json --limit 5
```

Pass condition: result cites both `inference/generate.py` and `inference/model.py`, and `answer` states that `generate.py` loads JSON into `ModelArgs`, consumed by `Transformer`.

### Task 5: Fix Domain Inference

**Files:**

- Modify: `repo_wiki/compile/generator.py`
- Test: `tests/test_retrieval_quality.py`

- [ ] Change `infer_domain(path, dependency_names)` so `model` alone does not imply `database`.
- [ ] Only return `database` for stronger evidence: `db`, `database`, `schema`, `prisma`, `sql`, `migration`, or dependency names like `sqlalchemy`, `django`, `prisma`, `sequelize`.
- [ ] Add a regression assertion:

```python
from repo_wiki.compile.generator import infer_domain

self.assertEqual(infer_domain("inference/model.py", set()), "general")
self.assertEqual(infer_domain("prisma/schema.prisma", set()), "database")
```

Pass condition: DeepSeek `inference/model.py` no longer appears as "Database implementation pattern".

### Task 6: Improve Benchmark Reporting

**Files:**

- Modify: `repo_wiki/benchmarks/report.py`
- Test: add or update the smallest existing benchmark/report test in `tests/test_end_to_end.py` or `tests/test_retrieval_quality.py`

- [ ] Add judged hit counts to benchmark output when expected paths are present.
- [ ] If a benchmark case has no expected paths, print `Expected hits: not configured` instead of `Expected hits: 0/0`.
- [ ] Add one test that would fail on the current misleading `0/0` output.

Check:

```bash
python3 -m unittest discover -s tests -v
```

### Task 7: Re-run The 10 Deep Queries

**Files:**

- Modify: `evaluation_report.md` only after running queries

- [ ] Re-run all 10 query commands from section `4.4 Real-World Use Report`.
- [ ] Save JSON output under `/tmp/repo-wiki-eval-queries`.
- [ ] Update the query table judgments.

Score target:

- Fully correct direct answers: at least 6/10.
- Expected-path hit rate: at least 8/10.
- Existing unit tests: 100% pass.
- No new dependency added.

### Final Acceptance Gate

Run:

```bash
python3 -m py_compile scripts/build_benchmark_dataset.py
python3 -m unittest discover -s tests -v
REPO_WIKI_DATA_DIR=/tmp/repo-wiki-eval-data python3 -m repo_wiki.interfaces.cli status
REPO_WIKI_DATA_DIR=/tmp/repo-wiki-eval-data python3 -m repo_wiki.interfaces.cli retrieve "What does app/api/auth.ts do?" --repo repo_7098e0d33e9ab578c066 --language TypeScript --framework Next.js --format json --limit 5
REPO_WIKI_DATA_DIR=/tmp/repo-wiki-eval-data python3 -m repo_wiki.interfaces.cli retrieve "Where is the inference config JSON loaded and who consumes ModelArgs?" --repo repo_87ae50091a922d6cab8e --language Python --format json --limit 5
```

Required output:

- Unit tests pass.
- `status` works against `/tmp/repo-wiki-eval-data`.
- NextChat auth query cites `app/api/auth.ts` and answers that it validates access code/API key and may inject a provider system API key.
- DeepSeek config query cites `inference/generate.py` and `inference/model.py` and answers that `generate.py` loads JSON into `ModelArgs`, then `Transformer` consumes it.

### Later, Not First

- LLM-wiki style retrieval/ingestion: useful after the deterministic fixes. Add repo-level wiki pages only if they improve judged query accuracy beyond the roadmap target.
- Full GraphRAG replacement: do not do this now. The current graph is useful as expansion after exact path/symbol retrieval; replacing the pipeline adds complexity before the simpler failure is fixed.
- MCP SDK migration and versioned migration files: valuable, but lower score impact than retrieval accuracy.
