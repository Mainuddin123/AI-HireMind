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
    return {
        "application_logging": True,
        "langsmith_tracing_configured": (
            os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"
            and bool(os.getenv("LANGCHAIN_API_KEY"))
        ),
        "langsmith_project": os.getenv(
            "LANGCHAIN_PROJECT",
            "ai-hiremind"
        ),
        "sensitive_document_content_logged": False
    }
