# Multi-Repository Retrieval Benchmark

## 1. Purpose

This benchmark evaluates how well repo-wiki ingests repositories and retrieves useful coding-agent context across real repositories before running coding-agent A/B tests. It measures retrieval of edit targets, runtime/use-site files, related tests, conventions, risks, citations, and context noise. Healthcare repositories are treated only as software-engineering references, not medical or clinical validation.

## 2. Repository Set

The input set contained 19 GitHub repositories across four categories.

| Category | Count | Completed | Skipped | Notes |
| -------- | ----: | --------: | ------: | ----- |
| Medical / Clinic / Assistant | 4 | 4 | 0 | All completed; frontend/API files were easier than related test pairing. |
| Agentic AI Workflow | 5 | 3 | 2 | Strongest completed category; CrewAI and n8n were skipped for size. |
| Backend / API Architecture | 5 | 5 | 0 | Weakest category because Go/C# sources were not first-class indexed. |
| Education AI Software | 5 | 5 | 0 | Mostly usable; mixed full-stack boundary and test-pairing quality. |

## 3. Methodology

- Repositories were shallow-cloned into `/tmp/repo-wiki-multi-repo-benchmark/repos` and never modified.
- repo-wiki used an isolated data directory: `REPO_WIKI_DATA_DIR=/tmp/repo-wiki-multi-repo-benchmark/data` and `REPO_WIKI_DB=/tmp/repo-wiki-multi-repo-benchmark/data/repo-wiki.db`.
- Each feasible repository was ingested through `python3 -m repo_wiki.interfaces.cli ingest local ...` with `permissive_only` for detected permissive licenses and `metadata_only` for restrictive or unclear licenses.
- One bounded retrieval task was created per repository and retrieved through the CLI with `--repo`, `--limit 10`, `--max-tokens 5000`, and JSON output.
- Ground truth was checked manually enough to identify expected edit targets, runtime/use-site files, related tests, convention examples, and risk-revealing files. `rg` inspection was used for the second pass on weak or suspicious cases.
- Full test suites were not run. The benchmark is retrieval-only and does not validate target-repository behavior.
- Strict scoring was used: 10 excellent, 7 useful with minor issues, 5 mixed, 3 weak/noisy, 1 failed.

Limitations: repo-wiki currently indexes Python, JavaScript, TypeScript, Markdown, JSON, TOML, YAML, SQL, CSS, and HTML text candidates. Go, C#, Rust, and Svelte source files are not fully extracted, so those repositories are judged as architecture/file-level retrieval only.

## 4. Overall Results

| Repository | Category | Language/framework | Ingest | Overall score | Verdict | Main issue |
| ---------- | -------- | ------------------ | -----: | ------------: | ------- | ---------- |
| Phlox / Scribe | Medical / Clinic / Assistant | JavaScript / React, FastAPI, Tauri | 10 | 7 | usable with issues | weak source-to-test pairing |
| AI Healthcare System | Medical / Clinic / Assistant | Python / FastAPI, React, SQLAlchemy, Ollama, FHIR-style integrations | 10 | 6 | usable with issues | weak source-to-test pairing |
| Imhotep Smart Clinic | Medical / Clinic / Assistant | Python / Django | 10 | 6 | usable with issues | weak source-to-test pairing |
| OpenScribe | Medical / Clinic / Assistant | TypeScript / Next.js, React, Turborepo-style packages | 10 | 8 | strong candidate for coding-agent A/B test | good runtime retrieval, weaker package-level test/convention pairing |
| LangGraph | Agentic AI Workflow | Python / LangGraph Python libraries | 10 | 7 | usable with issues | good config/runtime retrieval, weak checkpoint-specific tests/docs pairing |
| CrewAI | Agentic AI Workflow | Python / CrewAI Python framework | 1 | 1 | skipped / unsupported | repository too large for bounded CLI benchmark run |
| Dapr Agents | Agentic AI Workflow | Python / Dapr workflows, Python agents | 10 | 9 | strong candidate for coding-agent A/B test | missed example/docs conventions, but core runtime and tests were useful |
| VoltAgent | Agentic AI Workflow | TypeScript / TypeScript agent framework, Next.js examples | 10 | 8 | strong candidate for coding-agent A/B test | retrieved useful agent/memory files but test rank and risk labeling were weak |
| n8n | Agentic AI Workflow | TypeScript / Node.js workflow automation monorepo | 1 | 1 | skipped / unsupported | repository too large for bounded CLI benchmark run |
| Go Backend Clean Architecture | Backend / API Architecture | Go / Gin, MongoDB | 4 | 3 | retrieval weak | Go source files were not indexed by repo-wiki's current text/language filter |
| Domain-Driven Hexagon | Backend / API Architecture | TypeScript / NestJS, DDD, CQRS | 10 | 6 | usable with issues | weak source-to-test pairing |
| Modular Monolith with DDD | Backend / API Architecture | C# / .NET modular monolith, DDD, CQRS | 4 | 4 | retrieval weak | C# source files were not indexed by repo-wiki's current text/language filter |
| Jason Taylor CleanArchitecture | Backend / API Architecture | C# / ASP.NET Core, EF Core, MediatR, FluentValidation | 4 | 3 | retrieval weak | C# source files were not indexed by repo-wiki's current text/language filter |
| Ardalis CleanArchitecture | Backend / API Architecture | C# / ASP.NET Core, FastEndpoints, EF Core | 4 | 3 | retrieval weak | C# source files were not indexed by repo-wiki's current text/language filter |
| Open TutorAI Community Edition | Education AI Software | Svelte/Python / SvelteKit, FastAPI, AI services | 4 | 5 | usable with issues | Svelte support is architecture/file-level only |
| DeepTutor | Education AI Software | Python / FastAPI, agentic tutoring services | 10 | 7 | usable with issues | missed primary edit target |
| OpenMAIC | Education AI Software | TypeScript / Next.js, multi-agent classroom workflows | 10 | 8 | strong candidate for coding-agent A/B test | weak source-to-test pairing |
| AI LMS | Education AI Software | TypeScript / Next.js, Prisma, NextAuth | 10 | 7 | usable with issues | weak source-to-test pairing |
| openLesson | Education AI Software | TypeScript / Next.js, React | 10 | 6 | usable with issues | weak source-to-test pairing |

## 5. Category-Level Results

### Medical / Clinic / Assistant

- Average completed score: 6.8
- Strongest repo: OpenScribe
- Weakest repo: AI Healthcare System
- Common strengths: API/runtime files and privacy/security-adjacent risks were often surfaced.
- Common weaknesses: Specific tests and backend/frontend boundary pairing were inconsistent.

### Agentic AI Workflow

- Average completed score: 8.0
- Strongest repo: Dapr Agents
- Weakest repo: CrewAI
- Common strengths: Python/TypeScript agent runtime files were retrieved with useful ranks.
- Common weaknesses: Large monorepos need scoped ingestion; tests/examples were not always paired with source.

### Backend / API Architecture

- Average completed score: 3.8
- Strongest repo: Domain-Driven Hexagon
- Weakest repo: Go Backend Clean Architecture
- Common strengths: TypeScript DDD docs/controllers were partially useful; architecture docs were available.
- Common weaknesses: Go and C# source files were excluded by current ingestion filters, causing weak retrieval.

### Education AI Software

- Average completed score: 6.6
- Strongest repo: OpenMAIC
- Weakest repo: Open TutorAI Community Edition
- Common strengths: TypeScript/Python API routes and workflow settings were usually discoverable.
- Common weaknesses: Svelte and full-stack boundaries confused role selection; tests were often missing or low-ranked.

## 6. Per-Repository Results

### Repository: `Phlox / Scribe`

- URL: https://github.com/jfgonsalves/scribe
- Category: Medical / Clinic / Assistant
- Language/framework: JavaScript / React, FastAPI, Tauri
- License: MIT
- License policy used: permissive_only
- Size estimate: 394 text files, 2.3 MiB text
- Tests present: yes (11 detected by inspection)
- repo-wiki language support: full
- Retrieval task: Add validation around AI transcription job settings and identify the UI/runtime files and tests to update.
- Ingestion result: success; 381 files, 2718 symbols, 79 knowledge objects, 3657 graph nodes, 4649 graph edges; duration 4467 ms
- Context pack ID: ctx_e56b0cfcc3ee47c7
- Latency: 570 ms
- Ingest command: `/usr/bin/python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-multi-repo-benchmark/repos/scribe --license-policy permissive_only`
- Retrieval command: `/usr/bin/python3 -m repo_wiki.interfaces.cli retrieve Add validation around AI transcription job settings and identify the UI/runtime files and tests to update. --repo repo_15abd261ef5efd7655ee --limit 10 --max-tokens 5000 --format json --license-policy permissive_only --language JavaScript --framework FastAPI`

Top retrieved results:

| Rank | File/Object | Type | Role guessed by repo-wiki | Your judgment |
| ---: | ----------- | ---- | ------------------------- | ------------- |
| 1 | src/pages/Settings.jsx | CodeExample | edit target | Nearby/useful for Runtime/use-site. |
| 2 | src/pages/PatientDetails.jsx | CodeExample | runtime risk | Matched Runtime/use-site. |
| 3 | src/components/common/SplashScreen.jsx | CodeExample |  | Potentially useful but not an expected role. |
| 4 | src/components/settings/ModelSettingsPanel.jsx | CodeExample |  | Matched Primary edit target. |
| 5 | src/components/settings/UserSettingsPanel.jsx | CodeExample |  | Nearby/useful for Primary edit target. |
| 6 | src/components/settings/ChatSettingsPanel.jsx | CodeExample |  | Nearby/useful for Primary edit target. |
| 7 | src/components/modals/NewTemplateFromExampleModal.jsx | CodeExample |  | Potentially useful but not an expected role. |
| 8 | src/components/modals/DisclaimerModal.jsx | CodeExample |  | Potentially useful but not an expected role. |
| 9 | src/utils/hooks/splash/useTranscriptionStep.jsx | CodeExample |  | Potentially useful but not an expected role. |
| 10 | src/components/settings/ToolsSettingsTab.jsx | CodeExample |  | Nearby/useful for Primary edit target. |

Key role check:

| Role | Expected file/object | Found? | Rank | Useful? | Notes |
| ---- | -------------------- | -----: | ---: | ------: | ----- |
| Primary edit target | src/components/settings/ModelSettingsPanel.jsx | yes | 4 | yes | Exact expected file appeared in top results. |
| Runtime/use-site | src/pages/PatientDetails.jsx | yes | 2 | yes | Exact expected file appeared in top results. |
| Related test | server/tests/test_transcription.py | no | - | no | Not found in top 10. |
| Convention/example | server/demo/example_patients.json | no | - | no | Not found in top 10. |
| Risk-revealing file | server/utils/chat/tools/search_patient_notes.py | no | - | no | Not found in top 10. |

