# Coding-Agent A/B Benchmark

## 1. Purpose

This benchmark compares one coding agent, Codex CLI current agent, with and without repo-wiki context packs. The purpose is to measure whether repo-wiki context improves real coding-agent behavior: file discovery, planning, architecture consistency, test selection, patch quality, hallucination resistance, confidence, and validation results.

## 2. Methodology

- Selected repositories: Dapr Agents, OpenScribe, VoltAgent, OpenMAIC, and LangGraph from the previous 19-repository retrieval benchmark.
- Each repository used two isolated working copies under `/tmp/repo-wiki-coding-ab-benchmark/repos/<repo>/{baseline,assisted}`.
- Baseline runs received only the task and repository. Assisted runs received the same task plus one repo-wiki context pack, and were instructed to verify files before editing.
- Implementation was allowed. No remote pushes or destructive commands were used.
- Tasks were small validation/error-handling/parser tasks with one likely source file and one focused test file.
- Scoring is 1 to 10 per run, based on file discovery, architecture understanding, plan quality, test selection, correctness, minimality, convention following, risk awareness, hallucination resistance, validation, and overall quality.
- Validation was attempted with focused commands. In this environment, formal test runs were usually blocked by missing `pnpm`, `uv`, `pytest`, `vitest`, or project dependencies. Static checks and smoke checks are reported where available.
- Retrieval latency was not available in the saved context-pack outputs, so `retrieval_latency_ms` is recorded as `null` in JSON and blank in CSV.
- Ingestion/retrieval command fields are reconstructed from repo-wiki CLI conventions and saved context-pack metadata because the original CLI command transcripts for these five custom context packs were not preserved.

## 3. Repository Set

| Repository | Language/framework | Task | Implementation allowed |
| ---------- | ------------------ | ---- | ---------------------- |
| Dapr Agents | Python / Dapr workflows, Python agents | Add validation for WorkflowGrpcOptions keepalive options so keepalive_timeout_ms cannot be greater than keepalive_time_ms, and add a focused unit test in tests/workflow/test_grpc_options.py. | yes |
| OpenScribe | TypeScript / Next.js, React, Turborepo-style packages | Add validation to the transcription provider resolver so unknown TRANSCRIPTION_PROVIDER values throw a clear error instead of silently defaulting to whisper_local, and update packages/pipeline/transcribe/src/__tests__/provider-resolver.test.ts. | yes |
| VoltAgent | TypeScript / TypeScript agent framework, Next.js examples | Add validation to InMemoryLogBuffer so maxSize must be a positive integer, and add focused tests in packages/logger/src/buffer.spec.ts. | yes |
| OpenMAIC | TypeScript / Next.js, multi-agent classroom workflows | Extend the JSON repair parser to repair quoted numeric property fragments without a leading zero like "opacity: .5" and "x: -.25" without changing valid string content, and add focused tests in tests/generation/json-repair.test.ts. | yes |
| LangGraph | Python / LangGraph Python libraries | Add validation to JsonPlusSerializer allowlist normalization so allowed_msgpack_modules entries must be classes or non-empty string tuples, and add focused tests in libs/checkpoint/tests/test_jsonplus.py. | yes |

## 4. Overall Results

| Repository | Baseline score | Assisted score | Delta | Helped? | Main reason |
| ---------- | -------------: | -------------: | ----: | ------- | ----------- |
| Dapr Agents | 8.0 | 8.0 | +0.0 | no | Missed the exact focused test file and suggested unrelated runtime/type files as edit targets. |
| OpenScribe | 8.2 | 7.4 | -0.8 | no | Top edit targets were unrelated API-key/storage files, causing noisy discovery. |
| VoltAgent | 8.1 | 8.2 | +0.1 | yes | Correctly ranked packages/logger/src/buffer.ts as the top source file and included the exact spec file in test suggestions. |
| OpenMAIC | 8.0 | 7.7 | -0.3 | no | Top edit targets were unrelated importer/html-parser files, so source discovery still required manual search. |
| LangGraph | 8.0 | 6.9 | -1.1 | no | Assisted patch added a test expectation for allowed_msgpack_modules=True that the implementation does not satisfy because with_msgpack_allowlist returns self before validating extras. |

## 5. Per-Repository Results

### Repository: `Dapr Agents`

- URL/path: https://github.com/dapr/dapr-agents; local copies under `/tmp/repo-wiki-coding-ab-benchmark/repos/dapr-agents`
- Language/framework: Python / Dapr workflows, Python agents
- Package manager: uv / pytest
- Task: Add validation for WorkflowGrpcOptions keepalive options so keepalive_timeout_ms cannot be greater than keepalive_time_ms, and add a focused unit test in tests/workflow/test_grpc_options.py.
- Why task is suitable: Small validation invariant at a dataclass boundary with an obvious focused test file and runtime gRPC use site.
- Test command: `uv run pytest tests/workflow/test_grpc_options.py::test_keepalive_timeout_cannot_exceed_time`
- Implementation allowed: yes

