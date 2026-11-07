
import sqlite3
from pathlib import Path

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver

from agents.recruitment_state import RecruitmentState

from agents.recruitment_nodes import (
    memory_retrieval_node,
    resume_analysis_node,
    job_analysis_node,
    matching_node,
    explanation_node,
    human_review_node,
)


# --------------------------------------------------
# 1. SQLITE CHECKPOINT DATABASE
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

STORAGE_DIR = PROJECT_ROOT / "backend" / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

CHECKPOINT_PATH = STORAGE_DIR / "agent_checkpoints.sqlite"

sqlite_connection = sqlite3.connect(
    str(CHECKPOINT_PATH),
    check_same_thread=False,
    timeout=30,
)

checkpointer = SqliteSaver(sqlite_connection)

# Create checkpoint tables if they do not exist.
checkpointer.setup()


# --------------------------------------------------
# 2. BUILD RECRUITMENT GRAPH
# --------------------------------------------------

def build_recruitment_graph():

    builder = StateGraph(RecruitmentState)

    # Register workflow nodes
    builder.add_node(
        "memory_retrieval",
        memory_retrieval_node
    )

    builder.add_node(
        "resume_analysis",
        resume_analysis_node
    )

    builder.add_node(
        "job_analysis",
        job_analysis_node
    )

    builder.add_node(
        "matching",
        matching_node
    )

    builder.add_node(
        "explanation",
        explanation_node
    )

    builder.add_node(
        "human_review",
        human_review_node
    )

    # --------------------------------------------------
    # 3. DEFINE EXECUTION ORDER
    # --------------------------------------------------

    builder.add_edge(
        START,
        "memory_retrieval"
    )

    builder.add_edge(
        "memory_retrieval",
        "resume_analysis"
    )

    builder.add_edge(
        "resume_analysis",
        "job_analysis"
    )

    builder.add_edge(
        "job_analysis",
        "matching"
    )

    builder.add_edge(
        "matching",
        "explanation"
    )

    builder.add_edge(
        "explanation",
        "human_review"
    )

    builder.add_edge(
        "human_review",
        END
    )

    # Compile graph with persistent checkpointing
    return builder.compile(
        checkpointer=checkpointer
    )


# --------------------------------------------------
# 4. CREATE GRAPH INSTANCE
# --------------------------------------------------

recruitment_graph = build_recruitment_graph()