Scores:

| Metric | Score |
| ------ | ----: |
| Ingestion success | 10 |
| Primary edit target retrieval | 8 |
| Runtime/use-site retrieval | 10 |
| Related test retrieval | 2 |
| Convention/example retrieval | 2 |
| Risk explanation | 7 |
| Citation usefulness | 8 |
| Noise control | 8 |
| Context compactness | 8 |
| Overall agent usefulness | 7 |

Verdict: usable with issues

Notes:

- What worked: Found primary edit target, runtime/use-site.
- What failed: weak source-to-test pairing
- Recommended next action: Improve source-to-test pairing and role labeling before A/B.

### Repository: `AI Healthcare System`

- URL: https://github.com/pavanbadempet/AI-Healthcare-System
- Category: Medical / Clinic / Assistant
- Language/framework: Python / FastAPI, React, SQLAlchemy, Ollama, FHIR-style integrations
- License: MIT
- License policy used: permissive_only
- Size estimate: 608 text files, 5.1 MiB text
- Tests present: yes (171 detected by inspection)
- repo-wiki language support: full
- Retrieval task: Add error handling for offline Ollama or FHIR integration configuration and identify service, config, tests, and risks.
- Ingestion result: success; 597 files, 3789 symbols, 51 knowledge objects, 5175 graph nodes, 8191 graph edges; duration 10476 ms
- Context pack ID: ctx_db41684955464f17
- Latency: 4464 ms
- Ingest command: `/usr/bin/python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-multi-repo-benchmark/repos/ai-healthcare-system --license-policy permissive_only`
- Retrieval command: `/usr/bin/python3 -m repo_wiki.interfaces.cli retrieve Add error handling for offline Ollama or FHIR integration configuration and identify service, config, tests, and risks. --repo repo_230de8dcecbb39c23e1d --limit 10 --max-tokens 5000 --format json --license-policy permissive_only --language Python --framework Gin`

Top retrieved results:

| Rank | File/Object | Type | Role guessed by repo-wiki | Your judgment |
| ---: | ----------- | ---- | ------------------------- | ------------- |
| 1 | backend/appointments.py | CodeExample | edit target | Nearby/useful for Primary edit target, Runtime/use-site, Risk-revealing file. |
| 2 | backend/streaming_chat.py | CodeExample | edit target | Nearby/useful for Primary edit target, Runtime/use-site, Risk-revealing file. |
| 3 | backend/delta_lake_integration.py | CodeExample | runtime risk | Nearby/useful for Primary edit target, Runtime/use-site, Risk-revealing file. |
| 4 | backend/abdm.py | CodeExample | runtime risk | Nearby/useful for Primary edit target, Runtime/use-site, Risk-revealing file. |
| 5 | backend/core_ai.py | CodeExample | runtime risk | Matched Risk-revealing file. |
| 6 | backend/semantic_cache.py | CodeExample | runtime risk | Nearby/useful for Primary edit target, Runtime/use-site, Risk-revealing file. |
| 7 | tests/integration/test_clinos_smart_fhir.py | TestingPattern | related test | Nearby/useful for Primary edit target. |
| 8 | tests/unit/test_smart_fhir.py | TestingPattern | related test | Matched Related test. |
| 9 | tests/unit/test_interoperability.py | TestingPattern | related test | Nearby/useful for Runtime/use-site, Related test. |
| 10 | tests/unit/test_terminology.py | TestingPattern | related test | Nearby/useful for Related test. |

Key role check:

| Role | Expected file/object | Found? | Rank | Useful? | Notes |
| ---- | -------------------- | -----: | ---: | ------: | ----- |
| Primary edit target | backend/smart_fhir.py | no | 1 | yes | Related or nearby file appeared, but not the expected file. |
| Runtime/use-site | backend/interoperability.py | no | 1 | yes | Related or nearby file appeared, but not the expected file. |
| Related test | tests/unit/test_smart_fhir.py | yes | 8 | yes | Exact expected file appeared in top results. |
| Convention/example | docs/INTEROPERABILITY_EXPORTS.md | no | - | no | Not found in top 10. |
| Risk-revealing file | backend/core_ai.py | yes | 5 | yes | Exact expected file appeared in top results. |

Scores:

| Metric | Score |
| ------ | ----: |
| Ingestion success | 10 |
| Primary edit target retrieval | 5 |
| Runtime/use-site retrieval | 5 |
| Related test retrieval | 7 |
| Convention/example retrieval | 2 |
| Risk explanation | 7 |
| Citation usefulness | 8 |
| Noise control | 8 |
| Context compactness | 8 |
| Overall agent usefulness | 6 |

Verdict: usable with issues

Notes:

- What worked: Found related test, risk-revealing file.
- What failed: weak source-to-test pairing
- Recommended next action: Improve source-to-test pairing and role labeling before A/B.

### Repository: `Imhotep Smart Clinic`

- URL: https://github.com/Imhotep-Tech/imhotep_smart_clinic
- Category: Medical / Clinic / Assistant
- Language/framework: Python / Django
- License: GPL
- License policy used: metadata_only
- Size estimate: 105 text files, 0.6 MiB text
- Tests present: no (0 detected by inspection)
- repo-wiki language support: full
- Retrieval task: Add validation to appointment creation or scheduling and identify Django model/view/form tests and conventions.
- Ingestion result: success; 103 files, 188 symbols, 26 knowledge objects, 333 graph nodes, 411 graph edges; duration 1488 ms
- Context pack ID: ctx_25eb9b8faf3e4855
- Latency: 268 ms
- Ingest command: `/usr/bin/python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-multi-repo-benchmark/repos/imhotep-smart-clinic --license-policy metadata_only`
- Retrieval command: `/usr/bin/python3 -m repo_wiki.interfaces.cli retrieve Add validation to appointment creation or scheduling and identify Django model/view/form tests and conventions. --repo repo_49652f7902e3a5302533 --limit 10 --max-tokens 5000 --format json --license-policy metadata_only --language Python --framework Django`

Top retrieved results:

| Rank | File/Object | Type | Role guessed by repo-wiki | Your judgment |
| ---: | ----------- | ---- | ------------------------- | ------------- |
| 1 | doctor/appointments.py | CodeExample |  | Matched Primary edit target. |
| 2 | accounts/auth.py | CodeExample |  | Potentially useful but not an expected role. |
| 3 | doctor/doctor_settings.py | CodeExample |  | Nearby/useful for Primary edit target. |
| 4 | accounts/decorators.py | CodeExample |  | Potentially useful but not an expected role. |
| 5 | accounts/user_profile.py | CodeExample |  | Potentially useful but not an expected role. |
| 6 | doctor/views.py | CodeExample |  | Nearby/useful for Primary edit target. |
| 7 | doctor/patients.py | CodeExample |  | Nearby/useful for Primary edit target. |
| 8 | imhotep_smart_clinic/settings.py | CodeExample |  | Potentially useful but not an expected role. |
| 9 | doctor/models.py | CodeExample |  | Nearby/useful for Primary edit target. |
| 10 | doctor/migrations/0001_initial.py | CodeExample |  | Nearby/useful for Primary edit target. |

Key role check:

| Role | Expected file/object | Found? | Rank | Useful? | Notes |
| ---- | -------------------- | -----: | ---: | ------: | ----- |
| Primary edit target | doctor/appointments.py | yes | 1 | yes | Exact expected file appeared in top results. |
| Runtime/use-site | doctor/templates/schedule_appointment.html | no | - | no | Not found in top 10. |
| Related test | not found during inspection | no | - | no | No clear expected file found during bounded inspection. |
| Convention/example | README.md | no | - | no | Not found in top 10. |
| Risk-revealing file | doctor/templates/show_patient_details.html | no | - | no | Not found in top 10. |

Scores:

| Metric | Score |
| ------ | ----: |
| Ingestion success | 10 |
| Primary edit target retrieval | 10 |
| Runtime/use-site retrieval | 2 |
| Related test retrieval | 3 |
| Convention/example retrieval | 2 |
| Risk explanation | 7 |
| Citation usefulness | 4 |
| Noise control | 8 |
| Context compactness | 8 |
| Overall agent usefulness | 6 |

Verdict: usable with issues

Notes:

- What worked: Found primary edit target.
- What failed: weak source-to-test pairing
- Recommended next action: Improve source-to-test pairing and role labeling before A/B.

### Repository: `OpenScribe`

- URL: https://github.com/sammargolis/OpenScribe
- Category: Medical / Clinic / Assistant
- Language/framework: TypeScript / Next.js, React, Turborepo-style packages
- License: MIT
- License policy used: permissive_only
- Size estimate: 192 text files, 1.1 MiB text
- Tests present: yes (25 detected by inspection)
- repo-wiki language support: full
- Retrieval task: Add validation/error handling to the encounter recording-to-note generation flow and identify UI/API/tests/risks.
- Ingestion result: success; 167 files, 2143 symbols, 47 knowledge objects, 2470 graph nodes, 2923 graph edges; duration 3431 ms
- Context pack ID: ctx_f766fe3f81314943
- Latency: 1128 ms
- Ingest command: `/usr/bin/python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-multi-repo-benchmark/repos/openscribe --license-policy permissive_only`
- Retrieval command: `/usr/bin/python3 -m repo_wiki.interfaces.cli retrieve Add validation/error handling to the encounter recording-to-note generation flow and identify UI/API/tests/risks. --repo repo_1077e17671b8d8b3b5c5 --limit 10 --max-tokens 5000 --format json --license-policy permissive_only --language TypeScript --framework FastAPI`

Top retrieved results:

| Rank | File/Object | Type | Role guessed by repo-wiki | Your judgment |
| ---: | ----------- | ---- | ------------------------- | ------------- |
| 1 | apps/web/src/app/api/transcription/final/route.ts | CodeExample | runtime risk | Matched Primary edit target. |
| 2 | apps/web/src/app/api/transcription/segment/route.ts | CodeExample | runtime risk | Nearby/useful for Primary edit target, Runtime/use-site. |
| 3 | apps/web/src/app/page.tsx | CodeExample | runtime risk | Matched Runtime/use-site. |
| 4 | packages/pipeline/note-core/src/note-generator.ts | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 5 | packages/pipeline/shared/src/final-upload-error.ts | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 6 | apps/web/src/app/actions.ts | CodeExample | runtime risk | Nearby/useful for Runtime/use-site. |
| 7 | packages/pipeline/eval/src/tests/api-simple.test.ts | TestingPattern | related test | Potentially useful but not an expected role. |
| 8 | packages/pipeline/eval/src/tests/e2e-real-api.test.ts | TestingPattern | related test | Potentially useful but not an expected role. |
| 9 | packages/pipeline/note-core/src/__tests__/markdown-note.test.ts | TestingPattern | related test | Nearby/useful for Related test. |
| 10 | packages/pipeline/note-core/src/__tests__/note-generator.test.ts | TestingPattern | related test | Matched Related test. |

