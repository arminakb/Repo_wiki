# retrieval v0.1 Blind Holdout

This blind holdout was run after freezing retrieval v0.1. Retrieval logic was not changed during the run.

## Setup

- Workspace: `/tmp/repo-wiki-v0.1-blind-holdout`
- Data directory: `/tmp/repo-wiki-v0.1-blind-holdout/data`
- Target repositories: local snapshots only
- Implementation patches: none
- Target repository modifications: none

Expected files were selected from bounded source inspection before repo-wiki retrieval results were inspected.

## Results

| Repository | Language | Task focus | Score | Verdict | Primary rank | Top-5 hits | Top-10 hits | Latency |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| DeepSeek-V3 | Python | ModelArgs validation | 8/10 | pass | 1 | 2/3 | 2/3 | 158 ms |
| autoresearch | Python | GPTConfig validation | 8/10 | pass | 1 | 2/3 | 2/3 | 86 ms |
| NextChat | TypeScript | Authorization parsing | 7/10 | pass | 1 | 1/3 | 2/3 | 2204 ms |
| pretext | TypeScript | layout option validation | 7/10 | partial | 4 | 2/3 | 3/3 | 3490 ms |
| dexter | TypeScript | resolveRoute peer matching | 9/10 | pass | 1 | 3/3 | 3/3 | 3659 ms |

## Aggregate

- Repositories: 5.
- Pass / partial / fail: 4 / 1 / 0.
- Expected hits top 10: 12/15.
- Expected hits top 5: 10/15.
- Average score: 7.8/10.
- Average latency: 1919.4 ms.
- Citation coverage: 100%.

## Notes

- DeepSeek-V3 and autoresearch ranked the primary edit target first but did not surface project config files in the top 10.
- NextChat ranked the primary auth file first but missed the client access store.
- pretext found all expected files in the top 10, but the primary edit target ranked 4th behind noisy script/test files.
- dexter found all expected source, test, and config context in the top 5.

## Limitations

This is a retrieval-only check. It does not measure whether an autonomous coding agent would produce a better patch after reading the context pack.
