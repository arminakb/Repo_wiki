# MVP Benchmark Results

Generated: 2026-06-22T02:09:27Z

## Local Index Metrics

- Indexed repositories: 1
- Repository snapshots: 1
- Indexed files: 80
- Extracted symbols: 297
- Dependencies: 0
- Knowledge objects: 35
- Graph nodes: 425
- Graph edges: 791
- Context packs: 0
- Feedback records: 0
- Staged knowledge records: 0
- Supported languages: Python
- Supported interfaces: CLI, HTTP API, MCP

## Retrieval Quality Suite

- Tasks run: 5
- Average returned items: 5
- Average citation count: 9.6
- Average latency: 14 ms
- Citation coverage: 1.0
- Expected hits: 0/0
- Top-k precision: 0

| Task | Trace | Latency ms | Returned Items | Citations | Citation Coverage | Expected Hits | Candidate Counts |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| backend: implement FastAPI auth endpoint with tests | `trace_a311622b02344f9d` | 14 | 5 | 12 | 1.0 | 0/0 | fts=15, vector=20, merged=25, graph_expanded=0, total=25 |
| frontend: add Next.js route handler with validation | `trace_596ae6a8e1b94df8` | 11 | 5 | 7 | 1.0 | 0/0 | fts=1, vector=20, merged=20, graph_expanded=0, total=20 |
| testing: add pytest coverage for password reset | `trace_3119d3bb42454fb1` | 13 | 5 | 7 | 1.0 | 0/0 | fts=1, vector=20, merged=20, graph_expanded=0, total=20 |
| refactor: simplify service layer and update tests | `trace_3250906efc774292` | 12 | 5 | 12 | 1.0 | 0/0 | fts=15, vector=20, merged=29, graph_expanded=0, total=29 |
| bug-fix: fix route validation error handling | `trace_340e93fa2c294e7e` | 20 | 5 | 10 | 1.0 | 0/0 | fts=1, vector=20, merged=20, graph_expanded=0, total=20 |

## Per-Category Quality

| Category | Tasks | Citation Coverage | Expected Hits | Top-k Precision |
| --- | ---: | ---: | ---: | ---: |
| backend | 1 | 1.0 | 0/0 | 0 |
| frontend | 1 | 1.0 | 0/0 | 0 |
| testing | 1 | 1.0 | 0/0 | 0 |
| refactor | 1 | 1.0 | 0/0 | 0 |
| bug-fix | 1 | 1.0 | 0/0 | 0 |

## Reproduce

```bash
repo-wiki benchmark report --output docs/benchmarks/mvp-results.md
```
