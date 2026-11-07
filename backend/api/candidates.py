
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.database.connection import get_db
from backend.models.candidate import Candidate
from backend.schemas.candidate import CandidateCreate, CandidateResponse


router = APIRouter(
    prefix="/candidates",
    tags=["Candidate Management"]
)


# Register a candidate
@router.post(
    "/",
    response_model=CandidateResponse,
    status_code=status.HTTP_201_CREATED
)
def create_candidate(
    candidate_data: CandidateCreate,
    db: Session = Depends(get_db)
):

    candidate = Candidate(**candidate_data.model_dump())

    try:
        db.add(candidate)
        db.commit()
        db.refresh(candidate)

        return candidate

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A candidate with this email already exists."
        )


# Retrieve all candidates
@router.get(
    "/",
    response_model=list[CandidateResponse]
)
def get_candidates(db: Session = Depends(get_db)):

    candidates = (
        db.query(Candidate)
        .order_by(Candidate.id.desc())
        .all()
    )

    return candidates