Key role check:

| Role | Expected file/object | Found? | Rank | Useful? | Notes |
| ---- | -------------------- | -----: | ---: | ------: | ----- |
| Primary edit target | apps/web/src/app/api/transcription/final/route.ts | yes | 1 | yes | Exact expected file appeared in top results. |
| Runtime/use-site | apps/web/src/app/page.tsx | yes | 3 | yes | Exact expected file appeared in top results. |
| Related test | packages/pipeline/note-core/src/__tests__/note-generator.test.ts | yes | 10 | yes | Exact expected file appeared in top results. |
| Convention/example | packages/llm/src/prompts/clinical-note/templates/README.md | no | - | no | Not found in top 10. |
| Risk-revealing file | packages/storage/src/types.ts | no | - | no | Not found in top 10. |

Scores:

| Metric | Score |
| ------ | ----: |
| Ingestion success | 10 |
| Primary edit target retrieval | 10 |
| Runtime/use-site retrieval | 10 |
| Related test retrieval | 7 |
| Convention/example retrieval | 2 |
| Risk explanation | 7 |
| Citation usefulness | 8 |
| Noise control | 8 |
| Context compactness | 8 |
| Overall agent usefulness | 8 |

Verdict: strong candidate for coding-agent A/B test

Notes:

- What worked: Found primary edit target, runtime/use-site, related test.
- What failed: good runtime retrieval, weaker package-level test/convention pairing
- Recommended next action: Improve source-to-test pairing and role labeling before A/B.

### Repository: `LangGraph`

- URL: https://github.com/langchain-ai/langgraph
- Category: Agentic AI Workflow
- Language/framework: Python / LangGraph Python libraries
- License: MIT
- License policy used: permissive_only
- Size estimate: 591 text files, 6.9 MiB text
- Tests present: yes (225 detected by inspection)
- repo-wiki language support: full
- Retrieval task: Add validation for graph workflow checkpoint configuration and identify runtime, config, tests, and conventions.
- Ingestion result: success; 570 files, 8572 symbols, 68 knowledge objects, 10070 graph nodes, 17689 graph edges; duration 17387 ms
- Context pack ID: ctx_a7b54b15773542fe
- Latency: 3346 ms
- Ingest command: `/usr/bin/python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-multi-repo-benchmark/repos/langgraph --license-policy permissive_only`
- Retrieval command: `/usr/bin/python3 -m repo_wiki.interfaces.cli retrieve Add validation for graph workflow checkpoint configuration and identify runtime, config, tests, and conventions. --repo repo_bbf4569b4b67653a9d64 --limit 10 --max-tokens 5000 --format json --license-policy permissive_only --language Python --framework Gin`

Top retrieved results:

| Rank | File/Object | Type | Role guessed by repo-wiki | Your judgment |
| ---: | ----------- | ---- | ------------------------- | ------------- |
| 1 | libs/sdk-py/langgraph_sdk/runtime.py | CodeExample | edit target | Nearby/useful for Runtime/use-site, Risk-revealing file. |
| 2 | libs/langgraph/langgraph/config.py | CodeExample | edit target | Nearby/useful for Primary edit target, Runtime/use-site, Risk-revealing file. |
| 3 | libs/cli/langgraph_cli/config.py | CodeExample | edit target | Matched Primary edit target. |
| 4 | libs/langgraph/langgraph/runtime.py | CodeExample | edit target | Matched Runtime/use-site, Risk-revealing file. |
| 5 | libs/langgraph/tests/test_runtime.py | TestingPattern | related test | Nearby/useful for Runtime/use-site, Risk-revealing file. |
| 6 | libs/cli/tests/unit_tests/test_config.py | TestingPattern | related test | Matched Related test. |
| 7 | libs/langgraph/tests/test_retry.py | TestingPattern | related test | Potentially useful but not an expected role. |
| 8 | libs/langgraph/tests/test_pregel.py | TestingPattern | related test | Potentially useful but not an expected role. |
| 9 | libs/langgraph/tests/test_checkpoint_migration.py | TestingPattern | related test | Potentially useful but not an expected role. |
| 10 | libs/langgraph/tests/test_large_cases.py | TestingPattern | related test | Potentially useful but not an expected role. |

Key role check:

| Role | Expected file/object | Found? | Rank | Useful? | Notes |
| ---- | -------------------- | -----: | ---: | ------: | ----- |
| Primary edit target | libs/cli/langgraph_cli/config.py | yes | 3 | yes | Exact expected file appeared in top results. |
| Runtime/use-site | libs/langgraph/langgraph/runtime.py | yes | 4 | yes | Exact expected file appeared in top results. |
| Related test | libs/cli/tests/unit_tests/test_config.py | yes | 6 | yes | Exact expected file appeared in top results. |
| Convention/example | libs/checkpoint-conformance/README.md | no | - | no | Not found in top 10. |
| Risk-revealing file | libs/langgraph/langgraph/runtime.py | yes | 4 | yes | Exact expected file appeared in top results. |

Scores:

| Metric | Score |
| ------ | ----: |
| Ingestion success | 10 |
| Primary edit target retrieval | 10 |
| Runtime/use-site retrieval | 8 |
| Related test retrieval | 7 |
| Convention/example retrieval | 2 |
| Risk explanation | 7 |
| Citation usefulness | 8 |
| Noise control | 8 |
| Context compactness | 8 |
| Overall agent usefulness | 7 |

Verdict: usable with issues

Notes:

- What worked: Found primary edit target, runtime/use-site, related test, risk-revealing file.
- What failed: good config/runtime retrieval, weak checkpoint-specific tests/docs pairing
- Recommended next action: Improve source-to-test pairing and role labeling before A/B.

### Repository: `CrewAI`

- URL: https://github.com/crewAIInc/crewAI
- Category: Agentic AI Workflow
- Language/framework: Python / CrewAI Python framework
- License: MIT
- License policy used: not used
- Size estimate: 19968 text files, 183.2 MiB text
- Tests present: yes (966 detected by inspection)
- repo-wiki language support: limited
- Retrieval task: Add validation to agent/task configuration loading and identify runtime use sites, tests, examples, and risks.
- Ingestion result: failed/skipped; 0 files, 0 symbols, 0 knowledge objects, 0 graph nodes, 0 graph edges; duration 0 ms
- Context pack ID: none
- Latency: n/a ms
- Ingest command: `skipped before ingest: repository exceeds 15,000 inspectable text files`
- Retrieval command: `not run`

Top retrieved results:

| Rank | File/Object | Type | Role guessed by repo-wiki | Your judgment |
| ---: | ----------- | ---- | ------------------------- | ------------- |
| - | none | - | - | No retrieval because repository was skipped or retrieval failed. |

Key role check:

| Role | Expected file/object | Found? | Rank | Useful? | Notes |
| ---- | -------------------- | -----: | ---: | ------: | ----- |
| Primary edit target | lib/crewai/src/crewai/agent/planning_config.py | no | - | no | Not found in top 10. |
| Runtime/use-site | lib/crewai/src/crewai/agents/crew_agent_executor.py | no | - | no | Not found in top 10. |
| Related test | lib/crewai/tests/cassettes/agents/test_task_allow_crewai_trigger_context_no_payload.yaml | no | - | no | Not found in top 10. |
| Convention/example | docs/v1.15.1/en/learn/replay-tasks-from-latest-crew-kickoff.mdx | no | - | no | Not found in top 10. |
| Risk-revealing file | lib/crewai/src/crewai/security/security_config.py | no | - | no | Not found in top 10. |

Scores:

| Metric | Score |
| ------ | ----: |
| Ingestion success | 1 |
| Primary edit target retrieval | 1 |
| Runtime/use-site retrieval | 1 |
| Related test retrieval | 1 |
| Convention/example retrieval | 1 |
| Risk explanation | 1 |
| Citation usefulness | 1 |
| Noise control | 1 |
| Context compactness | 1 |
| Overall agent usefulness | 1 |

Verdict: skipped / unsupported

Notes:

- What worked: Clone/inspection succeeded, but ingestion was skipped or failed.
- What failed: repository too large for bounded CLI benchmark run
- Recommended next action: Re-run with scoped include patterns or incremental ingestion before A/B testing.

### Repository: `Dapr Agents`

- URL: https://github.com/dapr/dapr-agents
- Category: Agentic AI Workflow
- Language/framework: Python / Dapr workflows, Python agents
- License: Apache-2.0
- License policy used: permissive_only
- Size estimate: 613 text files, 3.0 MiB text
- Tests present: yes (88 detected by inspection)
- repo-wiki language support: full
- Retrieval task: Add retry/error handling for durable agent workflow execution and identify service, runtime, tests, and risks.
- Ingestion result: success; 612 files, 2797 symbols, 92 knowledge objects, 3615 graph nodes, 6540 graph edges; duration 12058 ms
- Context pack ID: ctx_c0891efa5ed64cb4
- Latency: 3548 ms
- Ingest command: `/usr/bin/python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-multi-repo-benchmark/repos/dapr-agents --license-policy permissive_only`
- Retrieval command: `/usr/bin/python3 -m repo_wiki.interfaces.cli retrieve Add retry/error handling for durable agent workflow execution and identify service, runtime, tests, and risks. --repo repo_8c68b358993e4a2e11ba --limit 10 --max-tokens 5000 --format json --license-policy permissive_only --language Python --framework Dapr`

Top retrieved results:

| Rank | File/Object | Type | Role guessed by repo-wiki | Your judgment |
| ---: | ----------- | ---- | ------------------------- | ------------- |
| 1 | dapr_agents/agents/durable.py | CodeExample | edit target | Matched Primary edit target. |
| 2 | dapr_agents/workflow/runners/agent.py | CodeExample | edit target | Matched Runtime/use-site, Risk-revealing file. |
| 3 | examples/09-durable-agent-hot-reload/agent.py | CodeExample | edit target | Matched Convention/example. |
| 4 | dapr_agents/observability/wrappers/workflow.py | CodeExample | edit target | Nearby/useful for Runtime/use-site, Convention/example, Risk-revealing file. |
| 5 | tests/agents/durableagent/test_durable_agent.py | TestingPattern | related test | Matched Related test. |
| 6 | tests/agents/durableagent/test_hitl_workflow.py | TestingPattern | related test | Nearby/useful for Primary edit target, Runtime/use-site, Related test, Convention/example, Risk-revealing file. |
| 7 | tests/integration/examples/test_06_agent_mcp_dapr_workflow.py | TestingPattern | related test | Nearby/useful for Runtime/use-site, Convention/example, Risk-revealing file. |
| 8 | tests/integration/quickstarts/test_01_dapr_agents_fundamentals.py | TestingPattern | related test | Nearby/useful for Runtime/use-site, Convention/example, Risk-revealing file. |
| 9 | tests/integration/quickstarts/test_08_hot_reload.py | TestingPattern | related test | Potentially useful but not an expected role. |
| 10 | tests/agents/durableagent/test_observability_config.py | TestingPattern | related test | Nearby/useful for Primary edit target, Runtime/use-site, Related test, Convention/example, Risk-revealing file. |

