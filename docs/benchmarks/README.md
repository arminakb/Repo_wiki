# Benchmarks

repo-wiki benchmarks are evidence records, not marketing claims. The current results show useful retrieval behavior, but they do not prove that repo-wiki consistently improves autonomous coding outcomes.

## Available artifacts

| Artifact | Purpose |
| --- | --- |
| [retrieval-quality.md](retrieval-quality.md) | Fixture-backed retrieval quality regression suite. |
| [multi-repo/retrieval-benchmark.md](multi-repo/retrieval-benchmark.md) | Multi-repository retrieval benchmark across varied projects. |
| [coding-ab/agent-ab-benchmark.md](coding-ab/agent-ab-benchmark.md) | Initial coding-agent A/B benchmark with and without repo-wiki context. |
| [coding-ab/retrieval-recheck.md](coding-ab/retrieval-recheck.md) | Retrieval-only recheck after retrieval/context-pack fixes. |
| [blind-holdout-v0.1.md](blind-holdout-v0.1.md) | Blind holdout retrieval run on new local repositories. |

## retrieval v0.1 blind holdout

- 5 new repositories.
- 4 pass.
- 1 partial.
- 0 fail.
- Average score: 7.8/10.
- Top-10 expected hits: 12/15.
- Top-5 expected hits: 10/15.
- Citation coverage: 100%.

The holdout used local snapshots and fixed expected files before retrieval results were inspected.

## Coding-agent A/B result

Initial coding-agent A/B results were mixed; repo-wiki did not yet consistently improve coding outcomes. The project currently treats retrieval quality and coding-agent usefulness as separate evaluation targets.

Observed A/B outcomes:

- Dapr Agents: no meaningful difference.
- OpenScribe: repo-wiki hurt.
- VoltAgent: repo-wiki slightly helped.
- OpenMAIC: no meaningful difference / slight hurt.
- LangGraph: repo-wiki hurt.

Those failures drove the retrieval v0.1 fixes for exact entities, cited context roles, source-to-test pairing, behavioral constraint notes, and actionable warnings.

## How to reproduce local smoke reports

```bash
python3 -m repo_wiki.interfaces.cli benchmark report --output docs/benchmarks/mvp-results.md
python3 -m unittest tests.test_retrieval_quality -v
```

Larger benchmarks require local repository snapshots or explicit clone steps and should be run with a temporary `REPO_WIKI_DATA_DIR`.

## Limitations

- Results depend on local snapshots and chosen tasks.
- Retrieval-only quality does not guarantee better code patches.
- Some coding A/B validation was blocked by missing project-specific dependencies.
- v0.1 benchmark tooling is intentionally lightweight and manually reviewed.
