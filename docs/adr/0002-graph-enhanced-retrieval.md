# ADR 0002: Graph-Enhanced Retrieval Instead of Graph-Only Retrieval

Status: Accepted

## Context

The system targets repository-scale knowledge for coding agents. A graph is useful for relationships between repos, files, symbols, tests, dependencies, frameworks, and patterns. But graph traversal alone is not enough for task retrieval.

## Decision

Use the graph as a relationship and expansion layer. V1 retrieval combines lexical search, metadata filtering, deterministic hash-vector scoring, graph expansion, reranking, and context compression.

## Consequences

- Retrieval remains practical for exact terms, fuzzy concepts, and relationship-aware expansion.
- The graph stores high-signal edges instead of noisy chunk-to-chunk relationships.
- The system can migrate to Neo4j later if graph traversal becomes central.

## Alternatives Considered

- Pure vector retrieval.
- Pure graph retrieval.
- Raw chunk GraphRAG.

These approaches either lose structural relationships or create too much noisy graph data.