#### Baseline Run

- Files inspected: `dapr_agents/agents/configs.py`, `tests/workflow/test_grpc_options.py`, `dapr_agents/workflow/utils/grpc.py`, `pyproject.toml`
- Files changed: `dapr_agents/agents/configs.py`, `tests/workflow/test_grpc_options.py`
- Implementation plan: Add a __post_init__ invariant after existing positive-value checks, then add one pytest case covering timeout > keepalive time.
- Tests identified: `uv run pytest tests/workflow/test_grpc_options.py::test_keepalive_timeout_ms_cannot_exceed_time`
- Tests run: `pytest command was blocked by missing uv/pytest in the environment`, `git diff captured in patches/dapr-agents-baseline.patch`
- Test result: Focused pytest could not be run because uv/pytest were unavailable; patch diff is minimal and syntactically straightforward.
- Confidence: 8/10
- Score: 8.0/10
- Notes: No saved final child-agent output was available, so this record is based on the isolated diff and transcript handoff.
- Patch: `docs/benchmarks/coding-ab/patches/dapr-agents-baseline.patch`

#### repo-wiki-Assisted Run

- Ingestion command: `Precomputed context pack used; original ingestion command not logged. CLI shape: REPO_WIKI_DATA_DIR=/tmp/repo-wiki-coding-ab-benchmark/data python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-coding-ab-benchmark/repos/dapr-agents/assisted --license-policy permissive_only`
- Retrieval command: `Precomputed context pack used; original retrieval command not logged. CLI shape: REPO_WIKI_DATA_DIR=/tmp/repo-wiki-coding-ab-benchmark/data python3 -m repo_wiki.interfaces.cli retrieve "Add validation for WorkflowGrpcOptions keepalive options so keepalive_timeout_ms cannot be greater than keepalive_time_ms, and add a focused unit test in tests/workflow/test_grpc_options.py." --repo repo_a12916253262216fa8fb --limit 10 --max-tokens 5000 --format json --license-policy permissive_only --language Python --framework "Dapr workflows"`
- Context pack ID: `ctx_56f6e5dfdb614335`
- Retrieval trace ID: `trace_7bf0e21fa1694f84`
- Retrieval latency: unavailable
- Top retrieved files: `dapr_agents/agents/configs.py`, `dapr_agents/workflow/utils/grpc.py`, `dapr_agents/types/workflow.py`
- Citations: present
- Warnings: Potential low-quality retrieval: exact task entities were detected but not found in the returned context.
- Files inspected: `dapr_agents/agents/configs.py`, `tests/workflow/test_grpc_options.py`, `dapr_agents/workflow/utils/grpc.py`, `dapr_agents/agents/durable.py`, `dapr_agents/agents/base.py`, `dapr_agents/agents/components.py`, `pyproject.toml`
- Files changed: `dapr_agents/agents/configs.py`, `tests/workflow/test_grpc_options.py`
- Implementation plan: Use the context pack to confirm WorkflowGrpcOptions, inspect the source and existing tests, add the cross-field guard, and run focused pytest if available.
- Tests identified: `uv run pytest tests/workflow/test_grpc_options.py::test_keepalive_timeout_cannot_exceed_time`
- Tests run: `uv run pytest tests/workflow/test_grpc_options.py::test_keepalive_timeout_cannot_exceed_time`, `python3 -m pytest tests/workflow/test_grpc_options.py::test_keepalive_timeout_cannot_exceed_time`, `python3 -m py_compile dapr_agents/agents/configs.py tests/workflow/test_grpc_options.py`, `git diff --check`, `direct module-load guard check`
- Test result: uv and pytest unavailable; py_compile, git diff --check, and a direct guard check passed.
- Confidence: 8/10
- Score: 8.0/10
- Notes: The context pack helped confirm the source file but did not identify the exact test file.
- Patch: `docs/benchmarks/coding-ab/patches/dapr-agents-assisted.patch`

#### Comparison

| Area | Baseline | Assisted | Winner | Evidence |
| ---- | -------- | -------- | ------ | -------- |
| file discovery | Found source and exact test manually. | Context found source; test found by inspection. | Tie | Both changed the same files. |
| architecture understanding | Placed invariant in dataclass boundary. | Same boundary after verifying context. | Tie | Both used __post_init__. |
| implementation planning | Simple source plus test plan. | Simple source plus test plan. | Tie | Equivalent plan quality. |
| test selection | Focused test file selected. | Focused test file selected after inspection. | Baseline | Context suggested unrelated tests. |
| patch quality | Correct minimal guard. | Correct minimal guard. | Tie | Diffs are functionally equivalent. |
| patch minimality | 16 insertions. | 16 insertions. | Tie | Same changed files. |
| convention following | Matched existing ValueError tests. | Matched existing ValueError tests. | Tie | Both follow local tests. |
| risk awareness | Covered cross-field invalid case. | Covered cross-field invalid case plus runtime use site inspection. | Assisted | Assisted inspected grpc utility. |
| hallucination resistance | No unsupported edits. | Ignored noisy suggested edit targets. | Tie | No unrelated file edits. |
| validation result | Formal tests blocked. | Formal tests blocked; extra static checks passed. | Assisted | Assisted recorded py_compile and guard smoke check. |

