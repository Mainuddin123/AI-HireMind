
from sqlalchemy.orm import Session

from backend.models.application import Application
from backend.models.candidate import Candidate
from backend.models.job import Job
from backend.schemas.application import ApplicationStatus


class ApplicationService:

    # Get an active job
    @staticmethod
    def get_active_job(db: Session, job_id: int):
        return db.query(Job).filter(
            Job.id == job_id,
            Job.is_active.is_(True)
        ).first()

    # Find candidate using email
    @staticmethod
    def get_candidate_by_email(db: Session, email: str):
        return db.query(Candidate).filter(
            Candidate.email == email.strip().lower()
        ).first()

    # Check duplicate applications
    @staticmethod
    def has_already_applied(
        db: Session,
        candidate_id: int,
        job_id: int
    ):
        return db.query(Application).filter(
            Application.candidate_id == candidate_id,
            Application.job_id == job_id
        ).first()

    # Get candidate's applications
    @staticmethod
    def get_candidate_applications(
        db: Session,
        candidate_id: int
    ):
        return (
            db.query(Application)
            .filter(Application.candidate_id == candidate_id)
            .order_by(Application.created_at.desc())
            .all()
        )

    # Get applications with candidate details
    @staticmethod
    def get_job_applications(
        db: Session,
        job_id: int
    ):
        return (
            db.query(Application, Candidate)
            .join(
                Candidate,
                Application.candidate_id == Candidate.id
            )
            .filter(Application.job_id == job_id)
            .order_by(Application.created_at.desc())
            .all()
        )

    # Update application status
    @staticmethod
    def update_application_status(
        db: Session,
        application: Application,
        new_status: ApplicationStatus
    ):
        application.status = new_status.value

        db.commit()
        db.refresh(application)

        return application
