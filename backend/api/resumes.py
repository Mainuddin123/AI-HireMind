
import re

from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    UploadFile,
    HTTPException
)

from sqlalchemy.orm import Session

from backend.database.connection import get_db
from backend.authentication.dependencies import get_current_user

from backend.models.candidate import Candidate
from backend.models.recruiter_resume import RecruiterResume

from backend.schemas.resume import (
    ResumeAnalysisResponse,
    RecruiterResumeUploadResponse
)

from backend.services.resume_service import (
    process_resume,
    delete_resume_file
)

from backend.services.resume_parser import analyze_resume


router = APIRouter(
    prefix="/resumes",
    tags=["Resume Intelligence"]
)


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def get_user_role(current_user):

    return getattr(
        current_user.role,
        "value",
        current_user.role
    )


def validate_candidate_identity(analysis: dict):

    full_name = analysis.get("full_name")
    email = analysis.get("email")

    if not full_name or len(full_name.strip()) < 2:

        raise HTTPException(
            status_code=422,
            detail=(
                "Candidate name could not be extracted. "
                "Please upload a resume with a clearly visible name."
            )
        )

    if not email:

        raise HTTPException(
            status_code=422,
            detail=(
                "Candidate email could not be extracted. "
                "Please upload a resume containing a valid email address."
            )
        )

    email = email.strip().lower()

    if not re.fullmatch(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        email
    ):

        raise HTTPException(
            status_code=422,
            detail="The extracted candidate email is invalid."
        )

    return {
        "full_name": full_name.strip(),
        "email": email,
        "phone": analysis.get("phone"),
        "location": analysis.get("location")
    }


# ==================================================
# 1. CANDIDATE RESUME UPLOAD
# ==================================================

@router.post(
    "/upload",
    response_model=ResumeAnalysisResponse
)
async def upload_resume(

    full_name: str = Form(
        ...,
        min_length=2,
        max_length=150
    ),

    file: UploadFile = File(...),

    phone: str | None = Form(None),

    location: str | None = Form(None),

    current_user=Depends(get_current_user),

    db: Session = Depends(get_db)
):

    if get_user_role(current_user) != "candidate":

        raise HTTPException(
            status_code=403,
            detail="Only candidates can upload resumes."
        )

    resume_path = None

    try:

        extracted_text, resume_path = await process_resume(file)

        analysis = analyze_resume(extracted_text)

        candidate = db.query(Candidate).filter(
            Candidate.email == current_user.email
        ).first()

        if candidate is None:

            candidate = Candidate(
                full_name=full_name.strip(),
                email=current_user.email,
                phone=phone,
                location=location
            )

            db.add(candidate)
            db.flush()

        else:

            candidate.full_name = full_name.strip()

            if phone is not None:
                candidate.phone = phone

            if location is not None:
                candidate.location = location

        candidate.resume_path = resume_path

        db.commit()
        db.refresh(candidate)

        return ResumeAnalysisResponse(
            message="Resume uploaded and analyzed successfully.",
            candidate_id=candidate.id,
            filename=Path(file.filename or "resume").name,
            extracted_text_length=len(extracted_text),
            skills=analysis["skills"],
            experience_years=analysis["experience_years"],
            education=analysis["education"],
            resume_path=resume_path
        )

    except HTTPException:
        db.rollback()

        if resume_path:
            delete_resume_file(resume_path)

        raise

    except Exception as exc:

        db.rollback()

        if resume_path:
            delete_resume_file(resume_path)

        raise HTTPException(
            status_code=500,
            detail="Unable to save candidate resume information."
        ) from exc


# ==================================================
# 2. RECRUITER RESUME UPLOAD
# AUTOMATIC CANDIDATE IDENTITY EXTRACTION
# ==================================================

@router.post(
    "/recruiter-upload",
    response_model=RecruiterResumeUploadResponse
)
async def recruiter_upload_resume(

    file: UploadFile = File(...),

    current_user=Depends(get_current_user),

    db: Session = Depends(get_db)
):

    if get_user_role(current_user) not in ("recruiter", "admin"):

        raise HTTPException(
            status_code=403,
            detail="Recruiter or admin access required."
        )

    resume_path = None
    old_path = None

    try:

        # ------------------------------------------
        # STEP 1: Extract document text
        # ------------------------------------------

        extracted_text, resume_path = await process_resume(file)

        if not extracted_text.strip():

            raise HTTPException(
                status_code=422,
                detail="No readable text found in the uploaded resume."
            )

        # ------------------------------------------
        # STEP 2: Analyze candidate resume
        # ------------------------------------------

        analysis = analyze_resume(extracted_text)

        identity = validate_candidate_identity(analysis)

        candidate_name = identity["full_name"]
        candidate_email = identity["email"]
        candidate_phone = identity["phone"]
        candidate_location = identity["location"]

        # ------------------------------------------
        # STEP 3: Find or create candidate
        # ------------------------------------------

        candidate = db.query(Candidate).filter(
            Candidate.email == candidate_email
        ).first()

        if candidate is None:

            candidate = Candidate(
                full_name=candidate_name,
                email=candidate_email,
                phone=candidate_phone,
                location=candidate_location
            )

            db.add(candidate)
            db.flush()

        else:

            candidate.full_name = candidate_name

            if candidate_phone:
                candidate.phone = candidate_phone

            if candidate_location:
                candidate.location = candidate_location

        # ------------------------------------------
        # STEP 4: Save recruiter resume record
        # ------------------------------------------

        upload_record = db.query(RecruiterResume).filter(
            RecruiterResume.recruiter_id == current_user.id,
            RecruiterResume.candidate_id == candidate.id
        ).first()

        if upload_record is None:

            upload_record = RecruiterResume(
                recruiter_id=current_user.id,
                candidate_id=candidate.id,
                filename=Path(file.filename or "resume").name,
                resume_path=resume_path,
                extracted_text=extracted_text,
                skills=analysis["skills"],
                experience_years=analysis["experience_years"],
                education=analysis["education"]
            )

            db.add(upload_record)

        else:

            old_path = upload_record.resume_path

            upload_record.filename = Path(
                file.filename or "resume"
            ).name

            upload_record.resume_path = resume_path

            upload_record.extracted_text = extracted_text

            upload_record.skills = analysis["skills"]

            upload_record.experience_years = analysis[
                "experience_years"
            ]

            upload_record.education = analysis["education"]

        # ------------------------------------------
        # STEP 5: Commit database changes
        # ------------------------------------------

        db.commit()
        db.refresh(candidate)

        # Delete previous file only after successful commit.
        if old_path and old_path != resume_path:
            delete_resume_file(old_path)

        # ------------------------------------------
        # STEP 6: Return extracted candidate profile
        # ------------------------------------------

        return RecruiterResumeUploadResponse(
            message=(
                "Resume uploaded and candidate "
                "details extracted successfully."
            ),

            candidate_id=candidate.id,

            full_name=candidate_name,

            candidate_email=candidate_email,

            phone=candidate_phone,

            location=candidate_location,

            filename=Path(file.filename or "resume").name,

            extracted_text=extracted_text,

            extracted_text_length=len(extracted_text),

            skills=analysis["skills"],

            experience_years=analysis["experience_years"],

            education=analysis["education"]
        )

    except HTTPException:

        db.rollback()

        if resume_path:
            delete_resume_file(resume_path)

        raise

    except Exception as exc:

        db.rollback()

        if resume_path:
            delete_resume_file(resume_path)

        raise HTTPException(
            status_code=500,
            detail="Unable to process and save recruiter resume."
        ) from exc