#### Verdict

repo-wiki made no meaningful difference. Baseline scored 8.0, assisted scored 8.0, delta +0.0. Main repo-wiki benefit: Identified dapr_agents/agents/configs.py as the source boundary. Main repo-wiki failure: Missed the exact focused test file and suggested unrelated runtime/type files as edit targets.

### Repository: `OpenScribe`

- URL/path: https://github.com/sammargolis/OpenScribe; local copies under `/tmp/repo-wiki-coding-ab-benchmark/repos/openscribe`
- Language/framework: TypeScript / Next.js, React, Turborepo-style packages
- Package manager: pnpm / node --test compiled output
- Task: Add validation to the transcription provider resolver so unknown TRANSCRIPTION_PROVIDER values throw a clear error instead of silently defaulting to whisper_local, and update packages/pipeline/transcribe/src/__tests__/provider-resolver.test.ts.
- Why task is suitable: Small resolver behavior change with explicit aliases, callers, and a focused Node test file.
- Test command: `pnpm build:test && node --test build/tests-dist/pipeline/transcribe/src/__tests__/provider-resolver.test.js`
- Implementation allowed: yes

#### Baseline Run

- Files inspected: `packages/pipeline/transcribe/src/providers/provider-resolver.ts`, `packages/pipeline/transcribe/src/__tests__/provider-resolver.test.ts`, `package.json`, `config/tsconfig.test.json`, `TRANSCRIPTION_PROVIDER usages`
- Files changed: `packages/pipeline/transcribe/src/providers/provider-resolver.ts`, `packages/pipeline/transcribe/src/__tests__/provider-resolver.test.ts`
- Implementation plan: Inspect resolver aliases, add a negative provider assertion, and throw for unknown non-empty normalized provider values while preserving blank/default behavior.
- Tests identified: `pnpm build:test`, `node --test build/tests-dist/pipeline/transcribe/src/__tests__/provider-resolver.test.js`
- Tests run: `pnpm build:test`, `git diff --check`
- Test result: pnpm build:test blocked because pnpm was not installed; git diff --check passed.
- Confidence: 8/10
- Score: 8.2/10
- Notes: Baseline error message listed canonical providers and supported aliases, including whisper-openai, openai, whisper, and med_asr.
- Patch: `docs/benchmarks/coding-ab/patches/openscribe-baseline.patch`

#### repo-wiki-Assisted Run

- Ingestion command: `Precomputed context pack used; original ingestion command not logged. CLI shape: REPO_WIKI_DATA_DIR=/tmp/repo-wiki-coding-ab-benchmark/data python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-coding-ab-benchmark/repos/openscribe/assisted --license-policy permissive_only`
- Retrieval command: `Precomputed context pack used; original retrieval command not logged. CLI shape: REPO_WIKI_DATA_DIR=/tmp/repo-wiki-coding-ab-benchmark/data python3 -m repo_wiki.interfaces.cli retrieve "Add validation to the transcription provider resolver so unknown TRANSCRIPTION_PROVIDER values throw a clear error instead of silently defaulting to whisper_local, and update packages/pipeline/transcribe/src/__tests__/provider-resolver.test.ts." --repo repo_45dd0bb56e58b2b1b858 --limit 10 --max-tokens 5000 --format json --license-policy permissive_only --language TypeScript --framework "Next.js"`
- Context pack ID: `ctx_dadea24335b44f63`
- Retrieval trace ID: `trace_9e93f8664611470f`
- Retrieval latency: unavailable
- Top retrieved files: `packages/storage/src/server-api-keys.ts`, `apps/web/src/app/api/settings/api-keys/route.ts`, `packages/pipeline/shared/src/error.ts`
- Citations: present
- Warnings: Potential low-quality retrieval: exact task entities were detected but not found in the returned context.
- Files inspected: `packages/pipeline/transcribe/src/providers/provider-resolver.ts`, `packages/pipeline/transcribe/src/__tests__/provider-resolver.test.ts`, `packages/pipeline/transcribe/src/index.ts`, `package.json`, `config/tsconfig.test.json`, `apps/web/src/app/api/transcription/segment/route.ts`, `apps/web/src/app/api/transcription/final/route.ts`
- Files changed: `packages/pipeline/transcribe/src/providers/provider-resolver.ts`, `packages/pipeline/transcribe/src/__tests__/provider-resolver.test.ts`
- Implementation plan: Disregard unrelated context targets after inspection, search the transcribe package, add unknown-provider test, and throw for unsupported non-empty providers.
- Tests identified: `pnpm build:test && node --test build/tests-dist/pipeline/transcribe/src/__tests__/provider-resolver.test.js`, `git diff --check`
- Tests run: `git diff --check`, `pnpm build:test && node --test build/tests-dist/pipeline/transcribe/src/__tests__/provider-resolver.test.js`
- Test result: git diff --check passed; focused test command blocked by missing pnpm.
- Confidence: 8/10
- Score: 7.4/10
- Notes: Patch is functional, but the error message lists canonical provider names only and uses the untrimmed env value in the message.
- Patch: `docs/benchmarks/coding-ab/patches/openscribe-assisted.patch`