Key role check:

| Role | Expected file/object | Found? | Rank | Useful? | Notes |
| ---- | -------------------- | -----: | ---: | ------: | ----- |
| Primary edit target | dapr_agents/agents/durable.py | yes | 1 | yes | Exact expected file appeared in top results. |
| Runtime/use-site | dapr_agents/workflow/runners/agent.py | yes | 2 | yes | Exact expected file appeared in top results. |
| Related test | tests/agents/durableagent/test_durable_agent.py | yes | 5 | yes | Exact expected file appeared in top results. |
| Convention/example | examples/09-durable-agent-hot-reload/agent.py | yes | 3 | yes | Exact expected file appeared in top results. |
| Risk-revealing file | dapr_agents/workflow/runners/agent.py | yes | 2 | yes | Exact expected file appeared in top results. |

Scores:

| Metric | Score |
| ------ | ----: |
| Ingestion success | 10 |
| Primary edit target retrieval | 10 |
| Runtime/use-site retrieval | 10 |
| Related test retrieval | 8 |
| Convention/example retrieval | 10 |
| Risk explanation | 7 |
| Citation usefulness | 8 |
| Noise control | 8 |
| Context compactness | 8 |
| Overall agent usefulness | 9 |

Verdict: strong candidate for coding-agent A/B test

Notes:

- What worked: Found primary edit target, runtime/use-site, related test, convention/example, risk-revealing file.
- What failed: missed example/docs conventions, but core runtime and tests were useful
- Recommended next action: Use as an A/B candidate; add example/doc role labeling later.

### Repository: `VoltAgent`

- URL: https://github.com/voltagent/voltagent
- Category: Agentic AI Workflow
- Language/framework: TypeScript / TypeScript agent framework, Next.js examples
- License: not detected
- License policy used: metadata_only
- Size estimate: 2606 text files, 16.8 MiB text
- Tests present: yes (218 detected by inspection)
- repo-wiki language support: full
- Retrieval task: Add a provider option to agent memory/tool configuration and identify TypeScript runtime, examples, tests, and risks.
- Ingestion result: success; 2514 files, 25059 symbols, 250 knowledge objects, 30859 graph nodes, 78217 graph edges; duration 70420 ms
- Context pack ID: ctx_b07bb730e236446c
- Latency: 3536 ms
- Ingest command: `/usr/bin/python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-multi-repo-benchmark/repos/voltagent --license-policy metadata_only`
- Retrieval command: `/usr/bin/python3 -m repo_wiki.interfaces.cli retrieve Add a provider option to agent memory/tool configuration and identify TypeScript runtime, examples, tests, and risks. --repo repo_b4f8d9156edc3b51109e --limit 10 --max-tokens 5000 --format json --license-policy metadata_only --language TypeScript --framework Gin`

Top retrieved results:

| Rank | File/Object | Type | Role guessed by repo-wiki | Your judgment |
| ---: | ----------- | ---- | ------------------------- | ------------- |
| 1 | examples/next-js-chatbot-starter-template/lib/agent/memory.ts | CodeExample | edit target | Matched Convention/example. |
| 2 | examples/next-js-chatbot-starter-template/lib/agent/agent.ts | CodeExample | edit target | Matched Runtime/use-site. |
| 3 | packages/core/src/agent/agent.ts | CodeExample | edit target | Matched Primary edit target, Risk-revealing file. |
| 4 | examples/with-assistant-ui/voltagent/memory.ts | CodeExample | edit target | Nearby/useful for Primary edit target, Runtime/use-site, Convention/example, Risk-revealing file. |
| 5 | packages/core/src/agent/agent-observability.spec.ts | TestingPattern | related test | Nearby/useful for Primary edit target, Runtime/use-site, Related test, Risk-revealing file. |
| 6 | packages/core/src/agent/subagent/index.spec.ts | TestingPattern | related test | Nearby/useful for Primary edit target, Runtime/use-site, Related test, Risk-revealing file. |
| 7 | packages/core/src/workflow/step-schemas-runtime.spec.ts | TestingPattern | related test | Potentially useful but not an expected role. |
| 8 | packages/core/src/agent/agent-semantic-search.spec.ts | TestingPattern | related test | Nearby/useful for Primary edit target, Runtime/use-site, Related test, Risk-revealing file. |
| 9 | packages/core/src/memory/adapters/embedding/ai-sdk.spec.ts | TestingPattern | related test | Nearby/useful for Convention/example. |
| 10 | packages/core/src/agent/agent.spec.ts | TestingPattern | related test | Matched Related test. |

Key role check:

| Role | Expected file/object | Found? | Rank | Useful? | Notes |
| ---- | -------------------- | -----: | ---: | ------: | ----- |
| Primary edit target | packages/core/src/agent/agent.ts | yes | 3 | yes | Exact expected file appeared in top results. |
| Runtime/use-site | examples/next-js-chatbot-starter-template/lib/agent/agent.ts | yes | 2 | yes | Exact expected file appeared in top results. |
| Related test | packages/core/src/agent/agent.spec.ts | yes | 10 | yes | Exact expected file appeared in top results. |
| Convention/example | examples/next-js-chatbot-starter-template/lib/agent/memory.ts | yes | 1 | yes | Exact expected file appeared in top results. |
| Risk-revealing file | packages/core/src/agent/agent.ts | yes | 3 | yes | Exact expected file appeared in top results. |

Scores:

| Metric | Score |
| ------ | ----: |
| Ingestion success | 10 |
| Primary edit target retrieval | 10 |
| Runtime/use-site retrieval | 10 |
| Related test retrieval | 7 |
| Convention/example retrieval | 10 |
| Risk explanation | 7 |
| Citation usefulness | 4 |
| Noise control | 8 |
| Context compactness | 8 |
| Overall agent usefulness | 8 |

Verdict: strong candidate for coding-agent A/B test

Notes:

- What worked: Found primary edit target, runtime/use-site, related test, convention/example, risk-revealing file.
- What failed: retrieved useful agent/memory files but test rank and risk labeling were weak
- Recommended next action: Improve source-to-test pairing and role labeling before A/B.

### Repository: `n8n`

- URL: https://github.com/n8n-io/n8n
- Category: Agentic AI Workflow
- Language/framework: TypeScript / Node.js workflow automation monorepo
- License: custom
- License policy used: not used
- Size estimate: 20242 text files, 124.3 MiB text
- Tests present: yes (6021 detected by inspection)
- repo-wiki language support: full
- Retrieval task: Add validation for an AI workflow node credential/parameter and identify node runtime, UI/use-site, tests, conventions, and risks.
- Ingestion result: failed/skipped; 0 files, 0 symbols, 0 knowledge objects, 0 graph nodes, 0 graph edges; duration 0 ms
- Context pack ID: none
- Latency: n/a ms
- Ingest command: `skipped before ingest: repository exceeds 15,000 inspectable text files`
- Retrieval command: `not run`

Top retrieved results:

| Rank | File/Object | Type | Role guessed by repo-wiki | Your judgment |
| ---: | ----------- | ---- | ------------------------- | ------------- |
| - | none | - | - | No retrieval because repository was skipped or retrieval failed. |

Key role check:

| Role | Expected file/object | Found? | Rank | Useful? | Notes |
| ---- | -------------------- | -----: | ---: | ------: | ----- |
| Primary edit target | packages/@n8n/ai-workflow-builder.ee/evaluations/evaluators/llm-judge/evaluators/node-configuration-evaluator.ts | no | - | no | Not found in top 10. |
| Runtime/use-site | packages/testing/playwright/expectations/instance-ai/should-apply-parameter-and-credential-edits-and-persist-them-to-the-workflow/0002-1780493870909-unknown-host-POST-_v1_messages-77bad225.json | no | - | no | Not found in top 10. |
| Related test | packages/@n8n/ai-workflow-builder.ee/src/tools/test/update-node-parameters.tool.test.ts | no | - | no | Not found in top 10. |
| Convention/example | packages/@n8n/node-cli/src/template/templates/programmatic/ai/model-ai-custom-example/template/README.md | no | - | no | Not found in top 10. |
| Risk-revealing file | packages/@n8n/nodes-langchain/nodes/llms/LmChatAzureOpenAi/credentials/N8nOAuth2TokenCredential.ts | no | - | no | Not found in top 10. |

Scores:

| Metric | Score |
| ------ | ----: |
| Ingestion success | 1 |
| Primary edit target retrieval | 1 |
| Runtime/use-site retrieval | 1 |
| Related test retrieval | 1 |
| Convention/example retrieval | 1 |
| Risk explanation | 1 |
| Citation usefulness | 1 |
| Noise control | 1 |
| Context compactness | 1 |
| Overall agent usefulness | 1 |

Verdict: skipped / unsupported

Notes:

- What worked: Clone/inspection succeeded, but ingestion was skipped or failed.
- What failed: repository too large for bounded CLI benchmark run
- Recommended next action: Re-run with scoped include patterns or incremental ingestion before A/B testing.

### Repository: `Go Backend Clean Architecture`

- URL: https://github.com/amitshekhariitbhu/go-backend-clean-architecture
- Category: Backend / API Architecture
- Language/framework: Go / Gin, MongoDB
- License: Apache-2.0
- License policy used: permissive_only
- Size estimate: 57 text files, 0.1 MiB text
- Tests present: yes (3 detected by inspection)
- repo-wiki language support: limited
- Retrieval task: Add validation to a login or signup request in the Gin API and identify handler/usecase/tests/conventions/risks.
- Ingestion result: success; 3 files, 0 symbols, 1 knowledge objects, 6 graph nodes, 5 graph edges; duration 596 ms
- Context pack ID: ctx_3590634a6a2d43f0
- Latency: 126 ms
- Ingest command: `/usr/bin/python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-multi-repo-benchmark/repos/go-backend-clean-architecture --license-policy permissive_only`
- Retrieval command: `/usr/bin/python3 -m repo_wiki.interfaces.cli retrieve Add validation to a login or signup request in the Gin API and identify handler/usecase/tests/conventions/risks. --repo repo_95deff121664d0aa5cb4 --limit 10 --max-tokens 5000 --format json --license-policy permissive_only`

Top retrieved results:

