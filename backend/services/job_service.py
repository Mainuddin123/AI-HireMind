
from sqlalchemy.orm import Session

from backend.models.job import Job
from backend.schemas.job import JobCreate


def create_job(
    db: Session,
    job_data: JobCreate,
    recruiter_id: int
) -> Job:

    new_job = Job(
        recruiter_id=recruiter_id,
        **job_data.model_dump()
    )

    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return new_job


def get_active_jobs(db: Session):
    return (
        db.query(Job)
        .filter(Job.is_active == True)
        .order_by(Job.created_at.desc())
        .all()
    )


def get_job_by_id(db: Session, job_id: int):
    return (
        db.query(Job)
        .filter(
            Job.id == job_id,
            Job.is_active == True
        )
        .first()
    )