#### Comparison

| Area | Baseline | Assisted | Winner | Evidence |
| ---- | -------- | -------- | ------ | -------- |
| file discovery | Directly found resolver and test. | Had to ignore unrelated context targets and search manually. | Baseline | Context top files were storage/API-key files. |
| architecture understanding | Understood alias resolver behavior. | Understood resolver after manual verification. | Baseline | Baseline preserved alias visibility in error text. |
| implementation planning | Focused resolver/test plan. | Plan corrected noisy context. | Baseline | Assisted spent effort overcoming context noise. |
| test selection | Selected exact test. | Context listed exact test as related. | Tie | Both used provider-resolver.test.ts. |
| patch quality | Clearer error includes aliases. | Clear but less complete provider list. | Baseline | Baseline message mentions alias spellings. |
| patch minimality | 11 insertions. | 13 insertions. | Baseline | Assisted line wrapping plus shorter provider list. |
| convention following | Existing node:test pattern. | Existing node:test pattern. | Tie | Both used assert.throws. |
| risk awareness | Preserved blank/default behavior. | Preserved blank/default behavior and inspected API callers. | Assisted | Assisted inspected runtime callers. |
| hallucination resistance | No unrelated edits. | Resisted unrelated context suggestions. | Assisted | Assisted avoided storage/API-key edits. |
| validation result | Formal tests blocked; diff check passed. | Formal tests blocked; diff check passed. | Tie | Same tooling blocker. |

#### Verdict

repo-wiki hurt performance. Baseline scored 8.2, assisted scored 7.4, delta -0.8. Main repo-wiki benefit: The context pack included the correct provider-resolver test as a related test. Main repo-wiki failure: Top edit targets were unrelated API-key/storage files, causing noisy discovery.

### Repository: `VoltAgent`

- URL/path: https://github.com/voltagent/voltagent; local copies under `/tmp/repo-wiki-coding-ab-benchmark/repos/voltagent`
- Language/framework: TypeScript / TypeScript agent framework, Next.js examples
- Package manager: pnpm / Vitest
- Task: Add validation to InMemoryLogBuffer so maxSize must be a positive integer, and add focused tests in packages/logger/src/buffer.spec.ts.
- Why task is suitable: Small constructor invariant with a direct test file and easy runtime risk in circular buffer behavior.
- Test command: `pnpm --filter @voltagent/logger test -- run src/buffer.spec.ts`
- Implementation allowed: yes

#### Baseline Run

- Files inspected: `packages/logger/src/buffer.ts`, `packages/logger/src/buffer.spec.ts`, `packages/logger/package.json`, `packages/logger/vitest.config.mts`, `packages/logger/src/types.ts`, `packages/logger/src/providers/pino.ts`, `package.json`, `pnpm-workspace.yaml`
- Files changed: `packages/logger/src/buffer.ts`, `packages/logger/src/buffer.spec.ts`
- Implementation plan: Add focused invalid-size constructor cases, then add a single Number.isInteger/maxSize > 0 guard.
- Tests identified: `pnpm --filter @voltagent/logger test -- src/buffer.spec.ts --run`
- Tests run: `pnpm --filter @voltagent/logger test -- src/buffer.spec.ts --run`
- Test result: Focused Vitest command blocked because pnpm was not installed and no local Vitest binary was present.
- Confidence: 8/10
- Score: 8.1/10
- Notes: Patch rejects 0, negatives, floats, NaN, and Infinity while preserving defaults.
- Patch: `docs/benchmarks/coding-ab/patches/voltagent-baseline.patch`

#### repo-wiki-Assisted Run

