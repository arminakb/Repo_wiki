from __future__ import annotations

from enum import StrEnum


class SourceType(StrEnum):
    GITHUB_REPO = "github_repo"
    LOCAL_REPO = "local_repo"


class KnowledgeType(StrEnum):
    PROJECT_PROFILE = "ProjectProfile"
    ARCHITECTURE_PATTERN = "ArchitecturePattern"
    IMPLEMENTATION_PATTERN = "ImplementationPattern"
    MODULE_PATTERN = "ModulePattern"
    TESTING_PATTERN = "TestingPattern"
    SECURITY_PATTERN = "SecurityPattern"
    ANTI_PATTERN = "AntiPattern"
    DECISION_RECORD = "DecisionRecord"
    CODE_EXAMPLE = "CodeExample"
    CONSTRAINT = "Constraint"
    TRADEOFF = "Tradeoff"


class GraphNodeType(StrEnum):
    REPOSITORY = "Repository"
    SNAPSHOT = "RepositorySnapshot"
    SOURCE_FILE = "SourceFile"
    SYMBOL = "Symbol"
    ROUTE = "Route"
    API_ENDPOINT = "APIEndpoint"
    DEPENDENCY = "Dependency"
    FRAMEWORK = "Framework"
    KNOWLEDGE_OBJECT = "KnowledgeObject"
    CONTEXT_PACK = "ContextPack"


class EdgeType(StrEnum):
    CONTAINS = "CONTAINS"
    IMPORTS = "IMPORTS"
    EXPORTS = "EXPORTS"
    CALLS = "CALLS"
    DEPENDS_ON = "DEPENDS_ON"
    TESTED_BY = "TESTED_BY"
    DEFINES_ROUTE = "DEFINES_ROUTE"
    HANDLES_ENDPOINT = "HANDLES_ENDPOINT"
    USES_FRAMEWORK = "USES_FRAMEWORK"
    DERIVED_FROM = "DERIVED_FROM"
    SIMILAR_TO = "SIMILAR_TO"
    CONFLICTS_WITH = "CONFLICTS_WITH"
    APPLIES_TO_LANGUAGE = "APPLIES_TO_LANGUAGE"
    APPLIES_TO_FRAMEWORK = "APPLIES_TO_FRAMEWORK"
    PRODUCED_CONTEXT = "PRODUCED_CONTEXT"
    PROMOTED_FROM = "PROMOTED_FROM"


class FeedbackStatus(StrEnum):
    PENDING = "pending"
    PROMOTED = "promoted"
    REJECTED = "rejected"
