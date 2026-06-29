from __future__ import annotations

from collections.abc import Callable
from typing import Any

from repo_wiki.domain.enums import EdgeType, FeedbackStatus, GraphNodeType, KnowledgeType
from repo_wiki.domain.errors import RepositoryNotFound
from repo_wiki.domain.ids import new_id, stable_id
from repo_wiki.domain.models import (
    FeedbackRecord,
    GraphEdge,
    GraphNode,
    KnowledgeObject,
    StagedKnowledge,
)
from repo_wiki.logging import log_event
from repo_wiki.storage.sqlite import SQLiteStore


class ReflexionService:
    def __init__(self, store: SQLiteStore):
        self.store = store

    def submit_feedback(
        self,
        *,
        context_pack_id: str | None,
        accepted: bool | None = None,
        rating: int | None = None,
        tests_passed: bool | None = None,
        lint_passed: bool | None = None,
        build_passed: bool | None = None,
        merged: bool | None = None,
        reviewer_approved: bool | None = None,
        rollback: bool | None = None,
        incident: bool | None = None,
        notes: str | None = None,
    ) -> tuple[FeedbackRecord, StagedKnowledge]:
        feedback = FeedbackRecord(
            id=new_id("fb"),
            context_pack_id=context_pack_id,
            user_rating=rating,
            accepted=accepted,
            tests_passed=tests_passed,
            lint_passed=lint_passed,
            build_passed=build_passed,
            merged=merged,
            reviewer_approved=reviewer_approved,
            rollback=rollback,
            incident=incident,
            notes=notes,
        )
        score = feedback_score(feedback)
        staged = StagedKnowledge(
            id=new_id("stage"),
            source_feedback_id=feedback.id,
            candidate_type=KnowledgeType.IMPLEMENTATION_PATTERN,
            payload={
                "context_pack_id": context_pack_id,
                "accepted": accepted,
                "rating": rating,
                "notes": notes,
                "signals": {
                    "tests_passed": tests_passed,
                    "lint_passed": lint_passed,
                    "build_passed": build_passed,
                    "merged": merged,
                    "reviewer_approved": reviewer_approved,
                    "rollback": rollback,
                    "incident": incident,
                },
            },
            score=score,
            dedupe_key=stable_id("dedupe", context_pack_id, notes or "", rating),
            status=FeedbackStatus.PENDING,
        )
        self.store.save_feedback(feedback)
        self.store.save_staged_knowledge(staged)
        log_event(
            "feedback.submitted",
            feedback_id=feedback.id,
            staged_id=staged.id,
            score=staged.score,
        )
        return feedback, staged

    def list_staged(self, status: str | None = "pending", limit: int = 20) -> list[dict]:
        return self.store.list_feedback(status=status, limit=limit)

    def promote_staged(self, stage_id: str, reason: str | None = None) -> dict:
        staged = self.store.get_staged_knowledge(stage_id)
        if staged is None:
            raise RepositoryNotFound(f"staged knowledge not found: {stage_id}")
        if staged["status"] != FeedbackStatus.PENDING:
            raise ValueError(f"staged knowledge is already {staged['status']}: {stage_id}")
        promoted = promoted_knowledge_object(staged, self.store.get_context_pack)
        self.store.save_knowledge_object(promoted)
        self.store.save_graph(*promotion_graph(stage_id, promoted))
        updated = self.store.update_staged_knowledge_status(
            stage_id,
            status=FeedbackStatus.PROMOTED,
            promotion_reason=reason or "promoted after review",
            promoted_object_id=promoted.id,
        )
        if updated is None:
            raise RepositoryNotFound(f"staged knowledge not found: {stage_id}")
        return updated

    def reject_staged(self, stage_id: str, reason: str | None = None) -> dict:
        staged = self.store.get_staged_knowledge(stage_id)
        if staged is None:
            raise RepositoryNotFound(f"staged knowledge not found: {stage_id}")
        if staged["status"] != FeedbackStatus.PENDING:
            raise ValueError(f"staged knowledge is already {staged['status']}: {stage_id}")
        updated = self.store.update_staged_knowledge_status(
            stage_id,
            status=FeedbackStatus.REJECTED,
            promotion_reason=reason or "rejected after review",
        )
        if updated is None:
            raise RepositoryNotFound(f"staged knowledge not found: {stage_id}")
        return updated