- Ingestion command: `Precomputed context pack used; original ingestion command not logged. CLI shape: REPO_WIKI_DATA_DIR=/tmp/repo-wiki-coding-ab-benchmark/data python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-coding-ab-benchmark/repos/voltagent/assisted --license-policy permissive_only`
- Retrieval command: `Precomputed context pack used; original retrieval command not logged. CLI shape: REPO_WIKI_DATA_DIR=/tmp/repo-wiki-coding-ab-benchmark/data python3 -m repo_wiki.interfaces.cli retrieve "Add validation to InMemoryLogBuffer so maxSize must be a positive integer, and add focused tests in packages/logger/src/buffer.spec.ts." --repo repo_a60d56a8a9dec6021052 --limit 10 --max-tokens 5000 --format json --license-policy permissive_only --language TypeScript --framework "TypeScript agent framework"`
- Context pack ID: `ctx_6424324d772c4a1a`
- Retrieval trace ID: `trace_c4293de43b8c49dc`
- Retrieval latency: unavailable
- Top retrieved files: `packages/logger/src/buffer.ts`, `packages/core/src/logger/console-logger.ts`, `packages/logger/src/index.ts`
- Citations: not present in saved pack
- Warnings: Potential low-quality retrieval: exact task entities were detected but not found in the returned context.
- Files inspected: `packages/logger/src/buffer.ts`, `packages/logger/src/buffer.spec.ts`, `packages/logger/src/index.ts`, `packages/logger/package.json`, `package.json`, `packages/logger/project.json`, `related logger test references`
- Files changed: `packages/logger/src/buffer.ts`, `packages/logger/src/buffer.spec.ts`
- Implementation plan: Use context to inspect buffer source/spec, add invalid maxSize tests, add constructor validation, and run focused logger tests.
- Tests identified: `pnpm --filter @voltagent/logger test -- run src/buffer.spec.ts`
- Tests run: `pnpm --filter @voltagent/logger test -- run src/buffer.spec.ts`, `git diff --check -- packages/logger/src/buffer.ts packages/logger/src/buffer.spec.ts`
- Test result: Focused Vitest command blocked by missing pnpm; git diff --check passed.
- Confidence: 8/10
- Score: 8.2/10
- Notes: Implementation matches baseline behavior with a loop-based test instead of it.each.
- Patch: `docs/benchmarks/coding-ab/patches/voltagent-assisted.patch`

#### Comparison

| Area | Baseline | Assisted | Winner | Evidence |
| ---- | -------- | -------- | ------ | -------- |
| file discovery | Found source/spec manually. | Context ranked source first and spec in test list. | Assisted | Correct top source in context pack. |
| architecture understanding | Constructor boundary understood. | Constructor boundary understood. | Tie | Same source guard. |
| implementation planning | Direct focused plan. | Direct focused plan with context confirmation. | Assisted | Context reduced search ambiguity. |
| test selection | Exact spec selected. | Exact spec selected. | Tie | Both used buffer.spec.ts. |
| patch quality | Correct guard and parametrized test. | Correct guard and loop test. | Tie | Equivalent behavior. |
| patch minimality | 13 insertions. | 12 insertions. | Assisted | Assisted test slightly shorter. |
| convention following | Vitest pattern. | Vitest pattern. | Tie | Both use expect/toThrow. |
| risk awareness | Covered NaN/Infinity. | Covered NaN/Infinity. | Tie | Same invalid classes. |
| hallucination resistance | No unrelated edits. | Ignored console logger suggestion. | Assisted | No unrelated file edits despite noisy candidate. |
| validation result | Tests blocked. | Tests blocked; diff check passed. | Assisted | Assisted recorded static check. |

#### Verdict

repo-wiki slightly helped. Baseline scored 8.1, assisted scored 8.2, delta +0.1. Main repo-wiki benefit: Correctly ranked packages/logger/src/buffer.ts as the top source file and included the exact spec file in test suggestions. Main repo-wiki failure: Also ranked an unrelated core console logger as an edit target and produced no citations in the saved pack.

### Repository: `OpenMAIC`

- URL/path: https://github.com/THU-MAIC/OpenMAIC; local copies under `/tmp/repo-wiki-coding-ab-benchmark/repos/openmaic`
- Language/framework: TypeScript / Next.js, multi-agent classroom workflows
- Package manager: pnpm / npm / Vitest
- Task: Extend the JSON repair parser to repair quoted numeric property fragments without a leading zero like "opacity: .5" and "x: -.25" without changing valid string content, and add focused tests in tests/generation/json-repair.test.ts.
- Why task is suitable: Small parser repair with a focused test and an edge case where naive fixes can emit invalid JSON or modify strings.
- Test command: `pnpm vitest run tests/generation/json-repair.test.ts`
- Implementation allowed: yes

#### Baseline Run

- Files inspected: `package.json`, `vitest.config.ts`, `tsconfig.json`, `tests/setup-env.ts`, `tests/generation/json-repair.test.ts`, `lib/generation/json-repair.ts`
- Files changed: `lib/generation/json-repair.ts`, `tests/generation/json-repair.test.ts`
- Implementation plan: Add a regression for leading-decimal numeric fragments, patch the existing repair regex, and normalize leading-dot numbers to legal JSON numbers.
- Tests identified: `pnpm vitest run tests/generation/json-repair.test.ts`
- Tests run: `pnpm vitest run tests/generation/json-repair.test.ts`, `node regex smoke check`
- Test result: Vitest blocked by missing pnpm/node_modules; direct Node regex smoke check passed.
- Confidence: 8/10
- Score: 8.0/10
- Notes: Baseline initially risked invalid JSON but caught it with the smoke check and fixed normalization.
- Patch: `docs/benchmarks/coding-ab/patches/openmaic-baseline.patch`

