# ADR 0004: Documentation and Presentation as First-Class Deliverables

Status: Accepted

## Context

For hiring and portfolio evaluation, code quality alone is not enough. Reviewers need to understand the architecture, decisions, roadmap, examples, benchmarks, and project maturity quickly.

## Decision

Treat documentation and presentation assets as core deliverables. Maintain:

- README.
- SAS.
- AGENT.md.
- ARCHITECTURE.md.
- ROADMAP.md.
- DECISIONS.md.
- CONTRIBUTING.md.
- ADRs.
- diagrams.
- examples.
- benchmarks.

## Consequences

- The project is easier for humans and agents to understand.
- Architecture changes must update docs.
- Benchmark results and usage examples become part of the product.

## Alternatives Considered

- Add documentation after implementation.
- Keep only a README.

Both would weaken agent usability and portfolio quality.
