# Multi-Repository Benchmark Failures

| Repository | Status | Reason | Next action |
| ---------- | ------ | ------ | ----------- |
| CrewAI | skipped / unsupported | repository too large for bounded CLI benchmark run | Re-run with scoped include patterns or incremental ingestion before A/B testing. |
| n8n | skipped / unsupported | repository too large for bounded CLI benchmark run | Re-run with scoped include patterns or incremental ingestion before A/B testing. |
| Go Backend Clean Architecture | retrieval weak | Go source files were not indexed by repo-wiki's current text/language filter | Add source-file ingestion and extractor support for this language before coding-agent A/B. |
| Modular Monolith with DDD | retrieval weak | C# source files were not indexed by repo-wiki's current text/language filter | Add source-file ingestion and extractor support for this language before coding-agent A/B. |
| Jason Taylor CleanArchitecture | retrieval weak | C# source files were not indexed by repo-wiki's current text/language filter | Add source-file ingestion and extractor support for this language before coding-agent A/B. |
| Ardalis CleanArchitecture | retrieval weak | C# source files were not indexed by repo-wiki's current text/language filter | Add source-file ingestion and extractor support for this language before coding-agent A/B. |