#### repo-wiki-Assisted Run

- Ingestion command: `Precomputed context pack used; original ingestion command not logged. CLI shape: REPO_WIKI_DATA_DIR=/tmp/repo-wiki-coding-ab-benchmark/data python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-coding-ab-benchmark/repos/openmaic/assisted --license-policy permissive_only`
- Retrieval command: `Precomputed context pack used; original retrieval command not logged. CLI shape: REPO_WIKI_DATA_DIR=/tmp/repo-wiki-coding-ab-benchmark/data python3 -m repo_wiki.interfaces.cli retrieve "Extend the JSON repair parser to repair quoted numeric property fragments without a leading zero like "opacity: .5" and "x: -.25" without changing valid string content, and add focused tests in tests/generation/json-repair.test.ts." --repo repo_5272845c8c97d05bac96 --limit 10 --max-tokens 5000 --format json --license-policy permissive_only --language TypeScript --framework "Next.js"`
- Context pack ID: `ctx_624b41a8fc024ac7`
- Retrieval trace ID: `trace_803c1a4846b04c53`
- Retrieval latency: unavailable
- Top retrieved files: `packages/@openmaic/importer/src/import-pipeline/index.ts`, `packages/@openmaic/importer/scripts/transvert.ts`, `lib/export/html-parser/parser.ts`, `lib/generation/generation-pipeline.ts`, `lib/generation/action-parser.ts`, `lib/generation/outline-generator.ts`, `lib/generation/json-repair.ts`
- Citations: present
- Warnings: Potential low-quality retrieval: exact task entities were detected but not found in the returned context.
- Files inspected: `lib/generation/json-repair.ts`, `tests/generation/json-repair.test.ts`, `package.json`, `vitest.config.ts`, `parser callers via rg`
- Files changed: `lib/generation/json-repair.ts`, `tests/generation/json-repair.test.ts`
- Implementation plan: Inspect shared parser helper and callers, add leading-dot regression test, extend numeric regex, normalize repaired values, and run focused tests or smoke checks.
- Tests identified: `tests/generation/json-repair.test.ts`, `pnpm vitest run tests/generation/json-repair.test.ts`, `npm test -- tests/generation/json-repair.test.ts`
- Tests run: `pnpm vitest run tests/generation/json-repair.test.ts`, `npm test -- tests/generation/json-repair.test.ts`, `git diff --check`, `node -e regex smoke check`
- Test result: pnpm and vitest unavailable; git diff --check and targeted regex smoke check passed.
- Confidence: 7/10
- Score: 7.7/10
- Notes: Correct patch, but slightly more verbose than baseline and context was noisy.
- Patch: `docs/benchmarks/coding-ab/patches/openmaic-assisted.patch`

#### Comparison

| Area | Baseline | Assisted | Winner | Evidence |
| ---- | -------- | -------- | ------ | -------- |
| file discovery | Found parser/test directly. | Context ranked parser low as runtime risk; agent searched manually. | Baseline | Top context files were importer/html-parser. |
| architecture understanding | Patched shared repair helper. | Patched shared repair helper. | Tie | Same boundary. |
| implementation planning | Added regression then normalized output. | Same plan after context verification. | Tie | Both cover string preservation. |
| test selection | Exact focused test selected. | Context included exact test. | Tie | Both used json-repair.test.ts. |
| patch quality | Correct concise normalization. | Correct normalization with local variable. | Baseline | Baseline is shorter. |
| patch minimality | 25 insertions, 2 deletions. | 27 insertions, 2 deletions. | Baseline | Assisted added extra lines. |
| convention following | Vitest style matched. | Vitest style matched. | Tie | Both add one test case. |
| risk awareness | Smoke check caught invalid JSON risk. | Explicitly noted string guard and ran smoke check. | Tie | Both validated edge case. |
| hallucination resistance | No unrelated edits. | Ignored unrelated context edit targets. | Assisted | Assisted resisted noisy context. |
| validation result | Formal tests blocked; smoke passed. | Formal tests blocked; smoke/diff passed. | Tie | Equivalent practical validation. |

#### Verdict

repo-wiki made no meaningful difference. Baseline scored 8.0, assisted scored 7.7, delta -0.3. Main repo-wiki benefit: Context included the correct json-repair test and source as lower-ranked runtime risk. Main repo-wiki failure: Top edit targets were unrelated importer/html-parser files, so source discovery still required manual search.

### Repository: `LangGraph`

