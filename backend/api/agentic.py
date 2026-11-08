import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from langgraph.types import Command

from backend.database.connection import get_db
from backend.authentication.dependencies import get_current_user

from backend.schemas.agentic import (
    AgenticEvaluationRequest,
    AgenticEvaluationResponse,
    ApprovalRequest,
    MemoryCreateRequest,
    MemoryResponse,
)

from backend.services.agent_memory_service import (
    get_user_memories,
    save_user_memory,
    delete_user_memory,
)

from backend.services.langsmith_tracing import (
    langsmith_privacy_context,
)

from backend.models.agent_review import AgentReview
from agents.recruitment_graph import recruitment_graph
from backend.services.agent_guardrails import validate_agent_inputs


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agentic", tags=["Agentic AI"])


# --------------------------------------------------
# AUTHORIZATION HELPERS
# --------------------------------------------------

def require_recruiter_or_admin(current_user):
    if current_user.role not in ("recruiter", "admin"):
        raise HTTPException(
            status_code=403,
            detail="Recruiter or admin access required."
        )


def make_thread_id(user_id: int, client_thread_id: str) -> str:
    return f"user-{user_id}:{client_thread_id}"


def get_graph_config(thread_id: str):
    return {
        "configurable": {
            "thread_id": thread_id
        },
        "recursion_limit": 12
    }


# --------------------------------------------------
# CHECKPOINT DIAGNOSTICS
# --------------------------------------------------

def log_checkpoint_state(label: str, user_id: int, thread_id: str):
    try:
        snapshot = recruitment_graph.get_state(
            get_graph_config(thread_id)
        )

        if snapshot is None:
            logger.warning(
                "%s | No checkpoint found | user_id=%s | thread_id=%s",
                label,
                user_id,
                thread_id
            )
            return None

        configurable = snapshot.config.get("configurable", {})

        logger.info(
            "%s | user_id=%s | thread_id=%s | next=%s | "
            "checkpoint_id=%s | values=%s",
            label,
            user_id,
            thread_id,
            snapshot.next,
            configurable.get("checkpoint_id"),
            list(snapshot.values.keys())
        )

        return snapshot

    except Exception:
        logger.exception(
            "%s | Checkpoint inspection failed | user_id=%s | thread_id=%s",
            label,
            user_id,
            thread_id
        )
        raise


# --------------------------------------------------
# AGENTIC CANDIDATE EVALUATION
# --------------------------------------------------

@router.post(
    "/evaluate",
    response_model=AgenticEvaluationResponse
)
def evaluate_with_agents(
    request: AgenticEvaluationRequest,
    current_user=Depends(get_current_user)
):
    require_recruiter_or_admin(current_user)

    try:
        guarded = validate_agent_inputs(
            request.resume_text,
            request.job_description
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc)
        )

    client_thread_id = request.thread_id or str(uuid4())

    thread_id = make_thread_id(
        current_user.id,
        client_thread_id
    )

    initial_state = {
        "user_id": current_user.id,
        "thread_id": client_thread_id,
        "job_title": request.job_title,
        "resume_text": guarded.resume_text,
        "job_description": guarded.job_description,
        "candidate_experience_years": (
            request.candidate_experience_years
        ),
        "guardrail_warnings": guarded.warnings,
    }

    try:
        # LangSmith privacy context applies to the root graph
        # and its nested LangGraph executions.
        with langsmith_privacy_context():
            result = recruitment_graph.invoke(
                initial_state,
                config=get_graph_config(thread_id)
            )

        snapshot = log_checkpoint_state(
            "EVALUATION CHECKPOINT",
            current_user.id,
            thread_id
        )

    except Exception:
        logger.exception(
            "Agent workflow failed for user_id=%s",
            current_user.id
        )

        raise HTTPException(
            status_code=502,
            detail="Agent workflow failed. Check server logs."
        )

    if result.get("__interrupt__"):

        analysis = result.get("analysis") or {}

        analysis["guardrail_warnings"] = guarded.warnings

        return {
            "thread_id": client_thread_id,
            "status": "awaiting_human_review",
            "analysis": analysis
        }

    logger.error(
        "Workflow did not interrupt | user_id=%s | thread_id=%s | next=%s",
        current_user.id,
        thread_id,
        snapshot.next if snapshot else None
    )

    raise HTTPException(
        status_code=500,
        detail="Workflow ended without reaching the review checkpoint."
    )


# --------------------------------------------------
# HUMAN APPROVAL / REJECTION
# --------------------------------------------------