| Rank | File/Object | Type | Role guessed by repo-wiki | Your judgment |
| ---: | ----------- | ---- | ------------------------- | ------------- |
| 1 | README.md | CodeExample |  | Potentially useful but not an expected role. |
| 2 | README.md | ProjectProfile |  | Potentially useful but not an expected role. |

Key role check:

| Role | Expected file/object | Found? | Rank | Useful? | Notes |
| ---- | -------------------- | -----: | ---: | ------: | ----- |
| Primary edit target | api/controller/login_controller.go | no | - | no | Not found in top 10. |
| Runtime/use-site | api/route/login_route.go | no | - | no | Not found in top 10. |
| Related test | api/controller/profile_controller_test.go | no | - | no | Not found in top 10. |
| Convention/example | usecase/task_usecase.go | no | - | no | Not found in top 10. |
| Risk-revealing file | api/middleware/jwt_auth_middleware.go | no | - | no | Not found in top 10. |

Scores:

| Metric | Score |
| ------ | ----: |
| Ingestion success | 4 |
| Primary edit target retrieval | 3 |
| Runtime/use-site retrieval | 3 |
| Related test retrieval | 3 |
| Convention/example retrieval | 3 |
| Risk explanation | 7 |
| Citation usefulness | 8 |
| Noise control | 8 |
| Context compactness | 8 |
| Overall agent usefulness | 3 |

Verdict: retrieval weak

Notes:

- What worked: Returned repository-scoped context, but role precision was weak.
- What failed: Go source files were not indexed by repo-wiki's current text/language filter
- Recommended next action: Add source-file ingestion and extractor support for this language before coding-agent A/B.

### Repository: `Domain-Driven Hexagon`

- URL: https://github.com/Sairyss/domain-driven-hexagon
- Category: Backend / API Architecture
- Language/framework: TypeScript / NestJS, DDD, CQRS
- License: MIT
- License policy used: permissive_only
- Size estimate: 116 text files, 0.2 MiB text
- Tests present: yes (11 detected by inspection)
- repo-wiki language support: full
- Retrieval task: Add validation to a command DTO in a DDD module and identify controller/use-case/domain/tests/conventions/risks.
- Ingestion result: success; 113 files, 278 symbols, 46 knowledge objects, 492 graph nodes, 688 graph edges; duration 3030 ms
- Context pack ID: ctx_3f344c11024e45f9
- Latency: 603 ms
- Ingest command: `/usr/bin/python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-multi-repo-benchmark/repos/domain-driven-hexagon --license-policy permissive_only`
- Retrieval command: `/usr/bin/python3 -m repo_wiki.interfaces.cli retrieve Add validation to a command DTO in a DDD module and identify controller/use-case/domain/tests/conventions/risks. --repo repo_80c9774c68a232ec7dc4 --limit 10 --max-tokens 5000 --format json --license-policy permissive_only --language TypeScript --framework Express`

Top retrieved results:

| Rank | File/Object | Type | Role guessed by repo-wiki | Your judgment |
| ---: | ----------- | ---- | ------------------------- | ------------- |
| 1 | src/libs/api/paginated-query.request.dto.ts | CodeExample | edit target | Potentially useful but not an expected role. |
| 2 | src/libs/ddd/domain-event.base.ts | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 3 | src/modules/user/commands/create-user/create-user.http.controller.ts | CodeExample | runtime risk | Matched Runtime/use-site. |
| 4 | src/modules/user/commands/create-user/create-user.message.controller.ts | CodeExample | runtime risk | Nearby/useful for Runtime/use-site. |
| 5 | src/libs/ddd/index.ts | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 6 | src/libs/ddd/command.base.ts | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 7 | src/modules/user/queries/find-users/find-users.http.controller.ts | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 8 | src/modules/user/commands/create-user/create-user.cli.controller.ts | CodeExample | runtime risk | Nearby/useful for Runtime/use-site. |
| 9 | src/libs/ddd/value-object.base.ts | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 10 | src/libs/ddd/repository.port.ts | CodeExample | runtime risk | Potentially useful but not an expected role. |

Key role check:

| Role | Expected file/object | Found? | Rank | Useful? | Notes |
| ---- | -------------------- | -----: | ---: | ------: | ----- |
| Primary edit target | src/modules/user/commands/create-user/graphql-example/dtos/create-user.gql-request.dto.ts | no | - | no | Not found in top 10. |
| Runtime/use-site | src/modules/user/commands/create-user/create-user.http.controller.ts | yes | 3 | yes | Exact expected file appeared in top results. |
| Related test | tests/user/delete-user/delete-user.e2e-spec.ts | no | - | no | Not found in top 10. |
| Convention/example | src/modules/user/commands/create-user/graphql-example/dtos/id.gql-response.dto.ts | no | - | no | Not found in top 10. |
| Risk-revealing file | src/modules/wallet/domain/wallet.errors.ts | no | - | no | Not found in top 10. |

Scores:

| Metric | Score |
| ------ | ----: |
| Ingestion success | 10 |
| Primary edit target retrieval | 2 |
| Runtime/use-site retrieval | 10 |
| Related test retrieval | 2 |
| Convention/example retrieval | 2 |
| Risk explanation | 7 |
| Citation usefulness | 8 |
| Noise control | 8 |
| Context compactness | 8 |
| Overall agent usefulness | 6 |

Verdict: usable with issues

Notes:

- What worked: Found runtime/use-site.
- What failed: weak source-to-test pairing
- Recommended next action: Improve source-to-test pairing and role labeling before A/B.

### Repository: `Modular Monolith with DDD`

- URL: https://github.com/kgrzybek/modular-monolith-with-ddd
- Category: Backend / API Architecture
- Language/framework: C# / .NET modular monolith, DDD, CQRS
- License: MIT
- License policy used: permissive_only
- Size estimate: 1193 text files, 2.0 MiB text
- Tests present: yes (144 detected by inspection)
- repo-wiki language support: limited
- Retrieval task: Explain where to add validation to a module command handler and identify application/domain/API/tests/risks.
- Ingestion result: success; 136 files, 0 symbols, 4 knowledge objects, 142 graph nodes, 147 graph edges; duration 4015 ms
- Context pack ID: ctx_e6fd430413944fb7
- Latency: 625 ms
- Ingest command: `/usr/bin/python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-multi-repo-benchmark/repos/modular-monolith-with-ddd --license-policy permissive_only`
- Retrieval command: `/usr/bin/python3 -m repo_wiki.interfaces.cli retrieve Explain where to add validation to a module command handler and identify application/domain/API/tests/risks. --repo repo_4d29349a4f9510c7999e --limit 10 --max-tokens 5000 --format json --license-policy permissive_only`

Top retrieved results:

| Rank | File/Object | Type | Role guessed by repo-wiki | Your judgment |
| ---: | ----------- | ---- | ------------------------- | ------------- |
| 1 | docs/architecture-decision-log/0005-create-one-rest-api-module.md | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 2 | docs/architecture-decision-log/0006-create-facade-between-api-and-business-module.md | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 3 | docs/architecture-decision-log/0012-use-domain-driven-design-tactical-patterns.md | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 4 | docs/architecture-decision-log/0011-create-rich-domain-models.md | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 5 | docs/architecture-decision-log/0017-implement-archictecture-tests.md | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 6 | docs/architecture-decision-log/0004-divide-the-system-into-4-modules.md | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 7 | docs/architecture-decision-log/0010-use-clean-architecture-for-writes.md | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 8 | docs/architecture-decision-log/0016-create-ioc-container-per-module.md | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 9 | docs/architecture-decision-log/0007-use-cqrs-architectural-style.md | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 10 | src/API/CompanyName.MyMeetings.API/appsettings.json | CodeExample | runtime risk | Potentially useful but not an expected role. |

Key role check:

| Role | Expected file/object | Found? | Rank | Useful? | Notes |
| ---- | -------------------- | -----: | ---: | ------: | ----- |
| Primary edit target | src/Modules/Administration/Application/MeetingGroupProposals/RequestMeetingGroupProposalVerification/RequestMeetingGroupProposalVerificationCommandHandler.cs | no | - | no | Not found in top 10. |
| Runtime/use-site | src/Modules/Meetings/Application/Meetings/ChangeMeetingMainAttributes/ChangeMeetingMainAttributesCommandHandler.cs | no | - | no | Not found in top 10. |
| Related test | src/Modules/UserAccess/Tests/UnitTests/SeedWork/DomainEventsTestHelper.cs | no | - | no | Not found in top 10. |
| Convention/example | src/Modules/Payments/Application/Subscriptions/RenewSubscription/RenewSubscriptionCommandHandler.cs | no | - | no | Not found in top 10. |
| Risk-revealing file | src/Modules/UserAccess/Application/Authentication/Authenticate/AuthenticateCommandHandler.cs | no | - | no | Not found in top 10. |

Scores:

| Metric | Score |
| ------ | ----: |
| Ingestion success | 4 |
| Primary edit target retrieval | 3 |
| Runtime/use-site retrieval | 3 |
| Related test retrieval | 3 |
| Convention/example retrieval | 3 |
| Risk explanation | 7 |
| Citation usefulness | 8 |
| Noise control | 8 |
| Context compactness | 8 |
| Overall agent usefulness | 4 |

Verdict: retrieval weak

Notes:

- What worked: Returned repository-scoped context, but role precision was weak.
- What failed: C# source files were not indexed by repo-wiki's current text/language filter
- Recommended next action: Add source-file ingestion and extractor support for this language before coding-agent A/B.

### Repository: `Jason Taylor CleanArchitecture`

- URL: https://github.com/jasontaylordev/CleanArchitecture
- Category: Backend / API Architecture
- Language/framework: C# / ASP.NET Core, EF Core, MediatR, FluentValidation
- License: MIT
- License policy used: permissive_only
- Size estimate: 217 text files, 0.9 MiB text
- Tests present: yes (34 detected by inspection)
- repo-wiki language support: limited
- Retrieval task: Add a small CQRS validation rule and identify command/query, endpoint, tests, conventions, and risks.
- Ingestion result: success; 101 files, 141 symbols, 24 knowledge objects, 1593 graph nodes, 1715 graph edges; duration 3256 ms
- Context pack ID: ctx_bd6528b9690a4428
- Latency: 441 ms
- Ingest command: `/usr/bin/python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-multi-repo-benchmark/repos/jason-taylor-cleanarchitecture --license-policy permissive_only`
- Retrieval command: `/usr/bin/python3 -m repo_wiki.interfaces.cli retrieve Add a small CQRS validation rule and identify command/query, endpoint, tests, conventions, and risks. --repo repo_83715853a6755309117a --limit 10 --max-tokens 5000 --format json --license-policy permissive_only`

Top retrieved results:

| Rank | File/Object | Type | Role guessed by repo-wiki | Your judgment |
| ---: | ----------- | ---- | ------------------------- | ------------- |
| 1 | README-template.md | CodeExample |  | Potentially useful but not an expected role. |
| 2 | docs/decisions/ADR-001-Use-EFCore-In-Application-Layer.md | CodeExample |  | Potentially useful but not an expected role. |
| 3 | src/Web/ClientApp/README.md | CodeExample |  | Potentially useful but not an expected role. |
| 4 | .template.config/template.json | CodeExample |  | Potentially useful but not an expected role. |
| 5 | src/Web/ClientApp/package-lock.json | CodeExample |  | Noisy/generic context. |
| 6 | .github/ISSUE_TEMPLATE/feature_request.md | ArchitecturePattern |  | Noisy/generic context. |
| 7 | src/Web/ClientApp-React/src/components/api-authorization/LoginPage.jsx | ImplementationPattern |  | Potentially useful but not an expected role. |
| 8 | src/Web/ClientApp-React/src/components/api-authorization/AuthContext.jsx | ImplementationPattern |  | Potentially useful but not an expected role. |
| 9 | src/Web/ClientApp/src/api-authorization/authorize.interceptor.spec.ts | TestingPattern | related test | Potentially useful but not an expected role. |
| 10 | .github/ISSUE_TEMPLATE/feature_request.md | ProjectProfile |  | Noisy/generic context. |

Key role check:

| Role | Expected file/object | Found? | Rank | Useful? | Notes |
| ---- | -------------------- | -----: | ---: | ------: | ----- |
| Primary edit target | src/Application/TodoLists/Commands/UpdateTodoList/UpdateTodoListCommandValidator.cs | no | - | no | Not found in top 10. |
| Runtime/use-site | src/Web/Endpoints/TodoLists.cs | no | - | no | Not found in top 10. |
| Related test | tests/Application.FunctionalTests/TodoLists/Commands/UpdateTodoListTests.cs | no | - | no | Not found in top 10. |
| Convention/example | src/Application/TodoLists/Commands/CreateTodoList/CreateTodoListCommandValidator.cs | no | - | no | Not found in top 10. |
| Risk-revealing file | src/Application/Common/Exceptions/ValidationException.cs | no | - | no | Not found in top 10. |

Scores:

| Metric | Score |
| ------ | ----: |
| Ingestion success | 4 |
| Primary edit target retrieval | 3 |
| Runtime/use-site retrieval | 3 |
| Related test retrieval | 3 |
| Convention/example retrieval | 3 |
| Risk explanation | 7 |
| Citation usefulness | 8 |
| Noise control | 3 |
| Context compactness | 8 |
| Overall agent usefulness | 3 |

Verdict: retrieval weak

Notes:

- What worked: Returned repository-scoped context, but role precision was weak.
- What failed: C# source files were not indexed by repo-wiki's current text/language filter
- Recommended next action: Add source-file ingestion and extractor support for this language before coding-agent A/B.

### Repository: `Ardalis CleanArchitecture`

- URL: https://github.com/ardalis/CleanArchitecture
- Category: Backend / API Architecture
- Language/framework: C# / ASP.NET Core, FastEndpoints, EF Core
- License: MIT
- License policy used: permissive_only
- Size estimate: 445 text files, 0.5 MiB text
- Tests present: yes (65 detected by inspection)
- repo-wiki language support: limited
- Retrieval task: Add validation/error handling to an endpoint or use case and identify domain/use-case/API/tests/conventions/risks.
- Ingestion result: success; 79 files, 7 symbols, 10 knowledge objects, 98 graph nodes, 104 graph edges; duration 2566 ms
- Context pack ID: ctx_0fb04b6495754e3f
- Latency: 221 ms
- Ingest command: `/usr/bin/python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-multi-repo-benchmark/repos/ardalis-cleanarchitecture --license-policy permissive_only`
- Retrieval command: `/usr/bin/python3 -m repo_wiki.interfaces.cli retrieve Add validation/error handling to an endpoint or use case and identify domain/use-case/API/tests/conventions/risks. --repo repo_6695dfff713143ebe202 --limit 10 --max-tokens 5000 --format json --license-policy permissive_only`

Top retrieved results:

| Rank | File/Object | Type | Role guessed by repo-wiki | Your judgment |
| ---: | ----------- | ---- | ------------------------- | ------------- |
| 1 | sample/src/NimblePros.SampleToDo.Web/wwwroot/lib/jquery-validation-unobtrusive/jquery.validate.unobtrusive.js | CodeExample | convention example | Noisy/generic context. |
| 2 | sample/src/NimblePros.SampleToDo.Web/wwwroot/lib/jquery-validation-unobtrusive/jquery.validate.unobtrusive.min.js | CodeExample | convention example | Noisy/generic context. |
| 3 | sample/src/NimblePros.SampleToDo.Web/wwwroot/lib/jquery-validation/LICENSE.md | CodeExample | convention example | Noisy/generic context. |
| 4 | sample/.github/copilot-instructions.md | CodeExample |  | Noisy/generic context. |
| 5 | .github/copilot-instructions.md | CodeExample |  | Noisy/generic context. |
| 6 | docs/content/migration-guides/v10-to-v11.md | CodeExample |  | Potentially useful but not an expected role. |
| 7 | src/Clean.Architecture.UseCases/README.md | CodeExample |  | Matched Convention/example. |
| 8 | docs/content/design-decisions.md | CodeExample |  | Potentially useful but not an expected role. |
| 9 | docs/content/minimal-clean-architecture.md | CodeExample |  | Potentially useful but not an expected role. |
| 10 | docs/content/architecture-decisions/README.md | CodeExample |  | Nearby/useful for Convention/example. |

Key role check:

| Role | Expected file/object | Found? | Rank | Useful? | Notes |
| ---- | -------------------- | -----: | ---: | ------: | ----- |
| Primary edit target | src/Clean.Architecture.UseCases/Contributors/Delete/DeleteContributorHandler.cs | no | - | no | Not found in top 10. |
| Runtime/use-site | src/Clean.Architecture.Web/Contributors/Update.cs | no | - | no | Not found in top 10. |
| Related test | sample/tests/NimblePros.SampleToDo.FunctionalTests/Contributors/ContributorUpdate.cs | no | - | no | Not found in top 10. |
| Convention/example | src/Clean.Architecture.UseCases/README.md | yes | 7 | yes | Exact expected file appeared in top results. |
| Risk-revealing file | src/Clean.Architecture.Web/Configurations/MiddlewareConfig.cs | no | - | no | Not found in top 10. |

Scores:

| Metric | Score |
| ------ | ----: |
| Ingestion success | 4 |
| Primary edit target retrieval | 3 |
| Runtime/use-site retrieval | 3 |
| Related test retrieval | 3 |
| Convention/example retrieval | 7 |
| Risk explanation | 7 |
| Citation usefulness | 8 |
| Noise control | 3 |
| Context compactness | 8 |
| Overall agent usefulness | 3 |

Verdict: retrieval weak

Notes:

- What worked: Found convention/example.
- What failed: C# source files were not indexed by repo-wiki's current text/language filter
- Recommended next action: Add source-file ingestion and extractor support for this language before coding-agent A/B.

### Repository: `Open TutorAI Community Edition`

- URL: https://github.com/Open-TutorAi/open-tutor-ai-CE
- Category: Education AI Software
- Language/framework: Svelte/Python / SvelteKit, FastAPI, AI services
- License: custom
- License policy used: metadata_only
- Size estimate: 687 text files, 12.4 MiB text
- Tests present: yes (22 detected by inspection)
- repo-wiki language support: limited
- Retrieval task: Add validation to an AI tutoring session setting and identify UI/API/runtime/tests/conventions/risks.
- Ingestion result: success; 269 files, 2462 symbols, 57 knowledge objects, 4471 graph nodes, 5508 graph edges; duration 11112 ms
- Context pack ID: ctx_baf4f2b003de4167
- Latency: 1515 ms
- Ingest command: `/usr/bin/python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-multi-repo-benchmark/repos/open-tutor-ai-ce --license-policy metadata_only`
- Retrieval command: `/usr/bin/python3 -m repo_wiki.interfaces.cli retrieve Add validation to an AI tutoring session setting and identify UI/API/runtime/tests/conventions/risks. --repo repo_b8d65407ec0a3f33be9f --limit 10 --max-tokens 5000 --format json --license-policy metadata_only`

Top retrieved results:

| Rank | File/Object | Type | Role guessed by repo-wiki | Your judgment |
| ---: | ----------- | ---- | ------------------------- | ------------- |
| 1 | gateway/http/routers/knowledge.py | CodeExample | edit target | Potentially useful but not an expected role. |
| 2 | gateway/http/routers/audio.py | CodeExample | edit target | Nearby/useful for Risk-revealing file. |
| 3 | gateway/http/routers/auth.py | CodeExample | edit target | Potentially useful but not an expected role. |
| 4 | gateway/http/routers/retrieval.py | CodeExample | edit target | Potentially useful but not an expected role. |
| 5 | gateway/http/routers/images.py | CodeExample | edit target | Potentially useful but not an expected role. |
| 6 | gateway/http/app.py | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 7 | ui/cypress/e2e/auth.cy.ts | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 8 | ui/cypress/support/e2e.ts | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 9 | tests/test_knowledge.py | TestingPattern | related test | Nearby/useful for Related test. |
| 10 | tests/test_files.py | TestingPattern | related test | Nearby/useful for Related test. |

Key role check:

| Role | Expected file/object | Found? | Rank | Useful? | Notes |
| ---- | -------------------- | -----: | ---: | ------: | ----- |
| Primary edit target | ai/providers/config_service.py | no | - | no | Not found in top 10. |
| Runtime/use-site | ui/src/routes/(app)/admin/paired-responses/+page.svelte | no | - | no | Not found in top 10. |
| Related test | tests/test_chats.py | no | 9 | yes | Related or nearby file appeared, but not the expected file. |
| Convention/example | docs/responsible-ai-notifications.md | no | - | no | Not found in top 10. |
| Risk-revealing file | ui/src/lib/components/chat/Settings/Audio.svelte | no | 2 | yes | Related or nearby file appeared, but not the expected file. |

Scores:

| Metric | Score |
| ------ | ----: |
| Ingestion success | 4 |
| Primary edit target retrieval | 3 |
| Runtime/use-site retrieval | 3 |
| Related test retrieval | 4 |
| Convention/example retrieval | 3 |
| Risk explanation | 7 |
| Citation usefulness | 4 |
| Noise control | 8 |
| Context compactness | 8 |
| Overall agent usefulness | 5 |

Verdict: usable with issues

Notes:

- What worked: Returned repository-scoped context, but role precision was weak.
- What failed: Svelte support is architecture/file-level only
- Recommended next action: Add source indexing/extraction for this language or scoped include patterns before A/B.

### Repository: `DeepTutor`

