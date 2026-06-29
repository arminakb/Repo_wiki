# Coding A/B Retrieval Recheck

## 1. Purpose

This retrieval-only recheck tests whether the recent repo-wiki retrieval/context-pack fixes address the failures observed in the first five-repository coding-agent A/B benchmark before rerunning implementation work. No target repository patches were implemented and repo-wiki retrieval logic was not changed during this recheck.

Method note: full clean exports of OpenScribe/OpenMAIC exceeded available `/tmp` space, so each repository was re-ingested from a clean `HEAD` path-limited snapshot containing the expected source/test files plus the noisy competitor files identified in the previous benchmark. This is sufficient for failure-mode verification, but it is not a full-corpus rerun.

## 2. Rechecked Tasks

| Repository | Task | Previous failure |
| ---------- | ---- | ---------------- |
| Dapr Agents | Add validation for WorkflowGrpcOptions keepalive options so keepalive_timeout_ms cannot be greater than keepalive_time_ms, and add a focused unit test in tests/workflow/test_grpc_options.py. | Missed the exact focused test file and suggested unrelated runtime/type files as edit targets. |
| OpenScribe | Add validation to the transcription provider resolver so unknown TRANSCRIPTION_PROVIDER values throw a clear error instead of silently defaulting to whisper_local, and update packages/pipeline/transcribe/src/__tests__/provider-resolver.test.ts. | Top edit targets were unrelated API-key/storage files, causing noisy discovery. |
| VoltAgent | Add validation to InMemoryLogBuffer so maxSize must be a positive integer, and add focused tests in packages/logger/src/buffer.spec.ts. | Also ranked an unrelated core console logger as an edit target and produced no citations in the saved pack. |
| OpenMAIC | Extend the JSON repair parser to repair quoted numeric property fragments without a leading zero like "opacity: .5" and "x: -.25" without changing valid string content, and add focused tests in tests/generation/json-repair.test.ts. | Top edit targets were unrelated importer/html-parser files, so source discovery still required manual search. |
| LangGraph | Add validation to JsonPlusSerializer allowlist normalization so allowed_msgpack_modules entries must be classes or non-empty string tuples, and add focused tests in libs/checkpoint/tests/test_jsonplus.py. | Assisted patch added a test expectation for allowed_msgpack_modules=True that the implementation does not satisfy because with_msgpack_allowlist returns self before validating extras. |

## 3. Overall Results

| Repository | Previous assisted verdict | New retrieval score | Ready for A/B rerun? | Main reason |
| ---------- | ------------------------- | ------------------: | -------------------- | ----------- |
| Dapr Agents | repo-wiki made no meaningful difference | 6.6 | No | The focused test is now rank 4 and cited, but grpc.py and workflow.py are still labeled edit targets and the low-quality warning remains. |
| OpenScribe | repo-wiki hurt performance | 4.7 | No | The exact test is rank 2, but provider-resolver.ts is only rank 5/runtime risk and noisy API-key/storage/error files still outrank it as edit targets. |
| VoltAgent | repo-wiki slightly helped | 6.6 | No | buffer.ts and buffer.spec.ts are ranks 1 and 2, but permissive-only retrieval still produced no citations, so confident roles were withheld. |
| OpenMAIC | repo-wiki made no meaningful difference | 4.0 | No | json-repair.ts improved only to rank 5/runtime risk while importer and html-parser files remain top edit targets. |
| LangGraph | repo-wiki hurt performance | 7.4 | No | jsonplus.py and test_jsonplus.py are ranks 1 and 2 with citations, but no behavioral constraint note was emitted for the allowlist early-return path. |

## 4. Per-Repository Recheck

### Repository: `Dapr Agents`