- URL/path: https://github.com/langchain-ai/langgraph; local copies under `/tmp/repo-wiki-coding-ab-benchmark/repos/langgraph`
- Language/framework: Python / LangGraph Python libraries
- Package manager: uv / pytest / ruff
- Task: Add validation to JsonPlusSerializer allowlist normalization so allowed_msgpack_modules entries must be classes or non-empty string tuples, and add focused tests in libs/checkpoint/tests/test_jsonplus.py.
- Why task is suitable: Small serializer validation task with constructor and helper method paths, local tests, and type/edge-case risks.
- Test command: `cd libs/checkpoint && make test TEST='tests/test_jsonplus.py -k "msgpack_allowlist_rejects_invalid_entries or with_msgpack_allowlist_rejects_invalid_entries"'`
- Implementation allowed: yes

#### Baseline Run

- Files inspected: `libs/checkpoint/langgraph/checkpoint/serde/jsonplus.py`, `libs/checkpoint/tests/test_jsonplus.py`, `libs/checkpoint/Makefile`, `pyproject.toml`
- Files changed: `libs/checkpoint/langgraph/checkpoint/serde/jsonplus.py`, `libs/checkpoint/tests/test_jsonplus.py`
- Implementation plan: Validate allowlist entries inside the shared normalizer, pass allowlist names for clearer errors, and add constructor plus with_msgpack_allowlist tests.
- Tests identified: `make test TEST='tests/test_jsonplus.py -k "msgpack_allowlist_rejects_invalid_entries or with_msgpack_allowlist_rejects_invalid_entries"'`
- Tests run: `make test focused command`, `python -m pytest focused command`, `python -m py_compile libs/checkpoint/langgraph/checkpoint/serde/jsonplus.py libs/checkpoint/tests/test_jsonplus.py`, `git diff --check`
- Test result: make/pytest blocked by missing uv and pytest; py_compile and diff check passed in available environment.
- Confidence: 7/10
- Score: 8.0/10
- Notes: Baseline test coverage is internally consistent for constructor invalid entries and with_msgpack_allowlist when base allowlist is None.
- Patch: `docs/benchmarks/coding-ab/patches/langgraph-baseline.patch`

#### repo-wiki-Assisted Run

- Ingestion command: `Precomputed context pack used; original ingestion command not logged. CLI shape: REPO_WIKI_DATA_DIR=/tmp/repo-wiki-coding-ab-benchmark/data python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-coding-ab-benchmark/repos/langgraph/assisted --license-policy permissive_only`
- Retrieval command: `Precomputed context pack used; original retrieval command not logged. CLI shape: REPO_WIKI_DATA_DIR=/tmp/repo-wiki-coding-ab-benchmark/data python3 -m repo_wiki.interfaces.cli retrieve "Add validation to JsonPlusSerializer allowlist normalization so allowed_msgpack_modules entries must be classes or non-empty string tuples, and add focused tests in libs/checkpoint/tests/test_jsonplus.py." --repo repo_cd0b1984375fdedde95b --limit 10 --max-tokens 5000 --format json --license-policy permissive_only --language Python --framework "LangGraph Python libraries"`
- Context pack ID: `ctx_1e0a643797f0437f`
- Retrieval trace ID: `trace_7c9bd2fbf30941ef`
- Retrieval latency: unavailable
- Top retrieved files: `libs/checkpoint/langgraph/checkpoint/serde/jsonplus.py`, `libs/checkpoint-conformance/langgraph/checkpoint/conformance/validate.py`, `libs/prebuilt/langgraph/prebuilt/tool_validator.py`
- Citations: present
- Warnings: Potential low-quality retrieval: exact task entities were detected but not found in the returned context.
- Files inspected: `libs/checkpoint/langgraph/checkpoint/serde/jsonplus.py`, `libs/checkpoint/tests/test_jsonplus.py`, `libs/checkpoint/Makefile`, `normalizer call sites via rg`
- Files changed: `libs/checkpoint/langgraph/checkpoint/serde/jsonplus.py`, `libs/checkpoint/tests/test_jsonplus.py`
- Implementation plan: Use context to locate jsonplus.py, add invalid allowlist tests, add validation in _normalize_module_keys, then run focused make test/format/lint or static checks.
- Tests identified: `make test TEST='tests/test_jsonplus.py -k "msgpack_allowlist_rejects_invalid_entries or with_msgpack_allowlist_rejects_invalid_entries"'`, `make format`, `make lint`
- Tests run: `make test focused command`, `python -m pytest focused command`, `python -m py_compile libs/checkpoint/langgraph/checkpoint/serde/jsonplus.py libs/checkpoint/tests/test_jsonplus.py`, `git diff --check`, `make format`, `make lint`
- Test result: make test/format/lint blocked by missing uv; python pytest/import dependencies unavailable; py_compile and diff check passed.
- Confidence: 6/10
- Score: 6.9/10
- Notes: Source validation is mostly correct, but one added test loops over None and True even though the True branch returns self before validating extra entries.
- Patch: `docs/benchmarks/coding-ab/patches/langgraph-assisted.patch`