- URL: https://github.com/HKUDS/DeepTutor
- Category: Education AI Software
- Language/framework: Python / FastAPI, agentic tutoring services
- License: Apache-2.0
- License policy used: permissive_only
- Size estimate: 1528 text files, 11.6 MiB text
- Tests present: yes (320 detected by inspection)
- repo-wiki language support: full
- Retrieval task: Add error handling to a tutoring/quiz generation workflow and identify agent runtime, UI/API, tests, examples, and risks.
- Ingestion result: success; 1511 files, 15382 symbols, 162 knowledge objects, 18266 graph nodes, 32446 graph edges; duration 58048 ms
- Context pack ID: ctx_25818f8de1694d81
- Latency: 5052 ms
- Ingest command: `/usr/bin/python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-multi-repo-benchmark/repos/deeptutor --license-policy permissive_only`
- Retrieval command: `/usr/bin/python3 -m repo_wiki.interfaces.cli retrieve Add error handling to a tutoring/quiz generation workflow and identify agent runtime, UI/API, tests, examples, and risks. --repo repo_0ee8ba5f68945d590d95 --limit 10 --max-tokens 5000 --format json --license-policy permissive_only --language Python --framework FastAPI`

Top retrieved results:

| Rank | File/Object | Type | Role guessed by repo-wiki | Your judgment |
| ---: | ----------- | ---- | ------------------------- | ------------- |
| 1 | deeptutor/api/routers/sessions.py | CodeExample | edit target | Nearby/useful for Primary edit target, Runtime/use-site. |
| 2 | deeptutor/api/routers/settings.py | CodeExample | edit target | Nearby/useful for Primary edit target, Runtime/use-site. |
| 3 | deeptutor/api/routers/mastery_path.py | CodeExample | edit target | Nearby/useful for Primary edit target, Runtime/use-site. |
| 4 | deeptutor/book/blocks/quiz.py | CodeExample | edit target | Matched Convention/example. |
| 5 | deeptutor/api/routers/quiz_judge.py | CodeExample | runtime risk | Matched Primary edit target. |
| 6 | deeptutor/api/routers/question.py | CodeExample | runtime risk | Matched Runtime/use-site. |
| 7 | deeptutor/api/routers/tools.py | CodeExample | runtime risk | Nearby/useful for Primary edit target, Runtime/use-site. |
| 8 | tests/api/test_unified_ws_turn_runtime.py | TestingPattern | related test | Potentially useful but not an expected role. |
| 9 | tests/agents/question/test_pipeline.py | TestingPattern | related test | Matched Related test. |
| 10 | tests/services/session/test_turn_runtime.py | TestingPattern | related test | Potentially useful but not an expected role. |

Key role check:

| Role | Expected file/object | Found? | Rank | Useful? | Notes |
| ---- | -------------------- | -----: | ---: | ------: | ----- |
| Primary edit target | deeptutor/api/routers/quiz_judge.py | yes | 5 | yes | Exact expected file appeared in top results. |
| Runtime/use-site | deeptutor/api/routers/question.py | yes | 6 | yes | Exact expected file appeared in top results. |
| Related test | tests/agents/question/test_pipeline.py | yes | 9 | yes | Exact expected file appeared in top results. |
| Convention/example | deeptutor/book/blocks/quiz.py | yes | 4 | yes | Exact expected file appeared in top results. |
| Risk-revealing file | deeptutor/agents/math_animator/retry_manager.py | no | - | no | Not found in top 10. |

Scores:

| Metric | Score |
| ------ | ----: |
| Ingestion success | 10 |
| Primary edit target retrieval | 8 |
| Runtime/use-site retrieval | 7 |
| Related test retrieval | 7 |
| Convention/example retrieval | 8 |
| Risk explanation | 7 |
| Citation usefulness | 8 |
| Noise control | 3 |
| Context compactness | 8 |
| Overall agent usefulness | 7 |

Verdict: usable with issues

Notes:

- What worked: Found primary edit target, runtime/use-site, related test, convention/example.
- What failed: missed primary edit target
- Recommended next action: Improve source-to-test pairing and role labeling before A/B.

### Repository: `OpenMAIC`

- URL: https://github.com/THU-MAIC/OpenMAIC
- Category: Education AI Software
- Language/framework: TypeScript / Next.js, multi-agent classroom workflows
- License: MIT
- License policy used: permissive_only
- Size estimate: 1316 text files, 10.8 MiB text
- Tests present: yes (238 detected by inspection)
- repo-wiki language support: full
- Retrieval task: Add validation to lesson quiz generation settings and identify agent workflow, API/UI, tests, examples, and risks.
- Ingestion result: success; 1293 files, 26259 symbols, 154 knowledge objects, 27980 graph nodes, 30860 graph edges; duration 67540 ms
- Context pack ID: ctx_25bcadb9c0154457
- Latency: 4968 ms
- Ingest command: `/usr/bin/python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-multi-repo-benchmark/repos/openmaic --license-policy permissive_only`
- Retrieval command: `/usr/bin/python3 -m repo_wiki.interfaces.cli retrieve Add validation to lesson quiz generation settings and identify agent workflow, API/UI, tests, examples, and risks. --repo repo_84b6365482973824c744 --limit 10 --max-tokens 5000 --format json --license-policy permissive_only --language TypeScript --framework Express`

Top retrieved results:

| Rank | File/Object | Type | Role guessed by repo-wiki | Your judgment |
| ---: | ----------- | ---- | ------------------------- | ------------- |
| 1 | lib/generation/scene-generator.ts | CodeExample | edit target | Potentially useful but not an expected role. |
| 2 | lib/store/settings.ts | CodeExample | edit target | Matched Convention/example. |
| 3 | lib/types/generation.ts | CodeExample | edit target | Potentially useful but not an expected role. |
| 4 | lib/store/settings-validation.ts | CodeExample | convention example | Matched Primary edit target. |
| 5 | lib/generation/outline-type.ts | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 6 | lib/generation/scene-builder.ts | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 7 | lib/api/stage-api-defaults.ts | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 8 | app/api/generate/scene-content/route.ts | CodeExample | runtime risk | Matched Runtime/use-site. |
| 9 | e2e/fixtures/mock-api.ts | CodeExample | runtime risk | Potentially useful but not an expected role. |
| 10 | e2e/tests/home-to-generation.spec.ts | TestingPattern | related test | Matched Related test. |

Key role check:

| Role | Expected file/object | Found? | Rank | Useful? | Notes |
| ---- | -------------------- | -----: | ---: | ------: | ----- |
| Primary edit target | lib/store/settings-validation.ts | yes | 4 | yes | Exact expected file appeared in top results. |
| Runtime/use-site | app/api/generate/scene-content/route.ts | yes | 8 | yes | Exact expected file appeared in top results. |
| Related test | e2e/tests/home-to-generation.spec.ts | yes | 10 | yes | Exact expected file appeared in top results. |
| Convention/example | lib/store/settings.ts | yes | 2 | yes | Exact expected file appeared in top results. |
| Risk-revealing file | lib/server/llm-error-response.ts | no | - | no | Not found in top 10. |

Scores:

| Metric | Score |
| ------ | ----: |
| Ingestion success | 10 |
| Primary edit target retrieval | 8 |
| Runtime/use-site retrieval | 7 |
| Related test retrieval | 7 |
| Convention/example retrieval | 10 |
| Risk explanation | 7 |
| Citation usefulness | 8 |
| Noise control | 8 |
| Context compactness | 8 |
| Overall agent usefulness | 8 |

Verdict: strong candidate for coding-agent A/B test

Notes:

- What worked: Found primary edit target, runtime/use-site, related test, convention/example.
- What failed: weak source-to-test pairing
- Recommended next action: Improve source-to-test pairing and role labeling before A/B.

### Repository: `AI LMS`

- URL: https://github.com/alfredang/ai-lms
- Category: Education AI Software
- Language/framework: TypeScript / Next.js, Prisma, NextAuth
- License: not detected
- License policy used: metadata_only
- Size estimate: 126 text files, 1.2 MiB text
- Tests present: no (0 detected by inspection)
- repo-wiki language support: full
- Retrieval task: Add validation for an AI learning assistance setting in the Next.js LMS and identify route/component/server/tests/conventions/risks.
- Ingestion result: success; 124 files, 700 symbols, 25 knowledge objects, 1606 graph nodes, 1844 graph edges; duration 6209 ms
- Context pack ID: ctx_e969e511a6304d59
- Latency: 1366 ms
- Ingest command: `/usr/bin/python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-multi-repo-benchmark/repos/ai-lms --license-policy metadata_only`
- Retrieval command: `/usr/bin/python3 -m repo_wiki.interfaces.cli retrieve Add validation for an AI learning assistance setting in the Next.js LMS and identify route/component/server/tests/conventions/risks. --repo repo_8b8c0cb64ecae5717ae5 --limit 10 --max-tokens 5000 --format json --license-policy metadata_only --language TypeScript --framework Gin`

Top retrieved results:

| Rank | File/Object | Type | Role guessed by repo-wiki | Your judgment |
| ---: | ----------- | ---- | ------------------------- | ------------- |
| 1 | src/app/api/ai/chat/route.ts | CodeExample | edit target | Matched Primary edit target. |
| 2 | src/app/api/lessons/complete/route.ts | CodeExample | edit target | Nearby/useful for Primary edit target, Risk-revealing file. |
| 3 | src/app/api/assignments/submit/route.ts | CodeExample | edit target | Nearby/useful for Primary edit target, Risk-revealing file. |
| 4 | src/app/api/payments/paypal/route.ts | CodeExample | edit target | Nearby/useful for Primary edit target, Risk-revealing file. |
| 5 | src/app/api/payments/stripe/route.ts | CodeExample | edit target | Nearby/useful for Primary edit target, Risk-revealing file. |
| 6 | src/app/api/enrollments/route.ts | CodeExample | edit target | Nearby/useful for Primary edit target, Risk-revealing file. |
| 7 | src/app/api/auth/register/route.ts | CodeExample | edit target | Matched Risk-revealing file. |
| 8 | src/app/api/auth/[...nextauth]/route.ts | CodeExample | edit target | Nearby/useful for Primary edit target, Risk-revealing file. |
| 9 | src/app/(dashboard)/superadmin/api-keys/page.tsx | CodeExample | runtime risk | Matched Runtime/use-site. |
| 10 | src/app/(docs)/docs/api/page.tsx | CodeExample | runtime risk | Matched Convention/example. |

Key role check:

| Role | Expected file/object | Found? | Rank | Useful? | Notes |
| ---- | -------------------- | -----: | ---: | ------: | ----- |
| Primary edit target | src/app/api/ai/chat/route.ts | yes | 1 | yes | Exact expected file appeared in top results. |
| Runtime/use-site | src/app/(dashboard)/superadmin/api-keys/page.tsx | yes | 9 | yes | Exact expected file appeared in top results. |
| Related test | not found during inspection | no | - | no | No clear expected file found during bounded inspection. |
| Convention/example | src/app/(docs)/docs/api/page.tsx | yes | 10 | yes | Exact expected file appeared in top results. |
| Risk-revealing file | src/app/api/auth/register/route.ts | yes | 7 | yes | Exact expected file appeared in top results. |