- Original task: Add validation for WorkflowGrpcOptions keepalive options so keepalive_timeout_ms cannot be greater than keepalive_time_ms, and add a focused unit test in tests/workflow/test_grpc_options.py.
- Previous repo-wiki failure: Missed the exact focused test file and suggested unrelated runtime/type files as edit targets.
- Retrieval command: `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-ab-retrieval-recheck/data/dapr-agents python3 -m repo_wiki.interfaces.cli retrieve 'Add validation for WorkflowGrpcOptions keepalive options so keepalive_timeout_ms cannot be greater than keepalive_time_ms, and add a focused unit test in tests/workflow/test_grpc_options.py.' --repo repo_f3845976f6c642aadfa7 --limit 10 --max-tokens 5000 --format json --license-policy permissive_only --language Python --framework 'Dapr workflows'`
- Context pack ID: `ctx_b79be31a09b44867`
- Latency: 169 ms
- Warnings: Potential low-quality retrieval: exact task entities were detected but not found in the returned context.
- Behavioral constraint notes: none

Top retrieved results:

| Rank | File/Object | Role label | Citation present? | Judgment |
| ---: | ----------- | ---------- | ----------------: | -------- |
| 1 | `dapr_agents/agents/configs.py` | edit target | yes | expected edit target |
| 2 | `dapr_agents/workflow/utils/grpc.py` | edit target | yes | candidate edit target |
| 3 | `dapr_agents/types/workflow.py` | edit target | yes | known noisy competitor |
| 4 | `tests/workflow/test_grpc_options.py` | related test | yes | expected focused test |
| 5 | `dapr-agents project profile` |  | yes | supporting context |
| 6 | `dapr-agents api architecture pattern` |  | yes | supporting context |

Expected key file check:

| Expected item | Previous status | Current rank | Improved? | Notes |
| ------------- | --------------- | -----------: | --------: | ----- |
| `dapr_agents/agents/configs.py` | rank 1 | 1 | no | ranked in top 10 |
| `tests/workflow/test_grpc_options.py` | missed/absent from old top related tests | 4 | yes | ranked in top 10 |
| `dapr_agents/workflow/utils/grpc.py` | ranked as edit target/runtime context | 2 | no | ranked in top 10 |

Quality scores:

| Metric | Score |
| ------ | ----: |
| Exact entity ranking | 8 |
| Related test retrieval | 7 |
| Citation quality | 9 |
| Role labeling | 5 |
| Behavioral constraint quality | 5 |
| Noise control | 5 |
| Likely coding-agent usefulness | 7 |

Verdict:

improved but needs another retrieval fix. The focused test is now rank 4 and cited, but grpc.py and workflow.py are still labeled edit targets and the low-quality warning remains.

### Repository: `OpenScribe`

- Original task: Add validation to the transcription provider resolver so unknown TRANSCRIPTION_PROVIDER values throw a clear error instead of silently defaulting to whisper_local, and update packages/pipeline/transcribe/src/__tests__/provider-resolver.test.ts.
- Previous repo-wiki failure: Top edit targets were unrelated API-key/storage files, causing noisy discovery.
- Retrieval command: `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-ab-retrieval-recheck/data/openscribe python3 -m repo_wiki.interfaces.cli retrieve 'Add validation to the transcription provider resolver so unknown TRANSCRIPTION_PROVIDER values throw a clear error instead of silently defaulting to whisper_local, and update packages/pipeline/transcribe/src/__tests__/provider-resolver.test.ts.' --repo repo_40eb9802430f092394d9 --limit 10 --max-tokens 5000 --format json --license-policy permissive_only --language TypeScript --framework Next.js`
- Context pack ID: `ctx_b2a3e374568f42c8`
- Latency: 66 ms
- Warnings: Potential low-quality retrieval: exact task entities were detected but not found in the returned context.
- Behavioral constraint notes: Behavioral constraint: check early return branch `if (provider === "medasr" || provider === "med_asr") {`.; Behavioral constraint: check early return branch `if (provider === "whisper_openai" || provider === "whisper-openai" || provider === "openai" || provider === "whisper") {`.

Top retrieved results:

| Rank | File/Object | Role label | Citation present? | Judgment |
| ---: | ----------- | ---------- | ----------------: | -------- |
| 1 | `packages/pipeline/shared/src/error.ts` | edit target | yes | known noisy competitor |
| 2 | `packages/pipeline/transcribe/src/__tests__/provider-resolver.test.ts` | related test | yes | expected focused test |
| 3 | `packages/storage/src/server-api-keys.ts` | edit target | yes | known noisy competitor |
| 4 | `apps/web/src/app/api/settings/api-keys/route.ts` | edit target | yes | known noisy competitor |
| 5 | `packages/pipeline/transcribe/src/providers/provider-resolver.ts` | runtime risk | yes | expected edit target |
| 6 | `openscribe project profile` |  | yes | supporting context |
| 7 | `openscribe fullstack architecture pattern` |  | yes | supporting context |

Expected key file check:

| Expected item | Previous status | Current rank | Improved? | Notes |
| ------------- | --------------- | -----------: | --------: | ----- |
| `packages/pipeline/transcribe/src/providers/provider-resolver.ts` | missed from old top recommended files | 5 | yes | ranked in top 10 |
| `packages/pipeline/transcribe/src/__tests__/provider-resolver.test.ts` | present as related test | 2 | yes | ranked in top 10 |
| `packages/storage/src/server-api-keys.ts` | rank 1 edit target | 3 | no | ranked in top 10 |
| `apps/web/src/app/api/settings/api-keys/route.ts` | rank 2 edit target | 4 | no | ranked in top 10 |

Quality scores:

| Metric | Score |
| ------ | ----: |
| Exact entity ranking | 3 |
| Related test retrieval | 8 |
| Citation quality | 9 |
| Role labeling | 2 |
| Behavioral constraint quality | 6 |
| Noise control | 2 |
| Likely coding-agent usefulness | 3 |

Verdict:

still weak. The exact test is rank 2, but provider-resolver.ts is only rank 5/runtime risk and noisy API-key/storage/error files still outrank it as edit targets.

### Repository: `VoltAgent`

- Original task: Add validation to InMemoryLogBuffer so maxSize must be a positive integer, and add focused tests in packages/logger/src/buffer.spec.ts.
- Previous repo-wiki failure: Also ranked an unrelated core console logger as an edit target and produced no citations in the saved pack.
- Retrieval command: `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-ab-retrieval-recheck/data/voltagent python3 -m repo_wiki.interfaces.cli retrieve 'Add validation to InMemoryLogBuffer so maxSize must be a positive integer, and add focused tests in packages/logger/src/buffer.spec.ts.' --repo repo_30da656415dd2432a151 --limit 10 --max-tokens 5000 --format json --license-policy permissive_only --language TypeScript --framework 'TypeScript agent framework'`
- Context pack ID: `ctx_b8bc7c92b8db43d5`
- Latency: 44 ms
- Warnings: Potential low-quality retrieval: exact task entities were detected but not found in the returned context.
- Behavioral constraint notes: none

Top retrieved results:

| Rank | File/Object | Role label | Citation present? | Judgment |
| ---: | ----------- | ---------- | ----------------: | -------- |
| 1 | `packages/logger/src/buffer.ts` |  | no | expected edit target |
| 2 | `packages/logger/src/buffer.spec.ts` | related test | no | expected focused test |
| 3 | `packages/logger/src/index.ts` |  | no | supporting context |
| 4 | `packages/core/src/logger/console-logger.ts` |  | no | known noisy competitor |
| 5 | `packages/logger/src` |  | no | supporting context |
| 6 | `voltagent project profile` |  | no | supporting context |
| 7 | `voltagent unknown architecture pattern` |  | no | supporting context |

Expected key file check:

| Expected item | Previous status | Current rank | Improved? | Notes |
| ------------- | --------------- | -----------: | --------: | ----- |
| `packages/logger/src/buffer.ts` | rank 1 but uncited | 1 | no | ranked in top 10 |
| `packages/logger/src/buffer.spec.ts` | present but behind unrelated logger tests | 2 | yes | ranked in top 10 |
| `packages/core/src/logger/console-logger.ts` | ranked as edit target | 4 | no | ranked in top 10 |

Quality scores:

| Metric | Score |
| ------ | ----: |
| Exact entity ranking | 10 |
| Related test retrieval | 10 |
| Citation quality | 1 |
| Role labeling | 5 |
| Behavioral constraint quality | 5 |
| Noise control | 8 |
| Likely coding-agent usefulness | 7 |

Verdict:

improved but needs another retrieval fix. buffer.ts and buffer.spec.ts are ranks 1 and 2, but permissive-only retrieval still produced no citations, so confident roles were withheld.

### Repository: `OpenMAIC`

- Original task: Extend the JSON repair parser to repair quoted numeric property fragments without a leading zero like "opacity: .5" and "x: -.25" without changing valid string content, and add focused tests in tests/generation/json-repair.test.ts.
- Previous repo-wiki failure: Top edit targets were unrelated importer/html-parser files, so source discovery still required manual search.
- Retrieval command: `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-ab-retrieval-recheck/data/openmaic python3 -m repo_wiki.interfaces.cli retrieve 'Extend the JSON repair parser to repair quoted numeric property fragments without a leading zero like "opacity: .5" and "x: -.25" without changing valid string content, and add focused tests in tests/generation/json-repair.test.ts.' --repo repo_7d625caf0441b32f1fc9 --limit 10 --max-tokens 5000 --format json --license-policy permissive_only --language TypeScript --framework Next.js`
- Context pack ID: `ctx_21c1e0e652544a0d`
- Latency: 88 ms
- Warnings: Potential low-quality retrieval: exact task entities were detected but not found in the returned context.
- Behavioral constraint notes: none

Top retrieved results:

| Rank | File/Object | Role label | Citation present? | Judgment |
| ---: | ----------- | ---------- | ----------------: | -------- |
| 1 | `packages/@openmaic/importer/src/import-pipeline/index.ts` | edit target | yes | known noisy competitor |
| 2 | `packages/@openmaic/importer/scripts/transvert.ts` | edit target | yes | known noisy competitor |
| 3 | `lib/export/html-parser/parser.ts` | edit target | yes | known noisy competitor |
| 4 | `tests/generation/json-repair.test.ts` | related test | yes | expected focused test |
| 5 | `lib/generation/json-repair.ts` | runtime risk | yes | expected edit target |
| 6 | `lib/generation/action-parser.ts` | runtime risk | yes | runtime risk |
| 7 | `lib/generation/outline-generator.ts` | runtime risk | yes | runtime risk |
| 8 | `lib/generation/generation-pipeline.ts` | runtime risk | yes | runtime risk |
| 9 | `openmaic project profile` |  | yes | supporting context |
| 10 | `lib/generation` |  | yes | supporting context |

Expected key file check:

| Expected item | Previous status | Current rank | Improved? | Notes |
| ------------- | --------------- | -----------: | --------: | ----- |
| `lib/generation/json-repair.ts` | rank 7/lower-ranked runtime risk | 5 | yes | ranked in top 10 |
| `tests/generation/json-repair.test.ts` | present as related test | 4 | yes | ranked in top 10 |
| `packages/@openmaic/importer/src/import-pipeline/index.ts` | rank 1 edit target | 1 | no | ranked in top 10 |
| `lib/export/html-parser/parser.ts` | rank 3 edit target | 3 | no | ranked in top 10 |

Quality scores:

| Metric | Score |
| ------ | ----: |
| Exact entity ranking | 3 |
| Related test retrieval | 8 |
| Citation quality | 9 |
| Role labeling | 2 |
| Behavioral constraint quality | 2 |
| Noise control | 1 |
| Likely coding-agent usefulness | 3 |

Verdict:

still weak. json-repair.ts improved only to rank 5/runtime risk while importer and html-parser files remain top edit targets.

### Repository: `LangGraph`