#### Comparison

| Area | Baseline | Assisted | Winner | Evidence |
| ---- | -------- | -------- | ------ | -------- |
| file discovery | Found serializer/test manually. | Context ranked serializer first. | Assisted | Correct top source file. |
| architecture understanding | Validated shared normalizer and helper path. | Validated shared normalizer but missed True no-op interaction in test expectation. | Baseline | Assisted test contradicts implementation. |
| implementation planning | Constructor and helper method covered. | Constructor and helper method covered plus extra True case. | Baseline | Extra True case is not implemented. |
| test selection | Exact test file selected. | Exact test file selected from context. | Tie | Both used test_jsonplus.py. |
| patch quality | Internally consistent validation patch. | Mostly correct source but likely failing assisted test. | Baseline | with_msgpack_allowlist returns self for True. |
| patch minimality | 48 insertions, 8 deletions. | 49 insertions, 6 deletions. | Tie | Similar size. |
| convention following | Local pytest parametrize style. | Local pytest parametrize style. | Tie | Both fit nearby tests. |
| risk awareness | Covers invalid strings, empty tuples, bad tuple values. | Covers additional object() but adds unsupported True expectation. | Baseline | Assisted has a false expectation risk. |
| hallucination resistance | No unrelated edits. | No unrelated edits and ignored examples. | Tie | Both changed only source/test. |
| validation result | Formal tests blocked; static checks passed. | Formal tests blocked; static checks passed but static review found test defect. | Baseline | No green formal test run to catch the defect. |

#### Verdict

repo-wiki hurt performance. Baseline scored 8.0, assisted scored 6.9, delta -1.1. Main repo-wiki benefit: Correctly ranked jsonplus.py as the primary edit target and identified validation convention examples. Main repo-wiki failure: Assisted patch added a test expectation for allowed_msgpack_modules=True that the implementation does not satisfy because with_msgpack_allowlist returns self before validating extras.

## 6. Aggregate Findings

- repo-wiki helped most when the task named a unique symbol and the pack ranked the primary file first. VoltAgent and LangGraph both had strong primary-source retrieval.
- repo-wiki did not help when lexical signals pulled the pack toward adjacent but unrelated configuration or importer files. OpenScribe and OpenMAIC are the clearest examples.
- The best assisted behavior was hallucination resistance: agents often ignored noisy context after inspecting the repository. The context pack did not force unrelated edits.
- The biggest weakness was source-to-test pairing. Dapr missed the exact focused test; VoltAgent listed the right test but after unrelated tests; OpenScribe and OpenMAIC buried correct files below noisy targets.
- Citations were useful when present, but the VoltAgent saved pack had no citations despite listing relevant files.
- Formal validation remains a benchmark limitation because the environment did not have the package managers and dependencies needed for most focused test commands.
- Best repo/task types for the next round: small validation changes around named classes or functions in TypeScript/Python repos with existing focused test files.
- Worst repo/task types in this run: tasks where common terms such as provider, JSON, config, or validation also appear heavily in unrelated packages.

## 7. Recommendations Before 0-to-100 Project Generation

- Improve exact symbol/path matching for task entities before broader benchmarks. The pack should rank `TRANSCRIPTION_PROVIDER`, `parseJsonResponse`, and focused test files above generic config/importer files.
- Add stronger source-to-test pairing so context packs surface the exact nearby test file in the top three results.
- Show confidence and warnings more bluntly in the context-pack header when retrieval is low quality, and include a short "do not edit these unless confirmed" note for noisy targets.
- Preserve citations for every recommended file. A pack with no citations should be treated as degraded.
- Capture retrieval latency and CLI command metadata automatically into the context pack or benchmark harness.
- Add benchmark tooling that launches paired baseline/assisted isolated worktrees and records transcripts, diffs, tests, and scores automatically.
- Include an agent workflow prompt that says to treat repo-wiki context as a hypothesis, inspect files, and report when context is wrong.
- Keep repository selection focused on Python and TypeScript until multi-language ingestion gaps from the previous benchmark are fixed.

## 8. Next Phase Plan

- Ready for more A/B tests: yes, but keep them limited and focused on Python/TypeScript repos with runnable dependency setup.
- Ready for multiple-agent comparison: not yet. First improve benchmark automation and context-pack logging so runs are reproducible.
- Ready for opencode testing: yes as a limited single-agent or two-agent comparison on the same five tasks, after dependency setup is made reproducible.
- Ready for 0-to-100 project generation: no. Current evidence only covers small maintenance tasks, and retrieval still produces noisy context on some repositories.

## Artifacts

- `docs/benchmarks/coding-ab/results.csv`
- `docs/benchmarks/coding-ab/results.json`
- `docs/benchmarks/coding-ab/patches/` with baseline and assisted diffs for all five repositories
