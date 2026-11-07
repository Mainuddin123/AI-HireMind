
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from sqlalchemy.orm import Session

from backend.database.connection import SessionLocal
from backend.authentication.dependencies import (
    get_current_user,
    require_role
)
from backend.schemas.job import JobCreate, JobResponse
from backend.services.job_service import (
    create_job,
    get_active_jobs,
    get_job_by_id
)


router = APIRouter(
    prefix="/jobs",
    tags=["Job Management"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# PUBLIC: List active jobs
@router.get(
    "/public",
    response_model=list[JobResponse]
)
def public_list_jobs(
    db: Session = Depends(get_db)
):
    return get_active_jobs(db)


# PUBLIC: View an individual active job
@router.get(
    "/public/{job_id}",
    response_model=JobResponse
)
def public_job_details(
    job_id: int,
    db: Session = Depends(get_db)
):
    job = get_job_by_id(db, job_id)

    if not job or not job.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or no longer accepting applications."
        )

    return job


# RECRUITER / ADMIN: Create job
@router.post(
    "/",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED
)
def create_job_endpoint(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role("recruiter", "admin")
    )
):
    return create_job(
        db,
        job_data,
        current_user.id
    )


# AUTHENTICATED: List active jobs
@router.get(
    "/",
    response_model=list[JobResponse]
)
def list_jobs(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return get_active_jobs(db)


# AUTHENTICATED: View job details
@router.get(
    "/{job_id}",
    response_model=JobResponse
)
def job_details(
    job_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    job = get_job_by_id(db, job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    return job
