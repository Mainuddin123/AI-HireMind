
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    status
)
from pydantic import TypeAdapter, EmailStr, ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.authentication.dependencies import (
    get_current_user,
    require_role
)
from backend.models.application import Application
from backend.models.job import Job
from backend.models.candidate import Candidate
from backend.schemas.application import (
    ApplicationStatus,
    ApplicationStatusUpdate,
    PublicApplicationResponse,
    ApplicationResponse,
    RecruiterApplicationResponse
)
from backend.services.application_service import ApplicationService


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/applications",
    tags=["Application Management"]
)

# Resume storage configuration
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESUME_DIR = PROJECT_ROOT / "uploads" / "resumes"

MAX_RESUME_SIZE = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt"
}


# PUBLIC: Submit an application without candidate login
@router.post(
    "/public/{job_id}/apply",
    response_model=PublicApplicationResponse,
    status_code=status.HTTP_201_CREATED
)
async def public_apply_for_job(
    job_id: int,
    full_name: str = Form(..., min_length=2, max_length=150),
    email: str = Form(...),
    phone: str = Form(..., min_length=7, max_length=20),
    location: str | None = Form(None, max_length=150),
    resume: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    # Validate email
    try:
        validated_email = TypeAdapter(EmailStr).validate_python(email)
        normalized_email = str(validated_email).lower().strip()

    except ValidationError:
        raise HTTPException(
            status_code=422,
            detail="Please provide a valid email address."
        )

    # Check active job
    job = ApplicationService.get_active_job(db, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found or no longer active."
        )

    # Validate resume extension
    extension = Path(resume.filename or "").suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX and TXT resumes are supported."
        )

    # Read and validate file size
    try:
        content = await resume.read(MAX_RESUME_SIZE + 1)

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded resume is empty."
            )

        if len(content) > MAX_RESUME_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Resume must not exceed 5 MB."
            )

        # Find existing candidate
        candidate = ApplicationService.get_candidate_by_email(
            db,
            normalized_email
        )

        # Prevent duplicate applications
        if candidate:
            existing_application = (
                ApplicationService.has_already_applied(
                    db,
                    candidate.id,
                    job_id
                )
            )

            if existing_application:
                raise HTTPException(
                    status_code=409,
                    detail="You have already applied for this job."
                )

        # Store resume
        RESUME_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        filename = f"{uuid4().hex}{extension}"
        file_path = RESUME_DIR / filename

        relative_path = Path("uploads") / "resumes" / filename

        file_saved = False

        try:
            file_path.write_bytes(content)
            file_saved = True

            # Create or update candidate
            if candidate is None:
                candidate = Candidate(
                    full_name=full_name.strip(),
                    email=normalized_email,
                    phone=phone.strip(),
                    location=(
                        location.strip() if location else None
                    ),
                    resume_path=str(relative_path)
                )

                db.add(candidate)
                db.flush()

            else:
                candidate.full_name = full_name.strip()
                candidate.phone = phone.strip()

                if location:
                    candidate.location = location.strip()

                candidate.resume_path = str(relative_path)

            # Create application
            application = Application(
                candidate_id=candidate.id,
                job_id=job_id,
                status=ApplicationStatus.APPLIED.value
            )

            db.add(application)

            db.commit()
            db.refresh(application)

        except IntegrityError as exc:
            db.rollback()

            if file_saved:
                file_path.unlink(missing_ok=True)

            logger.warning(
                "Duplicate or database constraint error for job_id=%s",
                job_id,
                exc_info=True
            )

            raise HTTPException(
                status_code=409,
                detail="An application for this job already exists."
            ) from exc

        except Exception:
            db.rollback()

            if file_saved:
                file_path.unlink(missing_ok=True)

            logger.exception(
                "Public application submission failed for job_id=%s",
                job_id
            )

            raise HTTPException(
                status_code=500,
                detail="Unable to submit application. Please try again."
            )

    finally:
        await resume.close()

    return PublicApplicationResponse(
        message="Application submitted successfully.",
        application_id=application.id,
        job_id=job_id,
        status=ApplicationStatus.APPLIED
    )


# CANDIDATE: View own applications
@router.get(
    "/my-applications",
    response_model=list[ApplicationResponse]
)
def get_my_applications(
    db: Session = Depends(get_db),
    current_user=Depends(require_role("candidate"))
):
    candidate = ApplicationService.get_candidate_by_email(
        db,
        current_user.email
    )

    if not candidate:
        return []

    return ApplicationService.get_candidate_applications(
        db,
        candidate.id
    )


# RECRUITER: View applications for owned jobs
@router.get(
    "/job/{job_id}",
    response_model=list[RecruiterApplicationResponse]
)
def get_job_applications(
    job_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("recruiter"))
):
    job = db.query(Job).filter(
        Job.id == job_id,
        Job.recruiter_id == current_user.id
    ).first()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found or access denied."
        )

    results = ApplicationService.get_job_applications(
        db,
        job_id
    )

    return [
        RecruiterApplicationResponse(
            id=application.id,
            candidate_id=candidate.id,
            job_id=application.job_id,
            status=application.status,
            created_at=application.created_at,
            candidate_name=candidate.full_name,
            candidate_email=candidate.email,
            candidate_phone=candidate.phone
        )
        for application, candidate in results
    ]


# RECRUITER / ADMIN: Update application status
@router.patch(
    "/{application_id}/status",
    response_model=ApplicationResponse
)
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if current_user.role not in ("recruiter", "admin"):
        raise HTTPException(
            status_code=403,
            detail="Only recruiters and admins can update application status."
        )

    application = db.query(Application).filter(
        Application.id == application_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found."
        )

    if current_user.role == "recruiter":
        job = db.query(Job).filter(
            Job.id == application.job_id,
            Job.recruiter_id == current_user.id
        ).first()

        if not job:
            raise HTTPException(
                status_code=403,
                detail="You cannot update applications for this job."
            )

    return ApplicationService.update_application_status(
        db,
        application,
        payload.status
    )
