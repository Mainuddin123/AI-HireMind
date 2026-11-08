import os
from contextlib import contextmanager

from dotenv import load_dotenv
from langsmith import Client, tracing_context

load_dotenv()

TRACING_ENABLED = (
    os.getenv("LANGSMITH_TRACING", "").strip().lower() == "true"
    and bool(os.getenv("LANGSMITH_API_KEY"))
)

LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "ai-hiremind")

langsmith_client = None

if TRACING_ENABLED:
    langsmith_client = Client(
        hide_inputs=True,
        hide_outputs=True,
    )


@contextmanager
def langsmith_privacy_context():
    if not TRACING_ENABLED or langsmith_client is None:
        with tracing_context(enabled=False):
            yield
        return

    with tracing_context(
        client=langsmith_client,
        enabled=True,
        project_name=LANGSMITH_PROJECT,
    ):
        yield