- Original task: Add validation to JsonPlusSerializer allowlist normalization so allowed_msgpack_modules entries must be classes or non-empty string tuples, and add focused tests in libs/checkpoint/tests/test_jsonplus.py.
- Previous repo-wiki failure: Assisted patch added a test expectation for allowed_msgpack_modules=True that the implementation does not satisfy because with_msgpack_allowlist returns self before validating extras.
- Retrieval command: `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-ab-retrieval-recheck/data/langgraph python3 -m repo_wiki.interfaces.cli retrieve 'Add validation to JsonPlusSerializer allowlist normalization so allowed_msgpack_modules entries must be classes or non-empty string tuples, and add focused tests in libs/checkpoint/tests/test_jsonplus.py.' --repo repo_85e522839d49488ad6bb --limit 10 --max-tokens 5000 --format json --license-policy permissive_only --language Python --framework 'LangGraph Python libraries'`
- Context pack ID: `ctx_693223e53cfe4540`
- Latency: 164 ms
- Warnings: Potential low-quality retrieval: exact task entities were detected but not found in the returned context.
- Behavioral constraint notes: none

Top retrieved results:

| Rank | File/Object | Role label | Citation present? | Judgment |
| ---: | ----------- | ---------- | ----------------: | -------- |
| 1 | `libs/checkpoint/langgraph/checkpoint/serde/jsonplus.py` | edit target | yes | expected edit target |
| 2 | `libs/checkpoint/tests/test_jsonplus.py` | related test | yes | expected focused test |
| 3 | `libs/prebuilt/langgraph/prebuilt/tool_validator.py` | convention example | yes | known noisy competitor |
| 4 | `libs/checkpoint-conformance/langgraph/checkpoint/conformance/validate.py` | convention example | yes | known noisy competitor |
| 5 | `langgraph project profile` |  | yes | supporting context |

Expected key file check:

| Expected item | Previous status | Current rank | Improved? | Notes |
| ------------- | --------------- | -----------: | --------: | ----- |
| `libs/checkpoint/langgraph/checkpoint/serde/jsonplus.py` | rank 1 | 1 | no | ranked in top 10 |
| `libs/checkpoint/tests/test_jsonplus.py` | present but behind test_encrypted | 2 | yes | ranked in top 10 |
| `allowlist True early return / guard behavior` | missing |  | no | still missing from risks/context notes |

Quality scores:

| Metric | Score |
| ------ | ----: |
| Exact entity ranking | 9 |
| Related test retrieval | 9 |
| Citation quality | 9 |
| Role labeling | 8 |
| Behavioral constraint quality | 2 |
| Noise control | 8 |
| Likely coding-agent usefulness | 7 |

Verdict:

improved but needs another retrieval fix. jsonplus.py and test_jsonplus.py are ranks 1 and 2 with citations, but no behavioral constraint note was emitted for the allowlist early-return path.

## 5. Aggregate Findings

- The fixes helped most when the query contained a rare exact symbol and the source file had a clear same-stem test: VoltAgent ranked `buffer.ts` first and `buffer.spec.ts` second; LangGraph ranked `jsonplus.py` first and `test_jsonplus.py` second.
- Dapr improved on the exact focused test: `tests/workflow/test_grpc_options.py` now appears at rank 4 with a citation, instead of being absent from the old top related tests.
- Citation-gated roles worked as a safety mechanism for VoltAgent: because the permissive-only run still produced no citations, context did not present uncited files as confident edit targets.
- OpenScribe and OpenMAIC still show the original generic-drift failure. API-key/storage/error files and importer/html-parser files remain above the true edit target and are still labeled as edit targets.
- Behavioral constraint extraction remains too narrow for LangGraph. The correct file and test are retrieved, but the context still does not mention the `with_msgpack_allowlist` early-return/guard behavior that caused the prior assisted test defect.
- The low-quality warning fires in all five runs. It correctly flags weak exact-entity coverage, but it is too generic and does not prevent noisy edit-target labels in OpenScribe/OpenMAIC.

## 6. Recommendation

Fix retrieval again before A/B. Do not rerun the full coding A/B on all five repositories yet. The next retrieval fix should target three concrete gaps: demote generic provider/parser/importer/API-key matches when exact path or symbol evidence exists, preserve citations or explicit metadata citations for unlicensed local repos such as VoltAgent, and extract behavioral constraints around related helper methods/tests even when the exact query symbol is a class rather than the helper function.
