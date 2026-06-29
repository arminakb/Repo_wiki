from __future__ import annotations

import json
import re
import sqlite3
import shutil
from contextlib import closing
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from repo_wiki.domain.errors import StorageError
from repo_wiki.domain.ids import stable_id
from repo_wiki.domain.models import (
    ContextPack,
    Dependency,
    FeedbackRecord,
    GraphEdge,
    GraphNode,
    KnowledgeObject,
    Repository,
    RepositorySnapshot,
    RetrievalTrace,
    SourceFile,
    SourceRef,
    StagedKnowledge,
    Symbol,
    now_utc,
)
from repo_wiki.storage.vector import (
    DIMENSION,
    MODEL_NAME,
    cosine_similarity,
    embed_text,
    text_for_knowledge_embedding,
    vector_content_hash,
    vector_from_uri,
    vector_to_uri,
)

RETRIEVAL_EDGE_TYPES = {
    "DERIVED_FROM",
    "TESTED_BY",
    "APPLIES_TO_FRAMEWORK",
    "USES_FRAMEWORK",
}


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> bool:
        result = super().__exit__(exc_type, exc_value, traceback)
        self.close()
        return bool(result)


def dumps(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def loads(value: str | None, fallback: Any) -> Any:
    if value is None or value == "":
        return fallback
    return json.loads(value)


class SQLiteStore:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        try:
            conn = sqlite3.connect(self.path, factory=ClosingConnection)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            return conn
        except sqlite3.Error as exc:
            raise StorageError(f"failed to open SQLite store: {self.path}") from exc

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            apply_migrations(conn)

    def schema_version(self) -> str | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT id FROM schema_migrations ORDER BY id DESC LIMIT 1"
            ).fetchone()
        return row["id"] if row is not None else None

    def integrity_check(self) -> str:
        with self.connect() as conn:
            return str(conn.execute("PRAGMA integrity_check").fetchone()[0])

    def backup_to(self, target: Path | str) -> Path:
        destination = Path(target)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as source:
            with closing(sqlite3.connect(destination)) as backup:
                source.backup(backup)
        return destination

    def restore_from(self, source: Path | str) -> None:
        backup = Path(source)
        if not backup.exists() or not backup.is_file():
            raise StorageError(f"backup does not exist: {backup}")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(backup, self.path)
        self.initialize()

    def save_extraction(self, result: Any) -> None:
        with self.connect() as conn:
            self.upsert_repository(conn, result.repository)
            self.upsert_snapshot(conn, result.snapshot)
            self.upsert_files(conn, result.files)
            self.upsert_symbols(conn, result.symbols)
            self.upsert_dependencies(conn, result.dependencies)
            self.upsert_source_refs(conn, result.source_refs)
            self.upsert_knowledge_objects(conn, result.knowledge_objects)
            self.upsert_graph_nodes(conn, result.graph_nodes)
            self.upsert_graph_edges(conn, result.graph_edges)

    def upsert_repository(self, conn: sqlite3.Connection, repo: Repository) -> None:
        conn.execute(
            """
            INSERT INTO repositories (
              id, source_type, owner, name, url, local_path, default_branch, visibility,
              license, primary_language, detected_languages_json, detected_frameworks_json,
              project_type, stars, quality_score, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              owner=excluded.owner,
              name=excluded.name,
              url=excluded.url,
              local_path=excluded.local_path,
              default_branch=excluded.default_branch,
              visibility=excluded.visibility,
              license=excluded.license,
              primary_language=excluded.primary_language,
              detected_languages_json=excluded.detected_languages_json,
              detected_frameworks_json=excluded.detected_frameworks_json,
              project_type=excluded.project_type,
              stars=excluded.stars,
              quality_score=excluded.quality_score,
              updated_at=excluded.updated_at
            """,
            (
                repo.id,
                repo.source_type,
                repo.owner,
                repo.name,
                repo.url,
                repo.local_path,
                repo.default_branch,
                repo.visibility,
                repo.license,
                repo.primary_language,
                dumps(repo.detected_languages),
                dumps(repo.detected_frameworks),
                repo.project_type,
                repo.stars,
                repo.quality_score,
                repo.created_at,
                repo.updated_at,
            ),
        )

    def upsert_snapshot(self, conn: sqlite3.Connection, snapshot: RepositorySnapshot) -> None:
        conn.execute(
            """
            INSERT INTO repository_snapshots (
              id, repo_id, commit_sha, branch, indexed_at, file_count, line_count,
              content_hash, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              file_count=excluded.file_count,
              line_count=excluded.line_count,
              content_hash=excluded.content_hash,
              status=excluded.status
            """,
            (
                snapshot.id,
                snapshot.repo_id,
                snapshot.commit_sha,
                snapshot.branch,
                snapshot.indexed_at,
                snapshot.file_count,
                snapshot.line_count,
                snapshot.content_hash,
                snapshot.status,
            ),
        )

    def upsert_files(self, conn: sqlite3.Connection, files: Iterable[SourceFile]) -> None:
        for file in files:
            conn.execute(
                """
                INSERT INTO source_files (
                  id, snapshot_id, path, language, mime_type, size_bytes, line_count, hash,
                  content, is_test, is_generated, is_dependency
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  path=excluded.path,
                  language=excluded.language,
                  mime_type=excluded.mime_type,
                  size_bytes=excluded.size_bytes,
                  line_count=excluded.line_count,
                  hash=excluded.hash,
                  content=excluded.content,
                  is_test=excluded.is_test,
                  is_generated=excluded.is_generated,
                  is_dependency=excluded.is_dependency
                """,
                (
                    file.id,
                    file.snapshot_id,
                    file.path,
                    file.language,
                    file.mime_type,
                    file.size_bytes,
                    file.line_count,
                    file.hash,
                    file.content,
                    int(file.is_test),
                    int(file.is_generated),
                    int(file.is_dependency),
                ),
            )
            if file.content:
                conn.execute("DELETE FROM file_fts WHERE file_id = ?", (file.id,))
                conn.execute(
                    """
                    INSERT INTO file_fts(file_id, path, content, language)
                    VALUES (?, ?, ?, ?)
                    """,
                    (file.id, file.path, file.content, file.language or ""),
                )

    def upsert_symbols(self, conn: sqlite3.Connection, symbols: Iterable[Symbol]) -> None:
        for sym in symbols:
            conn.execute(
                """
                INSERT INTO symbols (
                  id, file_id, snapshot_id, name, kind, qualified_name, start_line,
                  end_line, signature, docstring, visibility
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  name=excluded.name,
                  kind=excluded.kind,
                  qualified_name=excluded.qualified_name,
                  start_line=excluded.start_line,
                  end_line=excluded.end_line,
                  signature=excluded.signature,
                  docstring=excluded.docstring,
                  visibility=excluded.visibility
                """,
                (
                    sym.id,
                    sym.file_id,
                    sym.snapshot_id,
                    sym.name,
                    sym.kind,
                    sym.qualified_name,
                    sym.start_line,
                    sym.end_line,
                    sym.signature,
                    sym.docstring,
                    sym.visibility,
                ),
            )

    def upsert_dependencies(
        self, conn: sqlite3.Connection, dependencies: Iterable[Dependency]
    ) -> None:
        for dep in dependencies:
            conn.execute(
                """
                INSERT INTO dependencies (
                  id, snapshot_id, manager, name, version_spec, scope, manifest_path
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  version_spec=excluded.version_spec,
                  scope=excluded.scope,
                  manifest_path=excluded.manifest_path
                """,
                (
                    dep.id,
                    dep.snapshot_id,
                    dep.manager,
                    dep.name,
                    dep.version_spec,
                    dep.scope,
                    dep.manifest_path,
                ),
            )

    def upsert_source_refs(self, conn: sqlite3.Connection, refs: Iterable[SourceRef]) -> None:
        for ref in refs:
            conn.execute(
                """
                INSERT INTO source_refs (
                  id, repo_id, snapshot_id, file_id, path, start_line, end_line, license,
                  snippet_allowed
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  file_id=excluded.file_id,
                  path=excluded.path,
                  start_line=excluded.start_line,
                  end_line=excluded.end_line,
                  license=excluded.license,
                  snippet_allowed=excluded.snippet_allowed
                """,
                (
                    ref.id,
                    ref.repo_id,
                    ref.snapshot_id,
                    ref.file_id,
                    ref.path,
                    ref.start_line,
                    ref.end_line,
                    ref.license,
                    int(ref.snippet_allowed),
                ),
            )

    def upsert_knowledge_objects(
        self, conn: sqlite3.Connection, objects: Iterable[KnowledgeObject]
    ) -> None:
        for obj in objects:
            conn.execute(
                """
                INSERT INTO knowledge_objects (
                  id, type, title, summary, problem, solution, when_to_use_json,
                  when_not_to_use_json, language, frameworks_json, domain, project_type,
                  tags_json, quality_score, confidence, payload_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  title=excluded.title,
                  summary=excluded.summary,
                  problem=excluded.problem,
                  solution=excluded.solution,
                  when_to_use_json=excluded.when_to_use_json,
                  when_not_to_use_json=excluded.when_not_to_use_json,
                  language=excluded.language,
                  frameworks_json=excluded.frameworks_json,
                  domain=excluded.domain,
                  project_type=excluded.project_type,
                  tags_json=excluded.tags_json,
                  quality_score=excluded.quality_score,
                  confidence=excluded.confidence,
                  payload_json=excluded.payload_json,
                  updated_at=excluded.updated_at
                """,
                (
                    obj.id,
                    obj.type,
                    obj.title,
                    obj.summary,
                    obj.problem,
                    obj.solution,
                    dumps(obj.when_to_use),
                    dumps(obj.when_not_to_use),
                    obj.language,
                    dumps(obj.frameworks),
                    obj.domain,
                    obj.project_type,
                    dumps(obj.tags),
                    obj.quality_score,
                    obj.confidence,
                    dumps(obj.payload),
                    obj.created_at,
                    obj.updated_at,
                ),
            )
            conn.execute(
                "DELETE FROM knowledge_object_refs WHERE knowledge_object_id = ?", (obj.id,)
            )
            conn.execute("DELETE FROM knowledge_fts WHERE object_id = ?", (obj.id,))
            search_tags = " ".join(
                [
                    *obj.tags,
                    str(obj.payload.get("path", "")),
                    " ".join(
                        str(symbol.get("name", ""))
                        for symbol in obj.payload.get("symbols", [])
                        if isinstance(symbol, dict)
                    ),
                ]
            )
            conn.execute(
                """
                INSERT INTO knowledge_fts(object_id, title, summary, problem, solution, tags)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    obj.id,
                    obj.title,
                    obj.summary,
                    obj.problem or "",
                    obj.solution or "",
                    search_tags,
                ),
            )
            for ref_id in obj.source_refs:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO knowledge_object_refs
                    (knowledge_object_id, source_ref_id)
                    VALUES (?, ?)
                    """,
                    (obj.id, ref_id),
                )
            embedding_text = text_for_knowledge_embedding(
                title=obj.title,
                summary=obj.summary,
                problem=obj.problem,
                solution=obj.solution,
                tags=obj.tags,
                payload=obj.payload,
            )
            conn.execute(
                "DELETE FROM embeddings WHERE object_type = ? AND object_id = ?",
                ("KnowledgeObject", obj.id),
            )
            conn.execute(
                """
                INSERT INTO embeddings (
                  id, object_type, object_id, model, dimension, vector_uri,
                  content_hash, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    stable_embedding_id(obj.id, MODEL_NAME),
                    "KnowledgeObject",
                    obj.id,
                    MODEL_NAME,
                    DIMENSION,
                    vector_to_uri(embed_text(embedding_text)),
                    vector_content_hash(embedding_text),
                    now_utc(),
                ),
            )

    def upsert_graph_nodes(self, conn: sqlite3.Connection, nodes: Iterable[GraphNode]) -> None:
        for node in nodes:
            conn.execute(
                """
                INSERT INTO graph_nodes (id, node_type, object_id, label, metadata_json)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  node_type=excluded.node_type,
                  object_id=excluded.object_id,
                  label=excluded.label,
                  metadata_json=excluded.metadata_json
                """,
                (node.id, node.node_type, node.object_id, node.label, dumps(node.metadata)),
            )

    def upsert_graph_edges(self, conn: sqlite3.Connection, edges: Iterable[GraphEdge]) -> None:
        for edge in edges:
            conn.execute(
                """
                INSERT INTO graph_edges (
                  id, source_node_id, target_node_id, edge_type, weight, confidence,
                  source, metadata_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  weight=excluded.weight,
                  confidence=excluded.confidence,
                  metadata_json=excluded.metadata_json
                """,
                (
                    edge.id,
                    edge.source_node_id,
                    edge.target_node_id,
                    edge.edge_type,
                    edge.weight,
                    edge.confidence,
                    edge.source,
                    dumps(edge.metadata),
                    edge.created_at,
                ),
            )

    def save_knowledge_object(self, obj: KnowledgeObject) -> None:
        with self.connect() as conn:
            self.upsert_knowledge_objects(conn, [obj])

    def save_graph(self, nodes: Iterable[GraphNode], edges: Iterable[GraphEdge]) -> None:
        with self.connect() as conn:
            self.upsert_graph_nodes(conn, nodes)
            self.upsert_graph_edges(conn, edges)

    def list_knowledge(
        self,
        *,
        type: str | None = None,
        language: str | None = None,
        framework: str | None = None,
        limit: int = 20,
    ) -> list[KnowledgeObject]:
        clauses: list[str] = []
        params: list[Any] = []
        if type:
            clauses.append("type = ?")
            params.append(type)
        if language:
            clauses.append("language = ?")
            params.append(language)
        if framework:
            clauses.append("frameworks_json LIKE ?")
            params.append(f"%{framework}%")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM knowledge_objects
                {where}
                ORDER BY quality_score DESC, title ASC
                LIMIT ?
                """,
                (*params, limit),
            ).fetchall()
        refs_by_object = self.get_source_ref_ids_many(row["id"] for row in rows)
        return [row_to_knowledge_object(row, refs_by_object.get(row["id"], [])) for row in rows]

    def list_repositories(self, *, limit: int = 20) -> list[Repository]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM repositories
                ORDER BY updated_at DESC, name ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [row_to_repository(row) for row in rows]

    def get_repository(self, repo_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM repositories WHERE id = ?", (repo_id,)).fetchone()
            if row is None:
                return None
            snapshots = conn.execute(
                """
                SELECT * FROM repository_snapshots
                WHERE repo_id = ?
                ORDER BY indexed_at DESC
                """,
                (repo_id,),
            ).fetchall()
        return {
            "repository": row_to_repository(row).model_dump(),
            "snapshots": [dict(snapshot) for snapshot in snapshots],
        }

    def get_knowledge(self, object_id: str) -> KnowledgeObject | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM knowledge_objects WHERE id = ?", (object_id,)
            ).fetchone()
        if row is None:
            return None
        return row_to_knowledge_object(row, self.get_source_ref_ids(object_id))

    def get_source_ref_ids(self, object_id: str) -> list[str]:
        return self.get_source_ref_ids_many([object_id]).get(object_id, [])

    def get_source_ref_ids_many(self, object_ids: Iterable[str]) -> dict[str, list[str]]:
        ids = list(dict.fromkeys(object_ids))
        if not ids:
            return {}
        placeholders = ",".join("?" for _ in ids)
        refs_by_object = {object_id: [] for object_id in ids}
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT knowledge_object_id, source_ref_id FROM knowledge_object_refs
                WHERE knowledge_object_id IN ({placeholders})
                ORDER BY knowledge_object_id, source_ref_id
                """,
                ids,
            ).fetchall()
        for row in rows:
            refs_by_object[row["knowledge_object_id"]].append(row["source_ref_id"])
        return refs_by_object

    def get_source_refs(self, ref_ids: Iterable[str]) -> list[SourceRef]:
        ids = list(ref_ids)
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        with self.connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM source_refs WHERE id IN ({placeholders})", ids
            ).fetchall()
        return [row_to_source_ref(row) for row in rows]

    def get_source_ref_contents(self, ref_ids: Iterable[str]) -> dict[str, str]:
        ids = list(dict.fromkeys(ref_ids))
        if not ids:
            return {}
        placeholders = ",".join("?" for _ in ids)
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT sr.id, sf.content
                FROM source_refs sr
                JOIN source_files sf ON sf.id = sr.file_id
                WHERE sr.id IN ({placeholders}) AND sf.content IS NOT NULL
                """,
                ids,
            ).fetchall()
        return {row["id"]: row["content"] for row in rows}

    def search_knowledge(
        self,
        query: str,
        *,
        language: str | None = None,
        framework: str | None = None,
        project_type: str | None = None,
        repo_id: str | None = None,
        limit: int = 20,
    ) -> list[tuple[KnowledgeObject, float]]:
        safe_query = make_fts_query(query)
        if not safe_query:
            return []
        clauses = ["knowledge_fts MATCH ?"]
        params: list[Any] = [safe_query]
        if language:
            clauses.append("ko.language = ?")
            params.append(language)
        if framework:
            clauses.append("ko.frameworks_json LIKE ?")
            params.append(f"%{framework}%")
        if project_type:
            clauses.append("ko.project_type = ?")
            params.append(project_type)
        if repo_id:
            clauses.append(
                """
                EXISTS (
                  SELECT 1 FROM knowledge_object_refs kor
                  JOIN source_refs sr ON sr.id = kor.source_ref_id
                  WHERE kor.knowledge_object_id = ko.id AND sr.repo_id = ?
                )
                """
            )
            params.append(repo_id)
        where = " AND ".join(clauses)
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT ko.*, bm25(knowledge_fts) AS rank
                FROM knowledge_fts
                JOIN knowledge_objects ko ON ko.id = knowledge_fts.object_id
                WHERE {where}
                ORDER BY rank ASC, ko.quality_score DESC
                LIMIT ?
                """,
                (*params, limit),
            ).fetchall()
        results: list[tuple[KnowledgeObject, float]] = []
        refs_by_object = self.get_source_ref_ids_many(row["id"] for row in rows)
        for row in rows:
            obj = row_to_knowledge_object(row, refs_by_object.get(row["id"], []))
            lexical_score = bm25_score(float(row["rank"] or 0.0))
            results.append((obj, lexical_score))
        return results

    def vector_search_knowledge(
        self,
        query: str,
        *,
        language: str | None = None,
        framework: str | None = None,
        project_type: str | None = None,
        repo_id: str | None = None,
        limit: int = 20,
    ) -> list[tuple[KnowledgeObject, float]]:
        query_vector = embed_text(query)
        if not any(query_vector):
            return []
        clauses = ["e.object_type = 'KnowledgeObject'", "e.model = ?"]
        params: list[Any] = [MODEL_NAME]
        if language:
            clauses.append("ko.language = ?")
            params.append(language)
        if framework:
            clauses.append("ko.frameworks_json LIKE ?")
            params.append(f"%{framework}%")
        if project_type:
            clauses.append("ko.project_type = ?")
            params.append(project_type)
        if repo_id:
            clauses.append(
                """
                EXISTS (
                  SELECT 1 FROM knowledge_object_refs kor
                  JOIN source_refs sr ON sr.id = kor.source_ref_id
                  WHERE kor.knowledge_object_id = ko.id AND sr.repo_id = ?
                )
                """
            )
            params.append(repo_id)
        where = " AND ".join(clauses)
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT ko.*, e.vector_uri
                FROM embeddings e
                JOIN knowledge_objects ko ON ko.id = e.object_id
                WHERE {where}
                """,
                params,
            ).fetchall()
        scored: list[tuple[KnowledgeObject, float]] = []
        refs_by_object = self.get_source_ref_ids_many(row["id"] for row in rows)
        for row in rows:
            vector = vector_from_uri(row["vector_uri"])
            if vector is None:
                continue
            score = cosine_similarity(query_vector, vector)
            if score <= 0:
                continue
            scored.append(
                (
                    row_to_knowledge_object(row, refs_by_object.get(row["id"], [])),
                    score,
                )
            )
        scored.sort(key=lambda item: (item[1], item[0].quality_score), reverse=True)
        return scored[:limit]

    def search_source_files(
        self,
        query: str,
        *,
        language: str | None = None,
        repo_id: str | None = None,
        limit: int = 20,
    ) -> list[tuple[SourceFile, SourceRef | None, float]]:
        safe_query = make_fts_query(query)
        if not safe_query:
            return []
        clauses = ["file_fts MATCH ?"]
        params: list[Any] = [safe_query]
        if language:
            clauses.append("sf.language = ?")
            params.append(language)
        if repo_id:
            clauses.append(
                """
                EXISTS (
                  SELECT 1 FROM repository_snapshots snap
                  WHERE snap.id = sf.snapshot_id AND snap.repo_id = ?
                )
                """
            )
            params.append(repo_id)
        where = " AND ".join(clauses)
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT sf.*, sr.id AS ref_id, sr.repo_id, sr.start_line, sr.end_line,
                       sr.license, sr.snippet_allowed, bm25(file_fts) AS rank
                FROM file_fts
                JOIN source_files sf ON sf.id = file_fts.file_id
                LEFT JOIN source_refs sr
                  ON sr.file_id = sf.id
                 AND sr.path = sf.path
                 AND sr.start_line = 1
                 AND sr.end_line = sf.line_count
                WHERE {where}
                ORDER BY rank ASC, sf.is_test DESC, sf.path ASC
                LIMIT ?
                """,
                (*params, limit),
            ).fetchall()
        results: list[tuple[SourceFile, SourceRef | None, float]] = []
        for row in rows:
            source_file = row_to_source_file(row)
            source_ref = None
            if row["ref_id"]:
                source_ref = SourceRef(
                    id=row["ref_id"],
                    repo_id=row["repo_id"],
                    snapshot_id=source_file.snapshot_id,
                    file_id=source_file.id,
                    path=source_file.path,
                    start_line=row["start_line"],
                    end_line=row["end_line"],
                    license=row["license"],
                    snippet_allowed=bool(row["snippet_allowed"]),
                )
            results.append((source_file, source_ref, bm25_score(float(row["rank"] or 0.0))))
        return results

    def graph_neighbors(
        self, object_id: str, *, edge_type: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        params: list[Any] = [object_id]
        type_clause = ""
        if edge_type:
            type_clause = "AND e.edge_type = ?"
            params.append(edge_type)
        params.append(limit)
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT e.edge_type, e.weight, e.confidence, n2.*
                FROM graph_nodes n1
                JOIN graph_edges e ON e.source_node_id = n1.id
                JOIN graph_nodes n2 ON n2.id = e.target_node_id
                WHERE n1.object_id = ? {type_clause}
                ORDER BY e.weight DESC, e.confidence DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [
            {
                "edge_type": row["edge_type"],
                "weight": row["weight"],
                "confidence": row["confidence"],
                "node_id": row["id"],
                "node_type": row["node_type"],
                "object_id": row["object_id"],
                "label": row["label"],
                "metadata": loads(row["metadata_json"], {}),
            }
            for row in rows
        ]

    def export_graph_mermaid(self, *, limit: int = 200) -> str:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT
                  source.object_id AS source_object_id,
                  source.label AS source_label,
                  target.object_id AS target_object_id,
                  target.label AS target_label,
                  e.edge_type
                FROM graph_edges e
                JOIN graph_nodes source ON source.id = e.source_node_id
                JOIN graph_nodes target ON target.id = e.target_node_id
                ORDER BY e.created_at DESC, e.edge_type ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        lines = ["flowchart TD"]
        for row in rows:
            source_id = mermaid_id(row["source_object_id"])
            target_id = mermaid_id(row["target_object_id"])
            source_label = mermaid_label(row["source_label"])
            target_label = mermaid_label(row["target_label"])
            edge_type = mermaid_label(row["edge_type"])
            lines.append(
                f"    {source_id}[{source_label}] -->|{edge_type}| "
                f"{target_id}[{target_label}]"
            )
        return "\n".join(lines).strip() + "\n"

    def graph_expand_knowledge(
        self,
        object_ids: Iterable[str],
        *,
        max_depth: int = 2,
        max_neighbors_per_node: int = 12,
        min_confidence: float = 0.5,
        repo_id: str | None = None,
    ) -> list[tuple[KnowledgeObject, float, dict[str, Any]]]:
        seeds = list(dict.fromkeys(object_ids))
        if not seeds or max_depth < 1:
            return []

        expanded: dict[str, tuple[float, dict[str, Any]]] = {}

        with self.connect() as conn:
            seed_placeholders = ",".join("?" for _ in seeds)
            seed_rows = conn.execute(
                f"""
                SELECT id, object_id FROM graph_nodes
                WHERE object_id IN ({seed_placeholders})
                """,
                seeds,
            ).fetchall()
            frontier = [row["id"] for row in seed_rows]
            visited_nodes = set(frontier)
            seed_node_ids = set(frontier)

            for depth in range(1, max_depth + 1):
                if not frontier:
                    break
                placeholders = ",".join("?" for _ in frontier)
                rows = conn.execute(
                    f"""
                    SELECT
                      e.source_node_id AS frontier_node_id,
                      'outgoing' AS direction,
                      e.edge_type,
                      e.weight,
                      e.confidence,
                      e.metadata_json,
                      target.id AS neighbor_node_id,
                      target.node_type AS neighbor_node_type,
                      target.object_id AS neighbor_object_id
                    FROM graph_edges e
                    JOIN graph_nodes target ON target.id = e.target_node_id
                    WHERE e.source_node_id IN ({placeholders})
                      AND e.confidence >= ?
                      AND e.edge_type IN ({",".join("?" for _ in RETRIEVAL_EDGE_TYPES)})
                    UNION ALL
                    SELECT
                      e.target_node_id AS frontier_node_id,
                      'incoming' AS direction,
                      e.edge_type,
                      e.weight,
                      e.confidence,
                      e.metadata_json,
                      source.id AS neighbor_node_id,
                      source.node_type AS neighbor_node_type,
                      source.object_id AS neighbor_object_id
                    FROM graph_edges e
                    JOIN graph_nodes source ON source.id = e.source_node_id
                    WHERE e.target_node_id IN ({placeholders})
                      AND e.confidence >= ?
                      AND e.edge_type IN ({",".join("?" for _ in RETRIEVAL_EDGE_TYPES)})
                    ORDER BY weight DESC, confidence DESC
                    """,
                    (
                        *frontier,
                        min_confidence,
                        *RETRIEVAL_EDGE_TYPES,
                        *frontier,
                        min_confidence,
                        *RETRIEVAL_EDGE_TYPES,
                    ),
                ).fetchall()

                next_frontier: list[str] = []
                neighbor_counts: dict[str, int] = {}
                for row in rows:
                    frontier_node_id = row["frontier_node_id"]
                    if neighbor_counts.get(frontier_node_id, 0) >= max_neighbors_per_node:
                        continue
                    neighbor_node_id = row["neighbor_node_id"]
                    if neighbor_node_id in visited_nodes:
                        continue
                    neighbor_counts[frontier_node_id] = neighbor_counts.get(frontier_node_id, 0) + 1
                    visited_nodes.add(neighbor_node_id)
                    next_frontier.append(neighbor_node_id)
                    graph_score = round(
                        (float(row["weight"] or 0.0) * float(row["confidence"] or 0.0)) / depth,
                        4,
                    )
                    if (
                        row["neighbor_node_type"] == "KnowledgeObject"
                        and row["neighbor_object_id"] not in seeds
                        and neighbor_node_id not in seed_node_ids
                    ):
                        target_id = row["neighbor_object_id"]
                        existing = expanded.get(target_id)
                        if existing is None or graph_score > existing[0]:
                            expanded[target_id] = (
                                graph_score,
                                {
                                    "edge_type": row["edge_type"],
                                    "direction": row["direction"],
                                    "depth": depth,
                                    "weight": float(row["weight"] or 0.0),
                                    "confidence": float(row["confidence"] or 0.0),
                                    "metadata": loads(row["metadata_json"], {}),
                                },
                            )
                frontier = next_frontier

        objects = self.get_knowledge_many(expanded.keys(), repo_id=repo_id)
        return [(obj, *expanded[obj.id]) for obj in objects if obj.id in expanded]

    def get_knowledge_many(
        self,
        object_ids: Iterable[str],
        *,
        repo_id: str | None = None,
    ) -> list[KnowledgeObject]:
        ids = list(dict.fromkeys(object_ids))
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        params: list[Any] = ids.copy()
        repo_clause = ""
        if repo_id:
            repo_clause = """
              AND EXISTS (
                SELECT 1 FROM knowledge_object_refs kor
                JOIN source_refs sr ON sr.id = kor.source_ref_id
                WHERE kor.knowledge_object_id = knowledge_objects.id AND sr.repo_id = ?
              )
            """
            params.append(repo_id)
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM knowledge_objects
                WHERE id IN ({placeholders})
                {repo_clause}
                """,
                params,
            ).fetchall()
        refs_by_object = self.get_source_ref_ids_many(row["id"] for row in rows)
        by_id = {
            row["id"]: row_to_knowledge_object(row, refs_by_object.get(row["id"], []))
            for row in rows
        }
        return [by_id[item] for item in ids if item in by_id]

    def save_retrieval_trace(self, trace: RetrievalTrace) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO retrieval_traces (
                  id, task, created_at, retrievers_used_json, candidate_count,
                  reranked_count, returned_count, latency_ms, filters_json, payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    trace.id,
                    trace.task,
                    trace.created_at,
                    dumps(trace.retrievers_used),
                    trace.candidate_count,
                    trace.reranked_count,
                    trace.returned_count,
                    trace.latency_ms,
                    dumps(trace.filters),
                    dumps(trace.payload),
                ),
            )

    def get_retrieval_trace(self, trace_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM retrieval_traces WHERE id = ?",
                (trace_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "task": row["task"],
            "created_at": row["created_at"],
            "retrievers_used": loads(row["retrievers_used_json"], []),
            "candidate_count": row["candidate_count"],
            "reranked_count": row["reranked_count"],
            "returned_count": row["returned_count"],
            "latency_ms": row["latency_ms"],
            "filters": loads(row["filters_json"], {}),
            "payload": loads(row["payload_json"], {}),
        }

    def save_context_pack(self, pack: ContextPack) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO context_packs (
                  id, retrieval_trace_id, task, task_type, constraints_json,
                  json_payload, markdown_payload, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pack.id,
                    pack.retrieval_trace_id,
                    pack.task,
                    pack.task_type,
                    dumps(pack.constraints),
                    pack.model_dump_json(),
                    pack.markdown,
                    pack.created_at,
                ),
            )

    def get_context_pack(self, context_pack_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM context_packs WHERE id = ?", (context_pack_id,)
            ).fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "retrieval_trace_id": row["retrieval_trace_id"],
            "task": row["task"],
            "task_type": row["task_type"],
            "constraints": loads(row["constraints_json"], {}),
            "context_pack": loads(row["json_payload"], {}),
            "markdown": row["markdown_payload"],
            "created_at": row["created_at"],
        }

    def save_feedback(self, feedback: FeedbackRecord) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO feedback_records (
                  id, context_pack_id, task_id, user_rating, accepted, tests_passed,
                  lint_passed, build_passed, merged, reviewer_approved, rollback,
                  incident, notes, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feedback.id,
                    feedback.context_pack_id,
                    feedback.task_id,
                    feedback.user_rating,
                    none_bool(feedback.accepted),
                    none_bool(feedback.tests_passed),
                    none_bool(feedback.lint_passed),
                    none_bool(feedback.build_passed),
                    none_bool(feedback.merged),
                    none_bool(feedback.reviewer_approved),
                    none_bool(feedback.rollback),
                    none_bool(feedback.incident),
                    feedback.notes,
                    feedback.created_at,
                ),
            )

    def save_staged_knowledge(self, staged: StagedKnowledge) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO staged_knowledge (
                  id, source_feedback_id, candidate_type, payload_json, score, dedupe_key,
                  status, promotion_reason, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    staged.id,
                    staged.source_feedback_id,
                    staged.candidate_type,
                    dumps(staged.payload),
                    staged.score,
                    staged.dedupe_key,
                    staged.status,
                    staged.promotion_reason,
                    staged.created_at,
                    staged.updated_at,
                ),
            )

    def list_feedback(self, status: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as conn:
            if status:
                rows = conn.execute(
                    """
                    SELECT sk.*, fr.notes FROM staged_knowledge sk
                    LEFT JOIN feedback_records fr ON fr.id = sk.source_feedback_id
                    WHERE sk.status = ?
                    ORDER BY sk.created_at DESC
                    LIMIT ?
                    """,
                    (status, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT sk.*, fr.notes FROM staged_knowledge sk
                    LEFT JOIN feedback_records fr ON fr.id = sk.source_feedback_id
                    ORDER BY sk.created_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        return [dict(row) for row in rows]

    def update_staged_knowledge_status(
        self,
        stage_id: str,
        *,
        status: str,
        promotion_reason: str | None = None,
        promoted_object_id: str | None = None,
    ) -> dict[str, Any] | None:
        updated_at = now_utc()
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM staged_knowledge WHERE id = ?",
                (stage_id,),
            ).fetchone()
            if row is None:
                return None
            conn.execute(
                """
                UPDATE staged_knowledge
                SET status = ?,
                    promotion_reason = ?,
                    promoted_object_id = COALESCE(?, promoted_object_id),
                    updated_at = ?
                WHERE id = ?
                """,
                (status, promotion_reason, promoted_object_id, updated_at, stage_id),
            )
            updated = conn.execute(
                "SELECT * FROM staged_knowledge WHERE id = ?", (stage_id,)
            ).fetchone()
        return dict(updated) if updated is not None else None

    def get_staged_knowledge(self, stage_id: str) -> dict[str, Any] | None:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT * FROM staged_knowledge WHERE id = ?",
                (stage_id,),
            ).fetchone()
        if row is None:
            return None
        data = dict(row)
        data["payload"] = loads(data.pop("payload_json"), {})
        return data

    def metrics(self) -> dict[str, Any]:
        with self.connect() as conn:
            counts = {
                "indexed_repositories": count(conn, "repositories"),
                "repository_snapshots": count(conn, "repository_snapshots"),
                "indexed_files": count(conn, "source_files"),
                "extracted_symbols": count(conn, "symbols"),
                "dependencies": count(conn, "dependencies"),
                "knowledge_objects": count(conn, "knowledge_objects"),
                "graph_nodes": count(conn, "graph_nodes"),
                "graph_edges": count(conn, "graph_edges"),
                "context_packs": count(conn, "context_packs"),
                "feedback_records": count(conn, "feedback_records"),
                "staged_knowledge": count(conn, "staged_knowledge"),
                "schema_migrations": count(conn, "schema_migrations"),
            }
            langs = conn.execute(
                """
                SELECT primary_language FROM repositories
                WHERE primary_language IS NOT NULL
                GROUP BY primary_language
                ORDER BY primary_language
                """
            ).fetchall()
        counts["supported_languages"] = [row["primary_language"] for row in langs]
        counts["supported_interfaces"] = ["CLI", "HTTP API", "MCP"]
        return counts


def none_bool(value: bool | None) -> int | None:
    if value is None:
        return None
    return int(value)


def count(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def stable_embedding_id(object_id: str, model: str) -> str:
    return stable_id("emb", object_id, model)


def ensure_column(
    conn: sqlite3.Connection, table: str, column: str, definition: str
) -> None:
    columns = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def apply_migrations(conn: sqlite3.Connection) -> None:
    migrations = (
        ("0001_initial_schema", lambda: None),
        (
            "0002_feedback_objective_signals",
            lambda: (
                ensure_column(conn, "feedback_records", "reviewer_approved", "INTEGER"),
                ensure_column(conn, "feedback_records", "incident", "INTEGER"),
            ),
        ),
        (
            "0003_promoted_knowledge_link",
            lambda: ensure_column(conn, "staged_knowledge", "promoted_object_id", "TEXT"),
        ),
    )
    for migration_id, migration in migrations:
        applied = conn.execute(
            "SELECT 1 FROM schema_migrations WHERE id = ?",
            (migration_id,),
        ).fetchone()
        if applied:
            continue
        migration()
        conn.execute(
            "INSERT INTO schema_migrations (id, applied_at) VALUES (?, ?)",
            (migration_id, now_utc()),
        )


def row_to_repository(row: sqlite3.Row) -> Repository:
    return Repository(
        id=row["id"],
        source_type=row["source_type"],
        owner=row["owner"],
        name=row["name"],
        url=row["url"],
        local_path=row["local_path"],
        default_branch=row["default_branch"],
        visibility=row["visibility"],
        license=row["license"],
        primary_language=row["primary_language"],
        detected_languages=loads(row["detected_languages_json"], {}),
        detected_frameworks=loads(row["detected_frameworks_json"], []),
        project_type=row["project_type"],
        stars=row["stars"],
        quality_score=float(row["quality_score"] or 0.0),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def row_to_knowledge_object(row: sqlite3.Row, source_refs: list[str]) -> KnowledgeObject:
    return KnowledgeObject(
        id=row["id"],
        type=row["type"],
        title=row["title"],
        summary=row["summary"],
        problem=row["problem"],
        solution=row["solution"],
        when_to_use=loads(row["when_to_use_json"], []),
        when_not_to_use=loads(row["when_not_to_use_json"], []),
        language=row["language"],
        frameworks=loads(row["frameworks_json"], []),
        domain=row["domain"],
        project_type=row["project_type"],
        tags=loads(row["tags_json"], []),
        quality_score=float(row["quality_score"] or 0.0),
        confidence=float(row["confidence"] or 0.0),
        source_refs=source_refs,
        payload=loads(row["payload_json"], {}),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def row_to_source_file(row: sqlite3.Row) -> SourceFile:
    return SourceFile(
        id=row["id"],
        snapshot_id=row["snapshot_id"],
        path=row["path"],
        language=row["language"],
        mime_type=row["mime_type"],
        size_bytes=row["size_bytes"],
        line_count=row["line_count"],
        hash=row["hash"],
        content=row["content"],
        is_test=bool(row["is_test"]),
        is_generated=bool(row["is_generated"]),
        is_dependency=bool(row["is_dependency"]),
    )


def row_to_source_ref(row: sqlite3.Row) -> SourceRef:
    return SourceRef(
        id=row["id"],
        repo_id=row["repo_id"],
        snapshot_id=row["snapshot_id"],
        file_id=row["file_id"],
        path=row["path"],
        start_line=row["start_line"],
        end_line=row["end_line"],
        license=row["license"],
        snippet_allowed=bool(row["snippet_allowed"]),
    )


def make_fts_query(query: str) -> str:
    stopwords = {
        "a",
        "an",
        "and",
        "for",
        "in",
        "of",
        "the",
        "to",
        "with",
        "add",
        "implement",
        "create",
        "build",
        "system",
    }
    terms = []
    for term in re.findall(r"[A-Za-z0-9_]+", query.lower()):
        if len(term) < 2 or term in stopwords:
            continue
        terms.append(term)
    unique_terms = list(dict.fromkeys(terms))[:12]
    return " OR ".join(f'"{term}"' for term in unique_terms)


def bm25_score(rank: float) -> float:
    score = abs(rank)
    return round(score / (1.0 + score), 6)


def mermaid_id(value: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if not clean or clean[0].isdigit():
        clean = "n_" + clean
    return clean[:80]


def mermaid_label(value: str) -> str:
    return value.replace("[", "(").replace("]", ")").replace("|", "/").replace("\n", " ")[:80]


SCHEMA = """
CREATE TABLE IF NOT EXISTS repositories (
  id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,
  owner TEXT,
  name TEXT NOT NULL,
  url TEXT,
  local_path TEXT,
  default_branch TEXT,
  visibility TEXT NOT NULL,
  license TEXT,
  primary_language TEXT,
  detected_languages_json TEXT NOT NULL DEFAULT '{}',
  detected_frameworks_json TEXT NOT NULL DEFAULT '[]',
  project_type TEXT,
  stars INTEGER,
  quality_score REAL NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS repository_snapshots (
  id TEXT PRIMARY KEY,
  repo_id TEXT NOT NULL REFERENCES repositories(id),
  commit_sha TEXT,
  branch TEXT,
  indexed_at TEXT NOT NULL,
  file_count INTEGER NOT NULL DEFAULT 0,
  line_count INTEGER NOT NULL DEFAULT 0,
  content_hash TEXT,
  status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_files (
  id TEXT PRIMARY KEY,
  snapshot_id TEXT NOT NULL REFERENCES repository_snapshots(id),
  path TEXT NOT NULL,
  language TEXT,
  mime_type TEXT,
  size_bytes INTEGER NOT NULL,
  line_count INTEGER NOT NULL,
  hash TEXT NOT NULL,
  content TEXT,
  is_test INTEGER NOT NULL DEFAULT 0,
  is_generated INTEGER NOT NULL DEFAULT 0,
  is_dependency INTEGER NOT NULL DEFAULT 0,
  UNIQUE(snapshot_id, path)
);

CREATE TABLE IF NOT EXISTS symbols (
  id TEXT PRIMARY KEY,
  file_id TEXT NOT NULL REFERENCES source_files(id),
  snapshot_id TEXT NOT NULL REFERENCES repository_snapshots(id),
  name TEXT NOT NULL,
  kind TEXT NOT NULL,
  qualified_name TEXT NOT NULL,
  start_line INTEGER,
  end_line INTEGER,
  signature TEXT,
  docstring TEXT,
  visibility TEXT
);

CREATE TABLE IF NOT EXISTS dependencies (
  id TEXT PRIMARY KEY,
  snapshot_id TEXT NOT NULL REFERENCES repository_snapshots(id),
  manager TEXT NOT NULL,
  name TEXT NOT NULL,
  version_spec TEXT,
  scope TEXT,
  manifest_path TEXT
);

CREATE TABLE IF NOT EXISTS source_refs (
  id TEXT PRIMARY KEY,
  repo_id TEXT NOT NULL REFERENCES repositories(id),
  snapshot_id TEXT NOT NULL REFERENCES repository_snapshots(id),
  file_id TEXT REFERENCES source_files(id),
  path TEXT NOT NULL,
  start_line INTEGER,
  end_line INTEGER,
  license TEXT,
  snippet_allowed INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS knowledge_objects (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  problem TEXT,
  solution TEXT,
  when_to_use_json TEXT NOT NULL DEFAULT '[]',
  when_not_to_use_json TEXT NOT NULL DEFAULT '[]',
  language TEXT,
  frameworks_json TEXT NOT NULL DEFAULT '[]',
  domain TEXT,
  project_type TEXT,
  tags_json TEXT NOT NULL DEFAULT '[]',
  quality_score REAL NOT NULL DEFAULT 0,
  confidence REAL NOT NULL DEFAULT 0,
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS knowledge_object_refs (
  knowledge_object_id TEXT NOT NULL REFERENCES knowledge_objects(id),
  source_ref_id TEXT NOT NULL REFERENCES source_refs(id),
  PRIMARY KEY (knowledge_object_id, source_ref_id)
);

CREATE TABLE IF NOT EXISTS graph_nodes (
  id TEXT PRIMARY KEY,
  node_type TEXT NOT NULL,
  object_id TEXT NOT NULL,
  label TEXT NOT NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS graph_edges (
  id TEXT PRIMARY KEY,
  source_node_id TEXT NOT NULL REFERENCES graph_nodes(id),
  target_node_id TEXT NOT NULL REFERENCES graph_nodes(id),
  edge_type TEXT NOT NULL,
  weight REAL NOT NULL DEFAULT 1.0,
  confidence REAL NOT NULL DEFAULT 1.0,
  source TEXT NOT NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS embeddings (
  id TEXT PRIMARY KEY,
  object_type TEXT NOT NULL,
  object_id TEXT NOT NULL,
  model TEXT NOT NULL,
  dimension INTEGER NOT NULL,
  vector_uri TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS retrieval_traces (
  id TEXT PRIMARY KEY,
  task TEXT NOT NULL,
  created_at TEXT NOT NULL,
  retrievers_used_json TEXT NOT NULL DEFAULT '[]',
  candidate_count INTEGER NOT NULL,
  reranked_count INTEGER NOT NULL,
  returned_count INTEGER NOT NULL,
  latency_ms INTEGER NOT NULL,
  filters_json TEXT NOT NULL DEFAULT '{}',
  payload_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS context_packs (
  id TEXT PRIMARY KEY,
  retrieval_trace_id TEXT REFERENCES retrieval_traces(id),
  task TEXT NOT NULL,
  task_type TEXT,
  constraints_json TEXT NOT NULL DEFAULT '{}',
  json_payload TEXT NOT NULL,
  markdown_payload TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS feedback_records (
  id TEXT PRIMARY KEY,
  context_pack_id TEXT REFERENCES context_packs(id),
  task_id TEXT,
  user_rating INTEGER,
  accepted INTEGER,
  tests_passed INTEGER,
  lint_passed INTEGER,
  build_passed INTEGER,
  merged INTEGER,
  reviewer_approved INTEGER,
  rollback INTEGER,
  incident INTEGER,
  notes TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS staged_knowledge (
  id TEXT PRIMARY KEY,
  source_feedback_id TEXT REFERENCES feedback_records(id),
  candidate_type TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  score REAL NOT NULL DEFAULT 0,
  dedupe_key TEXT,
  status TEXT NOT NULL,
  promotion_reason TEXT,
  promoted_object_id TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schema_migrations (
  id TEXT PRIMARY KEY,
  applied_at TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
  object_id UNINDEXED,
  title,
  summary,
  problem,
  solution,
  tags
);

CREATE VIRTUAL TABLE IF NOT EXISTS file_fts USING fts5(
  file_id UNINDEXED,
  path,
  content,
  language
);

CREATE INDEX IF NOT EXISTS idx_knowledge_type ON knowledge_objects(type);
CREATE INDEX IF NOT EXISTS idx_knowledge_language ON knowledge_objects(language);
CREATE INDEX IF NOT EXISTS idx_source_files_snapshot ON source_files(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_symbols_snapshot ON symbols(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_graph_nodes_object ON graph_nodes(object_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_source ON graph_edges(source_node_id);
CREATE INDEX IF NOT EXISTS idx_graph_edges_type ON graph_edges(edge_type);
"""
