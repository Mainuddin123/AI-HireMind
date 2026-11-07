
from fastapi import FastAPI

from backend.config import settings
from backend.database.connection import engine, Base

# Import database models
from backend.models.candidate import Candidate
from backend.models.user import User
from backend.models.job import Job
from backend.models.application import Application
from backend.models.agent_memory import AgentMemory
from backend.models.agent_review import AgentReview

# Import API routers
from backend.api.candidates import router as candidate_router
from backend.api.auth import router as auth_router
from backend.api.jobs import router as job_router
from backend.api.applications import router as application_router
from backend.api.resumes import router as resume_router
from backend.api.job_descriptions import router as job_description_router
from backend.api.matching import router as matching_router
from backend.api.skills import router as skill_router
from backend.api.evaluation import router as evaluation_router
from backend.api.agentic import router as agentic_router
from backend.api.interviews import router as interview_router


# Initialize FastAPI
app = FastAPI(
    title=settings.app_name,
    description="Evidence-Driven Agentic AI Recruitment Intelligence Platform",
    version="1.0.0",
    debug=settings.debug
)


# Create database tables
Base.metadata.create_all(bind=engine)


# Register API routers
app.include_router(candidate_router)
app.include_router(auth_router)
app.include_router(job_router)
app.include_router(application_router)
app.include_router(resume_router)
app.include_router(job_description_router)
app.include_router(matching_router)
app.include_router(skill_router)
app.include_router(evaluation_router)
app.include_router(agentic_router)
app.include_router(interview_router)


@app.get("/")
def root():
    return {
        "project": settings.app_name,
        "environment": settings.app_env,
        "status": "Running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name
    }
