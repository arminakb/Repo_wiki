You are a senior autonomous coding agent and evaluator.

Your task is to run a strict A/B evaluation for a project called `repo-wiki`.

`repo-wiki` is a local-first repository knowledge system. It ingests software repositories, extracts architecture patterns, implementation patterns, modules, functions, dependencies, tests, and conventions, then builds a knowledge graph and an Obsidian-style vault. Its purpose is to help coding agents write better, faster, more architecture-consistent code with fewer hallucinations.

You must evaluate whether repo-wiki actually helps.

Important rules:

* Be honest and strict.
* Do not praise the tool unless the evidence supports it.
* Do not skip the baseline phase.
* Do not use repo-wiki during Phase A.
* Use the same repository and the same task for both Phase A and Phase B.
* Keep the task small enough to evaluate clearly.
* Do not push changes to remote.
* Do not make destructive changes.
* If implementation is risky or impossible, produce implementation plans only and explain why.

Inputs:

* repo-wiki project path: `/home/armin/Documents/repo-agent-architecture/.worktrees/plan-execution/repo_wiki/`
* target repository URL or local path: `/home/armin/Documents/repo-agent-architecture/.worktrees/plan-execution/dataset/graphrag-main/`
* preferred repo-wiki interface: `you choose`
* target task: `<TARGET_TASK_OR_LEAVE_EMPTY>`
* max time budget: `just do it right and complete`
* implementation allowed: `ask for premission`

If no target task is provided, choose one realistic bounded task from the target repository, such as:

* add a small API endpoint,
* add a validation rule,
* add or improve tests for an existing feature,
* refactor a small module to match existing conventions,
* add a utility function following existing project style,
* document an existing architecture pattern.

Avoid:

* huge redesigns,
* vague tasks,
* one-line cosmetic changes,
* tasks that require external paid services,
* tasks that require pushing to remote.

# A/B Evaluation Protocol

## Phase 0 — Repository and Task Setup

1. Identify the target repository.
2. Identify the main language and framework.
3. Inspect the repository structure briefly.
4. Select or confirm the task.
5. Explain why this task is a good evaluation target.
6. Define success criteria for the task.

Success criteria should include:

* correct files identified,
* architecture conventions followed,
* relevant tests identified or added,
* minimal hallucination,
* no unrelated changes,
* implementation plan is specific and actionable.

Do not use repo-wiki yet.

---

## Phase A — Baseline Without repo-wiki

In this phase, work like a normal coding agent without repo-wiki.

1. Inspect the repository manually.
2. Identify relevant files.
3. Identify relevant functions, classes, routes, configs, or tests.
4. Infer the architecture and conventions.
5. Create an implementation plan.
6. Identify risks and unknowns.
7. Estimate confidence from 1 to 10.
8. If implementation is allowed, implement the task on a clean branch or working tree state.
9. Run tests if feasible.

Record:

* time spent or rough effort,
* files inspected,
* files changed, if any,
* tests run,
* errors or uncertainty,
* final confidence.

Important:
Do not use repo-wiki, its vault, its graph, its context packs, or its retrieval tools during Phase A.

---

## Phase B — repo-wiki Assisted Run

Reset or clearly separate the working state from Phase A.

Now use repo-wiki.

1. Ingest the target repository into repo-wiki.
2. Retrieve a context pack for the exact same task.
3. Record the exact command, API call, or MCP tool call.
4. Capture the retrieved context pack.
5. Inspect:

   * recommended architecture patterns,
   * relevant files,
   * relevant functions/classes,
   * implementation patterns,
   * testing patterns,
   * risks,
   * anti-patterns,
   * citations/source references,
   * graph relationships, if available.

Then repeat the same task using the repo-wiki context.

Create:

1. repo-wiki-assisted implementation plan.
2. list of files you would inspect or edit.
3. list of tests you would run or add.
4. risk analysis.
5. confidence score from 1 to 10.

If implementation is allowed:

1. Implement the task.
2. Keep the patch small.
3. Run tests if feasible.
4. Record changed files and test results.

---

## Phase C — Direct Comparison

Compare Phase A and Phase B.

Answer these questions:

1. Did repo-wiki identify relevant files faster or more accurately?
2. Did repo-wiki reveal architecture conventions missed in the baseline?
3. Did repo-wiki suggest better tests?
4. Did repo-wiki reduce hallucination or guessing?
5. Did repo-wiki reduce uncertainty?
6. Did repo-wiki create any noise or misleading guidance?
7. Were the citations useful?
8. Were the citations specific enough?
9. Was the context pack compact enough for an agent?
10. Did repo-wiki improve the final implementation plan or patch?
11. Would you use repo-wiki again on this repository?
12. What should be improved before repo-wiki is useful in real agent workflows?

