import json
import logging
import os
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):

    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "event", record.getMessage()),
        }

        for field in (
            "user_id",
            "thread_id",
            "workflow",
            "duration_ms",
            "status",
            "error_type"
        ):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value

        return json.dumps(payload)


def configure_logging():
    logger = logging.getLogger("ai_hiremind")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

    logger.propagate = False
    return logger


logger = configure_logging()


def log_agent_event(
    event: str,
    user_id: int,
    thread_id: str,
    status: str,
    duration_ms: float | None = None,
    error_type: str | None = None
):
    extra = {
        "event": event,
        "user_id": user_id,
        "thread_id": thread_id,
        "workflow": "recruitment_agent",
        "status": status,
    }

    if duration_ms is not None:
        extra["duration_ms"] = round(duration_ms, 2)

    if error_type:
        extra["error_type"] = error_type

    if status == "error":
        logger.error(event, extra=extra)
    else:
        logger.info(event, extra=extra)


def get_observability_status():
    tracing_enabled = (
        os.getenv("LANGSMITH_TRACING", "").lower() == "true"
        and bool(os.getenv("LANGSMITH_API_KEY"))
    )

    return {
        "application_logging": True,
        "langsmith_tracing_configured": tracing_enabled,
        "langsmith_api_key_present": bool(
            os.getenv("LANGSMITH_API_KEY")
        ),
        "langsmith_project": os.getenv(
            "LANGSMITH_PROJECT",
            "default"
        ),
        "trace_inputs_hidden": (
            os.getenv("LANGSMITH_HIDE_INPUTS", "").lower() == "true"
        ),
        "trace_outputs_hidden": (
            os.getenv("LANGSMITH_HIDE_OUTPUTS", "").lower() == "true"
        ),
        "sensitive_document_content_logged": False
    }