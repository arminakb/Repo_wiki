# ADR 0001: Local-First SQLite Storage

Status: Accepted

## Context

The project needs to index repositories, store metadata, graph relationships, retrieval traces, feedback, and knowledge objects. The MVP must be easy to run locally and credible as a portfolio project.

## Decision

Use SQLite as the primary MVP store, with SQLite FTS5 for lexical retrieval and replaceable local hash-vector scoring.

## Consequences

- The project is easy to install and demo.
- Schema and query behavior remain transparent.
- The system can still migrate later to PostgreSQL, Qdrant, or a graph database.
- Large-scale distributed ingestion is deferred.

## Alternatives Considered

- PostgreSQL from day one.
- Neo4j from day one.
- Hosted vector database from day one.
- Semantic embeddings from day one.

These add operational complexity before the retrieval model is proven.
