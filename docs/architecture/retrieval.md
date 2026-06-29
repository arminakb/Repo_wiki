# Retrieval Architecture

Retrieval is hybrid:

- lexical search with SQLite FTS5.
- deterministic local hash-vector scoring.
- metadata and license filtering.
- graph expansion.
- reranking.
- context compression.

The output is a cited context pack for a coding agent.

The graph is used for high-signal relationships and expansion. It is not the only retrieval mechanism.

V1 vectors are normalized hashed bag-of-terms stored in SQLite. They are useful as a local ranking signal, but they are not semantic embeddings. Real embedding models should be added behind the same storage interface when retrieval quality work starts.
