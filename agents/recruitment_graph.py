
import os
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
# 1. CONFIGURABLE SQLITE CHECKPOINT DATABASE
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_STORAGE_DIR = PROJECT_ROOT / "backend" / "storage"
DEFAULT_STORAGE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_CHECKPOINT_PATH = (
    DEFAULT_STORAGE_DIR / "agent_checkpoints.sqlite"
)

configured_path = os.getenv("LANGGRAPH_CHECKPOINT_PATH")

if configured_path:
    CHECKPOINT_PATH = Path(configured_path).expanduser()

    if not CHECKPOINT_PATH.is_absolute():
        CHECKPOINT_PATH = PROJECT_ROOT / CHECKPOINT_PATH
else:
    CHECKPOINT_PATH = DEFAULT_CHECKPOINT_PATH

CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)

sqlite_connection = sqlite3.connect(
    str(CHECKPOINT_PATH),
    check_same_thread=False,
    timeout=30,
)

# Enable SQLite write-ahead logging.
sqlite_connection.execute("PRAGMA journal_mode=WAL")
sqlite_connection.execute("PRAGMA synchronous=FULL")
sqlite_connection.execute("PRAGMA busy_timeout=30000")

checkpointer = SqliteSaver(sqlite_connection)
checkpointer.setup()


# --------------------------------------------------
# 2. BUILD RECRUITMENT GRAPH
# --------------------------------------------------

def build_recruitment_graph():

    builder = StateGraph(RecruitmentState)

    builder.add_node("memory_retrieval", memory_retrieval_node)
    builder.add_node("resume_analysis", resume_analysis_node)
    builder.add_node("job_analysis", job_analysis_node)
    builder.add_node("matching", matching_node)
    builder.add_node("explanation", explanation_node)
    builder.add_node("human_review", human_review_node)

    # Workflow execution order
    builder.add_edge(START, "memory_retrieval")
    builder.add_edge("memory_retrieval", "resume_analysis")
    builder.add_edge("resume_analysis", "job_analysis")
    builder.add_edge("job_analysis", "matching")
    builder.add_edge("matching", "explanation")
    builder.add_edge("explanation", "human_review")
    builder.add_edge("human_review", END)

    return builder.compile(checkpointer=checkpointer)


# --------------------------------------------------
# 3. CREATE GRAPH INSTANCE
# --------------------------------------------------

recruitment_graph = build_recruitment_graph()
