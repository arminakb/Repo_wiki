from __future__ import annotations


class RepoWikiError(Exception):
    """Base exception for expected project errors."""


class RepositoryNotFound(RepoWikiError):
    """Raised when a repository path or record cannot be found."""


class UnsupportedSource(RepoWikiError):
    """Raised when ingestion source is unsupported."""


class LicensePolicyViolation(RepoWikiError):
    """Raised when content cannot be used under the requested license policy."""


class ExtractionFailed(RepoWikiError):
    """Raised when extraction cannot safely continue."""


class KnowledgeValidationFailed(RepoWikiError):
    """Raised when a knowledge object fails validation."""


class RetrievalFailed(RepoWikiError):
    """Raised when retrieval cannot produce a context pack."""


class StorageError(RepoWikiError):
    """Raised when SQLite storage cannot complete an operation."""


class MCPValidationError(RepoWikiError):
    """Raised when an MCP request is malformed."""