---

# Final Output Format

Produce the final report exactly in this structure:

# repo-wiki A/B Evaluation Report

## 1. Target Repository

* Repository:
* URL/path:
* Main language:
* Frameworks/libraries:
* License:
* Approximate size:
* Why this repository was chosen:

## 2. Selected Task

* Task:
* Why this task is suitable for evaluation:
* Success criteria:

## 3. Phase A — Baseline Without repo-wiki

### Repository understanding

Describe what you understood manually.

### Relevant files found manually

List files and explain why they seemed relevant.

### Baseline architecture assumptions

List the architecture conventions you inferred manually.

### Baseline implementation plan

Give the implementation plan.

### Baseline tests

List tests you would run or add.

### Baseline risks and unknowns

List risks.

### Baseline result

* Implemented: yes/no
* Changed files:
* Tests run:
* Test result:
* Confidence score before repo-wiki: `/10`
* Notes:

## 4. Phase B — With repo-wiki

### repo-wiki usage

* Interface used:
* Ingestion command/tool call:
* Retrieval command/tool call:
* Context pack ID, if available:
* Retrieval latency, if available:

### Retrieved context summary

Summarize the most useful retrieved knowledge.

### Retrieved relevant files/functions

List files, functions, classes, routes, configs, or tests suggested by repo-wiki.

### Retrieved architecture patterns

List patterns repo-wiki identified.

### Retrieved testing guidance

List tests suggested by repo-wiki.

### Retrieved risks or anti-patterns

List risks or anti-patterns suggested by repo-wiki.

### Citation quality

Evaluate whether citations were:

* present,
* specific,
* accurate,
* useful.

### repo-wiki-assisted implementation plan

Give the improved implementation plan.

### repo-wiki-assisted result

* Implemented: yes/no
* Changed files:
* Tests run:
* Test result:
* Confidence score after repo-wiki: `/10`
* Notes:

## 5. A/B Comparison Table

Create a table with these columns:

| Area | Baseline Without repo-wiki | With repo-wiki | Winner | Evidence |
| ---- | -------------------------- | -------------- | ------ | -------- |

Compare these areas:

* relevant file discovery,
* architecture understanding,
* implementation planning,
* test planning,
* risk detection,
* convention following,
* citation support,
* confidence,
* speed,
* hallucination reduction,
* final patch quality,
* overall usefulness.

## 6. Quantitative Scores

Score each item from 1 to 10.

### Baseline scores

* Relevant file discovery:
* Architecture understanding:
* Implementation plan quality:
* Test plan quality:
* Risk awareness:
* Confidence:
* Expected hallucination risk, where 10 means very low risk:
* Overall baseline quality:

### repo-wiki-assisted scores

* Retrieval relevance:
* Citation usefulness:
* Context compactness:
* Architecture guidance:
* Implementation usefulness:
* Test guidance:
* Risk awareness:
* Noise level, where 10 means very low noise:
* Confidence:
* Expected hallucination risk, where 10 means very low risk:
* Overall repo-wiki-assisted quality:

## 7. Measured Improvement

Estimate the improvement.

* Confidence improvement:
* Relevant file discovery improvement:
* Architecture understanding improvement:
* Test planning improvement:
* Hallucination risk reduction:
* Overall usefulness improvement:

Use percentages only if you can justify them. Otherwise use qualitative labels:

* none,
* small,
* moderate,
* high.

## 8. Final Verdict

Choose exactly one:

* repo-wiki was highly useful
* repo-wiki was moderately useful
* repo-wiki was slightly useful
* repo-wiki was not useful yet

Explain the verdict with evidence.

## 9. Concrete Product Feedback for repo-wiki

Give specific recommendations.

### What worked well

List the strongest parts.

### What did not work well

List weak or broken parts.

### Missing features

List missing features.

### Retrieval problems

List irrelevant, noisy, duplicated, or missing results.

### Citation problems

List citation issues.

### UX problems

List CLI/MCP/API usability issues.

### Suggested next priorities

Give a prioritized list of engineering improvements.

## 10. Reflexion Feedback Payload

Return this JSON filled with your evaluation:

```json
{
  "accepted": true,
  "rating": 0,
  "tests_passed": null,
  "lint_passed": null,
  "build_passed": null,
  "merged": false,
  "rollback": false,
  "notes": "",
  "helped_with": [],
  "failed_with": [],
  "suggested_improvements": [],
  "baseline_confidence": 0,
  "repo_wiki_confidence": 0,
  "overall_verdict": ""
}
```

Be strict. The goal is to determine whether repo-wiki gives measurable advantage over a normal autonomous coding agent workflow.
