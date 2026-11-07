
from sqlalchemy import select
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from backend.models.agent_memory import AgentMemory


ALLOWED_MEMORY_TYPES = {
    "recruiter_preference",
    "approved_knowledge"
}


def validate_memory_type(memory_type: str) -> None:
    if memory_type not in ALLOWED_MEMORY_TYPES:
        raise ValueError("Unsupported memory type.")


def get_user_memories(
    db: Session,
    user_id: int,
    memory_type: str | None = None
) -> list[dict]:

    if memory_type is not None:
        validate_memory_type(memory_type)

    statement = select(AgentMemory).where(
        AgentMemory.user_id == user_id
    )

    if memory_type:
        statement = statement.where(
            AgentMemory.memory_type == memory_type
        )

    records = db.scalars(statement).all()

    return [
        {
            "memory_type": item.memory_type,
            "memory_key": item.memory_key,
            "memory_value": item.memory_value
        }
        for item in records
    ]


def save_user_memory(
    db: Session,
    user_id: int,
    memory_type: str,
    memory_key: str,
    memory_value: dict
) -> None:

    validate_memory_type(memory_type)

    if not memory_key or not memory_key.strip():
        raise ValueError("Memory key cannot be empty.")

    if not isinstance(memory_value, dict):
        raise ValueError("Memory value must be a JSON object.")

    statement = insert(AgentMemory).values(
        user_id=user_id,
        memory_type=memory_type,
        memory_key=memory_key.strip(),
        memory_value=memory_value
    )

    statement = statement.on_duplicate_key_update(
        memory_value=statement.inserted.memory_value
    )

    db.execute(statement)
    db.commit()


def delete_user_memory(
    db: Session,
    user_id: int,
    memory_type: str,
    memory_key: str
) -> bool:

    validate_memory_type(memory_type)

    record = db.scalar(
        select(AgentMemory).where(
            AgentMemory.user_id == user_id,
            AgentMemory.memory_type == memory_type,
            AgentMemory.memory_key == memory_key
        )
    )

    if record is None:
        return False

    db.delete(record)
    db.commit()

    return True