def feedback_score(feedback: FeedbackRecord) -> float:
    score = 0.0
    if feedback.accepted:
        score += 0.25
    if feedback.tests_passed:
        score += 0.20
    if feedback.lint_passed:
        score += 0.15
    if feedback.build_passed:
        score += 0.15
    if feedback.merged:
        score += 0.15
    if feedback.reviewer_approved:
        score += 0.05
    if feedback.rollback is False:
        score += 0.05
    if feedback.incident is False:
        score += 0.05
    if feedback.user_rating:
        score += min(max(feedback.user_rating, 1), 5) / 100
    return round(min(score, 1.0), 4)


def promoted_knowledge_object(
    staged: dict[str, Any],
    get_context_pack: Callable[[str], dict[str, Any] | None],
) -> KnowledgeObject:
    payload = staged.get("payload", {})
    context_pack_id = payload.get("context_pack_id")
    context_pack = get_context_pack(context_pack_id) if context_pack_id else None
    pack_payload = context_pack.get("context_pack", {}) if context_pack else {}
    task = pack_payload.get("task") or "agent implementation feedback"
    citations = pack_payload.get("source_citations", [])
    source_refs = [
        citation["id"]
        for citation in citations
        if isinstance(citation, dict) and citation.get("id")
    ][:8]
    notes = payload.get("notes") or ""
    summary = (
        f"Accepted feedback for `{task}` with score {staged.get('score', 0):.2f}."
        if payload.get("accepted")
        else f"Reviewed feedback for `{task}` with score {staged.get('score', 0):.2f}."
    )
    if notes:
        summary = f"{summary} Reviewer note: {notes[:180]}"
    return KnowledgeObject(
        id=stable_id("ko", "promoted-feedback", staged.get("dedupe_key") or staged["id"]),
        type=staged.get("candidate_type") or KnowledgeType.IMPLEMENTATION_PATTERN,
        title=f"Promoted feedback: {task[:80]}",
        summary=summary,
        problem="Agents need proven implementation guidance from accepted context-pack usage.",
        solution="Prefer guidance that was accepted and backed by objective feedback signals.",
        when_to_use=["When a similar coding task appears in this or a related repository"],
        when_not_to_use=["When feedback was rejected, rolled back, or lacks matching constraints"],
        language=(pack_payload.get("constraints") or {}).get("language"),
        frameworks=[
            framework
            for framework in [(pack_payload.get("constraints") or {}).get("framework")]
            if framework
        ],
        domain=(pack_payload.get("constraints") or {}).get("domain"),
        project_type=(pack_payload.get("constraints") or {}).get("project_type"),
        tags=["feedback-promoted", "reflexion", *(["accepted"] if payload.get("accepted") else [])],
        quality_score=float(staged.get("score") or 0.0),
        confidence=float(staged.get("score") or 0.0),
        source_refs=source_refs,
        payload={
            "source_stage_id": staged["id"],
            "source_feedback_id": staged.get("source_feedback_id"),
            "context_pack_id": context_pack_id,
            "task": task,
            "signals": payload.get("signals", {}),
            "notes": notes,
        },
    )


def promotion_graph(
    stage_id: str,
    promoted: KnowledgeObject,
) -> tuple[list[GraphNode], list[GraphEdge]]:
    stage_node = GraphNode(
        id=stable_id("node", "StagedKnowledge", stage_id),
        node_type="StagedKnowledge",
        object_id=stage_id,
        label=stage_id,
        metadata={"status": "promoted"},
    )
    knowledge_node = GraphNode(
        id=stable_id("node", GraphNodeType.KNOWLEDGE_OBJECT, promoted.id),
        node_type=GraphNodeType.KNOWLEDGE_OBJECT,
        object_id=promoted.id,
        label=promoted.title,
        metadata={"type": promoted.type, "source": "reflexion"},
    )
    return (
        [stage_node, knowledge_node],
        [
            GraphEdge(
                id=stable_id("edge", knowledge_node.id, stage_node.id, EdgeType.PROMOTED_FROM),
                source_node_id=knowledge_node.id,
                target_node_id=stage_node.id,
                edge_type=EdgeType.PROMOTED_FROM,
                source="reflexion_service",
                metadata={"stage_id": stage_id},
            )
        ],
    )
