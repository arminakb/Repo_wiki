# Benchmarks

repo-wiki v0.1 is evaluated as a retrieval system first and a coding-agent improvement tool second.

## Retrieval Regression Tests

The focused regression suite lives in `tests/test_retrieval_quality.py`.

It checks whether retrieval ranks useful edit targets, related tests, runtime/use-site files, conventions, and citations for synthetic fixtures modeled after real repositories.

Covered scenarios include:

- GraphRAG-style config validation.
- FastAPI config endpoint validation.
- Parser behavior and same-stem tests.
- Exact entity/path ranking.
- Noisy competitor suppression.
- Citation and role-label behavior.

Run:

```bash
python3 -m unittest tests.test_retrieval_quality -v
```

## Multi-Repository Retrieval Benchmark

An earlier retrieval benchmark covered 19 repositories across healthcare, agentic AI workflow, backend/API architecture, and education AI software projects.

Summary:

- Python and TypeScript/JavaScript repositories were generally usable.
- Agentic AI workflow repositories were the strongest category.
- Go, C#, and Svelte repositories were weaker because v0.1 extraction is not first-class for those languages.
- Source-to-test pairing was the most common weakness.
- Large monorepos often needed scoped ingestion.

This benchmark informed the current retrieval-quality tests, but the raw cloned repositories and large result artifacts are intentionally not kept in the public repository.

## Coding-Agent A/B Benchmark

An initial five-repository A/B benchmark compared one coding agent with and without repo-wiki context packs.

| Repository | Baseline | Assisted | Delta | Interpretation |
| --- | ---: | ---: | ---: | --- |
| Dapr Agents | 8.0 | 8.0 | +0.0 | no meaningful difference |
| OpenScribe | 8.2 | 7.4 | -0.8 | context was noisy |
| VoltAgent | 8.1 | 8.2 | +0.1 | slight help |
| OpenMAIC | 8.0 | 7.7 | -0.3 | context was noisy |
| LangGraph | 8.0 | 6.9 | -1.1 | context missed an important behavior constraint |

Initial coding-agent A/B results were mixed, so repo-wiki currently treats retrieval quality and coding-agent improvement as separate evaluation targets.

## Blind Holdout Retrieval Benchmark

Retrieval v0.1 showed promising early results on a 5-repository blind holdout:

- 4 pass
- 1 partial
- 0 fail
- 12/15 expected targets found in the top 10
- full citation coverage

This is encouraging, but the sample is small and should not be treated as proof that repo-wiki improves coding agents in general.

## Key Results

- Retrieval can find likely edit targets and related tests for many Python and TypeScript tasks.
- File-level citations are available in context packs when license policy allows snippets.
- Role labels help separate edit targets, related tests, runtime risks, and convention examples.
- The benchmark work exposed weaknesses in source-to-test pairing and noisy generic matches.

## Limitations

- Benchmark sample sizes are small.
- Several regression cases are synthetic fixtures shaped like real repositories.
- The A/B benchmark used one agent and a small task set.
- Missing package managers or dependencies blocked some target-repository test runs.
- Results are not production claims.

## Reproduce Local Checks

```bash
python3 -m unittest tests.test_retrieval_quality -v
python3 -m unittest tests.test_end_to_end -v
python3 -m compileall repo_wiki
```
