from __future__ import annotations

from repo_wiki.domain.enums import EdgeType, GraphNodeType
from repo_wiki.domain.ids import stable_id
from repo_wiki.domain.models import (
    Dependency,
    GraphEdge,
    GraphNode,
    KnowledgeObject,
    Repository,
    RepositorySnapshot,
    SourceFile,
    Symbol,
)


class GraphBuilder:
    def build(
        self,
        repo: Repository,
        snapshot: RepositorySnapshot,
        files: list[SourceFile],
        symbols: list[Symbol],
        dependencies: list[Dependency],
        knowledge_objects: list[KnowledgeObject],
        imports_by_file: dict[str, list[str]] | None = None,
        calls_by_file: dict[str, list[dict]] | None = None,
        routes_by_file: dict[str, list[dict]] | None = None,
    ) -> tuple[list[GraphNode], list[GraphEdge]]:
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        repo_node = node(
            GraphNodeType.REPOSITORY,
            repo.id,
            repo.name,
            {"project_type": repo.project_type},
        )
        snapshot_node = node(
            GraphNodeType.SNAPSHOT,
            snapshot.id,
            snapshot.id,
            {"commit": snapshot.commit_sha},
        )
        nodes.extend([repo_node, snapshot_node])
        edges.append(edge(repo_node, snapshot_node, EdgeType.CONTAINS, "deterministic_parser"))

        for file in files:
            file_node = node(
                GraphNodeType.SOURCE_FILE,
                file.id,
                file.path,
                {"language": file.language, "is_test": file.is_test},
            )
            nodes.append(file_node)
            edges.append(edge(snapshot_node, file_node, EdgeType.CONTAINS, "deterministic_parser"))

        file_node_ids = {
            file.id: stable_id("node", GraphNodeType.SOURCE_FILE, file.id)
            for file in files
        }
        for sym in symbols:
            sym_node = node(GraphNodeType.SYMBOL, sym.id, sym.qualified_name, {"kind": sym.kind})
            nodes.append(sym_node)
            if sym.file_id in file_node_ids:
                edges.append(
                    GraphEdge(
                        id=stable_id(
                            "edge",
                            file_node_ids[sym.file_id],
                            sym_node.id,
                            EdgeType.CONTAINS,
                        ),
                        source_node_id=file_node_ids[sym.file_id],
                        target_node_id=sym_node.id,
                        edge_type=EdgeType.CONTAINS,
                        source="deterministic_parser",
                    )
                )

        for dep in dependencies:
            dep_node = node(GraphNodeType.DEPENDENCY, dep.id, dep.name, {"manager": dep.manager})
            nodes.append(dep_node)
            edges.append(edge(snapshot_node, dep_node, EdgeType.DEPENDS_ON, "manifest_parser"))

        dependency_node_by_name = {
            dep.name.lower(): stable_id("node", GraphNodeType.DEPENDENCY, dep.id)
            for dep in dependencies
        }
        file_node_ids = {
            file.id: stable_id("node", GraphNodeType.SOURCE_FILE, file.id)
            for file in files
        }
        for file_id, imports in (imports_by_file or {}).items():
            source_node_id = file_node_ids.get(file_id)
            if not source_node_id:
                continue
            for import_name in imports:
                dep_node_id = dependency_node_by_name.get(import_name.lower())
                if not dep_node_id:
                    continue
                edges.append(
                    GraphEdge(
                        id=stable_id("edge", source_node_id, dep_node_id, EdgeType.IMPORTS),
                        source_node_id=source_node_id,
                        target_node_id=dep_node_id,
                        edge_type=EdgeType.IMPORTS,
                        source="deterministic_parser",
                        metadata={"import": import_name},
                    )
                )

        file_node_ids = {
            file.id: stable_id("node", GraphNodeType.SOURCE_FILE, file.id)
            for file in files
        }
        symbol_node_by_name = {
            (sym.file_id, sym.name): stable_id("node", GraphNodeType.SYMBOL, sym.id)
            for sym in symbols
        }
        for file_id, calls in (calls_by_file or {}).items():
            for call in calls:
                caller_node_id = symbol_node_by_name.get((file_id, call.get("caller")))
                callee_node_id = symbol_node_by_name.get((file_id, call.get("callee")))
                if not caller_node_id or not callee_node_id or caller_node_id == callee_node_id:
                    continue
                edges.append(
                    GraphEdge(
                        id=stable_id(
                            "edge",
                            caller_node_id,
                            callee_node_id,
                            EdgeType.CALLS,
                            call.get("line"),
                        ),
                        source_node_id=caller_node_id,
                        target_node_id=callee_node_id,
                        edge_type=EdgeType.CALLS,
                        source="deterministic_parser",
                        metadata={"line": call.get("line")},
                    )
                )
        for file_id, routes in (routes_by_file or {}).items():
            source_node_id = file_node_ids.get(file_id)
            if not source_node_id:
                continue
            for route_info in routes:
                route_object_id = stable_id(
                    "route",
                    file_id,
                    route_info.get("method"),
                    route_info.get("path"),
                    route_info.get("line"),
                )
                route_label = f"{route_info.get('method')} {route_info.get('path')}"
                route_node = node(GraphNodeType.ROUTE, route_object_id, route_label, route_info)
                nodes.append(route_node)
                edges.append(
                    GraphEdge(
                        id=stable_id(
                            "edge",
                            source_node_id,
                            route_node.id,
                            EdgeType.DEFINES_ROUTE,
                        ),
                        source_node_id=source_node_id,
                        target_node_id=route_node.id,
                        edge_type=EdgeType.DEFINES_ROUTE,
                        source="route_detector",
                        metadata={
                            "path": route_info.get("path"),
                            "method": route_info.get("method"),
                        },
                    )
                )
                handler = route_info.get("handler")
                handler_node_id = symbol_node_by_name.get((file_id, handler))
                if handler_node_id:
                    edges.append(
                        GraphEdge(
                            id=stable_id(
                                "edge",
                                handler_node_id,
                                route_node.id,
                                EdgeType.HANDLES_ENDPOINT,
                            ),
                            source_node_id=handler_node_id,
                            target_node_id=route_node.id,
                            edge_type=EdgeType.HANDLES_ENDPOINT,
                            source="route_detector",
                            metadata={"handler": handler},
                        )
                    )

        for framework in repo.detected_frameworks:
            framework_node = node(GraphNodeType.FRAMEWORK, framework, framework, {})
            nodes.append(framework_node)
            edges.append(
                edge(repo_node, framework_node, EdgeType.USES_FRAMEWORK, "metadata_detector")
            )

        edges.extend(file_test_edges(files, file_node_ids))

        source_file_by_path = {file.path: file for file in files}
        for obj in knowledge_objects:
            ko_node = node(
                GraphNodeType.KNOWLEDGE_OBJECT,
                obj.id,
                obj.title,
                {"type": obj.type, "language": obj.language, "domain": obj.domain},
            )
            nodes.append(ko_node)
            edges.append(edge(repo_node, ko_node, EdgeType.CONTAINS, "knowledge_compiler"))
            for framework in obj.frameworks:
                framework_node_id = stable_id("node", GraphNodeType.FRAMEWORK, framework)
                edges.append(
                    GraphEdge(
                        id=stable_id(
                            "edge",
                            ko_node.id,
                            framework_node_id,
                            EdgeType.APPLIES_TO_FRAMEWORK,
                        ),
                        source_node_id=ko_node.id,
                        target_node_id=framework_node_id,
                        edge_type=EdgeType.APPLIES_TO_FRAMEWORK,
                        source="knowledge_compiler",
                    )
                )
            path = obj.payload.get("path")
            if isinstance(path, str) and path in source_file_by_path:
                source_node_id = file_node_ids[source_file_by_path[path].id]
                edges.append(
                    GraphEdge(
                        id=stable_id("edge", ko_node.id, source_node_id, EdgeType.DERIVED_FROM),
                        source_node_id=ko_node.id,
                        target_node_id=source_node_id,
                        edge_type=EdgeType.DERIVED_FROM,
                        source="knowledge_compiler",
                    )
                )

        knowledge_node_ids = {
            obj.id: stable_id("node", GraphNodeType.KNOWLEDGE_OBJECT, obj.id)
            for obj in knowledge_objects
        }
        testing_patterns = [obj for obj in knowledge_objects if obj.type == "TestingPattern"]
        for obj in knowledge_objects:
            if obj.type != "ImplementationPattern":
                continue
            for test_obj in testing_patterns:
                if obj.language != test_obj.language:
                    continue
                if obj.domain != test_obj.domain and not obj.payload.get("has_related_test"):
                    continue
                edges.append(
                    GraphEdge(
                        id=stable_id(
                            "edge",
                            knowledge_node_ids[obj.id],
                            knowledge_node_ids[test_obj.id],
                            EdgeType.TESTED_BY,
                        ),
                        source_node_id=knowledge_node_ids[obj.id],
                        target_node_id=knowledge_node_ids[test_obj.id],
                        edge_type=EdgeType.TESTED_BY,
                        source="knowledge_compiler",
                        confidence=0.75,
                        metadata={"domain": obj.domain, "language": obj.language},
                    )
                )

        unique_nodes = {item.id: item for item in nodes}
        unique_edges = {item.id: item for item in edges}
        return list(unique_nodes.values()), list(unique_edges.values())