Scores:

| Metric | Score |
| ------ | ----: |
| Ingestion success | 10 |
| Primary edit target retrieval | 10 |
| Runtime/use-site retrieval | 7 |
| Related test retrieval | 3 |
| Convention/example retrieval | 7 |
| Risk explanation | 7 |
| Citation usefulness | 4 |
| Noise control | 8 |
| Context compactness | 8 |
| Overall agent usefulness | 7 |

Verdict: usable with issues

Notes:

- What worked: Found primary edit target, runtime/use-site, convention/example, risk-revealing file.
- What failed: weak source-to-test pairing
- Recommended next action: Improve source-to-test pairing and role labeling before A/B.

### Repository: `openLesson`

- URL: https://github.com/dncolomer/openlesson
- Category: Education AI Software
- Language/framework: TypeScript / Next.js, React
- License: not detected
- License policy used: metadata_only
- Size estimate: 460 text files, 4.4 MiB text
- Tests present: yes (3 detected by inspection)
- repo-wiki language support: full
- Retrieval task: Add validation/error handling to Socratic tutoring session setup and identify client/server/runtime/tests/conventions/risks.
- Ingestion result: success; 449 files, 6493 symbols, 48 knowledge objects, 7952 graph nodes, 8487 graph edges; duration 23956 ms
- Context pack ID: ctx_ceca1750343240a7
- Latency: 970 ms
- Ingest command: `/usr/bin/python3 -m repo_wiki.interfaces.cli ingest local /tmp/repo-wiki-multi-repo-benchmark/repos/openlesson --license-policy metadata_only`
- Retrieval command: `/usr/bin/python3 -m repo_wiki.interfaces.cli retrieve Add validation/error handling to Socratic tutoring session setup and identify client/server/runtime/tests/conventions/risks. --repo repo_b2afc03c98b11ee52e50 --limit 10 --max-tokens 5000 --format json --license-policy metadata_only --language TypeScript --framework Gin`

Top retrieved results:

| Rank | File/Object | Type | Role guessed by repo-wiki | Your judgment |
| ---: | ----------- | ---- | ------------------------- | ------------- |
| 1 | app/api/session-chat/route.ts | CodeExample | edit target | Matched Primary edit target. |
| 2 | app/api/session-chat/welcome/route.ts | CodeExample |  | Matched Runtime/use-site. |
| 3 | app/api/session/performance-chat/route.ts | CodeExample |  | Nearby/useful for Primary edit target, Runtime/use-site. |
| 4 | app/api/session-plan/translate/route.ts | CodeExample |  | Nearby/useful for Primary edit target, Runtime/use-site. |
| 5 | app/api/session-plan/create/route.ts | CodeExample |  | Nearby/useful for Primary edit target, Runtime/use-site. |
| 6 | app/api/session-plan/reset-probes/route.ts | CodeExample |  | Nearby/useful for Primary edit target, Runtime/use-site. |
| 7 | app/api/session-plan/regenerate/route.ts | CodeExample |  | Nearby/useful for Primary edit target, Runtime/use-site. |
| 8 | app/api/session/stuck-policy/route.ts | CodeExample |  | Nearby/useful for Primary edit target, Runtime/use-site. |
| 9 | app/api/session-plan/get/route.ts | CodeExample |  | Nearby/useful for Primary edit target, Runtime/use-site. |
| 10 | app/api/session-files/upload/route.ts | CodeExample |  | Nearby/useful for Primary edit target, Runtime/use-site. |

Key role check:

| Role | Expected file/object | Found? | Rank | Useful? | Notes |
| ---- | -------------------- | -----: | ---: | ------: | ----- |
| Primary edit target | app/api/session-chat/route.ts | yes | 1 | yes | Exact expected file appeared in top results. |
| Runtime/use-site | app/api/session-chat/welcome/route.ts | yes | 2 | yes | Exact expected file appeared in top results. |
| Related test | tests/lib/plans.test.ts | no | - | no | Not found in top 10. |
| Convention/example | docs/example-integrations/pumadoc/pumadoc-shadow-mode-skill.md | no | - | no | Not found in top 10. |
| Risk-revealing file | app/privacy/page.tsx | no | - | no | Not found in top 10. |

Scores:

| Metric | Score |
| ------ | ----: |
| Ingestion success | 10 |
| Primary edit target retrieval | 10 |
| Runtime/use-site retrieval | 10 |
| Related test retrieval | 2 |
| Convention/example retrieval | 2 |
| Risk explanation | 7 |
| Citation usefulness | 4 |
| Noise control | 8 |
| Context compactness | 8 |
| Overall agent usefulness | 6 |

Verdict: usable with issues

Notes:

- What worked: Found primary edit target, runtime/use-site.
- What failed: weak source-to-test pairing
- Recommended next action: Improve source-to-test pairing and role labeling before A/B.

## 7. Best Repositories For Next A/B Coding Test

| Repository | Why suitable | Suggested coding task | Expected repo-wiki advantage |
| ---------- | ------------ | --------------------- | ---------------------------- |
| Dapr Agents | Best overall score; retrieved durable-agent runtime and tests. | Add retry/error handling to durable workflow execution. | Should point agents to durable runtime, runner, and local tests quickly. |
| OpenScribe | Healthcare TypeScript monorepo with strong runtime/API retrieval. | Add validation for final transcription recording errors. | Should surface final transcription route, UI page, and note/audio risks. |
| VoltAgent | TypeScript agent platform; useful agent and memory files retrieved. | Add a provider option to agent memory configuration. | Should locate core agent runtime and example memory setup. |
| OpenMAIC | Education agent workflow with good settings/generation hits. | Add validation to lesson generation settings. | Should surface settings validation, generation route, and e2e convention. |
| LangGraph | Large but completed Python agent framework; config/runtime retrieval was useful. | Add validation for checkpoint/runtime config. | Should find CLI config, runtime files, and nearby config tests. |

## 8. Worst / Weakest Cases

| Repository | Main failure | Likely cause | Suggested improvement |
| ---------- | ------------ | ------------ | --------------------- |
| CrewAI | repository too large for bounded CLI benchmark run | Repository exceeded bounded benchmark size limit or timed out during ingestion. | Re-run with scoped include patterns or incremental ingestion before A/B testing. |
| n8n | repository too large for bounded CLI benchmark run | Repository exceeded bounded benchmark size limit or timed out during ingestion. | Re-run with scoped include patterns or incremental ingestion before A/B testing. |
| Go Backend Clean Architecture | Go source files were not indexed by repo-wiki's current text/language filter | Main language was unsupported or only partially visible to repo-wiki extraction. | Add source-file ingestion and extractor support for this language before coding-agent A/B. |
| Jason Taylor CleanArchitecture | C# source files were not indexed by repo-wiki's current text/language filter | Main language was unsupported or only partially visible to repo-wiki extraction. | Add source-file ingestion and extractor support for this language before coding-agent A/B. |
| Ardalis CleanArchitecture | C# source files were not indexed by repo-wiki's current text/language filter | Main language was unsupported or only partially visible to repo-wiki extraction. | Add source-file ingestion and extractor support for this language before coding-agent A/B. |
| Modular Monolith with DDD | C# source files were not indexed by repo-wiki's current text/language filter | Main language was unsupported or only partially visible to repo-wiki extraction. | Add source-file ingestion and extractor support for this language before coding-agent A/B. |
| Open TutorAI Community Edition | Svelte support is architecture/file-level only | Ranking favored generic or adjacent context over precise task roles. | Add source indexing/extraction for this language or scoped include patterns before A/B. |
| AI Healthcare System | weak source-to-test pairing | Ranking lacks robust source-to-test pairing. | Improve source-to-test pairing and role labeling before A/B. |

## 9. Common Failure Patterns

- Unsupported language: Go and C# source files were not indexed as source candidates; Svelte was partially visible through adjacent Python/TS/API files rather than first-class component extraction.
- Missing tests: some repositories had few or no test files indexed for the selected workflow, so related-test retrieval fell back to generic tests or none.
- Weak source-to-test pairing: even in Python/TypeScript repositories, repo-wiki often found useful source files but not the most relevant test file.
- Poor citation propagation: restrictive or unclear license policy forced metadata-only citations, and some useful trace-ranked files were not exposed with enough citation detail.
- Noisy generic context: validation queries sometimes surfaced generic settings, docs, lock files, vendored frontend assets, or broad architecture docs ahead of precise implementation files.
- Architecture too large: CrewAI and n8n were too large for this bounded CLI pass without scoped include patterns or incremental ingestion.
- License/snippet restrictions: GPL or unknown-license repositories were ingested with metadata-only policy, reducing citation usefulness.
- Frontend/backend boundary confusion: full-stack education and healthcare apps often returned API routes where UI state or service-layer files were the better first edit targets.
- Monorepo complexity: LangGraph, VoltAgent, OpenScribe, and OpenMAIC showed useful hits, but role labeling and package-level source-to-test pairing need improvement.

## 10. Recommendations Before Agent A/B Benchmark

- Add source-file candidate support for `.go`, `.cs`, `.csproj`, and `.svelte`; the current text filter is the biggest blocker for backend architecture repos.
- Improve source-to-test pairing with same-stem, import graph, route-to-test, and package-local heuristics before using repo-wiki as a coding-agent advantage signal.
- Add explicit context role labeling for edit target, runtime/use-site, test, convention, and risk so agents can act without inferring each file's purpose from summaries.
- Prevent cross-repository fallback when a `--repo` filter is supplied and language/framework filters over-constrain results.
- Add scoped ingestion presets for very large monorepos, for example package-level include patterns for CrewAI and n8n.
- Penalize vendored/generated assets more strongly during ranking, especially `wwwroot/lib`, lock files, fixtures, and generated API clients.
- Preserve citations for trace-ranked source-file matches even when snippets are disallowed; metadata citations are still valuable.
- Add benchmark tooling that records commands, timings, trace ranking details, expected roles, and manual judgments in one reproducible run.

## 11. Next Phase Plan

1. Select the top 5 repositories from this report: Dapr Agents, OpenScribe, VoltAgent, OpenMAIC, and LangGraph.
2. Create fixed coding tasks with expected source, test, and risk files for each repository.
3. Run A/B coding-agent trials with and without repo-wiki context packs.
4. Compare agent output quality, correctness, test targeting, citation use, and noise sensitivity.
5. After coding-agent A/B validation, test 0-to-100 project generation separately with agents such as opencode.