@router.post("/approve")
def approve_agentic_evaluation(
    request: ApprovalRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_recruiter_or_admin(current_user)

    thread_id = make_thread_id(
        current_user.id,
        request.thread_id
    )

    config = get_graph_config(thread_id)

    decision = (
        "approved"
        if request.approved
        else "rejected"
    )

    # --------------------------------------------------
    # 1. INSPECT GRAPH CHECKPOINT
    # --------------------------------------------------

    try:
        graph_state = log_checkpoint_state(
            "APPROVAL CHECKPOINT",
            current_user.id,
            thread_id
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to inspect evaluation checkpoint."
        )

    if graph_state is None:
        raise HTTPException(
            status_code=404,
            detail="Evaluation checkpoint not found."
        )

    if "human_review" not in graph_state.next:
        logger.warning(
            "Approval rejected because graph is not awaiting review. "
            "user_id=%s thread_id=%s next=%s",
            current_user.id,
            thread_id,
            graph_state.next
        )

        raise HTTPException(
            status_code=409,
            detail={
                "message": "This evaluation is not awaiting human review.",
                "thread_id": request.thread_id,
                "next_nodes": list(graph_state.next)
            }
        )

    # --------------------------------------------------
    # 2. CHECK EXISTING AUDIT RECORD
    # --------------------------------------------------

    audit = db.query(AgentReview).filter(
        AgentReview.thread_id == thread_id,
        AgentReview.reviewer_id == current_user.id
    ).first()

    if audit and audit.status == "completed":
        raise HTTPException(
            status_code=409,
            detail="A review decision has already been completed."
        )

    if audit and audit.status == "pending":
        raise HTTPException(
            status_code=409,
            detail="A review decision is already being processed."
        )

    # --------------------------------------------------
    # 3. SAVE REVIEW INTENT
    # --------------------------------------------------

    try:
        if audit and audit.status == "failed":
            audit.decision = decision
            audit.comment = request.comment or None
            audit.status = "pending"

        else:
            audit = AgentReview(
                reviewer_id=current_user.id,
                thread_id=thread_id,
                decision=decision,
                status="pending",
                comment=request.comment or None
            )

            db.add(audit)

        db.commit()
        db.refresh(audit)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="A review record already exists for this evaluation."
        )

    except Exception:
        db.rollback()

        logger.exception(
            "Unable to create review audit for user_id=%s",
            current_user.id
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to record the review decision."
        )

    # --------------------------------------------------
    # 4. RESUME LANGGRAPH WITH PRIVACY PROTECTION
    # --------------------------------------------------

    try:
        with langsmith_privacy_context():
            result = recruitment_graph.invoke(
                Command(
                    resume={
                        "approved": request.approved,
                        "reviewer_id": current_user.id,
                        "comment": request.comment
                    }
                ),
                config=config
            )

    except Exception:
        logger.exception(
            "Unable to resume review for user_id=%s",
            current_user.id
        )

        try:
            audit.status = "failed"
            db.commit()

        except Exception:
            db.rollback()

            logger.exception(
                "Unable to update failed review audit."
            )

        raise HTTPException(
            status_code=409,
            detail="Workflow resumption failed. Review audit requires recovery."
        )

    # --------------------------------------------------
    # 5. VERIFY WORKFLOW RESULT
    # --------------------------------------------------

    if result.get("__interrupt__"):
        audit.status = "failed"
        db.commit()

        raise HTTPException(
            status_code=409,
            detail="Workflow interrupted again instead of completing review."
        )

    returned_decision = result.get("approval_status")

    if returned_decision != decision:
        audit.status = "failed"
        db.commit()

        raise HTTPException(
            status_code=500,
            detail="Graph decision does not match the submitted review."
        )

    # --------------------------------------------------
    # 6. COMPLETE AUDIT
    # --------------------------------------------------

    try:
        audit.status = "completed"
        db.commit()
        db.refresh(audit)

    except Exception:
        db.rollback()

        logger.exception(
            "Workflow resumed but audit completion failed for user_id=%s",
            current_user.id
        )

        raise HTTPException(
            status_code=500,
            detail="Workflow completed but audit completion failed."
        )

    return {
        "thread_id": request.thread_id,
        "approval_status": returned_decision,
        "reviewer_id": current_user.id,
        "audit_status": audit.status,
        "message": "Human review decision recorded successfully."
    }


# --------------------------------------------------
# RECRUITER MEMORY — LIST
# --------------------------------------------------

@router.get(
    "/memories",
    response_model=list[MemoryResponse]
)
def list_memories(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_recruiter_or_admin(current_user)

    try:
        return get_user_memories(
            db,
            current_user.id
        )

    except Exception:
        logger.exception(
            "Memory retrieval failed for user_id=%s",
            current_user.id
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve recruiter memories."
        )


# --------------------------------------------------
# RECRUITER MEMORY — CREATE / UPDATE
# --------------------------------------------------

@router.post(
    "/memories",
    status_code=201
)
def create_or_update_memory(
    request: MemoryCreateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_recruiter_or_admin(current_user)

    try:
        save_user_memory(
            db,
            current_user.id,
            request.memory_type,
            request.memory_key,
            request.memory_value
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception:
        db.rollback()

        logger.exception(
            "Memory save failed for user_id=%s",
            current_user.id
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to save recruiter memory."
        )

    return {
        "message": "Memory saved successfully."
    }


# --------------------------------------------------
# RECRUITER MEMORY — DELETE
# --------------------------------------------------

@router.delete(
    "/memories/{memory_type}/{memory_key}"
)
def remove_memory(
    memory_type: str,
    memory_key: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_recruiter_or_admin(current_user)

    try:
        deleted = delete_user_memory(
            db,
            current_user.id,
            memory_type,
            memory_key
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception:
        db.rollback()

        logger.exception(
            "Memory deletion failed for user_id=%s",
            current_user.id
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to delete recruiter memory."
        )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Memory not found."
        )

    return {
        "message": "Memory deleted successfully."
    }