def node(node_type: GraphNodeType, object_id: str, label: str, metadata: dict) -> GraphNode:
    return GraphNode(
        id=stable_id("node", node_type, object_id),
        node_type=node_type,
        object_id=object_id,
        label=label,
        metadata=metadata,
    )


def edge(source: GraphNode, target: GraphNode, edge_type: EdgeType, source_name: str) -> GraphEdge:
    return GraphEdge(
        id=stable_id("edge", source.id, target.id, edge_type),
        source_node_id=source.id,
        target_node_id=target.id,
        edge_type=edge_type,
        source=source_name,
    )


def file_test_edges(files: list[SourceFile], file_node_ids: dict[str, str]) -> list[GraphEdge]:
    source_files = [file for file in files if not file.is_test]
    test_files = [file for file in files if file.is_test]
    edges: list[GraphEdge] = []
    for source_file in source_files:
        source_stem = stem_key(source_file.path)
        for test_file in test_files:
            if source_stem not in test_file.path.lower():
                continue
            edges.append(
                GraphEdge(
                    id=stable_id(
                        "edge",
                        file_node_ids[source_file.id],
                        file_node_ids[test_file.id],
                        EdgeType.TESTED_BY,
                    ),
                    source_node_id=file_node_ids[source_file.id],
                    target_node_id=file_node_ids[test_file.id],
                    edge_type=EdgeType.TESTED_BY,
                    source="test_linker",
                    confidence=0.7,
                    metadata={"source_path": source_file.path, "test_path": test_file.path},
                )
            )
    return edges


def stem_key(path: str) -> str:
    stem = path.rsplit("/", 1)[-1].rsplit(".", 1)[0].lower()
    return stem.removeprefix("test_").removesuffix("_test")
